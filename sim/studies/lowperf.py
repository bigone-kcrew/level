# -*- coding: utf-8 -*-
"""사측 관심 지표 — 저성과자가 실제로 C를 받는가 / 우수자가 억울하게 C를 받는가
정본 sim/sim.py 의 상수·함수를 그대로 쓴다."""
import os
import sys, random, statistics as st
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
import sim as S

def run(mode, reps=400, seed=S.SEED):
    random.seed(seed)
    # 하위10% / 하위25% / 상위50% 별로 C·B·A·S 획득률, 부서장 유형별
    acc = {ty: {band: {g: 0 for g in "SABC"} for band in ("bot10","bot25","top50")}
           for ty in ("S","N")}
    cnt = {ty: {band: 0 for band in ("bot10","bot25","top50")} for ty in ("S","N")}
    for _ in range(reps):
        people, dept_hq, dept_ty, dmem, hmem, hq_ty = S.build()
        tot = S.composite(people, dept_ty, dmem, hmem, mode,
                          mean_cap_slack=(3.0 if mode == "current" else 0.0),
                          hq_ty=hq_ty)
        gr, _pts = S.assign_grades(tot, lambda i: people[i]["g"],
                                   S.ABSOLUTE_REFORM if mode == "reform" else ())
        ab = [p["a"] for p in people]
        n = len(ab); srt = sorted(ab)
        c10, c25, med = srt[int(.10*n)], srt[int(.25*n)], srt[int(.50*n)]
        for i, p in enumerate(people):
            if gr[i] is None: continue
            ty = dept_ty[p["d"]]
            for band, ok in (("bot10", ab[i] <= c10), ("bot25", ab[i] <= c25),
                             ("top50", ab[i] >= med)):
                if ok:
                    cnt[ty][band] += 1
                    acc[ty][band][gr[i]] += 1
    return acc, cnt

LBL = {"bot10": "실력 하위 10%", "bot25": "실력 하위 25%", "top50": "실력 상위 50%"}
TY  = {"S": "극단 성향 부서장", "N": "균등 성향 부서장"}
for mode, name in (("current", "현행 (사전조정계수)"), ("reform", "개선 (순위기반 보정 + ±5점)")):
    a, c = run(mode)
    print(f"\n[{name}]")
    print(f"{'':<28} {'C':>7} {'B':>7} {'A':>7} {'S':>7}")
    for band in ("bot10", "bot25", "top50"):
        for ty in ("S", "N"):
            t = c[ty][band] or 1
            r = [acc_ / t * 100 for acc_ in (a[ty][band]["C"], a[ty][band]["B"],
                                             a[ty][band]["A"], a[ty][band]["S"])]
            print(f"{LBL[band]:<14}{TY[ty]:<14}" + "".join(f"{v:6.1f}%" for v in r))


# ── C 정원은 고정인가 — 부서장 유형별 C 인원 (문서의 「정원은 고정입니다」 표 정본)
#    유형별 인원은 반복마다 무작위 배정되므로 평균 인원으로 낸다.
def c_headcount(mode, reps=400, seed=S.SEED):
    random.seed(seed)
    tot_c = {"S": 0.0, "N": 0.0}
    tot_n = {"S": 0.0, "N": 0.0}
    for _ in range(reps):
        people, dept_hq, dept_ty, dmem, hmem, hq_ty = S.build()
        t = S.composite(people, dept_ty, dmem, hmem, mode,
                        mean_cap_slack=(3.0 if mode == "current" else 0.0), hq_ty=hq_ty)
        gr, _ = S.assign_grades(t, lambda i: people[i]["g"],
                                S.ABSOLUTE_REFORM if mode == "reform" else ())
        for i, p in enumerate(people):
            ty = dept_ty[p["d"]]
            if ty not in tot_c or gr[i] is None:
                continue
            tot_n[ty] += 1
            if gr[i] == "C":
                tot_c[ty] += 1
    return {ty: (tot_c[ty] / reps, tot_n[ty] / reps) for ty in ("S", "N")}

print("\n[C 정원은 고정인가 — 부서장 유형별 C 인원]")
print(f"{'':<12}{'극단 성향 부서':>22}{'균등 성향 부서':>22}{'합계':>10}")
res = {}
for mode, name in (("current", "현행"), ("reform", "개선")):
    h = c_headcount(mode); res[mode] = h
    s_c, s_n = h["S"]; n_c, n_n = h["N"]
    print(f"{name:<12}{s_c:>11.1f}명 ({100*s_c/s_n:>4.1f}%)"
          f"{n_c:>11.1f}명 ({100*n_c/n_n:>4.1f}%){s_c+n_c:>8.1f}명")
d_s = res["reform"]["S"][0] - res["current"]["S"][0]
d_n = res["reform"]["N"][0] - res["current"]["N"][0]
print(f"{'변화':<12}{d_s:>+16.1f}명{d_n:>+21.1f}명{d_s+d_n:>+15.1f}명")
print("※ 유형별 인원은 반복마다 무작위 배정되므로 400회 평균 인원이다. 원장직속(유형 O)은 제외.")
