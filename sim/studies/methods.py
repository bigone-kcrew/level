# -*- coding: utf-8 -*-
"""근본적 통계보정 방법 (가)~(마) 구현과 비교"""
import random, math, statistics as st
from core import *
from drive1 import build

# ─────────────────────────────────────────────────────────────────
# 공통: 관측 신호 생성 + 전보 앵커
# ─────────────────────────────────────────────────────────────────
def observe(people, dmem, hmem, dty, hty, rng, s1n, s2n, tau=0.0, nd=None):
    """반환: sg1, sg2, prev(전보 앵커: i -> (이전부서 d, 신호))"""
    sg1={}; sg2={}
    for i,p in enumerate(people):
        f1=FAVOR[dty[p["d"]]]; f2=FAVOR[hty[p["h"]]]
        sg1[i]=(1-f1)*p["a"]+f1*p["f"]+rng.gauss(0,s1n)
        sg2[i]=(1-f2)*p["a"]+f2*p["f"]+rng.gauss(0,s2n)
    prev={}
    if tau>0:
        for i,p in enumerate(people):
            if rng.random()<tau:
                d0=rng.randrange(nd)
                if d0==p["d"]: continue
                f0=FAVOR[dty[d0]]
                prev[i]=(d0,(1-f0)*p["a"]+f0*p["f"]+rng.gauss(0,s1n))
    return sg1,sg2,prev

def raw_scores(members, gtype, sig, rng):
    """현행 방식 원점수 — 평가자 성향(폭·수준)이 그대로 남는다"""
    out={}
    if not members: return out
    vals=[sig[i] for i in members]; rk=ranks(vals); bl=blom(len(members))
    base = TARGET_MEAN - rng.uniform(0,MEAN_SLACK) if gtype!="O" else TARGET_MEAN
    sd = SPREAD[gtype]
    for k,i in enumerate(members): out[i]=clamp(base+sd*bl[rk[k]-1])
    return out

# ─────────────────────────────────────────────────────────────────
# (가) 정밀도 가중 — 1차·2차 불일치도에서 σ 역산
# ─────────────────────────────────────────────────────────────────
def ivw_weight(s1, s2, n, est=True, s1n=0.3, s2n=0.9):
    """est=True: 관측 가능한 1·2차 불일치로 가중 추정. False: 참 최적가중"""
    if not est:
        return (s2n**2)/(s1n**2+s2n**2)
    # 1차·2차 점수의 부서/본부 내 편차 크기로 상대 정밀도를 근사한다.
    # 잡음이 큰 평가자는 자기 신호가 실력과 덜 맞으므로 두 평가자 점수의
    # 상관이 낮아진다. 상관만으로는 어느 쪽이 부정확한지 알 수 없어
    # '각 평가자 점수와 두 점수 평균의 상관'을 신뢰도 대리지표로 쓴다.
    a=[s1[i] for i in range(n)]; b=[s2[i] for i in range(n)]
    m=[(x+y)/2 for x,y in zip(a,b)]
    def corr(u,v):
        mu,mv=st.mean(u),st.mean(v)
        num=sum((x-mu)*(y-mv) for x,y in zip(u,v))
        du=math.sqrt(sum((x-mu)**2 for x in u)); dv=math.sqrt(sum((y-mv)**2 for y in v))
        return num/(du*dv) if du>0 and dv>0 else 0.5
    r1=max(1e-6,corr(a,m)); r2=max(1e-6,corr(b,m))
    return r1**2/(r1**2+r2**2)

# ─────────────────────────────────────────────────────────────────
# (나) 혼합효과 — 평가자 임의효과 제거, 개인효과(BLUP) 추출
# ─────────────────────────────────────────────────────────────────
def blup(obs, n_person, n_eval, lam_p=0.5, lam_v=2.0, iters=60):
    """obs: [(i, j, y)]  →  개인효과 p_i
    ALS + 축소. lam_p=σε²/σp², lam_v=σε²/σv²"""
    if not obs: return [0.0]*n_person
    mu=st.mean([y for _,_,y in obs])
    p=[0.0]*n_person; v=[0.0]*n_eval
    byi={}; byj={}
    for i,j,y in obs:
        byi.setdefault(i,[]).append((j,y)); byj.setdefault(j,[]).append((i,y))
    for _ in range(iters):
        for i,lst in byi.items():
            p[i]=sum(y-mu-v[j] for j,y in lst)/(len(lst)+lam_p)
        for j,lst in byj.items():
            v[j]=sum(y-mu-p[i] for i,y in lst)/(len(lst)+lam_v)
        mv=st.mean(v); v=[x-mv for x in v]
    return p

# ─────────────────────────────────────────────────────────────────
# (다) 순위 통합 — Bradley-Terry (MM 알고리즘)
# ─────────────────────────────────────────────────────────────────
def bradley_terry(groups, n, iters=60, alpha=2.0):
    """groups: [[(person, 신호)] ...] 각 평가자 그룹의 순위.
    쌍대비교를 인접목록으로 만들고 MM 반복. 척도 차이는 순위만 쓰므로 자동 제거."""
    W=[0.0]*n
    adj=[dict() for _ in range(n)]      # adj[i][k] = i,k 대결 횟수
    for g in groups:
        order=sorted(g, key=lambda t:-t[1])
        ids=[t[0] for t in order]
        for x in range(len(ids)):
            i=ids[x]
            for y in range(x+1,len(ids)):
                k=ids[y]
                W[i]+=1
                adj[i][k]=adj[i].get(k,0)+1
                adj[k][i]=adj[k].get(i,0)+1
    # 축소: 각자 가상 평균 상대(π=1)와 alpha 승 alpha 패를 추가한다.
    # 3명 부서 1위가 무패로 발산하는 것을 막는다.
    pi=[1.0]*n
    for _ in range(iters):
        new_=list(pi)
        for i in range(n):
            den=2*alpha/(pi[i]+1.0); pii=pi[i]
            for k,c in adj[i].items(): den+=c/(pii+pi[k])
            if den>0: new_[i]=(W[i]+alpha)/den
        s_=st.mean([x for x in new_ if x>0]) or 1.0
        pi=[max(1e-9,x/s_) for x in new_]
    return [math.log(x) for x in pi]

# ─────────────────────────────────────────────────────────────────
# (마) 구간 평정 — 5구간만 부여, 겹치면 동급
# ─────────────────────────────────────────────────────────────────
def band_scores(members, sig, nb=5):
    out={}
    if not members: return out
    vals=[sig[i] for i in members]; rk=ranks(vals); m=len(members)
    mid=[60+ (100-60)*(k+0.5)/nb for k in range(nb)]
    for k,i in enumerate(members):
        b=min(nb-1, int((rk[k]-1)*nb/m))
        out[i]=mid[b]
    return out
