# -*- coding: utf-8 -*-
"""임계값 정밀 탐색 + 1차 100:0 + 규모 격차"""
from core import *
from drive1 import run
import statistics as st

print("═══ ①-1 역전 임계값 정밀 탐색 (실제 조직 · 400회) ═══")
print("   지표2 SD — 낮을수록 좋다. 60:40(현행) 대비 50:50 의 차이\n")
print(f"{'σ2':>5} {'70:30':>8} {'60:40':>8} {'50:50':>8} {'40:60':>8}   {'50:50−60:40':>12}  판정")
for s2n in (0.3,0.5,0.6,0.7,0.8,0.9,1.0,1.2):
    row={}
    for w1 in (0.70,0.60,0.50,0.40):
        row[w1]=run(REAL,"reform",w1,0.3,s2n,reps=400)['sd']
    d=row[0.50]-row[0.60]
    verdict="50:50 이 낫다" if d<-0.005 else ("60:40 이 낫다" if d>0.005 else "차이 없음")
    print(f"{s2n:5.2f} {row[0.70]:8.3f} {row[0.60]:8.3f} {row[0.50]:8.3f} {row[0.40]:8.3f}   {d:+12.3f}  {verdict}")

print("\n═══ ①-2 1차 100:0 (2차 평가자 폐지) ═══")
print(f"{'σ2':>5} {'100:0':>8} {'70:30':>8} {'60:40':>8}   최적")
for s2n in (0.3,0.6,0.9,1.2,1.5):
    r100=run(REAL,"reform",1.0,0.3,s2n,reps=400)
    r70=run(REAL,"reform",0.70,0.3,s2n,reps=400)['sd']
    r60=run(REAL,"reform",0.60,0.3,s2n,reps=400)['sd']
    best=min([(r100['sd'],'100:0'),(r70,'70:30'),(r60,'60:40')])
    print(f"{s2n:5.1f} {r100['sd']:8.3f} {r70:8.3f} {r60:8.3f}   {best[1]}")

print("\n═══ ①-3 규모 격차 (합성 조직 240명 · 상위20% · 16명−3명 부서) ═══")
print(f"{'σ2':>5} {'1차비율':>7} {'지표2':>8} {'규모격차':>9} {'부서%':>6}")
for s2n in (0.3,0.9,1.5):
    for w1 in (1.0,0.70,0.60,0.50,0.40):
        r=run(SYNTH,"reform",w1,0.3,s2n,reps=400)
        lbl="100:0" if w1==1.0 else f"{int(w1*100)}:{int((1-w1)*100)}"
        print(f"{s2n:5.1f} {lbl:>7} {r['sd']:8.3f} {r['size']:+9.3f} {r['v_dept']:6.1f}")
    print()

print("═══ ①-4 현행 vs 개선 — 관측오차를 넣어도 총량 판정이 유지되는가 ═══")
print(f"{'σ2':>5} {'제도':>22} {'지표2':>8} {'rho':>7} {'부서%':>6}")
for s2n in (0.3,0.9,1.5):
    c=run(REAL,"current",0.60,0.3,s2n,reps=400)
    b=run(REAL,"reform",0.60,0.3,s2n,reps=400)
    a=run(REAL,"reform",0.60,0.3,s2n,reps=400,adj=5.0)
    i=run(REAL,"reform",0.60,0.3,s2n,reps=400,ideal=True)
    for nm,r in (("현행",c),("개선·보정만",b),("개선·보정+제7호",a),("(이상적)",i)):
        print(f"{s2n:5.1f} {nm:>22} {r['sd']:8.3f} {r['rho']:7.3f} {r['v_dept']:6.1f}")
    print()
