# -*- coding: utf-8 -*-
"""이상치 한 명이 나머지에게 무슨 일을 하는가

일치법(A)은 평가군의 표준편차를 목표값에 맞춘다. 그래서 한 명에게 극단적으로 낮은
점수를 주면 그 한 명이 표준편차를 부풀리고, 나머지는 목표 표준편차 안으로 눌려
서로 구별되지 않게 된다. 순위환산(C·D)은 순위만 쓰므로 이 현상이 없다.

실제 사례 형태: 10명 부서에서 9명에게 87~90점, 문제 직원 1명에게 55점.
규정으로 막을 수 있는지가 협의 쟁점이므로 크기를 측정한다.
"""
import sys, math, statistics as st
B = "/tmp/claude-1026/-workspace-level/d1335fd1-a874-4b1d-8f74-fa3659a33222/scratchpad"
sys.path.insert(0, B + "/yellow"); sys.path.insert(0, B + "/observer")
from ycore import blom_at, zfix
from core import TARGET_MEAN, TARGET_SD, clamp

def s_of(n):
    b = [blom_at(r, n) for r in range(1, n + 1)]
    m = sum(b) / n
    return math.sqrt(sum((x - m) ** 2 for x in b) / n) or 1.0

def conv(raw, method):
    n = len(raw); mem = list(range(n))
    if method == "meansd":
        d = zfix(mem, {i: raw[i] for i in mem}); return [d[i] for i in mem]
    rk = {i: k + 1 for k, i in enumerate(sorted(mem, key=lambda i: raw[i]))}
    if method == "linear":
        return [clamp(60.0 + (40.0 / n) * (n - rk[i] + 1)) for i in mem]
    s = s_of(n)
    return [clamp(TARGET_MEAN + TARGET_SD * blom_at(rk[i], n) / s) for i in mem]

print("10명 부서 · 상위 9명은 실력 순으로 87~90점 · 나머지 1명에게만 낮은 점수를 준다")
print("측정: 상위 9명이 받는 보정점수의 폭(최고−최저). 이 폭이 좁으면 9명은 서로 구별되지 않는다")
print()
print(f"{'문제직원 원점수':>14}{'평가군 SD':>11}   "
      f"{'A 일치법':>10}{'C 선형':>10}{'D 정규(개정안)':>16}")
print("─" * 66)
nine = [87.0 + 3.0 * k / 8 for k in range(9)]          # 87.00 … 90.00, 등간
for low in (86.0, 80.0, 70.0, 60.0, 55.0, 40.0):
    raw = nine + [low]
    sd = st.pstdev(raw)
    row = [f"{low:>13.0f}점{sd:>10.2f}   "]
    for m in ("meansd", "linear", "blom_s"):
        out = conv(raw, m)
        top9 = sorted(out)[1:]                          # 문제직원 제외
        row.append(f"{max(top9)-min(top9):>10.2f}")
    print("".join(row[:1] + [f"{x:>10}" if False else x for x in row[1:]]))
print()
print("A 일치법의 9명 폭은 문제직원 점수가 낮아질수록 줄어든다 — 한 사람의 점수가")
print("나머지 9명의 변별력을 결정한다. C·D 는 순위만 쓰므로 폭이 고정된다.")
