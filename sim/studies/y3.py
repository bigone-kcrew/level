# -*- coding: utf-8 -*-
"""후보 6 — 조문 1~2개로 목적을 달성하는 조합 탐색.
 (ㄱ) 순위제출을 1차만 / 2차만 / 양쪽
 (ㄴ) [별표 2] 1차:2차 반영비율 변경 (별표 1건)
 (ㄷ) 순위제출 + ±5점 + 비율 조합"""
import os
import sys, random, math, statistics as st
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from ycore import *

def one(org,rng,who,w1,s1n,s2n,gap,tau,adj):
    people,dmem,hmem,dty,hty=build(org,rng,gap)
    n=len(people); ab=[p["a"] for p in people]; w2=1.0-w1
    sg1,sg2,prev=observe(people,dmem,hmem,dty,hty,rng,s1n,s2n,tau,len(org))
    s1={};s2={}
    if who in ("both","first"):
        for d,m in dmem.items(): s1.update(rank_convert(m,sg1,rng,"strict"))
        if adj>0:
            for d,m in dmem.items(): s1.update(apply_adj(m,{i:s1[i] for i in m},sg1,adj))
    else:
        for d,m in dmem.items(): s1.update(award(m,dty[d],sg1,"current",rng))
    if who in ("both","second"):
        for h,m in hmem.items(): s2.update(rank_convert(m,sg2,rng,"strict"))
    else:
        for h,m in hmem.items(): s2.update(award(m,hty[h],sg2,"current",rng))
    core=[w1*s1[i]+w2*s2[i] for i in range(n)]
    tot=[W_CORE*core[i]+W_MULTI*clamp(92+4*rng.gauss(0,1),20,100)
         +W_COMMON*clamp(95+4*rng.gauss(0,1),70,100) for i in range(n)]
    return metrics(org,people,ab,tot)

def run(who="both",w1=0.60,reps=400,s1n=0.3,s2n=0.9,gap=0.0,tau=0.45,adj=0.0,seed=20260910,org=REAL):
    rng=random.Random(seed); M=[one(org,rng,who,w1,s1n,s2n,gap,tau,adj) for _ in range(reps)]
    def avg(k):
        v=[m[k] for m in M if not (isinstance(m[k],float) and math.isnan(m[k]))]
        return st.mean(v) if v else float('nan')
    return dict(rho=avg(0),sd=avg(1),v_dept=avg(3),size=avg(5))

def cur_run(w1=0.60,reps=400,**kw): return run("none",w1=w1,reps=reps,**kw)

if __name__=="__main__":
    R=400
    import y1
    cur=y1.run("current",reps=R); idl=y1.run("ideal",reps=R)
    span=cur["sd"]-idl["sd"]
    def pc(v): return (cur["sd"]-v)/span*100
    print("기준선: 현행 %.4f · 하한 %.4f (반복 %d)"%(cur["sd"],idl["sd"],R))
    print(f"\n{'안':<48}{'지표2':>8}{'제거율':>8}{'rho':>7}{'부서%':>7}{'규모격차':>8}")
    def row(nm,r): print(f"{nm:<48}{r['sd']:8.3f}{pc(r['sd']):7.1f}%{r['rho']:7.3f}{r['v_dept']:7.1f}{r['size']:8.2f}")
    row("현행", cur)
    print("  ── (ㄱ) 순위 제출을 누구에게 적용하는가 (1차:2차=60:40 고정)")
    for w,nm in (("first","1차(부서장)만 순위 제출"),("second","2차(본부장)만 순위 제출"),
                 ("both","1·2차 모두 순위 제출")):
        row(f"  {nm}", run(w,reps=R))
    print("  ── (ㄴ) [별표 2] 1차:2차 반영비율만 변경 (현행 산식 유지 · 별표 1건)")
    for w1 in (0.60,0.70,0.80,0.90,1.00):
        row(f"  현행 산식 · 1차 {int(w1*100)}:{100-int(w1*100)}", cur_run(w1=w1,reps=R))
    print("  ── (ㄷ) 순위 제출 + 반영비율 (조문 1 + 별표 2건)")
    for w1 in (0.60,0.70,0.80,0.90,1.00):
        row(f"  1·2차 순위제출 · 1차 {int(w1*100)}:{100-int(w1*100)}", run("both",w1=w1,reps=R))
    print("  ── (ㄹ) 순위 제출 + 제7호 ±5점 + 반영비율")
    for w1 in (0.60,0.80,1.00):
        row(f"  순위제출+±5 · 1차 {int(w1*100)}:{100-int(w1*100)}", run("both",w1=w1,adj=5.0,reps=R))
    print("  ── (ㅁ) 1차만 순위제출 + 반영비율 (2차 현행 유지)")
    for w1 in (0.60,0.80,1.00):
        row(f"  1차만 순위제출 · 1차 {int(w1*100)}:{100-int(w1*100)}", run("first",w1=w1,reps=R))
    row("이상적 하한", idl)
