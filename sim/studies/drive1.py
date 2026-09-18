# -*- coding: utf-8 -*-
"""실험 ① — 1차·2차 관측오차 비대칭 × 반영비율 교차"""
import random, math, statistics as st
from core import *

def build(org, rng, gap=0.0):
    """부서 배치 + 실력. gap: 부서 간 실력 격차(σ)"""
    nd=len(org); nhq=max(h for h,_ in org)+1
    dty={d:("S" if rng.random()<MGR_S else "N") for d in range(nd)}
    # 본부 유형 무작위 (원장직속은 O 고정)
    hs=[h for h in range(nhq) if h!=DIRECTOR_HQ or DIRECTOR_HQ>=nhq]
    hs=[h for h in range(nhq) if h!=DIRECTOR_HQ]
    rng.shuffle(hs)
    hty={}
    if DIRECTOR_HQ<nhq: hty[DIRECTOR_HQ]="O"
    for k,h in enumerate(hs): hty[h]="S" if k<N_EXTREME else "N"
    # 부서 고정 실력 편차
    doff={d: rng.gauss(0,1)*gap for d in range(nd)}
    people=[]; dmem={d:[] for d in range(nd)}; hmem={h:[] for h in range(nhq)}
    for d,(h,sz) in enumerate(org):
        for _ in range(sz):
            people.append({"a":rng.gauss(0,1)+doff[d], "f":rng.gauss(0,1), "d":d, "h":h})
            dmem[d].append(len(people)-1); hmem[h].append(len(people)-1)
    for i,g in enumerate(rank_labels(len(people),rng)): people[i]["g"]=g
    return people,dmem,hmem,dty,hty

def run(org, mode, w1, s1n, s2n, reps=400, gap=0.0, adj=0.0, seed=20260910, ideal=False):
    rng=random.Random(seed); w2=1.0-w1
    M=[]
    for _ in range(reps):
        people,dmem,hmem,dty,hty=build(org,rng,gap)
        n=len(people); ab=[p["a"] for p in people]
        if ideal:
            tot=[TARGET_MEAN+TARGET_SD*p["a"] for p in people]
        else:
            # 신호: 평가자별 독립 관측오차
            sg1={}; sg2={}
            for i,p in enumerate(people):
                f1=FAVOR[dty[p["d"]]]; f2=FAVOR[hty[p["h"]]]
                sg1[i]=(1-f1)*p["a"]+f1*p["f"]+rng.gauss(0,s1n)
                sg2[i]=(1-f2)*p["a"]+f2*p["f"]+rng.gauss(0,s2n)
            s1={}; s2={}
            for d,mem in dmem.items(): s1.update(award(mem,dty[d],sg1,mode,rng,adj))
            for h,mem in hmem.items(): s2.update(award(mem,hty[h],sg2,mode,rng))
            tot=[W_CORE*(w1*s1[i]+w2*s2[i])
                 + W_MULTI*clamp(92+4*rng.gauss(0,1),20,100)
                 + W_COMMON*clamp(95+4*rng.gauss(0,1),70,100) for i in range(n)]
        gr,pts=assign_grades(tot, lambda i: people[i]["g"])
        dep=[p["d"] for p in people]
        va,vd,vr=var_decomp(pts,ab,dep)
        # 규모 격차: 상위 20% 실력자의 평정점, 큰 부서 − 작은 부서
        cut=sorted(ab)[int(0.8*n)]
        big=[pts[i] for i,p in enumerate(people) if ab[i]>=cut and org[p["d"]][1]>=16]
        sml=[pts[i] for i,p in enumerate(people) if ab[i]>=cut and org[p["d"]][1]<=3]
        gapsz=(st.mean(big)-st.mean(sml)) if (big and sml) else float('nan')
        M.append((spearman(ab,pts), decile_sd(ab,pts), va,vd,vr, gapsz))
    def avg(k):
        v=[m[k] for m in M if not (isinstance(m[k],float) and math.isnan(m[k]))]
        return st.mean(v) if v else float('nan')
    return dict(rho=avg(0), sd=avg(1), v_ab=avg(2), v_dept=avg(3), v_res=avg(4), size=avg(5))

if __name__=="__main__":
    print("═══ 실험 ① 관측오차 비대칭 × 1차 반영비율 (실제 조직 213명 · 400회) ═══")
    print("   σ1 = 0.3σ 고정. 개선안(순위기반 보정, 조정 없음) 기준\n")
    print(f"{'σ2':>5} {'1차비율':>7} {'지표2 SD':>9} {'rho':>7} {'실력%':>7} {'부서%':>6} {'잔차%':>7}")
    base={}
    for s2n in (0.3,0.6,0.9,1.2,1.5):
        for w1 in (0.70,0.60,0.50,0.40):
            r=run(REAL,"reform",w1,0.3,s2n,reps=400)
            print(f"{s2n:5.1f} {int(w1*100):5d}:{int((1-w1)*100):2d} "
                  f"{r['sd']:9.3f} {r['rho']:7.3f} {r['v_ab']:7.1f} {r['v_dept']:6.1f} {r['v_res']:7.1f}")
            base[(s2n,w1)]=r
        print()
    import json
    json.dump({f"{k[0]}|{k[1]}":v for k,v in base.items()}, open("out1.json","w"))
