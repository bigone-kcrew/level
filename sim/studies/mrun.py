# -*- coding: utf-8 -*-
"""② 방법별 비교 — 동일 조건에서 지표2 로 판정"""
import random, math, statistics as st
from core import *
from drive1 import build
from methods import *

def zstd(v, mean=TARGET_MEAN, sd=TARGET_SD):
    m=st.mean(v); s=st.pstdev(v) or 1.0
    return [mean+sd*(x-m)/s for x in v]

def one_rep(org, rng, method, s1n, s2n, w1, gap, tau, adj, hist=0):
    people,dmem,hmem,dty,hty=build(org,rng,gap)
    n=len(people); nd=len(org); nhq=max(h for h,_ in org)+1
    ab=[p["a"] for p in people]
    sg1,sg2,prev=observe(people,dmem,hmem,dty,hty,rng,s1n,s2n,tau,nd)
    w2=1.0-w1

    if method=="ideal":
        core=[TARGET_MEAN+TARGET_SD*a for a in ab]

    elif method=="current":
        s1={}; s2={}
        for d,mem in dmem.items(): s1.update(award(mem,dty[d],sg1,"current",rng))
        for h,mem in hmem.items(): s2.update(award(mem,hty[h],sg2,"current",rng))
        core=[w1*s1[i]+w2*s2[i] for i in range(n)]

    elif method in ("blom","blom_adj"):
        a_=adj if method=="blom_adj" else 0.0
        s1={}; s2={}
        for d,mem in dmem.items(): s1.update(award(mem,dty[d],sg1,"reform",rng,a_))
        for h,mem in hmem.items(): s2.update(award(mem,hty[h],sg2,"reform",rng))
        core=[w1*s1[i]+w2*s2[i] for i in range(n)]

    elif method=="ivw":
        s1={}; s2={}
        for d,mem in dmem.items(): s1.update(award(mem,dty[d],sg1,"reform",rng))
        for h,mem in hmem.items(): s2.update(award(mem,hty[h],sg2,"reform",rng))
        ww=ivw_weight(s1,s2,n,est=True)
        core=[ww*s1[i]+(1-ww)*s2[i] for i in range(n)]

    elif method=="ivw_true":
        s1={}; s2={}
        for d,mem in dmem.items(): s1.update(award(mem,dty[d],sg1,"reform",rng))
        for h,mem in hmem.items(): s2.update(award(mem,hty[h],sg2,"reform",rng))
        ww=ivw_weight(s1,s2,n,est=False,s1n=s1n,s2n=s2n)
        core=[ww*s1[i]+(1-ww)*s2[i] for i in range(n)]

    elif method=="blup":
        # 원점수(평가자 성향 잔존)로 관측을 만든 뒤 개인효과만 추출
        obs=[]
        for d,mem in dmem.items():
            sc=raw_scores(mem,dty[d],sg1,rng)
            for i in mem: obs.append((i,d,sc[i]))
        for h,mem in hmem.items():
            sc=raw_scores(mem,hty[h],sg2,rng)
            for i in mem: obs.append((i,nd+h,sc[i]))
        if prev:
            byd={}
            for i,(d0,v) in prev.items(): byd.setdefault(d0,[]).append((i,v))
            for d0,lst in byd.items():
                mem=[i for i,_ in lst]
                sig={i:v for i,v in lst}
                sc=raw_scores(mem,dty[d0],sig,rng)
                for i in mem: obs.append((i,d0,sc[i]))
        p=blup(obs,n,nd+nhq)
        core=zstd(p)


    elif method=="blom_blup":
        # 순위 정규화로 척도를 먼저 없애고, 남은 평가자 수준차를 BLUP 으로 축소
        s1={}; s2={}
        for d,mem in dmem.items(): s1.update(award(mem,dty[d],sg1,"reform",rng))
        for h,mem in hmem.items(): s2.update(award(mem,hty[h],sg2,"reform",rng))
        obs=[]
        for d,mem in dmem.items():
            for i in mem: obs.append((i,d,s1[i]))
        for h,mem in hmem.items():
            for i in mem: obs.append((i,nd+h,s2[i]))
        if prev:
            byd={}
            for i,(d0,v) in prev.items(): byd.setdefault(d0,[]).append((i,v))
            for d0,lst in byd.items():
                mem=[i for i,_ in lst]; sig={i:v for i,v in lst}
                sc=award(mem,dty[d0],sig,"reform",rng)
                for i in mem: obs.append((i,d0,sc[i]))
        p=blup(obs,n,nd+nhq,lam_p=0.3,lam_v=3.0)
        core=zstd(p)

    elif method=="bt":
        groups=[]
        for d,mem in dmem.items(): groups.append([(i,sg1[i]) for i in mem])
        for h,mem in hmem.items(): groups.append([(i,sg2[i]) for i in mem])
        lp=bradley_terry(groups,n)
        core=zstd(lp)

    elif method=="eb":
        # 평가자별 신뢰도를 과거 hist 년의 1·2차 일치도로 추정해 가중
        rel1={}; rel2={}
        for _ in range(max(1,hist)):
            h1,h2,_=observe(people,dmem,hmem,dty,hty,rng,s1n,s2n,0.0,nd)
            for d,mem in dmem.items():
                if len(mem)<3: continue
                a=[h1[i] for i in mem]; b=[h2[i] for i in mem]
                rel1.setdefault(d,[]).append(abs(spearman(a,b)))
            for h,mem in hmem.items():
                if len(mem)<3: continue
                a=[h2[i] for i in mem]; b=[h1[i] for i in mem]
                rel2.setdefault(h,[]).append(abs(spearman(a,b)))
        s1={}; s2={}
        for d,mem in dmem.items(): s1.update(award(mem,dty[d],sg1,"reform",rng))
        for h,mem in hmem.items(): s2.update(award(mem,hty[h],sg2,"reform",rng))
        # 부서 내 분산이 큰 평가자를 덜 신뢰: 1·2차 일치도가 높은 쪽에 가중
        core=[]
        for i,p in enumerate(people):
            r1=st.mean(rel1.get(p["d"],[0.5])); r2=st.mean(rel2.get(p["h"],[0.5]))
            t=(r1**2)/((r1**2)+(r2**2)) if (r1 or r2) else 0.5
            core.append(t*s1[i]+(1-t)*s2[i])

    elif method=="band":
        s1={}; s2={}
        for d,mem in dmem.items(): s1.update(band_scores(mem,sg1))
        for h,mem in hmem.items(): s2.update(band_scores(mem,sg2))
        core=[w1*s1[i]+w2*s2[i] for i in range(n)]

    else: raise ValueError(method)

    tot=[W_CORE*core[i]
         + W_MULTI*clamp(92+4*rng.gauss(0,1),20,100)
         + W_COMMON*clamp(95+4*rng.gauss(0,1),70,100) for i in range(n)]
    gr,pts=assign_grades(tot, lambda i: people[i]["g"])
    dep=[p["d"] for p in people]
    va,vd,vr=var_decomp(pts,ab,dep)
    cut=sorted(ab)[int(0.8*n)]
    big=[pts[i] for i,p in enumerate(people) if ab[i]>=cut and org[p["d"]][1]>=16]
    sml=[pts[i] for i,p in enumerate(people) if ab[i]>=cut and org[p["d"]][1]<=3]
    gs=(st.mean(big)-st.mean(sml)) if (big and sml) else float('nan')
    return (spearman(ab,pts), decile_sd(ab,pts), va,vd,vr, gs)

def run(org, method, reps=400, s1n=0.3, s2n=0.9, w1=0.60, gap=0.0, tau=0.45,
        adj=5.0, hist=3, seed=20260910):
    rng=random.Random(seed); M=[]
    for _ in range(reps):
        M.append(one_rep(org,rng,method,s1n,s2n,w1,gap,tau,adj,hist))
    def avg(k):
        v=[m[k] for m in M if not (isinstance(m[k],float) and math.isnan(m[k]))]
        return st.mean(v) if v else float('nan')
    return dict(rho=avg(0), sd=avg(1), v_ab=avg(2), v_dept=avg(3), v_res=avg(4), size=avg(5))
