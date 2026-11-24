---
id: inference-technical-reference
title: "Inference, Technically: Sampling Distributions, Intervals, Tests and Regression"
sidebar_label: Technical reference
order: 16
summary: "The formal layer under parts 12 to 15: the sampling distribution of the mean, intervals and the t distribution, p-values and permutation tests, multiple testing, and least-squares regression."
level: intermediate
type: reference
domains:
  - statistics
tags:
  - statistics
relations:
  prerequisites:
    - why-averages-behave
  related:
    - how-sure-are-you
    - the-courtroom-for-numbers
    - two-things-moving-together
    - inference-quick-guide
---

# Inference, Technically: Sampling Distributions, Intervals, Tests and Regression

> The formal layer under parts 12 to 15. The stories give the intuition; this page gives statements you can check and reuse. Every number was recomputed with Python's standard library, and the script at the end asserts each identity, including an exact permutation test.

## 1. The sampling distribution of the mean

For `n` independent draws with mean `μ` and standard deviation `σ`:

```text
E[x̄]    = μ                      unbiased: the average of averages is the population mean
Var(x̄)  = σ² / n                 standard error  SE = σ / sqrt(n)
```

Both follow from the rules `E[X + Y] = E[X] + E[Y]` and `Var(X + Y) = Var X + Var Y` for independent values, divided by `n`. Exact check on Mira's 20 scores (`μ = 75.2`): enumerate all 400 ordered pairs drawn with replacement; the 400 means average to exactly `μ` and have variance exactly `σ²/2`.

- **Law of large numbers:** `x̄` converges to `μ` as `n` grows.
- **Central limit theorem:** for any crowd with a finite mean and variance, `(x̄ - μ) / (σ / sqrt(n))` approaches a standard normal. `n >= 30` is a rule of thumb, not a theorem: skewed crowds need more.
- **Bias is not cured by `n`:** `E[x̄]` is the mean of what you actually draw from. A biased frame gives a narrow net around the wrong value.
- Drawing without replacement from a small population shrinks the variance a little (finite-population correction); the series ignores it.

## 2. Confidence intervals

```text
interval for a mean        x̄ ± c × SE,     SE = s / sqrt(n)          c = z (1.96 for 95%) or t
interval for a proportion  p̂ ± z × sqrt(p̂ (1 - p̂) / n)
width                      proportional to 1 / sqrt(n)               4x the data halves the width
sample size for margin m   n = (z σ / m)^2, rounded up
```

Example: Mira's scores have `σ = 17.22`; for a margin of 5 points at 95%, `n = (1.96 × 17.22 / 5)² = 45.6`, so `n = 46`.

**Small samples.** `s` replaces `σ`, which adds uncertainty, so use the t distribution with `n - 1` degrees of freedom. The 97.5th percentiles are `2.262` for `n = 10` and `2.023` for `n = 40`, against `1.96` for the normal; they tend to 1.96 as `n` grows.

**What 95% means.** It describes the method, not one interval: about 95 of 100 intervals built from fresh samples contain the fixed true value. A single interval either does, or does not; the truth does not move.

**Bootstrap.** Resample the sample with replacement, many times; take the middle 95% of the resampled means (the 2.5th to 97.5th percentiles). It needs no formula, but it only reflects the sample you have: it cannot repair a biased one, and it is poor for tiny samples or extreme statistics.

## 3. Hypothesis tests

```text
null H0         "luck only": the labels mean nothing
p-value         P(a result at least this extreme | H0 is true)
type I error    reject a true H0      rate = the significance level α (often 0.05, a convention)
type II error   keep a false H0       power = 1 - P(type II error)
```

**Permutation test.** Pool the values, re-deal the labels at random, and count how often the re-dealt statistic is at least as extreme as the one seen. With 3 values per blend (`8, 9, 7` against `5, 6, 7`), all `C(6,3) = 20` splits can be listed: 2 of them match the observed lead of 2.0, so `p = 2/20 = 0.10`. With 10 per blend (Mira's data), `C(20,10) = 184,756` splits can be listed too: the **exact** one-sided `p = 1413/92378 = 0.0153`. The page's 10,000-shuffle estimate of 0.0143 differs by about what Monte Carlo noise allows (standard error near 0.0012). A simulation's accuracy improves as `1/sqrt(shuffles)`.

**What a p-value is not:** not `P(H0 is true)`, not the size of the effect, and a large p is not proof of no effect. Significance and importance come apart: with enough data a trivial gap becomes "significant". Report the effect size and its interval.

**Many tests.** With `k` independent tests at level 0.05, `P(at least one false alarm) = 1 - 0.95^k`: `0.6415` for `k = 20`. A Bonferroni correction tests each at `α / k` (here 0.0025), which keeps the overall rate at `1 - (1 - 0.0025)^20 = 0.0488`, below 0.05. Say how many things you tried.

## 4. Correlation and least squares

```text
r        = (1/n) Σ z_x z_y  (population SDs)  =  Σ(x - x̄)(y - ȳ) / sqrt(Σ(x - x̄)² Σ(y - ȳ)²)       -1 to +1
slope    b = r × s_y / s_x        intercept a = ȳ - b x̄           the line passes through (x̄, ȳ)
residual e = y - (a + b x)        Σe = 0                          least squares minimises Σe²
r²       = 1 - Σe² / Σ(y - ȳ)²    the share of the squared miss the line removes
```

On the tea-shop days (temperature against cups), `r = -0.9823`, slope `-2.643`, intercept `63.79`: each extra degree goes with about 2.6 fewer cups. Predicting at a temperature far outside the 2 to 16 degrees seen is extrapolation: the line is not a law.

**Limits of `r`.** It measures straight-line association only: a perfect curve can have `r = 0`; one outlier can swing it; correlation is not causation (a hidden third variable such as sun can drive both). Anscombe's four sets share `r = 0.816` and the line `y = 3 + 0.5x` while looking completely different, which is why you draw the scatter first.

## 5. Choosing a method

| Question | Tool | Check before trusting it |
|---|---|---|
| How wobbly is my average? | standard error `s / sqrt(n)` | sample drawn at random from the right frame |
| A range for the truth | interval; t if `n` is small | independence; the 95% describes the method |
| Is this gap just luck? | permutation test or classical test | one planned question; report effect size |
| Do two columns move together? | `r` and the least-squares line | scatter plot first; no extrapolation |

## 6. Run the identities

Each identity above, asserted with exact fractions or enumeration (Mira's data, the tea-shop days, Anscombe's first three sets). The t percentiles are computed by numeric integration of the t density. If an assertion fails Python stops; otherwise it prints the last line.

```python
import itertools, math, statistics as st
from fractions import Fraction as F
from statistics import NormalDist

# 1. Sampling distribution of the mean, exactly: all 400 ordered draws of 2 (with replacement)
pop = [52,55,55,58,58,58,62,62,62,71,71,89,89,89,93,93,94,94,95,104]
mu = F(sum(pop), len(pop)); var = sum((F(x) - mu) ** 2 for x in pop) / len(pop)     # population variance
means = [F(a + b, 2) for a, b in itertools.product(pop, repeat=2)]
assert sum(means) / len(means) == mu                                                   # centred on mu
assert sum((m - mu) ** 2 for m in means) / len(means) == var / 2                       # variance sigma^2 / n

# 2. Critical values: z and t (t cdf by numeric integration, quantile by bisection)
def t_cdf(x, df):
    c = math.gamma((df + 1) / 2) / (math.sqrt(df * math.pi) * math.gamma(df / 2))
    f = lambda u: c * (1 + u * u / df) ** (-(df + 1) / 2)
    n = 4000; h = x / n
    return 0.5 + h / 3 * (f(0) + f(x) + sum((4 if i % 2 else 2) * f(i * h) for i in range(1, n)))
def t_crit(df, p=0.975):
    lo, hi = 0.0, 10.0
    for _ in range(60):
        mid = (lo + hi) / 2
        lo, hi = (mid, hi) if t_cdf(mid, df) < p else (lo, mid)
    return (lo + hi) / 2
assert round(NormalDist().inv_cdf(0.975), 2) == 1.96
assert round(t_crit(9), 3) == 2.262 and round(t_crit(39), 3) == 2.023                  # n = 10 and n = 40

# 3. Width and sample size: SE = sigma / sqrt(n); 4x the data halves the width
sigma = st.pstdev(pop)
assert abs(sigma / math.sqrt(100) - (sigma / math.sqrt(25)) / 2) < 1e-12
n_needed = math.ceil((1.96 * sigma / 5) ** 2)                                           # margin of 5 points
assert n_needed == 46

# 4. Exact permutation test (no shuffling error): three per blend, then Mira's ten per blend
a, b = [8, 9, 7], [5, 6, 7]
pool, seen = a + b, st.fmean(a) - st.fmean(b)
hits = sum(1 for idx in itertools.combinations(range(6), 3)
           if st.fmean([pool[i] for i in idx]) - st.fmean([pool[i] for i in range(6) if i not in idx]) >= seen - 1e-9)
assert (hits, math.comb(6, 3)) == (2, 20)
A = [7, 8, 6, 9, 7, 8, 9, 7, 8, 6]; B = [6, 7, 5, 7, 6, 8, 6, 5, 7, 6]
pool = A + B
need = sum(A)                                  # equal group sizes, so a lead in the mean is a lead in the sum
p_exact = F(sum(1 for idx in itertools.combinations(range(20), 10) if sum(pool[i] for i in idx) >= need), math.comb(20, 10))
assert round(float(p_exact), 4) == 0.0153 and p_exact == F(1413, 92378)

# 5. Many tests
assert round(1 - 0.95 ** 20, 4) == 0.6415 and round(1 - (1 - 0.05 / 20) ** 20, 4) == 0.0488

# 6. Regression on the tea-shop days
temp = [2, 4, 6, 8, 10, 12, 14, 16]; cups = [58, 50, 52, 42, 40, 30, 28, 20]
r = st.correlation(temp, cups); fit = st.linear_regression(temp, cups)
zr = sum((x - st.fmean(temp)) / st.pstdev(temp) * (y - st.fmean(cups)) / st.pstdev(cups) for x, y in zip(temp, cups)) / len(temp)
assert abs(r - zr) < 1e-12
assert abs(fit.slope - r * st.stdev(cups) / st.stdev(temp)) < 1e-12 and abs(fit.intercept - (st.fmean(cups) - fit.slope * st.fmean(temp))) < 1e-9
res = [y - (fit.slope * x + fit.intercept) for x, y in zip(temp, cups)]
ss_res, ss_tot = sum(e * e for e in res), sum((y - st.fmean(cups)) ** 2 for y in cups)
assert abs(sum(res)) < 1e-9 and abs(r * r - (1 - ss_res / ss_tot)) < 1e-12
# Anscombe: one line, four crowds
x123 = [10, 8, 13, 9, 11, 14, 6, 4, 12, 7, 5]
ys = [[8.04, 6.95, 7.58, 8.81, 8.33, 9.96, 7.24, 4.26, 10.84, 4.82, 5.68], [9.14, 8.14, 8.74, 8.77, 9.26, 8.10, 6.13, 3.10, 9.13, 7.26, 4.74],
      [7.46, 6.77, 12.74, 7.11, 7.81, 8.84, 6.08, 5.39, 8.15, 6.42, 5.73]]
for y in ys: assert round(st.correlation(x123, y), 3) == 0.816
print("all checks passed", round(r, 4), round(fit.slope, 3), round(fit.intercept, 2), round(float(p_exact), 4), n_needed)
```

```text
all checks passed -0.9823 -2.643 63.79 0.0153 46
```

Run with Python 3 and the standard library only.

## Try it

Draw samples and watch the averages pile into a bell and the intervals catch the truth, then shuffle labels to see a p-value, then drag a point to see a regression line move. Short steps: [Inference quick guide](/fields/data-science/probability-statistics/inference/quick-guide.md).

[Sampling and intervals lab](/fields/data-science/probability-statistics/labs/sampling.html#embed ':ignore')

[Permutation test lab](/fields/data-science/probability-statistics/labs/permutation.html#embed ':ignore')

[Correlation lab](/fields/data-science/probability-statistics/labs/regression.html#embed ':ignore')

## References

- Series pages: [Why Averages Behave](/fields/data-science/probability-statistics/inference/why-averages-behave.md), [How Sure Are You?](/fields/data-science/probability-statistics/inference/how-sure-are-you.md), [The Courtroom for Numbers](/fields/data-science/probability-statistics/inference/the-courtroom-for-numbers.md), [Two Things Moving Together](/fields/data-science/probability-statistics/inference/two-things-moving-together.md).
- Anscombe, F. J. (1973), *Graphs in Statistical Analysis*, The American Statistician 27(1): 17-21 (the four data sets and their shared summaries; also quoted on the correlation page).
- Python `statistics`: `fmean`, `pstdev`, `stdev`, `correlation`, `linear_regression`, `NormalDist`.
- Every figure above was recomputed with Python's standard library; the exact permutation p-value and the t percentiles are this page's additions, produced by the script.
