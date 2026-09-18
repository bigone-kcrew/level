# -*- coding: utf-8 -*-
"""후보 6 — [별표 9] 제3호 산식에 기호 하나만 더한 안.
   z 를 해당 평가군 z값들의 표준편차로 나눠 모든 평가군의 부여폭을 같게 만든다.
   (조문 수 증가 0 · 부서 내 순위 100% 보존)"""
import os
import sys, random, math, statistics as st
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from ycore import *

_S={}
def sn(n):
    if n not in _S:
        z=blom(n); _S[n]=st.pstdev(z) if n>1 else 1.0
    return _S[n] or 1.0

def conv(members, sig, norm):
    out={}; n=len(members)
    if not n: return out
    r=ranks([sig[i] for i in members]); s = sn(n) if norm else 1.0
    for k,i in enumerate(members):
        out[i]=clamp(TARGET_MEAN+TARGET_SD*probit((r[k]-0.375)/(n+0.25))/s)
    return out

def one(org,rng,norm,adj,w1=0.60,s1n=0.3,s2n=0.9,tau=0.45,gap=0.0):
    people,dmem,hmem,dty,hty=build(org,rng,gap)
    n=len(people); ab=[p["a"] for p in people]; w2=1.0-w1
    sg1,sg2,prev=observe(people,dmem,hmem,dty,hty,rng,s1n,s2n,tau,len(org))
    s1={};s2={}
    for d,m in dmem.items():
        c=conv(m,sg1,norm)
        if adj>0: c=apply_adj(m,c,sg1,adj)
        s1.update(c)
    for h,m in hmem.items(): s2.update(conv(m,sg2,norm))
    core=[w1*s1[i]+w2*s2[i] for i in range(n)]
    tot=[W_CORE*core[i]+W_MULTI*clamp(92+4*rng.gauss(0,1),20,100)
         +W_COMMON*clamp(95+4*rng.gauss(0,1),70,100) for i in range(n)]
    return metrics(org,people,ab,tot)

def run(norm=False,adj=0.0,reps=400,seed=20260910,org=REAL,gap=0.0):
    rng=random.Random(seed); M=[one(org,rng,norm,adj,gap=gap) for _ in range(reps)]
    def avg(k):
        v=[m[k] for m in M if not (isinstance(m[k],float) and math.isnan(m[k]))]
        return st.mean(v) if v else float('nan')
    return dict(rho=avg(0),sd=avg(1),v_dept=avg(3),size=avg(5))

if __name__=="__main__":
    R=400
    import y1
    cur=y1.run("current",reps=R); idl=y1.run("ideal",reps=R)
    span=cur["sd"]-idl["sd"]
    def pc(v): return (cur["sd"]-v)/span*100
    print("기준선: 현행 %.4f (0%%) · 하한 %.4f (100%%) · 반복 %d\n"%(cur["sd"],idl["sd"],R))
    print("평가군 규모별 부여점수 (1위 / 최하위 / 부여폭)")
    print(f"{'n':>4} {'원안 1위':>9}{'원안 폭':>8}   {'정규화 1위':>10}{'정규화 폭':>9}")
    for n in (3,4,6,10,16):
        z=blom(n); s=sn(n)
        print(f"{n:4d} {80+7*z[-1]:9.2f}{7*(z[-1]-z[0]):8.2f}   {80+7*z[-1]/s:10.2f}{7*(z[-1]-z[0])/s:9.2f}")
    print()
    print(f"{'안':<40}{'지표2':>8}{'제거율':>8}{'rho':>7}{'부서%':>7}{'규모격차':>8}")
    def row(nm,r): print(f"{nm:<40}{r['sd']:8.3f}{pc(r['sd']):7.1f}%{r['rho']:7.3f}{r['v_dept']:7.1f}{r['size']:8.2f}")
    row("현행",cur)
    row("[별표9] 원안 (순위→Blom)",run(False,0.0,reps=R))
    row("[별표9] 원안 + ±5",run(False,5.0,reps=R))
    row("★ 부여폭 정규화 (z÷s_n)",run(True,0.0,reps=R))
    row("★ 부여폭 정규화 + ±5",run(True,5.0,reps=R))
    print("  ── 합성조직 240명 (규모 3~16 균형) 에서 규모격차 재확인")
    row("  원안 · 합성조직",run(False,0.0,reps=R,org=SYNTH))
    row("  정규화 · 합성조직",run(True,0.0,reps=R,org=SYNTH))
    print("  ── 부서 간 실제 실력격차 ±0.6σ 조건")
    row("  원안 · 격차 0.6",run(False,0.0,reps=R,gap=0.6))
    row("  정규화 · 격차 0.6",run(True,0.0,reps=R,gap=0.6))
    row("이상적 하한",idl)
