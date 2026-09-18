# -*- coding: utf-8 -*-
"""관측 정확도 비대칭을 넣은 근무평정 모형 + 지표.
원본 sim.py 를 복제·확장한 것이며 원본을 수정하지 않는다."""
import random, math, statistics as st

# ── 실제 조직 (22개 평가군 · 213명). 원장직속은 hq=5
REAL = [(0,10),(0,8),(0,14),(0,6), (1,11),(1,8),(1,12),(1,9),
        (2,12),(2,11),(2,14),(2,16),(2,6), (3,12),(3,9),(3,12),
        (4,11),(4,6),(4,10),(4,9), (5,4),(5,3)]
DIRECTOR_HQ = 5
# ── 합성 조직 (규모 효과 측정용) — 원장직속 없음, 규모 3~16 균형 배치
SYNTH = [(h, s) for h in range(4) for s in (3,6,10,16)] + [(h, s) for h in range(4) for s in (4,8,13)]

GRADE = [("S",0.20),("A",0.30),("B",0.40),("C",0.10)]
BANDS = {"S":100,"A":90,"B":80,"C":70}
RANK_MIX = [("1(나)급",4),("2급",11),("3급",29),("4급",40),("5급",107),("공무직",5)]
W_CORE, W_MULTI, W_COMMON = 0.85, 0.10, 0.05
SPREAD = {"S":13.0,"N":2.0,"O":7.0}
FAVOR  = {"S":0.70,"N":0.0,"O":0.0}
TARGET_MEAN, TARGET_SD = 80.0, 7.0
ADJ_COEF = 4.0
MEAN_SLACK = 3.0
N_EXTREME = 2
MGR_S = 0.50

def probit(p):
    a=[-3.969683028665376e+01,2.209460984245205e+02,-2.759285104469687e+02,
       1.383577518672690e+02,-3.066479806614716e+01,2.506628277459239e+00]
    b=[-5.447609879822406e+01,1.615858368580409e+02,-1.556989798598866e+02,
       6.680131188771972e+01,-1.328068155288572e+01]
    c=[-7.784894002430293e-03,-3.223964580411365e-01,-2.400758277161838e+00,
       -2.549732539343734e+00,4.374664141464968e+00,2.938163982698783e+00]
    d=[7.784695709041462e-03,3.224671290700398e-01,2.445134137142996e+00,3.754408661907416e+00]
    pl=0.02425
    if p<pl:
        q=math.sqrt(-2*math.log(p))
        return (((((c[0]*q+c[1])*q+c[2])*q+c[3])*q+c[4])*q+c[5])/((((d[0]*q+d[1])*q+d[2])*q+d[3])*q+1)
    if p>1-pl:
        q=math.sqrt(-2*math.log(1-p))
        return -(((((c[0]*q+c[1])*q+c[2])*q+c[3])*q+c[4])*q+c[5])/((((d[0]*q+d[1])*q+d[2])*q+d[3])*q+1)
    q=p-0.5; r=q*q
    return (((((a[0]*r+a[1])*r+a[2])*r+a[3])*r+a[4])*r+a[5])*q/(((((b[0]*r+b[1])*r+b[2])*r+b[3])*r+b[4])*r+1)

_BL={}
def blom(n):
    if n not in _BL: _BL[n]=[probit((i-0.375)/(n+0.25)) for i in range(1,n+1)]
    return _BL[n]

def s_norm(n):
    """[별표 9] 제3호 — 정규 순서통계량 n개의 모집단 표준편차 s(n).
    나누지 않으면 부여폭이 s(n)배로 줄어 목표 표준편차에 도달하지 못한다."""
    b=blom(n); m=sum(b)/n
    return math.sqrt(sum((x-m)**2 for x in b)/n) or 1.0


def ranks(v):
    o=sorted(range(len(v)), key=lambda i:v[i]); r=[0]*len(v)
    for p,i in enumerate(o): r[i]=p+1
    return r

def spearman(x,y):
    rx,ry=ranks(x),ranks(y); m=(len(x)+1)/2
    num=sum((a-m)*(b-m) for a,b in zip(rx,ry))
    dx=sum((a-m)**2 for a in rx); dy=sum((b-m)**2 for b in ry)
    den=math.sqrt(dx*dy); return num/den if den else 0.0

def clamp(v,lo=60.0,hi=100.0): return max(lo,min(hi,v))

# ── 지표 2: 실력 십분위 내 평정점 표준편차의 가중평균
def decile_sd(ability, pts, q=10):
    n=len(ability); order=sorted(range(n), key=lambda i:ability[i])
    tot=0.0; wsum=0
    for k in range(q):
        lo=k*n//q; hi=(k+1)*n//q
        grp=[pts[i] for i in order[lo:hi]]
        if len(grp)>1:
            tot+=st.pstdev(grp)*len(grp); wsum+=len(grp)
    return tot/wsum if wsum else 0.0

# ── 지표 3: 분산분해 (FWL) — 실력 먼저, 그 다음 부서 고정효과 증분
def var_decomp(pts, ability, dept):
    n=len(pts); my=st.mean(pts)
    sst=sum((y-my)**2 for y in pts)
    if sst<=0: return (0.0,0.0,100.0)
    mx=st.mean(ability)
    sxx=sum((x-mx)**2 for x in ability)
    sxy=sum((x-mx)*(y-my) for x,y in zip(ability,pts))
    b=sxy/sxx if sxx>0 else 0.0
    res1=[y-(my+b*(x-mx)) for x,y in zip(ability,pts)]
    ss1=sum(r*r for r in res1)
    r2_a=1-ss1/sst
    # 부서 더미 추가: 잔차를 부서 평균으로 한 번 더 설명
    by={}
    for r,d in zip(res1,dept): by.setdefault(d,[]).append(r)
    dm={d:st.mean(v) for d,v in by.items()}
    res2=[r-dm[d] for r,d in zip(res1,dept)]
    ss2=sum(r*r for r in res2)
    r2_full=1-ss2/sst
    return (100*r2_a, 100*(r2_full-r2_a), 100*(1-r2_full))

def rank_labels(n, rng):
    tot=sum(c for _,c in RANK_MIX)
    quota=[(l, n*c/tot) for l,c in RANK_MIX]
    cnt={l:int(q) for l,q in quota}; used=sum(cnt.values())
    order=sorted(range(len(quota)), key=lambda k:-(quota[k][1]-int(quota[k][1])))
    for k in order[:n-used]: cnt[quota[k][0]]+=1
    out=[]
    for l,_ in RANK_MIX: out+=[l]*cnt[l]
    rng.shuffle(out); return out[:n]

def _alloc(idx, scores, grade, pts):
    m=len(idx)
    if not m: return
    cnt=[]; acc=0
    for _,p in GRADE[:-1]:
        c=round(m*p); cnt.append(c); acc+=c
    cnt.append(max(0,m-acc))
    if m<10 and cnt[-1]>0: cnt[-2]+=cnt[-1]; cnt[-1]=0
    order=sorted(idx, key=lambda i:-scores[i]); ix=0
    for (g,_),c in zip(GRADE,cnt):
        hi=BANDS[g]
        for j in range(c):
            if ix>=m: break
            i=order[ix]; grade[i]=g; pts[i]=hi-(10.0/c)*j if c else hi; ix+=1

def assign_grades(scores, rank_of):
    n=len(scores); grade=[None]*n; pts=[0.0]*n
    groups={}
    for i in range(n): groups.setdefault(rank_of(i),[]).append(i)
    for lbl,idx in groups.items(): _alloc(idx,scores,grade,pts)
    return grade,pts

def award(members, gtype, sig, mode, rng, adj_band=0.0):
    """sig: {i: 신호값}. mode='current'|'reform'"""
    out={}
    if not members: return out
    vals=[sig[i] for i in members]; rk=ranks(vals); bl=blom(len(members))
    sn=s_norm(len(members))        # [별표 9] 제3호 — 목표 표준편차에 실제로 도달시킨다
    if mode=="reform": base,sd = TARGET_MEAN, TARGET_SD
    elif gtype=="O":   base,sd = TARGET_MEAN, SPREAD["O"]
    else:              base,sd = TARGET_MEAN - rng.uniform(0,MEAN_SLACK), SPREAD[gtype]
    for k,i in enumerate(members): out[i]=clamp(base+sd*bl[rk[k]-1]/sn)
    if mode=="reform" and adj_band>0 and len(members)>1:
        m=st.mean(vals)
        adj=[max(-adj_band,min(adj_band,ADJ_COEF*(v-m))) for v in vals]
        ma=st.mean(adj)
        for k,i in enumerate(members): out[i]=clamp(out[i]+adj[k]-ma)
    return out
