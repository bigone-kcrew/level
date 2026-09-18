# -*- coding: utf-8 -*-
"""후보2(순위 제출→[별표9] 변환) 이 정본 award(mode='reform') 과 수학적으로 동일한지 확인.
난수 스트림 소비를 같게 맞추고 개인별 점수를 직접 대조한다."""
import os
import sys, random, statistics as st
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from ycore import *

rng=random.Random(1)
maxdiff=0.0; ncmp=0
for _ in range(300):
    n=rng.choice([3,4,6,9,11,14,16])
    mem=list(range(n)); sig={i:rng.gauss(0,1) for i in mem}
    a=award(mem,"S",sig,"reform",rng,0.0)           # 정본: 점수→순위→Blom
    # 후보2: 부서장이 순위만 제출, 인사부서가 z=probit((r-0.375)/(n+0.25)), 80+7z
    vals=[sig[i] for i in mem]; r=ranks(vals)
    b={i: clamp(TARGET_MEAN+TARGET_SD*probit((r[k]-0.375)/(n+0.25))) for k,i in enumerate(mem)}
    for i in mem:
        maxdiff=max(maxdiff, abs(a[i]-b[i])); ncmp+=1
print("비교 인원 %d명 · 최대 절대차 %.12f" % (ncmp, maxdiff))
print("→ 동일" if maxdiff<1e-9 else "→ 불일치")
# 부여점수 예시 (평가군 규모별 1위 점수)
print("\n[별표 9] 산식으로 산출되는 평가군 규모별 점수 (1위/최하위)")
for n in (3,4,5,6,8,10,12,14,16):
    z=[probit((r-0.375)/(n+0.25)) for r in range(1,n+1)]
    print(f"  n={n:2d}  1위 {80+7*z[-1]:6.2f}  최하위 {80+7*z[0]:6.2f}  부여폭 {7*(z[-1]-z[0]):5.2f}")
