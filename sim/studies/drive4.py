# -*- coding: utf-8 -*-
"""실험 ④ — '평가자를 늘린다'의 현실적 수단: 다면평가 비중 확대
   현행 모형은 다면평가를 순수 잡음(92+4z)으로 두어 실력정보가 0이었다.
   여기서는 다면을 k명의 동료 평가자로 모형화한다.
     동료 신호 = (1-fp)*실력 + fp*선호_동료 + N(0, sp^2),  k명 평균 후 순위기반 표준화
   비교 기준: 1차:2차 비율 조정(60:40 vs 50:50)의 효과와 같은 눈금으로 읽는다."""
import random, math, statistics as st
from core import *
from drive1 import build

def run(org, w1, s1n, s2n, w_multi, k_peer, sp, fp, mode="reform",
        reps=400, gap=0.0, adj=0.0, seed=20260910, ideal=False, peer_signal=True):
    rng=random.Random(seed); w2=1.0-w1
    w_core=1.0-w_multi-W_COMMON
    M=[]
    for _ in range(reps):
        people,dmem,hmem,dty,hty=build(org,rng,gap)
        n=len(people); ab=[p["a"] for p in people]
        if ideal:
            tot=[TARGET_MEAN+TARGET_SD*p["a"] for p in people]
        else:
            sg1={}; sg2={}; sgp={}
            for i,p in enumerate(people):
                f1=FAVOR[dty[p["d"]]]; f2=FAVOR[hty[p["h"]]]
                sg1[i]=(1-f1)*p["a"]+f1*p["f"]+rng.gauss(0,s1n)
                sg2[i]=(1-f2)*p["a"]+f2*p["f"]+rng.gauss(0,s2n)
                if peer_signal:
                    # 동료 k명: 각자 독립 선호 + 독립 관측오차
                    acc=0.0
                    for _j in range(k_peer):
                        acc += (1-fp)*p["a"] + fp*rng.gauss(0,1) + rng.gauss(0,sp)
                    sgp[i]=acc/k_peer
                else:
                    sgp[i]=rng.gauss(0,1)          # 현행: 실력정보 0
            s1={}; s2={}
            for d,mem in dmem.items(): s1.update(award(mem,dty[d],sg1,mode,rng,adj))
            for h,mem in hmem.items(): s2.update(award(mem,hty[h],sg2,mode,rng))
            # 다면은 기관 전체를 하나의 평가군으로 순위기반 표준화
            allm=list(range(n))
            sp_out=award(allm,"N",sgp,"reform",rng)
            tot=[w_core*(w1*s1[i]+w2*s2[i]) + w_multi*sp_out[i]
                 + W_COMMON*clamp(95+4*rng.gauss(0,1),70,100) for i in range(n)]
        gr,pts=assign_grades(tot, lambda i: people[i]["g"])
        dep=[p["d"] for p in people]
        va,vd,vr=var_decomp(pts,ab,dep)
        cut=sorted(ab)[int(0.8*n)]
        big=[pts[i] for i,p in enumerate(people) if ab[i]>=cut and org[p["d"]][1]>=16]
        sml=[pts[i] for i,p in enumerate(people) if ab[i]>=cut and org[p["d"]][1]<=3]
        gz=(st.mean(big)-st.mean(sml)) if (big and sml) else float('nan')
        M.append((spearman(ab,pts), decile_sd(ab,pts), va,vd,vr, gz))
    def avg(k):
        v=[m[k] for m in M if not (isinstance(m[k],float) and math.isnan(m[k]))]
        return st.mean(v) if v else float('nan')
    return dict(rho=avg(0), sd=avg(1), v_ab=avg(2), v_dept=avg(3), v_res=avg(4), size=avg(5))

if __name__=="__main__":
    S2=0.9; R=400
    hi=run(REAL,0.60,0.3,S2,0.10,4,0.6,0.30,mode="current",peer_signal=False,reps=R)
    lo=run(REAL,0.60,0.3,S2,0.10,4,0.6,0.30,ideal=True,reps=R)
    def pct(v): return (hi["sd"]-v)/(hi["sd"]-lo["sd"])*100
    print("═══ ④ 다면평가 비중 확대 (실제 조직 213명 · σ1=0.3 σ2=0.9 · 400회) ═══")
    print("   동료 4명 · 동료 관측오차 0.6σ · 동료 선호반영 0.30 (부서장 0.70의 절반 이하)")
    print(f"   기준: 현행 {hi['sd']:.3f} (0%) / 이상적 하한 {lo['sd']:.3f} (100%)\n")
    print(f"{'안':<34}{'지표2 SD':>9}{'하한대비':>9}{'rho':>7}{'부서%':>7}{'규모격차':>9}")
    rows=[]
    rows.append(("현행 (사전조정 · 다면 잡음)", run(REAL,0.60,0.3,S2,0.10,4,0.6,0.30,mode="current",peer_signal=False,reps=R)))
    rows.append(("보정만 · 다면 10% (개선 원안)", run(REAL,0.60,0.3,S2,0.10,4,0.6,0.30,reps=R)))
    rows.append(("└ 1차 50:50 으로 바꿈", run(REAL,0.50,0.3,S2,0.10,4,0.6,0.30,reps=R)))
    for wm in (0.20,0.30,0.40):
        rows.append((f"보정 + 다면 {int(wm*100)}% (동료 4명)", run(REAL,0.60,0.3,S2,wm,4,0.6,0.30,reps=R)))
    rows.append(("보정 + 다면 30% · 동료 8명", run(REAL,0.60,0.3,S2,0.30,8,0.6,0.30,reps=R)))
    rows.append(("보정 + 다면 30% · 동료 2명", run(REAL,0.60,0.3,S2,0.30,2,0.6,0.30,reps=R)))
    rows.append(("보정 + 다면 30% · 동료선호 0.70", run(REAL,0.60,0.3,S2,0.30,4,0.6,0.70,reps=R)))
    rows.append(("보정 + 다면 30% · 동료오차 1.2σ", run(REAL,0.60,0.3,S2,0.30,4,1.2,0.30,reps=R)))
    rows.append(("보정 + 다면 30% + 제7호 ±5", run(REAL,0.60,0.3,S2,0.30,4,0.6,0.30,adj=5.0,reps=R)))
    rows.append(("이상적 (하한)", lo))
    for nm,r in rows:
        print(f"{nm:<34}{r['sd']:9.3f}{pct(r['sd']):8.1f}%{r['rho']:7.3f}{r['v_dept']:7.1f}{r['size']:9.2f}")
