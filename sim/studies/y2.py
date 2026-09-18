# -*- coding: utf-8 -*-
"""후보 4 — 다면 지명제만 (배점 10% 유지). mix.py 의 다면 모형을 그대로 쓰고
core 산식을 'current'(현행) / 'reform'(순위 제출) 로 갈라서 측정한다."""
import os
import sys, random, math, statistics as st
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from ycore import *

NEAR = dict(sp=0.4, fp=0.30)
FAR  = dict(sp=2.0, fp=0.60)

def run(w_multi, k, q, mode="reform", reps=400, s2n=0.9, w1=0.60, s1n=0.3,
        seed=20260910, ideal=False, peer_signal=True):
    rng=random.Random(seed); w2=1.0-w1
    w_core = 1.0 - w_multi - W_COMMON
    k_near=int(round(q*k)); k_far=k-k_near
    M=[]
    for _ in range(reps):
        people,dmem,hmem,dty,hty=build(REAL,rng,0.0)
        n=len(people); ab=[p["a"] for p in people]
        if ideal:
            tot=[TARGET_MEAN+TARGET_SD*p["a"] for p in people]
        else:
            sg1={};sg2={};sgp={}
            for i,p in enumerate(people):
                f1=FAVOR[dty[p["d"]]]; f2=FAVOR[hty[p["h"]]]
                sg1[i]=(1-f1)*p["a"]+f1*p["f"]+rng.gauss(0,s1n)
                sg2[i]=(1-f2)*p["a"]+f2*p["f"]+rng.gauss(0,s2n)
                if peer_signal and k>0:
                    acc=0.0
                    for _j in range(k_near):
                        acc+=(1-NEAR["fp"])*p["a"]+NEAR["fp"]*rng.gauss(0,1)+rng.gauss(0,NEAR["sp"])
                    for _j in range(k_far):
                        acc+=(1-FAR["fp"])*p["a"]+FAR["fp"]*rng.gauss(0,1)+rng.gauss(0,FAR["sp"])
                    sgp[i]=acc/k
                else: sgp[i]=rng.gauss(0,1)
            s1={};s2={}
            for d,m in dmem.items(): s1.update(award(m,dty[d],sg1,mode,rng,0.0))
            for h,m in hmem.items(): s2.update(award(m,hty[h],sg2,mode,rng))
            sp_out=award(list(range(n)),"N",sgp,"reform",rng)
            tot=[w_core*(w1*s1[i]+w2*s2[i]) + w_multi*sp_out[i]
                 + W_COMMON*clamp(95+4*rng.gauss(0,1),70,100) for i in range(n)]
        gr,pts=assign_grades(tot, lambda i: people[i]["g"])
        M.append((spearman(ab,pts), decile_sd(ab,pts),
                  var_decomp(pts,ab,[p["d"] for p in people])[1]))
    return dict(rho=st.mean(m[0] for m in M), sd=st.mean(m[1] for m in M),
                v_dept=st.mean(m[2] for m in M))

if __name__=="__main__":
    R=400
    hi=run(0.10,4,1.0,mode="current",peer_signal=False,reps=R)
    lo=run(0.10,4,1.0,ideal=True,reps=R)
    span=hi["sd"]-lo["sd"]
    def pc(v): return (hi["sd"]-v)/span*100
    print("[다면 모형 조건] 현행 %.3f · 이상적 하한 %.3f · 폭 %.3f (반복 %d)"%(hi["sd"],lo["sd"],span,R))
    print()
    print(f"{'안':<52}{'지표2':>8}{'제거율':>8}{'rho':>7}{'부서%':>7}")
    def row(nm,r): print(f"{nm:<52}{r['sd']:8.3f}{pc(r['sd']):7.1f}%{r['rho']:7.3f}{r['v_dept']:7.1f}")
    row("현행 (core 현행 · 다면=변별력 없음)", hi)
    print("  ── 후보 4 : core 산식 그대로(현행) · 다면 10% 유지 · 선정만 바꿈")
    for k,q,nm in [(4,0.35,"무작위 4인 (q=0.35)"),(9,0.35,"부서 전원 자동 9인 (q=0.35)"),
                   (4,0.67,"지명 4인+무관 2인 (q=0.67)"),(4,1.0,"업무관련자 지명 4인 (q=1.00)"),
                   (6,1.0,"업무관련자 지명 6인 (q=1.00)")]:
        row(f"  현행 core + 다면10% {nm}", run(0.10,k,q,mode="current",reps=R))
    print("  ── 대조 : core 를 순위 제출로 바꾼 경우 (후보 2 + 후보 4)")
    for k,q,nm in [(4,0.35,"무작위 4인"),(4,1.0,"지명 4인")]:
        row(f"  순위제출 core + 다면10% {nm}", run(0.10,k,q,mode="reform",reps=R))
    row("  순위제출 core + 다면10% (다면 변별력 없음)", run(0.10,4,1.0,mode="reform",peer_signal=False,reps=R))
    print("  ── 대조 : 현 16건 (순위제출 + 다면 20% 지명제)")
    row("  순위제출 core + 다면20% 지명 4인", run(0.20,4,1.0,mode="reform",reps=R))
    row("이상적 하한", lo)
