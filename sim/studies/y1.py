# -*- coding: utf-8 -*-
import os
import sys, random, math, statistics as st
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from ycore import *

def one(org, rng, method, s1n, s2n, w1, gap, tau, adj=5.0, grain=0.0, ties="strict", jit=True):
    people,dmem,hmem,dty,hty=build(org,rng,gap)
    n=len(people); ab=[p["a"] for p in people]; w2=1.0-w1
    sg1,sg2,prev=observe(people,dmem,hmem,dty,hty,rng,s1n,s2n,tau,len(org))
    absolute=False; core=None

    if method=="ideal":
        core=[TARGET_MEAN+TARGET_SD*a for a in ab]

    elif method in ("current","c5_abs"):
        s1={};s2={}
        for d,m in dmem.items(): s1.update(award(m,dty[d],sg1,"current",rng))
        for h,m in hmem.items(): s2.update(award(m,hty[h],sg2,"current",rng))
        core=[w1*s1[i]+w2*s2[i] for i in range(n)]
        absolute = (method=="c5_abs")

    elif method in ("blom","blom_adj"):
        a_=adj if method=="blom_adj" else 0.0
        s1={};s2={}
        for d,m in dmem.items(): s1.update(award(m,dty[d],sg1,"reform",rng,a_))
        for h,m in hmem.items(): s2.update(award(m,hty[h],sg2,"reform",rng))
        core=[w1*s1[i]+w2*s2[i] for i in range(n)]

    # ── 후보 2: 부서장·본부장이 순위만 제출, 인사부서가 [별표 9]로 변환
    elif method in ("c2_rank","c2_rank_adj","c2_abs"):
        s1={};s2={}
        for d,m in dmem.items(): s1.update(rank_convert(m,sg1,rng,"strict"))
        for h,m in hmem.items(): s2.update(rank_convert(m,sg2,rng,"strict"))
        if method=="c2_rank_adj":
            for d,m in dmem.items(): s1.update(apply_adj(m,{i:s1[i] for i in m},sg1,adj))
        core=[w1*s1[i]+w2*s2[i] for i in range(n)]
        absolute = (method=="c2_abs")

    # ── 후보 2 변형: 동점 허용 → 균등형 평가자가 전원 동점 제출
    elif method=="c2_ties_all":
        s1={};s2={}
        for d,m in dmem.items():
            key = {i:0.0 for i in m} if dty[d]=="N" else sg1
            s1.update(rank_convert(m,key,rng,"allow"))
        for h,m in hmem.items():
            key = {i:0.0 for i in m} if hty[h]=="N" else sg2
            s2.update(rank_convert(m,key,rng,"allow"))
        core=[w1*s1[i]+w2*s2[i] for i in range(n)]

    # ── 후보 1: 평가자는 점수를 제출, 인사부서가 사후 평균·표준편차 보정
    elif method=="c1_zfix":
        s1={};s2={}
        for d,m in dmem.items(): s1.update(zfix(m, submit_score(m,dty[d],sg1,rng,grain)))
        for h,m in hmem.items(): s2.update(zfix(m, submit_score(m,hty[h],sg2,rng,grain)))
        core=[w1*s1[i]+w2*s2[i] for i in range(n)]

    # ── 후보 2 (해상도 제약 조건): 제출점수의 순위 + 동점 강제 서열화
    elif method=="c2_grain":
        s1={};s2={}
        for d,m in dmem.items():
            raw=submit_score(m,dty[d],sg1,rng,grain)
            s1.update(rank_convert(m,raw,rng,"strict", jitter=(sg1 if jit else None)))
        for h,m in hmem.items():
            raw=submit_score(m,hty[h],sg2,rng,grain)
            s2.update(rank_convert(m,raw,rng,"strict", jitter=(sg2 if jit else None)))
        core=[w1*s1[i]+w2*s2[i] for i in range(n)]

    else: raise ValueError(method)

    tot=[W_CORE*core[i] + W_MULTI*clamp(92+4*rng.gauss(0,1),20,100)
         + W_COMMON*clamp(95+4*rng.gauss(0,1),70,100) for i in range(n)]
    return metrics(org,people,ab,tot,absolute,ABS_SD[0])

ABS_SD=[None]
def run(method, org=REAL, reps=400, s1n=0.3, s2n=0.9, w1=0.60, gap=0.0, tau=0.45,
        adj=5.0, grain=0.0, ties="strict", jit=True, seed=20260910):
    rng=random.Random(seed); M=[]
    for _ in range(reps): M.append(one(org,rng,method,s1n,s2n,w1,gap,tau,adj,grain,ties,jit))
    def avg(k):
        v=[m[k] for m in M if not (isinstance(m[k],float) and math.isnan(m[k]))]
        return st.mean(v) if v else float('nan')
    return dict(rho=avg(0), sd=avg(1), v_ab=avg(2), v_dept=avg(3), v_res=avg(4),
                size=avg(5), ptsd=avg(6))

if __name__=="__main__":
    R=400
    cur=run("current",reps=R); idl=run("ideal",reps=R)
    ABS_SD[0]=cur["ptsd"]
    span=cur["sd"]-idl["sd"]
    def pc(v): return (cur["sd"]-v)/span*100
    print("기준선: 현행 %.4f · 이상적 하한 %.4f · 제거가능 폭 %.4f · 현행 평정점 SD %.3f (반복 %d)"
          % (cur["sd"], idl["sd"], span, cur["ptsd"], R))
    print()
    hdr=f"{'안':<40}{'지표2':>8}{'제거율':>8}{'rho':>7}{'부서%':>7}{'규모격차':>8}{'평정점SD':>9}"
    def row(nm,r): print(f"{nm:<40}{r['sd']:8.3f}{pc(r['sd']):7.1f}%{r['rho']:7.3f}{r['v_dept']:7.1f}{r['size']:8.2f}{r['ptsd']:9.2f}")
    print(hdr)
    row("현행 (기준선 0%)",cur)
    row("정본 개선 원안 blom (대조)",run("blom",reps=R))
    row("정본 개선+제7호±5 (대조)",run("blom_adj",reps=R))
    print("  ── 후보 2 · 순위 제출안")
    row("후보2 순위제출 (동점금지)",run("c2_rank",reps=R))
    row("후보2 순위제출 + 제7호±5",run("c2_rank_adj",reps=R))
    row("후보2 순위제출 + 동점허용(균등형 전원동점)",run("c2_ties_all",reps=R))
    print("  ── 후보 1 · 사후 평균·표준편차 보정 (계획만) · 해상도 가정별")
    for g,lbl in ((0.0,"무제약"),(0.5,"0.5점 단위"),(1.0,"1점 단위"),(2.0,"2점 단위")):
        row(f"후보1 사후z보정 · 제출점수 {lbl}",run("c1_zfix",reps=R,grain=g))
    print("  ── 같은 해상도 조건에서 후보 2 (동점→강제서열)")
    for g,lbl in ((0.0,"무제약"),(0.5,"0.5점 단위"),(1.0,"1점 단위"),(2.0,"2점 단위")):
        row(f"후보2 순위 · 제출 {lbl} · 서열정보 있음",run("c2_grain",reps=R,grain=g,jit=True))
    for g,lbl in ((1.0,"1점 단위"),(2.0,"2점 단위")):
        row(f"후보2 순위 · 제출 {lbl} · 동점 무작위",run("c2_grain",reps=R,grain=g,jit=False))
    print("  ── 후보 5 · 절대평가 (등급 강제배분 폐지)")
    row("후보5 절대평가 (현행 산식 유지)",run("c5_abs",reps=R))
    row("후보5+후보2 절대평가+순위제출",run("c2_abs",reps=R))
    row("이상적 하한 (100%)",idl)
