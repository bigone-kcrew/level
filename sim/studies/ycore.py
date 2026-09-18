# -*- coding: utf-8 -*-
"""제3안 후보 측정 — 기존 observer/core.py·drive1.build 재사용.
조건: REAL 213명 · s1n=0.3 · s2n=0.9 · w1=0.60 · gap=0 · tau=0.45 · reps=400 · seed=20260910
"""
import sys, os, random, math, statistics as st
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from core import *          # REAL, GRADE, BANDS, SPREAD, FAVOR, award, assign_grades, blom, probit, spearman, decile_sd, var_decomp, clamp, TARGET_MEAN, TARGET_SD, W_CORE, W_MULTI, W_COMMON, ADJ_COEF, MEAN_SLACK
from drive1 import build
from methods import observe

# ── 순위(동점 허용) → 평균순위
def avg_ranks(vals):
    n=len(vals); order=sorted(range(n), key=lambda i:vals[i])
    r=[0.0]*n; k=0
    while k<n:
        j=k
        while j+1<n and vals[order[j+1]]==vals[order[k]]: j+=1
        mr=(k+j)/2.0+1.0
        for t in range(k,j+1): r[order[t]]=mr
        k=j+1
    return r

def blom_at(r, n):
    """평균순위 r(1..n, 실수 허용) 에 대한 Blom z"""
    return probit((r-0.375)/(n+0.25))

# ── 평가자가 '점수를 부여'할 때: 자기 수준(base)·부여폭(sd)·해상도(grain) 반영, 거리정보 보존
def submit_score(members, gtype, sig, rng, grain=0.0):
    out={}
    if not members: return out
    vals=[sig[i] for i in members]
    m=st.mean(vals); s=st.pstdev(vals) or 1.0
    base = TARGET_MEAN if gtype=="O" else TARGET_MEAN - rng.uniform(0,MEAN_SLACK)
    sd = SPREAD[gtype]
    for i in members:
        v = base + sd*(sig[i]-m)/s
        if grain>0: v = round(v/grain)*grain
        out[i]=clamp(v)
    return out

# ── 사후 보정: 평균·표준편차 일치법 (평가군 단위)
def zfix(members, raw):
    out={}
    if not members: return out
    v=[raw[i] for i in members]
    m=st.mean(v); s=st.pstdev(v)
    if s<=1e-12:
        for i in members: out[i]=TARGET_MEAN
        return out
    for i in members: out[i]=clamp(TARGET_MEAN+TARGET_SD*(raw[i]-m)/s)
    return out

# ── 순위 제출 → Blom 변환 (인사부서 수행). ties: 'strict'(동점금지) | 'allow'(동점허용)
def rank_convert(members, order_key, rng, ties="strict", jitter=None):
    out={}
    n=len(members)
    if not n: return out
    vals=[order_key[i] for i in members]
    if ties=="strict":
        # 동점 금지 — 값이 같으면 jitter(있으면 부서장의 내적 신호, 없으면 무작위)로 강제 서열화
        if jitter is None:
            vals=[(v, rng.random()) for v in vals]
        else:
            vals=[(v, jitter[i]) for v,i in zip(vals,members)]
        order=sorted(range(n), key=lambda k: vals[k])
        r=[0]*n
        for p,k in enumerate(order): r[k]=p+1
        for k,i in enumerate(members): out[i]=clamp(TARGET_MEAN+TARGET_SD*blom_at(r[k],n)/s_norm(n))
    else:
        r=avg_ranks(vals)
        for k,i in enumerate(members): out[i]=clamp(TARGET_MEAN+TARGET_SD*blom_at(r[k],n)/s_norm(n))
    return out

# ── ±5점 조정 ([별표 9] 제7호) — 합계 0
def apply_adj(members, base, sig, band=5.0):
    if band<=0 or len(members)<2: return base
    vals=[sig[i] for i in members]; m=st.mean(vals)
    adj={i: max(-band,min(band,ADJ_COEF*(sig[i]-m))) for i in members}
    ma=st.mean(adj.values())
    return {i: clamp(base[i]+adj[i]-ma) for i in members}

def metrics(org, people, ab, tot, absolute=False, abs_sd=None):
    n=len(people)
    if absolute:
        m=st.mean(tot); s=st.pstdev(tot) or 1.0
        sd = abs_sd if abs_sd else TARGET_SD
        pts=[clamp(TARGET_MEAN+sd*(x-m)/s, 0, 200) for x in tot]
        raw=[x for x in tot]
    else:
        gr,pts=assign_grades(tot, lambda i: people[i]["g"]); raw=pts
    dep=[p["d"] for p in people]
    va,vd,vr=var_decomp(pts,ab,dep)
    cut=sorted(ab)[int(0.8*n)]
    big=[pts[i] for i,p in enumerate(people) if ab[i]>=cut and org[p["d"]][1]>=16]
    sml=[pts[i] for i,p in enumerate(people) if ab[i]>=cut and org[p["d"]][1]<=3]
    gs=(st.mean(big)-st.mean(sml)) if (big and sml) else float('nan')
    return (spearman(ab,pts), decile_sd(ab,pts), va,vd,vr, gs, st.pstdev(pts))
