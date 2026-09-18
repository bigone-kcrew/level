# -*- coding: utf-8 -*-
"""배치 편중 가설 — 극단 성향 부서에 우수인력, 균등 성향 부서에 기피인원이 모인다면?
   인사배치는 정성 판단이고 피평가자는 부서를 선택할 수 없다.
   g = 두 유형 부서 간 실제 실력 평균 격차(σ 단위). 극단형 +g/2, 균등형 -g/2."""
import os
import sys, random, statistics as st
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
import sim as S

def build_shift(g):
    depts, dept_hq = [], {}
    for hq, ds in enumerate(S.ORG.values()):
        for _n, sz in ds.items():
            dept_hq[len(depts)] = hq; depts.append(sz)
    nd = len(depts)
    dept_ty = {d: ("S" if random.random() < S.MGR_MIX["S"] else "N") for d in range(nd)}
    people, dmem, hmem = [], {d: [] for d in range(nd)}, {h: [] for h in range(S.N_HQ)}
    for d, sz in enumerate(depts):
        mu = (+g/2) if dept_ty[d] == "S" else (-g/2)      # 배치 편중
        for _ in range(sz):
            people.append({"a": random.gauss(0,1) + mu, "f": random.gauss(0,1), "d": d})
            dmem[d].append(len(people)-1); hmem[dept_hq[d]].append(len(people)-1)
    for i, lb in enumerate(S.rank_labels(len(people))): people[i]["g"] = lb
    return people, dept_hq, dept_ty, dmem, hmem, S.draw_hq_types()

def run(mode, g, reps=400, seed=S.SEED):
    random.seed(seed)
    dec, rho = [], []
    hit = {ty: {"botC":0, "botN":0, "topC":0, "topN":0} for ty in ("S","N")}
    for _ in range(reps):
        people, dhq, dty, dmem, hmem, hty = build_shift(g)
        tot = S.composite(people, dty, dmem, hmem, mode,
                          mean_cap_slack=(3.0 if mode=="current" else 0.0), hq_ty=hty)
        gr, pts = S.assign_grades(tot, lambda i: people[i]["g"],
                                  S.ABSOLUTE_REFORM if mode=="reform" else ())
        ab = [p["a"] for p in people]; n = len(ab); srt = sorted(ab)
        c10, med = srt[int(.10*n)], srt[int(.50*n)]
        rho.append(S.spearman(ab, pts))
        # 지표2 — 같은 실력 십분위 내 평정점 표준편차
        order = sorted(range(n), key=lambda i: ab[i]); sds = []
        for k in range(10):
            grp = order[int(k*n/10):int((k+1)*n/10)]
            v = [pts[i] for i in grp if gr[i] is not None]
            if len(v) > 1: sds.append(st.pstdev(v))
        dec.append(st.mean(sds))
        for i, p in enumerate(people):
            if gr[i] is None: continue
            ty = dty[p["d"]]
            if ab[i] <= c10:
                hit[ty]["botN"] += 1; hit[ty]["botC"] += (gr[i] == "C")
            if ab[i] >= med:
                hit[ty]["topN"] += 1; hit[ty]["topC"] += (gr[i] == "C")
    f = lambda ty,k: hit[ty][k+"C"]/max(1,hit[ty][k+"N"])*100
    return dict(sd=st.mean(dec), rho=st.mean(rho),
                botS=f("S","bot"), botN=f("N","bot"), topS=f("S","top"), topN=f("N","top"))

print(f"{'배치격차 g':>10} {'제도':>6} {'지표2':>7} {'제거율':>7} {'rho':>6} "
      f"{'하위10%C:극단':>13} {'하위10%C:균등':>13} {'상위50%C:극단':>13}")
LO = {}
for g in (0.0, 0.4, 0.8):
    cur = run("current", g); ref = run("reform", g)
    # 이상적 하한: 실력을 완전 관측 (400회)
    random.seed(S.SEED); dec=[]
    for _ in range(400):
        people,_dhq,dty,_dm,_hm,_ht = build_shift(g)
        tot=[80+7*p["a"] for p in people]
        gr,pts=S.assign_grades(tot, lambda i: people[i]["g"], ())
        ab=[p["a"] for p in people]; n=len(ab)
        order=sorted(range(n), key=lambda i: ab[i]); sds=[]
        for k in range(10):
            grp=order[int(k*n/10):int((k+1)*n/10)]
            v=[pts[i] for i in grp]
            if len(v)>1: sds.append(st.pstdev(v))
        dec.append(st.mean(sds))
    lo=st.mean(dec)
    if g == 0.0: LO["span"] = cur["sd"] - lo; LO["cur"] = cur["sd"]
    span = LO["span"]                    # ★ 분모는 g=0 조건으로 고정한다
    for nm, r in (("현행", cur), ("개선", ref)):
        pc=(LO["cur"]-r["sd"])/span*100 if span else 0.0
        print(f"{g:10.1f} {nm:>6} {r['sd']:7.3f} {pc:6.1f}% {r['rho']:6.3f} "
              f"{r['botS']:12.1f}% {r['botN']:12.1f}% {r['topS']:12.1f}%")
    print(f"{'':10} {'(하한)':>6} {lo:7.3f} {100.0:6.1f}%")
