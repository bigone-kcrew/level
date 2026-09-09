# -*- coding: utf-8 -*-
"""
창업진흥원 근무평정 사전조정계수 시뮬레이션 (재현용)

웹 시뮬레이터와 동일한 계산을 수행한다. 외부 패키지가 필요하지 않다.
  python3 sim/sim.py

※ 창업진흥원의 실제 평정 결과가 아니다. 제도의 규칙만을 입력하여 산출한 모의 결과이며,
   평정자 유형 비율·유형별 부여점수 표준편차·전보율은 가정값이다.
"""
import random, math, statistics as st

SEED       = 20260909
N_TARGET   = 107          # 2025년 5급 상대평가군 인원
DEPT_MIN, DEPT_MAX = 3, 9
TYPE_MIX   = {"F": 0.50, "N": 0.25, "S": 0.25}   # 공정형 / 균등형 / 전략형
SPREAD     = {"F": 7.0, "N": 2.0, "S": 13.0}     # 현행: 유형별 부여점수 표준편차
FAVOR_W    = {"F": 0.0, "N": 0.0, "S": 0.70}     # 전략형의 선호 반영률
TARGET_SD  = 7.0                                  # 개선안 목표 표준편차
GRADE      = [("S", 0.20), ("A", 0.30), ("B", 0.40), ("C", 0.10)]
BANDS      = {"S": 100, "A": 90, "B": 80, "C": 70}
MOVE_P     = 0.40         # 연간 전보율
REPS       = 400


# ---------- 수학 ----------
def probit(p):
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
        return ((((( c[0]*q+c[1])*q+c[2])*q+c[3])*q+c[4])*q+c[5]) / ((((d[0]*q+d[1])*q+d[2])*q+d[3])*q+1)
    if p > 1 - pl:
        q = math.sqrt(-2 * math.log(1 - p))
        return -((((( c[0]*q+c[1])*q+c[2])*q+c[3])*q+c[4])*q+c[5]) / ((((d[0]*q+d[1])*q+d[2])*q+d[3])*q+1)
    q = p - 0.5; r = q * q
    return ((((( a[0]*r+a[1])*r+a[2])*r+a[3])*r+a[4])*r+a[5]) * q / (((((b[0]*r+b[1])*r+b[2])*r+b[3])*r+b[4])*r+1)


def blom(n):
    """정규 순서통계량 기대값 근사 (Blom). 1위(최저)부터 n위(최고)."""
    return [probit((i - 0.375) / (n + 0.25)) for i in range(1, n + 1)]


def rank_positions(vals):
    order = sorted(range(len(vals)), key=lambda i: vals[i])
    r = [0] * len(vals)
    for pos, i in enumerate(order):
        r[i] = pos + 1
    return r


def spearman(x, y):
    rx, ry = rank_positions(x), rank_positions(y)
    mx, my = st.mean(rx), st.mean(ry)
    num = sum((a - mx) * (b - my) for a, b in zip(rx, ry))
    den = math.sqrt(sum((a - mx) ** 2 for a in rx) * sum((b - my) ** 2 for b in ry))
    return num / den if den else 0.0


# ---------- 제도 ----------
def dept_sizes(n):
    s, tot = [], 0
    while tot < n:
        sz = random.randint(DEPT_MIN, DEPT_MAX)
        if tot + sz > n:
            sz = n - tot
        if sz < DEPT_MIN and s:
            s[-1] += sz
            break
        s.append(sz); tot += sz
    return s


def pick_type():
    r, cum = random.random(), 0.0
    for t, w in TYPE_MIX.items():
        cum += w
        if r <= cum:
            return t
    return "S"


def assign_grades(scores):
    """종합점수 고득점순 → 등급 배정 → 등급 구간 내 인원수에 따른 평정점 산출"""
    n = len(scores)
    counts, acc = [], 0
    for _, p in GRADE[:-1]:
        c = round(n * p); counts.append(c); acc += c
    counts.append(max(0, n - acc))
    order = sorted(range(n), key=lambda i: -scores[i])
    grade, pts, ix = [None] * n, [0.0] * n, 0
    for (g, _), cnt in zip(GRADE, counts):
        hi = BANDS[g]
        for j in range(cnt):
            if ix >= n:
                break
            i = order[ix]; grade[i] = g
            pts[i] = hi - (10.0 / cnt) * j if cnt else hi
            ix += 1
    return grade, pts


def score_year(people, dtype, mode):
    """people: [dept, true, favor].  mode: 'current' | 'reform'"""
    depts = sorted(set(p[0] for p in people))
    scores = [0.0] * len(people)
    for d in depts:
        idxs = [i for i, p in enumerate(people) if p[0] == d]
        if not idxs:
            continue
        ty = dtype[d]
        w = FAVOR_W[ty]
        sig = [(1 - w) * people[i][1] + w * people[i][2] for i in idxs]
        rk = rank_positions(sig)
        bl = blom(len(sig))
        sd = TARGET_SD if mode == "reform" else SPREAD[ty]
        for k, i in enumerate(idxs):
            scores[i] = max(60.0, min(100.0, 80.0 + sd * bl[rk[k] - 1]))
    return scores


def build_population():
    sizes = dept_sizes(N_TARGET)
    dtype = {d: pick_type() for d in range(len(sizes))}
    people = []
    for d, sz in enumerate(sizes):
        for _ in range(sz):
            people.append([d, random.gauss(0, 1), random.gauss(0, 1)])
    return sizes, dtype, people


# ---------- 실험 ----------
def experiment_main(mode):
    s_hit = {"F": [0, 0], "N": [0, 0], "S": [0, 0]}
    c_hit = {"F": [0, 0], "N": [0, 0], "S": [0, 0]}
    zero, rho = [], []
    for _ in range(REPS):
        sizes, dtype, people = build_population()
        grade, pts = assign_grades(score_year(people, dtype, mode))
        for i, p in enumerate(people):
            t = dtype[p[0]]
            s_hit[t][1] += 1; c_hit[t][1] += 1
            if grade[i] == "S": s_hit[t][0] += 1
            if grade[i] == "C": c_hit[t][0] += 1
        nz = sum(1 for d in range(len(sizes))
                 if not any(grade[i] == "S" for i, p in enumerate(people) if p[0] == d))
        zero.append(nz / len(sizes))
        rho.append(spearman([p[1] for p in people], pts))
    pc = lambda o: 100 * o[0] / o[1] if o[1] else 0.0
    return ({t: pc(v) for t, v in s_hit.items()},
            {t: pc(v) for t, v in c_hit.items()},
            100 * st.mean(zero), st.mean(rho))


SCHEMES = [("1회", (1, 0, 0)),
           ("현행 2회 (60/40)", (0.6, 0.4, 0)),
           ("3년 50/30/20", (0.5, 0.3, 0.2)),
           ("3년 균등", (1/3, 1/3, 1/3))]


def experiment_promotion(mode):
    acc = {nm: {"rho": [], "exp": [0, 0], "non": [0, 0]} for nm, _ in SCHEMES}
    reps = max(40, int(REPS * 0.6))
    for _ in range(reps):
        sizes, dtype, people = build_population()
        nd = len(sizes)
        yearly, expo = [], []
        for y in range(3):
            if y > 0:
                for p in people:
                    if random.random() < MOVE_P:
                        p[0] = random.randrange(nd)
            yearly.append(assign_grades(score_year(people, dtype, mode))[1])
            expo.append([dtype[p[0]] for p in people])
        true = [p[1] for p in people]
        exposed = [any(expo[y][i] == "N" for y in range(3)) for i in range(len(people))]
        for nm, w in SCHEMES:
            agg = [sum(w[y] * yearly[y][i] for y in range(3)) for i in range(len(people))]
            thr = sorted(agg, reverse=True)[max(0, int(0.2 * len(agg)) - 1)]
            acc[nm]["rho"].append(spearman(true, agg))
            for i, a in enumerate(agg):
                top = 1 if a >= thr else 0
                key = "exp" if exposed[i] else "non"
                acc[nm][key][0] += top; acc[nm][key][1] += 1
    out = []
    for nm, _ in SCHEMES:
        v = acc[nm]
        f = lambda o: 100 * o[0] / o[1] if o[1] else float("nan")
        out.append((nm, st.mean(v["rho"]), f(v["exp"]), f(v["non"])))
    return out


def experiment_sensitivity():
    xs = [0.5, 1, 2, 3, 4, 5, 6, 7]
    mixes = [0.15, 0.25, 0.40]
    reps = max(30, int(REPS * 0.25))
    grid = []
    for sd_n in xs:
        row = []
        for mx in mixes:
            global SPREAD, TYPE_MIX
            SPREAD = dict(SPREAD); SPREAD["N"] = sd_n
            rest = 1.0 - mx
            TYPE_MIX = {"F": rest * (0.50 / 0.75), "N": mx, "S": rest * (0.25 / 0.75)}
            hit = tot = 0
            for _ in range(reps):
                sizes, dtype, people = build_population()
                grade, _ = assign_grades(score_year(people, dtype, "current"))
                for i, p in enumerate(people):
                    if dtype[p[0]] == "N":
                        tot += 1
                        if grade[i] == "S":
                            hit += 1
            row.append(100 * hit / tot if tot else 0.0)
        grid.append((sd_n, row))
    return xs, mixes, grid


def main():
    random.seed(SEED)
    print("=" * 78)
    print(" 창업진흥원 근무평정 사전조정계수 시뮬레이션 (모의데이터)")
    print(" 5급 상대평가군 %d명 · 부서 %d~%d명 · 평정자 F%.0f:N%.0f:S%.0f · 반복 %d회"
          % (N_TARGET, DEPT_MIN, DEPT_MAX,
             TYPE_MIX["F"] * 100, TYPE_MIX["N"] * 100, TYPE_MIX["S"] * 100, REPS))
    print("=" * 78)

    for mode, label in [("current", "[현행] 부서 평균 80점 강제"),
                        ("reform", "[개선] 사전 제약 폐지 + 사후 평균·표준편차일치법")]:
        s, c, zero, rho = experiment_main(mode)
        print("\n%s" % label)
        print("  S등급 획득률   공정형 %5.1f%%   균등형 %5.1f%%   전략형 %5.1f%%" % (s["F"], s["N"], s["S"]))
        print("  C등급 획득률   공정형 %5.1f%%   균등형 %5.1f%%   전략형 %5.1f%%" % (c["F"], c["N"], c["S"]))
        print("  S등급자 0명 부서 비율 : %5.1f%%" % zero)
        print("  실력-평정점 순위상관  : %5.3f" % rho)

    print("\n" + "=" * 78)
    print(" 승진후보자 서열명부 반영 회차 (연 %.0f%% 전보)" % (MOVE_P * 100))
    print("=" * 78)
    for mode, label in [("current", "[현행]"), ("reform", "[개선]")]:
        print("\n%s  %-20s %7s %14s %12s" % (label, "반영 방식", "rho", "균등형 경험자", "미경험자"))
        for nm, rho, e, n in experiment_promotion(mode):
            print("      %-20s %7.3f %13.1f%% %11.1f%%" % (nm, rho, e, n))

    print("\n" + "=" * 78)
    print(" 민감도 — 균등형 평정자 부서원의 S등급 획득률 (현행 제도, 기준선 20.0%)")
    print("=" * 78)
    xs, mixes, grid = experiment_sensitivity()
    print("  %-16s %s" % ("부여 표준편차", "  ".join("균등형 %2.0f%%" % (m * 100) for m in mixes)))
    for sd_n, row in grid:
        print("  %-16s %s" % ("%.1f점" % sd_n, "  ".join("%8.1f%%" % v for v in row)))
    print("\n * 실제 창업진흥원 평정 결과가 아니다. 가정값은 파일 상단 상수에서 조정할 수 있다.")


if __name__ == "__main__":
    main()
