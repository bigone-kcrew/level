# -*- coding: utf-8 -*-
"""후보 2 의 두 취약점을 정량화한다.
 (A) 동점 처리 — 균등형 평가자가 어느 정도까지 동점을 제출하면 제도가 무력화되는가
 (B) 회피 — 부서장이 실력과 무관한 순위(연공·가나다순 등)를 제출할 때
     ① 지표2 손실 ② 개정 16 의 「1차–2차 순위 일치도」로 탐지되는가"""
import os
import sys, random, math, statistics as st
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from ycore import *

def coarse(members, sig, nb):
    """균등형 평가자가 nb 개 구간으로만 구분해 제출 → 구간 내는 동점"""
    if nb<=1: return {i:0.0 for i in members}
    n=len(members); vals=[sig[i] for i in members]; r=ranks(vals)
    return {i: float(min(nb-1, int((r[k]-1)*nb/n))) for k,i in enumerate(members)}

def one(org,rng,mode,nb=1,pev=0.0,w1=0.60,s1n=0.3,s2n=0.9,tau=0.45):
    people,dmem,hmem,dty,hty=build(org,rng,0.0)
    n=len(people); ab=[p["a"] for p in people]; w2=1.0-w1
    sg1,sg2,prev=observe(people,dmem,hmem,dty,hty,rng,s1n,s2n,tau,len(org))
    # 회피 부서장: 확률 pev 로 실력과 무관한 고정 순서(연공 등)를 제출
    evade={d:(rng.random()<pev) for d in dmem}
    seni={i:rng.gauss(0,1) for i in range(n)}   # 연공 등 실력 무관 속성
    s1={};s2={}; agree=[]; agree_ev=[]
    for d,m in dmem.items():
        if mode=="ties":
            key = coarse(m,sg1,nb) if dty[d]=="N" else sg1
            s1.update(rank_convert(m,key,rng,"allow"))
            k1=[key[i] for i in m]
        else:
            key = seni if evade[d] else sg1
            s1.update(rank_convert(m,key,rng,"strict"))
            k1=[key[i] for i in m]
        if len(m)>=3:
            sp=spearman(k1,[sg2[i] for i in m])
            (agree_ev if (mode!="ties" and evade[d]) else agree).append(sp)
    for h,m in hmem.items(): s2.update(rank_convert(m,sg2,rng,"strict"))
    core=[w1*s1[i]+w2*s2[i] for i in range(n)]
    tot=[W_CORE*core[i]+W_MULTI*clamp(92+4*rng.gauss(0,1),20,100)
         +W_COMMON*clamp(95+4*rng.gauss(0,1),70,100) for i in range(n)]
    mt=metrics(org,people,ab,tot)
    return mt+(st.mean(agree) if agree else float('nan'),
               st.mean(agree_ev) if agree_ev else float('nan'))

def run(mode,nb=1,pev=0.0,reps=400,seed=20260910):
    rng=random.Random(seed); M=[one(REAL,rng,mode,nb,pev) for _ in range(reps)]
    def avg(k):
        v=[m[k] for m in M if not (isinstance(m[k],float) and math.isnan(m[k]))]
        return st.mean(v) if v else float('nan')
    return dict(rho=avg(0),sd=avg(1),v_dept=avg(3),size=avg(5),ag=avg(7),agev=avg(8))

if __name__=="__main__":
    R=400
    import y1
    cur=y1.run("current",reps=R); idl=y1.run("ideal",reps=R)
    span=cur["sd"]-idl["sd"]
    def pc(v): return (cur["sd"]-v)/span*100
    print("기준선: 현행 %.4f (0%%) · 하한 %.4f (100%%) · 반복 %d"%(cur["sd"],idl["sd"],R))
    print("\n【A】동점 허용 시 — 균등형 평가자가 구분하는 구간 수")
    print(f"{'균등형 평가자의 제출':<34}{'지표2':>8}{'제거율':>8}{'rho':>7}{'규모격차':>8}")
    print(f"{'  (현행)':<34}{cur['sd']:8.3f}{0.0:7.1f}%{cur['rho']:7.3f}{cur['size']:8.2f}")
    for nb,lbl in ((1,"전원 동점 (1구간)"),(2,"상·하 2구간"),(3,"상·중·하 3구간"),
                   (5,"5구간"),(99,"동점 없음 (완전 서열)")):
        r=run("ties",nb=nb,reps=R)
        print(f"  {lbl:<32}{r['sd']:8.3f}{pc(r['sd']):7.1f}%{r['rho']:7.3f}{r['size']:8.2f}")
    print("\n【B】회피 — 부서장이 실력 무관 순위(연공순 등)를 제출하는 비율")
    print(f"{'회피 부서장 비율':<34}{'지표2':>8}{'제거율':>8}{'rho':>7}{'정상 ρ(1-2차)':>13}{'회피 ρ(1-2차)':>13}")
    for p in (0.0,0.10,0.25,0.50,1.00):
        r=run("evade",pev=p,reps=R)
        ev = f"{r['agev']:13.3f}" if not math.isnan(r['agev']) else f"{'—':>13}"
        print(f"  {int(p*100):>3}%{'':<28}{r['sd']:8.3f}{pc(r['sd']):7.1f}%{r['rho']:7.3f}{r['ag']:13.3f}{ev}")
