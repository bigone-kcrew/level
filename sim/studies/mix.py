# -*- coding: utf-8 -*-
"""반박 검증 — '나와 같이 일하지 않은 동료가 평가하는 게 맞나'
동료를 두 종류로 나눈다.
  접점 동료  : 관측오차 0.4σ · 선호반영 0.30   (실제 협업)
  무접점 동료: 관측오차 2.0σ · 선호반영 0.60   (거의 모름 → 평판·인기로 대체)
q = 평가자 중 접점 동료 비율. q를 0부터 1까지 훑는다."""
import random, math, statistics as st
from core import *
from drive1 import build

NEAR = dict(sp=0.4, fp=0.30)
FAR  = dict(sp=2.0, fp=0.60)

def run(w_multi, k, q, mode="reform", reps=400, s2n=0.9, w1=0.60, s1n=0.3,
        seed=20260910, ideal=False, peer_signal=True):
    rng = random.Random(seed); w2 = 1.0 - w1
    w_core = 1.0 - w_multi - W_COMMON
    k_near = int(round(q * k)); k_far = k - k_near
    M = []
    for _ in range(reps):
        people, dmem, hmem, dty, hty = build(REAL, rng, 0.0)
        n = len(people); ab = [p["a"] for p in people]
        if ideal:
            tot = [TARGET_MEAN + TARGET_SD * p["a"] for p in people]
        else:
            sg1 = {}; sg2 = {}; sgp = {}
            for i, p in enumerate(people):
                f1 = FAVOR[dty[p["d"]]]; f2 = FAVOR[hty[p["h"]]]
                sg1[i] = (1-f1)*p["a"] + f1*p["f"] + rng.gauss(0, s1n)
                sg2[i] = (1-f2)*p["a"] + f2*p["f"] + rng.gauss(0, s2n)
                if peer_signal and k > 0:
                    acc = 0.0
                    for _j in range(k_near):
                        acc += (1-NEAR["fp"])*p["a"] + NEAR["fp"]*rng.gauss(0,1) + rng.gauss(0, NEAR["sp"])
                    for _j in range(k_far):
                        acc += (1-FAR["fp"])*p["a"] + FAR["fp"]*rng.gauss(0,1) + rng.gauss(0, FAR["sp"])
                    sgp[i] = acc / k
                else:
                    sgp[i] = rng.gauss(0, 1)
            s1 = {}; s2 = {}
            for d, mem in dmem.items(): s1.update(award(mem, dty[d], sg1, mode, rng, 0.0))
            for h, mem in hmem.items(): s2.update(award(mem, hty[h], sg2, mode, rng))
            sp_out = award(list(range(n)), "N", sgp, "reform", rng)
            tot = [w_core*(w1*s1[i] + w2*s2[i]) + w_multi*sp_out[i]
                   + W_COMMON*clamp(95 + 4*rng.gauss(0,1), 70, 100) for i in range(n)]
        gr, pts = assign_grades(tot, lambda i: people[i]["g"])
        M.append((spearman(ab, pts), decile_sd(ab, pts)))
    return dict(rho=st.mean(m[0] for m in M), sd=st.mean(m[1] for m in M))

R = 400
hi = run(0.10, 4, 1.0, mode="current", peer_signal=False, reps=R)
lo = run(0.10, 4, 1.0, ideal=True, reps=R)
span = hi["sd"] - lo["sd"]
def pct(v): return (hi["sd"] - v) / span * 100

print("현행 %.3f · 이상적 하한 %.3f · 제거가능 폭 %.3f  (반복 %d)" % (hi["sd"], lo["sd"], span, R))
print()
print("【접점 비율 q에 따른 다면 배점의 가치】 평가자 4인 고정")
print(f"{'q(접점비율)':>11} {'다면10%':>9} {'다면20%':>9} {'20−10':>8} {'다면30%':>9}")
for q in (0.0, 0.25, 0.50, 0.75, 1.0):
    a = pct(run(0.10, 4, q, reps=R)["sd"])
    b = pct(run(0.20, 4, q, reps=R)["sd"])
    c = pct(run(0.30, 4, q, reps=R)["sd"])
    print(f"{q:11.2f} {a:8.1f}% {b:8.1f}% {b-a:+7.1f}p {c:8.1f}%")
print()
print("【평가자 선정 방식 비교】 다면 20% 고정 — 같은 배점, 다른 선정")
print(f"{'선정 방식':<38} {'평가자수':>7} {'접점비율':>7} {'제거율':>8}")
for name, k, q in [
    ("부서 전원 자동 지정 (10명 부서)",        9, 0.35),
    ("부서 전원 자동 지정 (16명 부서)",       15, 0.25),
    ("업무 관련자 지명 4인",                   4, 1.00),
    ("업무 관련자 지명 4인 + 무관자 2인 혼입", 6, 0.67),
    ("업무 관련자 지명 6인",                   6, 1.00),
    ("무작위 4인 (접점 무관)",                 4, 0.35),
]:
    print(f"{name:<38} {k:7d} {q:7.2f} {pct(run(0.20, k, q, reps=R)['sd']):7.1f}%")
