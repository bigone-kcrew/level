# -*- coding: utf-8 -*-
"""목표 표준편차 민감도 — 규칙 [별표 9] 제4호에 박히는 유일한 상수.
   조건 ①. 분모(현행 지표2 · 이상적 하한)는 목표 표준편차와 무관하므로 고정한다.
   절단은 보정 결과가 60/100 을 벗어나 clamp 된 건수다."""
import os, sys, random, statistics as st
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
import sim as S

def metric(mode, reps=400, seed=S.SEED):
    random.seed(seed)
    dec, rho, lo_hit, hi_hit, tot_n = [], [], 0, 0, 0
    for _ in range(reps):
        people, dhq, dty, dmem, hmem, hty = S.build()
        t = S.composite(people, dty, dmem, hmem, mode,
                        mean_cap_slack=(3.0 if mode == "current" else 0.0), hq_ty=hty)
        gr, pts = S.assign_grades(t, lambda i: people[i]["g"],
                                  S.ABSOLUTE_REFORM if mode == "reform" else ())
        ab = [p["a"] for p in people]; n = len(ab)
        rho.append(S.spearman(ab, pts))
        order = sorted(range(n), key=lambda i: ab[i]); sds = []
        for k in range(10):
            grp = order[int(k*n/10):int((k+1)*n/10)]
            v = [pts[i] for i in grp if gr[i] is not None]
            if len(v) > 1: sds.append(st.pstdev(v))
        dec.append(st.mean(sds))
        # 절단 — 1차 평가군 부여값이 60/100 을 벗어나는지 직접 센다
        for d, mem in dmem.items():
            if not mem: continue
            nn = len(mem); sn = S.s_norm(nn); bl = S.blom(nn)
            for k in range(nn):
                v = S.TARGET_MEAN + S.TARGET_SD * bl[k] / sn
                tot_n += 1
                if v < 60.0: lo_hit += 1
                if v > 100.0: hi_hit += 1
    return st.mean(dec), st.mean(rho), lo_hit, hi_hit, tot_n

def ideal(reps=400, seed=S.SEED):
    random.seed(seed); dec = []
    for _ in range(reps):
        people, dhq, dty, dmem, hmem, hty = S.build()
        t = [80 + 7*p["a"] for p in people]
        gr, pts = S.assign_grades(t, lambda i: people[i]["g"], ())
        ab = [p["a"] for p in people]; n = len(ab)
        order = sorted(range(n), key=lambda i: ab[i]); sds = []
        for k in range(10):
            grp = order[int(k*n/10):int((k+1)*n/10)]
            v = [pts[i] for i in grp]
            if len(v) > 1: sds.append(st.pstdev(v))
        dec.append(st.mean(sds))
    return st.mean(dec)

S.TARGET_SD = 7.0
CUR, cur_rho = metric("current")[:2]
LOW = ideal(); SPAN = CUR - LOW
print(f"분모 고정 — 현행 {CUR:.3f} · 이상적 하한 {LOW:.3f} · 제거 가능 폭 {SPAN:.3f}"
      f"  (조건 ① · 반복 400 · 시드 {S.SEED})")
print()
print(f"{'목표 표준편차':>12}{'지표2':>8}{'제거율':>9}{'rho':>8}{'절단(하/상)':>13}{'±3σ 구간':>12}")
print("─" * 64)
for sd in (5.0, 6.0, 20.0/3.0, 7.0, 8.0, 9.0, 10.0):
    S.TARGET_SD = sd
    d, r, lo, hi, n = metric("reform")
    lbl = "6.667점" if abs(sd - 20/3) < 1e-9 else f"{sd:g}점"
    star = " ←개정안" if sd == 7.0 else ""
    print(f"{lbl:>12}{d:>8.3f}{(CUR-d)/SPAN*100:>8.1f}%{r:>8.3f}"
          f"{lo:>6} / {hi:<4}{80-3*sd:>5.0f}~{80+3*sd:<4.0f}{star}")
print()
print(f"※ 절단은 1차 평가군 부여값 {metric('reform')[4]:,}건 중 60 미만·100 초과 건수다.")
