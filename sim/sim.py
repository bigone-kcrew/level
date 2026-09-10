# -*- coding: utf-8 -*-
"""
창업진흥원 근무평정제도 — 제도 규칙 시뮬레이션 (정본)

이 스크립트가 공개 자료에 실린 모든 수치의 출처다. 외부 패키지 없이 실행된다.
    python3 sim/sim.py

※ 창업진흥원의 실제 평정 결과가 아니다. 제도의 규칙과 조합의 관찰을 입력해
   산출한 모의 결과이며, 가정값은 아래 상수에서 조정할 수 있다.
   실측 평정 분포 자료가 제공되면 모수를 재산정해야 한다.
"""
import random, math, statistics as st

# ═══════════════════════════════════════════════════════════════════
#  1. 상수 — 실측값과 가정값을 구분해 표기한다
# ═══════════════════════════════════════════════════════════════════

# ─── [실측] 조직 구조 ─────────────────────────────────────────────
# 출처: 창업진흥원 업무분장 및 직원연락처(2026.7.31. 기준) — 부서별 인원 명시
# 평가군 단위: 실 하위 팀·TF는 소속 실장이 평가하므로 상위 실에 통합한다.
#   (안전문화팀→재무계약실, 데이터분석팀→정책전략실, 정보보안팀→디지털AI실,
#    기업가정신팀→대학창업실, 정보관리TF→창업확산실, AX전략TF→기획조정실)
# 본부장 유형: 극단(과도한 차등) 2명 / 균등(과도한 균등) 3명  [조합 관찰]
# 원장 직속(감사실·홍보실)은 원장이 2차 평가자이며 평균 제약을 받지 않는다.

ORG = {
    "경영본부":        ("S", {"기획조정실": 10, "미래인재실": 8, "재무계약실": 14, "성과윤리실": 6}),
    "정책본부":        ("S", {"정책전략실": 11, "원스톱지원실": 8, "사업관리실": 12, "디지털AI실": 9}),
    "스케일업본부":    ("N", {"딥테크전략실": 12, "민관협력실": 11, "대학창업실": 14,
                              "창업확산실": 16, "대전팁스팀": 6}),
    "창업촉진본부":    ("N", {"지역전략실": 12, "예비재도전실": 9, "초기도약실": 12}),
    "글로벌본부":      ("N", {"글로벌전략실": 11, "글로벌허브실": 6, "글로벌협력실": 10,
                              "글로벌확산TF": 9}),
    "원장직속":        ("O", {"감사실": 4, "홍보실": 3}),          # O = 원장(평균 제약 없음)
}
DEPT_SIZES = [n for _, d in ORG.values() for n in d.values()]     # 22개 평가군 · 213명

# [실측] 근무평정규칙 제9조② / 별표 2 — 평가별·평가자별 반영비율
W_CORE   = 0.85      # 업적 65% + 역량 20%
W_1ST    = 0.60      # 업적·역량 중 1차 평가자(부서장)
W_2ND    = 0.40      # 업적·역량 중 2차 평가자(본부장)
W_MULTI  = 0.10      # 다면(부서장은 상향)
W_COMMON = 0.05      # 공통(정보보안)

# [실측] 규칙 제26조 + 연도별 계획 — 등급별 비율
GRADE = [("S", 0.20), ("A", 0.30), ("B", 0.40), ("C", 0.10)]
BANDS = {"S": 100, "A": 90, "B": 80, "C": 70}                  # 별표 7 평정점 구간

# [실측] 규칙 제26조① — 등급 배정 단위는 '부서'가 아니라 '직급'이다.
#   점수 부여 시 평균 제약은 평가자별 피평가자 그룹(부서) 단위,
#   등급 배정은 직급별 전사 단위. 두 단위가 다른 것이 이 제도의 핵심 구조다.
# 출처: 2025년 근무평정 계획 〈상대평가 대상자(196명) 직급별 배정 현황〉
RANK_MIX = [("1(나)급", 4), ("2급", 11), ("3급", 29), ("4급", 40), ("5급", 107), ("공무직", 5)]
ABSOLUTE_REFORM = ("공무직",)     # 개정 7 — 개선안에서 공무직은 절대평가(등급 배정 제외)

# [가정] 직급과 부서의 교차 분포는 공개 자료로 확인되지 않아 무작위 배정한다.
#   실측 직급×부서 자료가 제공되면 재산정 대상.

# [실측] 인사규정 제23조 + 2026 승진평가 계획 — 서열명부
W_EVAL_IN_LIST = 0.90    # 근무평정 평정점
W_TENURE       = 0.10    # 근속기간

# [가정 — 조합 관찰] 평정자 성향은 '과도한 차등(극단)'과 '과도한 균등' 두 방향으로 갈린다.
#   공정형(적정 차등)을 별도로 두지 않는다. 실측 분포 자료 확보 시 재산정 대상.
HQ_TYPES  = [t for t, _ in ORG.values()]  # ORG 에서 파생 (원장직속 포함 6개 평가단위)
MGR_MIX   = {"S": 0.50, "N": 0.50}        # 부서장 22명: 극단 : 균등 (미확인 — 가정)
SPREAD    = {"S": 13.0, "N": 2.0, "O": 7.0}         # 유형별 부서 내 부여점수 표준편차(점)
FAVOR     = {"S": 0.70, "N": 0.0, "O": 0.0}         # 실력과 무관한 선호의 반영 비중

# [가정] 개선안 — 순위기반 표준화의 목표 모수 (규칙 [별표 9] 개정안과 동일)
TARGET_MEAN = 80.0
TARGET_SD   = 7.0

# [가정] 이동자 낙인 — 전 부서장이 '나갈 사람'에게, 신 부서장이 '온 지 얼마 안 된 사람'에게
DEPART_PENALTY  = 0.6     # 표준화 실력 단위(σ)
NEWCOMER_PENALTY = 0.8

# [실측] 복무규정 — 정기전보 연 2회(1월·7월). 유형별 비중은 가정.
MOVE_MIX = [("잔류", 0.55), ("1월 전보", 0.12), ("7월 전보", 0.12),
            ("연중 조직개편", 0.08), ("중도 휴직", 0.07), ("중도 파견", 0.06)]

REPS = 400
SEED = 20260910


# ═══════════════════════════════════════════════════════════════════
#  2. 수학 도구
# ═══════════════════════════════════════════════════════════════════

def probit(p):
    """표준정규 분위수 (Acklam 근사)"""
    a = [-3.969683028665376e+01, 2.209460984245205e+02, -2.759285104469687e+02,
         1.383577518672690e+02, -3.066479806614716e+01, 2.506628277459239e+00]
    b = [-5.447609879822406e+01, 1.615858368580409e+02, -1.556989798598866e+02,
         6.680131188771972e+01, -1.328068155288572e+01]
    c = [-7.784894002430293e-03, -3.223964580411365e-01, -2.400758277161838e+00,
         -2.549732539343734e+00, 4.374664141464968e+00, 2.938163982698783e+00]
    d = [7.784695709041462e-03, 3.224671290700398e-01, 2.445134137142996e+00,
         3.754408661907416e+00]
    pl = 0.02425
    if p < pl:
        q = math.sqrt(-2 * math.log(p))
        return (((((c[0]*q+c[1])*q+c[2])*q+c[3])*q+c[4])*q+c[5]) / ((((d[0]*q+d[1])*q+d[2])*q+d[3])*q+1)
    if p > 1 - pl:
        q = math.sqrt(-2 * math.log(1 - p))
        return -(((((c[0]*q+c[1])*q+c[2])*q+c[3])*q+c[4])*q+c[5]) / ((((d[0]*q+d[1])*q+d[2])*q+d[3])*q+1)
    q = p - 0.5; r = q * q
    return (((((a[0]*r+a[1])*r+a[2])*r+a[3])*r+a[4])*r+a[5]) * q / (((((b[0]*r+b[1])*r+b[2])*r+b[3])*r+b[4])*r+1)


def blom(n):
    """정규 순서통계량 기대값 근사. 1위(최저) → n위(최고)"""
    return [probit((i - 0.375) / (n + 0.25)) for i in range(1, n + 1)]


def ranks(vals):
    order = sorted(range(len(vals)), key=lambda i: vals[i])
    r = [0] * len(vals)
    for pos, i in enumerate(order):
        r[i] = pos + 1
    return r


def spearman(x, y):
    rx, ry = ranks(x), ranks(y)
    mx, my = st.mean(rx), st.mean(ry)
    num = sum((a - mx) * (b - my) for a, b in zip(rx, ry))
    den = math.sqrt(sum((a - mx) ** 2 for a in rx) * sum((b - my) ** 2 for b in ry))
    return num / den if den else 0.0


def clamp(v, lo=60.0, hi=100.0):
    return max(lo, min(hi, v))


# ═══════════════════════════════════════════════════════════════════
#  3. 제도 구현
# ═══════════════════════════════════════════════════════════════════

def rank_labels(n):
    """전체 n명을 RANK_MIX 비율로 직급에 배분한다(최대잔여법)."""
    tot = sum(c for _, c in RANK_MIX)
    quota = [(lbl, n * c / tot) for lbl, c in RANK_MIX]
    base = [(lbl, int(q)) for lbl, q in quota]
    rest = n - sum(c for _, c in base)
    order = sorted(range(len(quota)), key=lambda k: -(quota[k][1] - int(quota[k][1])))
    cnt = dict(base)
    for k in order[:rest]:
        cnt[quota[k][0]] += 1
    out = []
    for lbl, c in RANK_MIX:
        out += [lbl] * cnt[lbl]
    random.shuffle(out)
    return out[:n]


def _alloc_one_group(idx, scores, grade, pts):
    """한 직급군 안에서 등급 배정 + 별표 7 평정점 산출."""
    m = len(idx)
    if m == 0:
        return
    counts, acc = [], 0
    for _, p in GRADE[:-1]:
        c = round(m * p); counts.append(c); acc += c
    counts.append(max(0, m - acc))
    # 개정 10⑤ — 10명 미만 평가군은 C 미부여, 그 인원을 B에 가산
    if m < 10 and counts[-1] > 0:
        counts[-2] += counts[-1]; counts[-1] = 0
    order = sorted(idx, key=lambda i: -scores[i])
    ix = 0
    for (g, _), cnt in zip(GRADE, counts):
        hi = BANDS[g]
        for j in range(cnt):
            if ix >= m:
                break
            i = order[ix]; grade[i] = g
            pts[i] = hi - (10.0 / cnt) * j if cnt else hi
            ix += 1


def assign_grades(scores, rank_of=None, absolute=()):
    """등급 배정. rank_of 가 주어지면 규칙 제26조①대로 '직급별'로 배정한다.

    absolute : 절대평가 대상 직급 라벨. 등급 배정 인원에서 제외하고(제26조① 단서)
               평정점 80(B)을 부여한다. 개정 7(공무직 절대평가) 적용 시 사용.
    """
    n = len(scores)
    grade, pts = [None] * n, [0.0] * n
    if rank_of is None:
        _alloc_one_group(list(range(n)), scores, grade, pts)
        return grade, pts
    groups = {}
    for i in range(n):
        groups.setdefault(rank_of(i), []).append(i)
    for lbl, idx in groups.items():
        if lbl in absolute:
            for i in idx:
                grade[i] = "B"; pts[i] = float(BANDS["B"])
            continue
        _alloc_one_group(idx, scores, grade, pts)
    return grade, pts


def award(members, gtype, signal_of, mode, mean_cap_slack=0.0):
    """한 평가자가 자기 피평가자 그룹에 점수를 부여한다.

    mode='current' : 유형별 부여폭 그대로. 그룹 평균은 80점 '이내'(상한)
    mode='reform'  : 순위기반 표준화. 평균 80 · 표준편차 TARGET_SD 로 통일
    """
    out = {}
    if not members:
        return out
    sig = [signal_of(i) for i in members]
    rk = ranks(sig)
    bl = blom(len(members))
    if mode == "reform":
        base, sd = TARGET_MEAN, TARGET_SD
    elif gtype == "O":                     # 원장: 평균 제약 미적용 (2025 계획 확인)
        base, sd = TARGET_MEAN, TARGET_SD
    else:
        base = TARGET_MEAN - (random.uniform(0, mean_cap_slack) if mean_cap_slack else 0.0)
        sd = SPREAD[gtype]
    for k, i in enumerate(members):
        out[i] = clamp(base + sd * bl[rk[k] - 1])
    return out


def build(ability_scale=None):
    """실제 조직 구조(ORG)로 부서·본부·인원 생성."""
    depts, dept_hq = [], {}
    for hq, (hqty, ds) in enumerate(ORG.values()):
        for _name, sz in ds.items():
            dept_hq[len(depts)] = hq
            depts.append(sz)
    nd, nhq = len(depts), len(ORG)
    dept_ty = {d: ("S" if random.random() < MGR_MIX["S"] else "N") for d in range(nd)}
    people, dmem, hmem = [], {d: [] for d in range(nd)}, {h: [] for h in range(nhq)}
    for d, sz in enumerate(depts):
        sc = ability_scale(d, dept_ty[d]) if ability_scale else 1.0
        for _ in range(sz):
            people.append({"a": random.gauss(0, 1) * sc, "f": random.gauss(0, 1), "d": d})
            dmem[d].append(len(people) - 1)
            hmem[dept_hq[d]].append(len(people) - 1)
    for i, g in enumerate(rank_labels(len(people))):     # 직급 배정 (등급 배정 단위)
        people[i]["g"] = g
    return people, dept_hq, dept_ty, dmem, hmem


def composite(people, dept_ty, dmem, hmem, mode, noise_of=None, mean_cap_slack=0.0):
    """2단계 평가 → 종합점수"""
    def sig(gtype):
        w = FAVOR[gtype]
        def f(i):
            s = (1 - w) * people[i]["a"] + w * people[i]["f"]
            if noise_of:
                s += noise_of(gtype)
            return s
        return f

    s1 = {}
    for d, mem in dmem.items():
        s1.update(award(mem, dept_ty[d], sig(dept_ty[d]), mode, mean_cap_slack))
    s2 = {}
    for h, mem in hmem.items():
        s2.update(award(mem, HQ_TYPES[h], sig(HQ_TYPES[h]), mode, mean_cap_slack))

    n = len(people)
    multi  = [clamp(92 + 4 * random.gauss(0, 1), 20, 100) for _ in range(n)]
    common = [clamp(95 + 4 * random.gauss(0, 1), 70, 100) for _ in range(n)]
    return [W_CORE * (W_1ST * s1[i] + W_2ND * s2[i])
            + W_MULTI * multi[i] + W_COMMON * common[i] for i in range(n)]


# ═══════════════════════════════════════════════════════════════════
#  4. 실험
# ═══════════════════════════════════════════════════════════════════

def exp_grade_distribution(mode, reps=REPS, **kw):
    """평정자 유형별·본부별 등급 획득률과 실력 반영도"""
    s_by_mgr = {"S": [0, 0], "N": [0, 0]}
    c_by_mgr = {"S": [0, 0], "N": [0, 0]}
    s_by_hq  = {h: [0, 0] for h in range(len(HQ_TYPES))}
    rho = []
    for _ in range(reps):
        people, dept_hq, dept_ty, dmem, hmem = build(kw.get("ability_scale"))
        total = composite(people, dept_ty, dmem, hmem, mode,
                          kw.get("noise_of"), kw.get("mean_cap_slack", 0.0))
        grade, pts = assign_grades(total, lambda i: people[i]["g"],
                                   ABSOLUTE_REFORM if mode == "reform" else ())
        for i, p in enumerate(people):
            mt = dept_ty[p["d"]]; hq = dept_hq[p["d"]]
            s_by_mgr[mt][1] += 1; c_by_mgr[mt][1] += 1; s_by_hq[hq][1] += 1
            if grade[i] == "S": s_by_mgr[mt][0] += 1; s_by_hq[hq][0] += 1
            if grade[i] == "C": c_by_mgr[mt][0] += 1
        rho.append(spearman([p["a"] for p in people], pts))
    pc = lambda o: 100 * o[0] / o[1] if o[1] else 0.0
    return {
        "S_mgr": {k: pc(v) for k, v in s_by_mgr.items()},
        "C_mgr": {k: pc(v) for k, v in c_by_mgr.items()},
        "S_hq":  {k: pc(v) for k, v in s_by_hq.items()},
        "rho":   st.mean(rho),
    }


def exp_transfer(mode, depart=DEPART_PENALTY, newcomer=NEWCOMER_PENALTY, reps=REPS):
    """전보·휴직·개편 시점에 따른 불이익.

    규칙 제6조① — 30일 이상 근무한 부서를 기준으로 평가하고 근무기간 비율로 가중.
    7월 전보자는 전 부서(0.5) + 신 부서(0.5), 연중 개편자는 전 부서(0.9) + 신 부서(0.1).
    1월 전보자는 전년도 평정이 끝난 뒤 이동하므로 신 부서 12개월.
    """
    names = [n for n, _ in MOVE_MIX]
    acc = {n: [0, 0, 0.0] for n in names}
    rho = []
    for _ in range(reps):
        nd = len(DEPT_SIZES)
        dept_ty = {d: ("S" if random.random() < MGR_MIX["S"] else "N") for d in range(nd)}
        people = []
        for d, sz in enumerate(DEPT_SIZES):
            for _ in range(sz):
                r, cum, mt = random.random(), 0.0, names[-1]
                for nm, w in MOVE_MIX:
                    cum += w
                    if r <= cum: mt = nm; break
                if mt in ("잔류", "1월 전보"):
                    seg = [(d, 1.0, False, False)]
                elif mt == "7월 전보":
                    seg = [(d, 0.5, True, False), (random.randrange(nd), 0.5, False, False)]
                elif mt == "연중 조직개편":
                    seg = [(d, 0.9, True, False), (random.randrange(nd), 0.1, False, True)]
                else:                                   # 중도 휴직·파견
                    seg = [(d, 0.5, True, False)]
                people.append({"a": random.gauss(0, 1), "f": random.gauss(0, 1),
                               "mt": mt, "seg": seg})
        for i, g in enumerate(rank_labels(len(people))):
            people[i]["g"] = g
        grp = {d: [] for d in range(nd)}
        for i, p in enumerate(people):
            for (d, w, out, new) in p["seg"]:
                grp[d].append((i, w, out, new))
        part = {}
        for d, mem in grp.items():
            if not mem: continue
            ty = dept_ty[d]; w = FAVOR[ty]
            sig = []
            for (i, _, out, new) in mem:
                s = (1 - w) * people[i]["a"] + w * people[i]["f"]
                if mode != "reform":
                    if out: s -= depart
                    if new: s -= newcomer
                sig.append(s)
            rk = ranks(sig); bl = blom(len(mem))
            sd = TARGET_SD if mode == "reform" else SPREAD[ty]
            for k, (i, _, _, _) in enumerate(mem):
                part[(i, d)] = clamp(TARGET_MEAN + sd * bl[rk[k] - 1])
        total = []
        for i, p in enumerate(people):
            num = sum(part[(i, d)] * w for (d, w, _, _) in p["seg"])
            den = sum(w for (_, w, _, _) in p["seg"])
            total.append(num / den)
        grade, pts = assign_grades(total, lambda i: people[i]["g"],
                                   ABSOLUTE_REFORM if mode == "reform" else ())
        for i, p in enumerate(people):
            a = acc[p["mt"]]; a[1] += 1; a[2] += pts[i]
            if grade[i] == "S": a[0] += 1
        rho.append(spearman([p["a"] for p in people], pts))
    return ({n: (100 * v[0] / v[1] if v[1] else 0, v[2] / v[1] if v[1] else 0, v[1])
             for n, v in acc.items()}, st.mean(rho))


SCHEMES = [("2회 산술평균 (4급 승진 현행)", 2), ("3회 산술평균 (2·3급 현행)", 3),
           ("4회 산술평균 (1(나)급 현행)", 4)]


def exp_promotion(mode, persistence=1.0, reps=None):
    """서열명부 = 근무평정 평정점 90% + 근속기간 10%. 반영 회차별 실력 반영도.

    persistence : 인접 연도 실력 상관. 1.0 이면 실력이 4년간 불변.
    """
    reps = reps or max(60, int(REPS * 0.5))
    out = {nm: [] for nm, _ in SCHEMES}
    for _ in range(reps):
        nd = len(DEPT_SIZES)
        dept_hq = {d: d % len(HQ_TYPES) for d in range(nd)}
        dept_ty = {d: ("S" if random.random() < MGR_MIX["S"] else "N") for d in range(nd)}
        base = []
        for d, sz in enumerate(DEPT_SIZES):
            for _ in range(sz):
                base.append({"a": random.gauss(0, 1), "f": random.gauss(0, 1), "d": d})
        for i, g in enumerate(rank_labels(len(base))):   # 직급은 4회차 동안 고정
            base[i]["g"] = g
        tenure = [random.uniform(0, 1) for _ in base]
        years = []
        cur = [p["a"] for p in base]
        for _ in range(4):
            people = [{"a": cur[i], "f": base[i]["f"], "d": base[i]["d"], "g": base[i]["g"]}
                      for i in range(len(base))]
            dmem = {d: [] for d in range(nd)}; hmem = {h: [] for h in range(len(HQ_TYPES))}
            for i, p in enumerate(people):
                dmem[p["d"]].append(i); hmem[dept_hq[p["d"]]].append(i)
            total = composite(people, dept_ty, dmem, hmem, mode)
            years.append(assign_grades(total, lambda i: people[i]["g"],
                                       ABSOLUTE_REFORM if mode == "reform" else ())[1])
            cur = [persistence * cur[i] + math.sqrt(max(0.0, 1 - persistence ** 2)) * random.gauss(0, 1)
                   for i in range(len(cur))]
        latent = [p["a"] for p in base]
        for nm, k in SCHEMES:
            avg = [st.mean([years[-j - 1][i] for j in range(k)]) for i in range(len(base))]
            listpt = [W_EVAL_IN_LIST * avg[i] + W_TENURE * (60 + 40 * tenure[i]) for i in range(len(base))]
            out[nm].append(spearman(latent, listpt))
    return {nm: st.mean(v) for nm, v in out.items()}


def exp_baseline(reps=REPS):
    """실력을 완전히 관측하는 이상적 제도의 기준선 (자진 공개용)"""
    zero, rho = [], []
    for _ in range(reps):
        people, dept_hq, dept_ty, dmem, hmem = build()
        total = [TARGET_MEAN + TARGET_SD * p["a"] for p in people]
        grade, pts = assign_grades(total, lambda i: people[i]["g"])
        nz = sum(1 for d in range(len(DEPT_SIZES))
                 if not any(grade[i] == "S" for i in dmem[d]))
        zero.append(nz / len(DEPT_SIZES))
        rho.append(spearman([p["a"] for p in people], pts))
    theory = st.mean([0.8 ** n for n in DEPT_SIZES])
    return 100 * st.mean(zero), 100 * theory, st.mean(rho)


# ═══════════════════════════════════════════════════════════════════
#  5. 출력
# ═══════════════════════════════════════════════════════════════════

def line(c="─", n=84): return c * n

def main():
    random.seed(SEED)
    print(line("="))
    print(" 창업진흥원 근무평정제도 시뮬레이션  (모의데이터 · 실제 평정 결과 아님)")
    print(f" 부서 {len(DEPT_SIZES)}개 {min(DEPT_SIZES)}~{max(DEPT_SIZES)}명(중위 {st.median(DEPT_SIZES):.0f}) · 인원 {sum(DEPT_SIZES)}명")
    print(f" 2단계 평가: 업적·역량 {W_CORE:.0%}(1차 {W_1ST:.0%}/2차 {W_2ND:.0%}) + 다면 {W_MULTI:.0%} + 공통 {W_COMMON:.0%}")
    print(f" 평가단위 {list(ORG.keys())}")
    print(f" 본부장 유형 {HQ_TYPES} (S=극단 N=균등 O=원장) · 부서장 극단:균등 = {MGR_MIX['S']:.0%}:{MGR_MIX['N']:.0%}")
    nN = sum(sum(d.values()) for t, d in ORG.values() if t == "N")
    print(f" 균등형 본부장 아래 인원 {nN}명 / 전체 {sum(DEPT_SIZES)}명 = {100*nN/sum(DEPT_SIZES):.0f}%  [조합 관찰]")
    print(f" 반복 {REPS}회 · 시드 {SEED}")
    print(line("="))

    # ── 1. 등급 분포
    print("\n【1】 평정자 유형별 등급 획득률과 실력 반영도\n")
    res = {}
    for mode, lb in [("current", "현행 (사전조정계수)"), ("reform", "개선 (순위기반 표준화)")]:
        random.seed(SEED)
        res[mode] = exp_grade_distribution(mode, mean_cap_slack=3.0 if mode == "current" else 0.0)
        r = res[mode]
        hqS = [r["S_hq"][h] for h in sorted(r["S_hq"]) if HQ_TYPES[h] == "S"]
        hqN = [r["S_hq"][h] for h in sorted(r["S_hq"]) if HQ_TYPES[h] == "N"]
        print(f"  [{lb}]")
        print(f"    부서장 유형별 S : 극단 {r['S_mgr']['S']:5.1f}%   균등 {r['S_mgr']['N']:5.1f}%"
              f"    (편차 {abs(r['S_mgr']['S']-r['S_mgr']['N']):4.1f}%p)")
        print(f"    부서장 유형별 C : 극단 {r['C_mgr']['S']:5.1f}%   균등 {r['C_mgr']['N']:5.1f}%")
        print(f"    본부장 유형별 S : 극단 {st.mean(hqS):5.1f}%   균등 {st.mean(hqN):5.1f}%"
              f"    (격차 {st.mean(hqS)/st.mean(hqN):4.2f}배)")
        print(f"    실력-평정점 rho : {r['rho']:.3f}\n")
    print(f"  → 개선 효과 : rho {res['current']['rho']:.3f} → {res['reform']['rho']:.3f}"
          f"  ({res['reform']['rho']-res['current']['rho']:+.3f})")

    # ── 2. 이론 기준선 (자진 공개)
    z, th, orho = exp_baseline()
    print("\n" + line())
    print("\n【2】 이상적 제도의 기준선 — 어디까지가 제도 결함이 아닌가\n")
    print(f"  실력을 완전히 관측하는 제도에서도 S등급자가 없는 부서 비율 : {z:.1f}%")
    print(f"  같은 값의 이론치 E[(1-0.20)^n]                  : {th:.1f}%")
    print("  → 'S등급자 0명 부서' 비율은 제도 결함 지표로 쓸 수 없다.")

    # ── 3. 전보 불이익
    print("\n" + line())
    print("\n【3】 전보·휴직·조직개편 시점에 따른 불이익\n")
    print(f"  가정: 전 부서장이 '나갈 사람'에게 {DEPART_PENALTY}σ, "
          f"신 부서장이 '온 지 얼마 안 된 사람'에게 {NEWCOMER_PENALTY}σ 낮게 평가\n")
    for mode, lb in [("current", "현행"), ("noStigma", "현행 · 낙인 없음(대조)"), ("reform", "개선")]:
        random.seed(SEED + 3)
        kw = dict(depart=0.0, newcomer=0.0) if mode == "noStigma" else {}
        r, rho = exp_transfer("current" if mode == "noStigma" else mode, **kw)
        b = r["잔류"]
        print(f"  [{lb}]   rho {rho:.3f}")
        print(f"    {'이동 유형':<16}{'S획득률':>9}{'평정점':>9}{'잔류자 대비':>12}")
        for nm, _ in MOVE_MIX:
            s, p, _n = r[nm]
            print(f"    {nm:<16}{s:>8.1f}%{p:>9.2f}{p-b[1]:>+11.2f}점")
        print()
    print("  → 낙인을 0으로 두면 유형 간 격차가 사라진다. 원인은 제도가 아니라 낙인 행동이며,")
    print("    순위기반 표준화는 평정점 격차는 없애지만 S획득률 격차는 부분적으로만 해소한다.")

    # ── 4. 승진명부 반영 회차 × 실력 지속성
    print("\n" + line())
    print("\n【4】 서열명부 반영 회차 (근무평정 90% + 근속 10%, 산술평균)\n")
    print(f"  {'실력 지속성':<12}" + "".join(f"{nm[:14]:>18}" for nm, _ in SCHEMES))
    for pers in (1.0, 0.9, 0.8, 0.7):
        random.seed(SEED + 5)
        r = exp_promotion("current", persistence=pers)
        best = max(r, key=r.get)
        cells = "".join(f"{r[nm]:>17.3f}{'*' if nm == best else ' '}" for nm, _ in SCHEMES)
        print(f"  {pers:<12.1f}" + cells)
    print("  * = 해당 지속성에서 최적.  실력이 해마다 변할수록 회차 확대의 이점이 줄어든다.")

    # ── 5. 민감도 (다차원)
    print("\n" + line())
    print("\n【5】 민감도 — 결론이 무너지는 영역을 먼저 밝힌다\n")
    print("  (가) 평정자 부여폭이 서로 비슷해질 때")
    print(f"    {'극단/균등 부여폭':<20}{'현행 rho':>10}{'개선 rho':>10}{'개선효과':>10}")
    orig = dict(SPREAD)
    for sS, sN in [(13, 2), (11, 3), (9, 4), (8, 5), (7, 6)]:
        SPREAD["S"], SPREAD["N"] = float(sS), float(sN)
        random.seed(SEED + 7); c = exp_grade_distribution("current", reps=200, mean_cap_slack=3.0)["rho"]
        random.seed(SEED + 7); f = exp_grade_distribution("reform", reps=200)["rho"]
        print(f"    {f'{sS} / {sN}점':<20}{c:>10.3f}{f:>10.3f}{f-c:>+10.3f}")
    SPREAD.update(orig)

    print("\n  (나) 균등형 평정자가 실력을 정확히 보지 못할 때 (관측오차)")
    print(f"    {'관측오차(σ)':<20}{'현행 rho':>10}{'개선 rho':>10}{'개선효과':>10}")
    for noise in (0.0, 1.0, 2.0, 3.0):
        nz = (lambda ty: random.gauss(0, noise) if ty == "N" and noise else 0.0)
        random.seed(SEED + 9); c = exp_grade_distribution("current", reps=200, noise_of=nz, mean_cap_slack=3.0)["rho"]
        random.seed(SEED + 9); f = exp_grade_distribution("reform", reps=200, noise_of=nz)["rho"]
        print(f"    {noise:<20.1f}{c:>10.3f}{f:>10.3f}{f-c:>+10.3f}")

    print("\n  (다) 식별 문제 — 좁은 부여폭을 '부서 균질'로 해석하면")
    print(f"    {'해석':<28}{'현행 rho':>10}{'개선 rho':>10}{'개선효과':>10}")
    for lb, sc in [("좁은 폭 = 평정자 무능 (조합)", None),
                   ("좁은 폭 = 부서 균질 (사측)", lambda d, ty: SPREAD[ty] / 7.0)]:
        random.seed(SEED + 11); c = exp_grade_distribution("current", reps=200, ability_scale=sc, mean_cap_slack=3.0)["rho"]
        random.seed(SEED + 11); f = exp_grade_distribution("reform", reps=200, ability_scale=sc)["rho"]
        print(f"    {lb:<28}{c:>10.3f}{f:>10.3f}{f-c:>+10.3f}")
    print("\n  (라) '넓은 부여폭'이 선호 때문인지 판별력 때문인지 — 극단형의 선호 반영률")
    print(f"    {'선호 반영률':<20}{'현행 rho':>10}{'개선 rho':>10}{'개선효과':>10}")
    of = FAVOR["S"]
    for fv in (0.7, 0.5, 0.3, 0.1, 0.0):
        FAVOR["S"] = fv
        random.seed(SEED + 13); c = exp_grade_distribution("current", reps=200, mean_cap_slack=3.0)["rho"]
        random.seed(SEED + 13); f = exp_grade_distribution("reform", reps=200)["rho"]
        print(f"    {fv:<20.1f}{c:>10.3f}{f:>10.3f}{f-c:>+10.3f}")
    FAVOR["S"] = of
    print("    → 극단형이 선호가 아니라 판별력으로 벌린다면(반영률 0) 개선 효과가 크게 줄어든다.")

    print("\n  (마) 본부 단위에서는 '균질' 해석이 성립하기 어렵다")
    print(f"    부서 평균 {sum(DEPT_SIZES)/len(DEPT_SIZES):.1f}명 · 본부 평균 {sum(DEPT_SIZES)/len(HQ_TYPES):.1f}명")
    print(f"    → 10명 부서가 균질할 수는 있으나, {sum(DEPT_SIZES)/len(HQ_TYPES):.0f}명 본부가 균질하다고 보기는 어렵다.")
    print("      2차 평가자(본부장) 단계의 좁은 부여폭은 '집단 균질성'으로 설명되지 않는다.")

    print("\n  → 두 해석을 구별할 자료는 노사 모두에게 없다. 실측 평정 분포 자료가 필요한 이유다.")
    print("\n" + line("="))
    print(" 이 결과는 창업진흥원의 실제 평정 결과가 아니다. 상단 상수를 조정해 재현할 수 있다.")
    print(line("="))


if __name__ == "__main__":
    main()
