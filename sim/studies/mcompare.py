# -*- coding: utf-8 -*-
from core import *
from mrun import run
import statistics as st

MET=[("current","현행"),("blom","개선 원안 (Blom)"),("blom_adj","개선+제7호 ±5"),
     ("ivw","(가) 정밀도가중 추정"),("ivw_true","(가) 정밀도가중 참값"),
     ("blup","(나) 혼합효과 원점수"),("blom_blup","(나) Blom+혼합효과"),
     ("bt","(다) Bradley-Terry"),("eb","(라) 경험베이즈 3년"),
     ("band","(마) 구간 평정 5구간"),("ideal","이상적 (하한)")]
R=400

def blk(title, org, **kw):
    print(f"\n═══ {title} ═══")
    print(f"{'방법':>20} {'지표2 SD':>9} {'하한대비':>8} {'rho':>7} {'부서%':>6} {'규모격차':>9}")
    base=None; low=None
    res={}
    for key,nm in MET:
        r=run(org,key,reps=R,**kw); res[key]=r
        if key=="current": base=r['sd']
        if key=="ideal": low=r['sd']
    for key,nm in MET:
        r=res[key]
        imp = 100*(base-r['sd'])/(base-low) if (base and low and base>low) else float('nan')
        sz = f"{r['size']:+9.2f}" if r['size']==r['size'] else f"{'—':>9}"
        print(f"{nm:>20} {r['sd']:9.3f} {imp:7.1f}% {r['rho']:7.3f} {r['v_dept']:6.1f} {sz}")
    return res

blk("②-1 기본 조건 (실제 조직 · σ1=0.3 σ2=0.9 · 1차 60:40 · 부서격차 0 · 전보 45%)", REAL)
blk("②-2 부서 간 실력 격차 ±0.6σ 존재 (실제 조직)", REAL, gap=0.6)
blk("②-3 관측오차 대칭 σ2=0.3 (실제 조직)", REAL, s2n=0.3)
blk("②-4 합성 조직 (규모 효과 측정용 · 240명 · 원장직속 없음)", SYNTH)

print("\n═══ ②-5 (나) 혼합효과의 식별 — 전보(앵커) 비율 민감도 ═══")
print("   Blom+혼합효과. 전보자는 두 부서장에게 평가받아 척도를 잇는 앵커가 된다.")
print(f"{'전보율':>7} {'지표2 SD':>9} {'rho':>7} {'부서%':>6}")
for tau in (0.0,0.15,0.30,0.45,0.60):
    r=run(REAL,"blom_blup",reps=R,tau=tau)
    print(f"{tau*100:6.0f}% {r['sd']:9.3f} {r['rho']:7.3f} {r['v_dept']:6.1f}")
print("   (대조) Blom 원안 — 앵커 무관")
r=run(REAL,"blom",reps=R); print(f"{'—':>7} {r['sd']:9.3f} {r['rho']:7.3f} {r['v_dept']:6.1f}")

print("\n═══ ②-6 경험베이즈 — 필요한 이력 연수 ═══")
print(f"{'이력':>5} {'지표2 SD':>9} {'rho':>7}")
for h in (1,2,3,5,8):
    r=run(REAL,"eb",reps=R,hist=h)
    print(f"{h:4d}년 {r['sd']:9.3f} {r['rho']:7.3f}")
