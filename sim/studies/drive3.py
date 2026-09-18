# -*- coding: utf-8 -*-
"""선호(favor)의 정체에 따라 결론이 갈리는지 검증.

 shared  : 선호가 개인 속성 — 모든 평가자가 같은 f_i 를 본다("호감형")
           → 실력과 구별 불가. 어떤 통계기법도 제거할 수 없다.
 per_eval: 선호가 평가자×개인 — 부서장 A 의 편애와 본부장 B 의 편애가 독립
           → 평가자를 늘리거나 혼합효과로 제거 가능하다.
"""
import random, math, statistics as st
from core import *
from drive1 import build
from methods import blup, bradley_terry

def rep(org, rng, method, favor_mode, s1n, s2n, w1, gap, tau=0.45):
    people,dmem,hmem,dty,hty=build(org,rng,gap)
    n=len(people); nd=len(org); nhq=max(h for h,_ in org)+1
    ab=[p["a"] for p in people]; w2=1.0-w1
    # 신호
    sg1={}; sg2={}; prev={}
    for i,p in enumerate(people):
        f1=FAVOR[dty[p["d"]]]; f2=FAVOR[hty[p["h"]]]
        fav1 = p["f"] if favor_mode=="shared" else rng.gauss(0,1)
        fav2 = p["f"] if favor_mode=="shared" else rng.gauss(0,1)
        sg1[i]=(1-f1)*p["a"]+f1*fav1+rng.gauss(0,s1n)
        sg2[i]=(1-f2)*p["a"]+f2*fav2+rng.gauss(0,s2n)
    if tau>0:
        for i,p in enumerate(people):
            if rng.random()<tau:
                d0=rng.randrange(nd)
                if d0==p["d"]: continue
                f0=FAVOR[dty[d0]]
                fav0 = p["f"] if favor_mode=="shared" else rng.gauss(0,1)
                prev[i]=(d0,(1-f0)*p["a"]+f0*fav0+rng.gauss(0,s1n))
    # 방법
    if method=="ideal":
        core=[TARGET_MEAN+TARGET_SD*a for a in ab]
    elif method=="current":
        s1={};s2={}
        for d,m in dmem.items(): s1.update(award(m,dty[d],sg1,"current",rng))
        for h,m in hmem.items(): s2.update(award(m,hty[h],sg2,"current",rng))
        core=[w1*s1[i]+w2*s2[i] for i in range(n)]
    elif method=="blom":
        s1={};s2={}
        for d,m in dmem.items(): s1.update(award(m,dty[d],sg1,"reform",rng))
        for h,m in hmem.items(): s2.update(award(m,hty[h],sg2,"reform",rng))
        core=[w1*s1[i]+w2*s2[i] for i in range(n)]
    elif method=="blom_blup":
        s1={};s2={}
        for d,m in dmem.items(): s1.update(award(m,dty[d],sg1,"reform",rng))
        for h,m in hmem.items(): s2.update(award(m,hty[h],sg2,"reform",rng))
        obs=[(i,d,s1[i]) for d,m in dmem.items() for i in m] + \
            [(i,nd+h,s2[i]) for h,m in hmem.items() for i in m]
        if prev:
            byd={}
            for i,(d0,v) in prev.items(): byd.setdefault(d0,[]).append((i,v))
            for d0,lst in byd.items():
                mem=[i for i,_ in lst]; sig={i:v for i,v in lst}
                sc=award(mem,dty[d0],sig,"reform",rng)
                obs+= [(i,d0,sc[i]) for i in mem]
        p=blup(obs,n,nd+nhq,lam_p=0.3,lam_v=3.0)
        m_=st.mean(p); s_=st.pstdev(p) or 1.0
        core=[TARGET_MEAN+TARGET_SD*(x-m_)/s_ for x in p]
    elif method=="multi3":
        # 평가자 3명(부서장·본부장·동료집단) 독립 관측 후 평균
        s1={};s2={};s3={}
        sg3={i:(1-0.3)*people[i]["a"]+0.3*(people[i]["f"] if favor_mode=="shared" else rng.gauss(0,1))
               +rng.gauss(0,0.6) for i in range(n)}
        for d,m in dmem.items():
            s1.update(award(m,dty[d],sg1,"reform",rng))
            s3.update(award(m,"N",sg3,"reform",rng))
        for h,m in hmem.items(): s2.update(award(m,hty[h],sg2,"reform",rng))
        core=[(s1[i]+s2[i]+s3[i])/3 for i in range(n)]
    else: raise ValueError(method)
    tot=[W_CORE*core[i]+W_MULTI*clamp(92+4*rng.gauss(0,1),20,100)
         +W_COMMON*clamp(95+4*rng.gauss(0,1),70,100) for i in range(n)]
    gr,pts=assign_grades(tot, lambda i: people[i]["g"])
    va,vd,vr=var_decomp(pts,ab,[p["d"] for p in people])
    return (spearman(ab,pts), decile_sd(ab,pts), vd)

def run(org, method, favor_mode, reps=400, s1n=0.3, s2n=0.9, w1=0.60, gap=0.0, seed=20260910):
    rng=random.Random(seed)
    M=[rep(org,rng,method,favor_mode,s1n,s2n,w1,gap) for _ in range(reps)]
    return dict(rho=st.mean(m[0] for m in M), sd=st.mean(m[1] for m in M),
                v_dept=st.mean(m[2] for m in M))

if __name__=="__main__":
    print("═══ ②-7 선호(favor)의 정체가 결론을 바꾸는가 ═══")
    print("   shared  = 선호가 개인 속성(모든 평가자가 같은 편애) → 실력과 구별 불가")
    print("   per_eval= 선호가 평가자별 독립 → 관측자를 늘리면 제거 가능\n")
    for fm,lbl in (("shared","선호=개인 속성"),("per_eval","선호=평가자별 독립")):
        print(f"── {lbl}")
        print(f"{'방법':>18} {'지표2 SD':>9} {'하한대비':>8} {'rho':>7} {'부서%':>6}")
        base=run(REAL,"current",fm)['sd']; low=run(REAL,"ideal",fm)['sd']
        for me,nm in (("current","현행"),("blom","Blom 원안"),
                      ("blom_blup","Blom+혼합효과"),("multi3","평가자 3명 평균"),
                      ("ideal","이상적(하한)")):
            r=run(REAL,me,fm)
            imp=100*(base-r['sd'])/(base-low) if base>low else float('nan')
            print(f"{nm:>18} {r['sd']:9.3f} {imp:7.1f}% {r['rho']:7.3f} {r['v_dept']:6.1f}")
        print()
