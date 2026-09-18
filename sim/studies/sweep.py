# -*- coding: utf-8 -*-
"""다면평가 배점 확대 곡선 — 조밀 스윕 + 20% 지점 강건성"""
from core import *
from drive4 import run

S2, R = 0.9, 400          # 본부장 관측오차 0.9σ (조합에 불리한 쪽), 반복 400회
hi = run(REAL,0.60,0.3,S2,0.10,4,0.6,0.30,mode="current",peer_signal=False,reps=R)
lo = run(REAL,0.60,0.3,S2,0.10,4,0.6,0.30,ideal=True,reps=R)
span = hi["sd"] - lo["sd"]
def pct(v): return (hi["sd"] - v) / span * 100

print("현행 지표2 SD %.3f · 이상적 하한 %.3f · 제거가능 폭 %.3f" % (hi["sd"], lo["sd"], span))
print()
print("【다면 배점 곡선】 동료 4인 · 관측오차 0.6σ · 선호반영 0.30")
print(f"{'다면%':>6} {'업적역량%':>9} {'지표2 SD':>9} {'제거율':>8} {'rho':>6} {'부서%':>6} {'규모격차':>8}")
for wm in (0.0,0.05,0.10,0.15,0.20,0.25,0.30,0.40,0.50):
    r = run(REAL,0.60,0.3,S2,wm,4,0.6,0.30,reps=R)
    core = (1.0 - wm - W_COMMON) * 100
    print(f"{wm*100:6.0f} {core:9.0f} {r['sd']:9.3f} {pct(r['sd']):7.1f}% {r['rho']:6.3f} {r['v_dept']:6.1f} {r['size']:+8.2f}")

print()
print("【20% 지점 강건성】 조합에 불리한 방향으로 하나씩 틀어본다")
print(f"{'조건':<34} {'제거율':>8} {'10%대비':>9}")
base10 = pct(run(REAL,0.60,0.3,S2,0.10,4,0.6,0.30,reps=R)["sd"])
CASES = [
    ("기준 (동료 4인·오차0.6·선호0.30)", dict(k_peer=4, sp=0.6, fp=0.30)),
    ("동료 8인", dict(k_peer=8, sp=0.6, fp=0.30)),
    ("동료 2인", dict(k_peer=2, sp=0.6, fp=0.30)),
    ("동료 관측오차 1.2σ", dict(k_peer=4, sp=1.2, fp=0.30)),
    ("동료 선호반영 0.70 (극단형 수준)", dict(k_peer=4, sp=0.6, fp=0.70)),
    ("동료 2인 + 오차1.2 + 선호0.70", dict(k_peer=2, sp=1.2, fp=0.70)),
]
for name, kw in CASES:
    v = pct(run(REAL,0.60,0.3,S2,0.20,kw["k_peer"],kw["sp"],kw["fp"],reps=R)["sd"])
    print(f"{name:<34} {v:7.1f}% {v-base10:+8.1f}p")
print()
print(f"※ 비교 기준: 다면 10%(현행 배점)의 제거율 {base10:.1f}%")
