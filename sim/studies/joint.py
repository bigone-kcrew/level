# -*- coding: utf-8 -*-
"""결합 효과 — 1차(부서장) 유형과 2차(본부장) 유형이 겹치면 어떻게 되는가.
   문서의 「부서장 × 본부장」 결합표 정본. 조건 ①.
   부서원은 부서장(1차) 60% + 본부장(2차) 40% 로 평가되므로, 두 유형의 조합이
   실제로 겪는 조건이다. 유형은 반복마다 무작위 배정되며 특정 본부를 지목하지 않는다."""
import os, sys, random, statistics as st
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
import sim as S

CELLS = (("S", "S"), ("S", "N"), ("N", "S"), ("N", "N"))
LBL = {("S","S"): "극단 부서장 × 극단 본부장", ("S","N"): "극단 부서장 × 균등 본부장",
       ("N","S"): "균등 부서장 × 극단 본부장", ("N","N"): "균등 부서장 × 균등 본부장"}

def run(mode, reps=400, seed=S.SEED):
    random.seed(seed)
    hit = {c: {"S": 0, "C": 0, "n": 0} for c in CELLS}
    tot_n = 0
    for _ in range(reps):
        people, dept_hq, dty, dmem, hmem, hty = S.build()
        t = S.composite(people, dty, dmem, hmem, mode,
                        mean_cap_slack=(3.0 if mode == "current" else 0.0), hq_ty=hty)
        gr, _ = S.assign_grades(t, lambda i: people[i]["g"],
                                S.ABSOLUTE_REFORM if mode == "reform" else ())
        for i, p in enumerate(people):
            if gr[i] is None:
                continue
            c = (dty[p["d"]], hty[dept_hq[p["d"]]])
            if c not in hit:                      # 원장직속(유형 O) 제외
                continue
            hit[c]["n"] += 1; tot_n += 1
            if gr[i] == "S": hit[c]["S"] += 1
            if gr[i] == "C": hit[c]["C"] += 1
    return hit, tot_n

cur, cn = run("current"); ref, rn = run("reform")
print(f"{'조합':<26}{'현행 S':>9}{'개선 S':>9}{'현행 C':>9}{'개선 C':>9}{'인원 비중':>11}")
print("─" * 74)
for c in CELLS:
    a, b = cur[c], ref[c]
    print(f"{LBL[c]:<24}{100*a['S']/a['n']:>8.1f}%{100*b['S']/b['n']:>8.1f}%"
          f"{100*a['C']/a['n']:>8.1f}%{100*b['C']/b['n']:>8.1f}%{100*a['n']/cn:>10.1f}%")
sc = [100*cur[c]['S']/cur[c]['n'] for c in CELLS]
sr = [100*ref[c]['S']/ref[c]['n'] for c in CELLS]
cc = [100*cur[c]['C']/cur[c]['n'] for c in CELLS]
print()
print(f"S 획득률 — 현행 최고 {max(sc):.1f}% · 최저 {min(sc):.1f}% · 배율 {max(sc)/min(sc):.2f}배")
print(f"           개선 최고 {max(sr):.1f}% · 최저 {min(sr):.1f}% · 배율 {max(sr)/min(sr):.2f}배")
print(f"C 획득률 — 현행 최고 {max(cc):.1f}% · 최저 {min(cc):.1f}%")
print(f"※ 「균등 부서장 × 균등 본부장」에 해당하는 인원이 전체의 "
      f"{100*cur[('N','N')]['n']/cn:.1f}% 다.")
