---
id: probability-technical-reference
title: "Probability, Technically: Definitions, Identities and Assumptions"
sidebar_label: Technical reference
order: 12
summary: "The formal layer under parts 7 to 11: axioms, Bayes in odds form, pmf, cdf and density, moment rules, the Poisson limit, the normal approximation and each model's assumptions."
level: intermediate
type: reference
domains:
  - statistics
tags:
  - statistics
relations:
  prerequisites:
    - counting-the-ways
  related:
    - the-test-that-was-99-percent-accurate
    - what-to-expect
    - coins-and-calls
    - the-bell-curve
    - probability-quick-guide
---

# Probability, Technically: Definitions, Identities and Assumptions

> The formal layer under parts 7 to 11. The stories give the intuition; this page gives the statements you can check and reuse. Every number was recomputed with Python's standard library (`math`, `fractions`, `statistics.NormalDist`).

## 1. Foundations

A probability model is a sample space `Ω` (all outcomes), events (subsets of `Ω`) and a function `P` with three rules:

```text
P(A) >= 0                      for every event A
P(Ω) = 1
P(A or B) = P(A) + P(B)        when A and B cannot both happen (disjoint)
```

Everything in [Counting the Ways](/fields/data-science/probability-statistics/probability/counting-the-ways.md) follows from these:

```text
P(not A)      = 1 - P(A)
P(A or B)     = P(A) + P(B) - P(A and B)          inclusion-exclusion
P(A and B)    = P(A) P(B | A)                     chain rule
independent   <=> P(A and B) = P(A) P(B)          (equivalently P(A | B) = P(A))
```

**Equally likely outcomes** are an assumption, not a law: `P(A) = |A| / |Ω|` holds only then. Counting tools: ordered picks `n!/(n-k)!` (`math.perm`), unordered `n!/(k!(n-k)!)` (`math.comb`).

## 2. Conditioning and Bayes

```text
P(A | B) = P(A and B) / P(B)                       needs P(B) > 0
P(B)     = sum over i of P(B | A_i) P(A_i)         law of total probability (A_i partition Ω)
P(A | B) = P(B | A) P(A) / P(B)                    Bayes' rule
```

**Odds form** (often easier than the fraction): posterior odds = prior odds × likelihood ratio.

```text
odds(A)            = P(A) / (1 - P(A))
likelihood ratio   = P(positive | A) / P(positive | not A)
```

For the 99% test: prior 1/1000 gives odds 1/999; the likelihood ratio is `0.99 / 0.01 = 99`; posterior odds are `99/999 = 11/111`, so `P = 11/122 = 9.02%`. A second independent positive multiplies the odds by 99 again, giving `363/400 = 90.75%`. The odds form shows the whole mechanism: **evidence multiplies odds, it never replaces the prior.**

> [!WARNING]
> Repeated tests multiply likelihood ratios only if the test errors are conditionally independent given the true state. A shared reagent or batch breaks that, and the update overstates the evidence.

## 3. Random variables

A random variable `X` is a function from outcomes to numbers. It is described by

```text
discrete:    pmf  p(x) = P(X = x),             sum of p(x) = 1
continuous:  density f(x) >= 0, area = 1,      P(a <= X <= b) = area under f from a to b,   P(X = x) = 0
either:      cdf  F(x) = P(X <= x),            non-decreasing, from 0 to 1
```

Moments, with `μ = E[X]`:

```text
E[X]      = sum of x p(x)                 (integral of x f(x) dx if continuous)
E[g(X)]   = sum of g(x) p(x)              no need to find the distribution of g(X)
Var(X)    = E[(X - μ)^2] = E[X^2] - μ^2
E[aX + b]   = a E[X] + b          Var(aX + b) = a^2 Var(X)
E[X + Y]    = E[X] + E[Y]         always
Var(X + Y)  = Var X + Var Y + 2 Cov(X, Y)       Cov = 0 when X and Y are independent
```

The lucky tin shows both halves of the last line: for two independent pulls `Var = 149/2`, while one pull paid twice (`2X`) gives `4 × 37.25 = 149`, because `Cov(X, X) = Var X`. Independent implies uncorrelated, **not** the other way round.

## 4. The two counting recipes

```text
Bernoulli(p)        X in {0, 1}, E = p, Var = p(1 - p)
Binomial(n, p)      sum of n independent Bernoulli(p)
                    P(k) = C(n, k) p^k (1-p)^(n-k)    E = np    Var = np(1-p)
Poisson(λ)          P(k) = e^(-λ) λ^k / k!             E = λ     Var = λ
```

Because the binomial is a **sum** of independent Bernoullis, linearity gives `np` and the independent-variance rule gives `np(1-p)`; no table is needed. Closure facts: independent Poissons add (`Poisson(λ1) + Poisson(λ2) = Poisson(λ1 + λ2)`); binomials with the same `p` add (`n1 + n2` tries).

**Poisson as a limit.** Fix `λ = np` and let `n` grow: `Binomial(n, λ/n)` approaches `Poisson(λ)`. The distance is measurable. For `λ = 4`, total variation distance (half the summed gaps between the two tables) is:

| n | p = 4/n | distance | Le Cam bound `n p²` |
|---|---|---|---|
| 10 | 0.4 | 0.1253 | 1.6 (useless) |
| 100 | 0.04 | 0.0102 | 0.16 |
| 1000 | 0.004 | 0.0010 | 0.016 |

The distance falls roughly like `1/n`, as the bound `λ²/n` says. Use Poisson for the binomial when `n` is large **and** `p` small; with `n = 10, p = 0.4` it is a poor stand-in.

**Dispersion check.** Index of dispersion = `variance / mean`. Poisson says 1. Ravi's 12 windows give `7.85 / 3.75 ≈ 2.1` (mixed rates); couples ordering together push a binomial's variance from 2.1 to 4.2 (over-dispersion). Under-dispersion (below 1) signals something too regular to be random arrivals.

## 5. The normal curve

```text
density   f(x) = exp(-(x - μ)^2 / (2σ^2)) / (σ sqrt(2π))
standardise   z = (x - μ) / σ         Z ~ Normal(0, 1)
P(a <= X <= b) = Φ((b - μ)/σ) - Φ((a - μ)/σ)       Φ has no closed form: use cdf
within 1, 2, 3 σ:  68.27%, 95.45%, 99.73%          within 1.96 σ: 95.00%
```

In Python: `NormalDist(mu, sigma).cdf(x)`, `.inv_cdf(p)`, `.zscore(x)`.

**Normal approximation to the binomial.** `Binomial(n, p)` is roughly `Normal(np, np(1-p))` when both `np` and `n(1-p)` are comfortably large (a common rule of thumb is 10 or more; it is a guideline, not a theorem). Because the binomial is discrete and the normal continuous, apply a **continuity correction**: `P(X <= k)` becomes `Φ((k + 0.5 - np) / sd)`. Example, `n = 30, p = 0.5`, `P(X <= 12)`:

```text
exact                          0.18080
normal, no correction          0.13666
normal, with k + 0.5           0.18066
```

At `n = 10, p = 0.3` the same trick gives 0.365 against the exact 0.383, and without the correction 0.245. The skew of a small `np` is what the bell cannot copy.

## 6. Assumptions at a glance

| Model | Assumes | Breaks when | Quick check |
|---|---|---|---|
| Equally likely list | Every outcome has the same chance | Loaded dice, uneven sampling | Compare long-run frequencies |
| `P(A)P(B)` product | A and B independent | One tells you about the other | Count the overlap directly |
| Repeated Bayes update | Conditionally independent evidence | Shared reagent, same batch | Ask what the tests share |
| Binomial | Fixed `n`, same `p`, independent tries | Couples, changing `p` | Variance vs `np(1-p)` |
| Poisson | Constant rate, independent arrivals | Rush hours, bursts | Variance vs mean |
| Normal | One hump, symmetric, thin tails | Two clumps, long tail | Histogram first, then the 0.5 / 1 / 2 SD count |

## 7. Computing it safely

- **Exact first:** `fractions.Fraction` keeps small problems free of rounding, as in the stories.
- **Large `n`:** `comb(n, k) p^k (1-p)^(n-k)` overflows or underflows in floating point; sum the logs (`lgamma`) and exponentiate once, as the [lab](/fields/data-science/probability-statistics/labs/distributions.html ':ignore') does.
- **Tails:** compute `1 - cdf` carefully for tiny tails (`sf` in SciPy, if you use it); subtracting two numbers close to 1 loses digits.
- **Simulate to check, seed to repeat:** `random.seed(9)` makes a run reproducible, and a simulation should agree with the exact answer within its own noise (about `1/sqrt(draws)` for a probability).

**Try it:** [Bayes lab](/fields/data-science/probability-statistics/labs/bayes.html ':ignore') (move the base rate and see the posterior) and [distributions lab](/fields/data-science/probability-statistics/labs/distributions.html ':ignore') (binomial, Poisson, normal, with a Poisson overlay and sampled draws). Short steps: [Probability quick guide](/fields/data-science/probability-statistics/probability/quick-guide.md).

## 8. Short derivations

```text
Bayes          P(A and B) = P(A | B) P(B) = P(B | A) P(A)      divide by P(B)
Variance       E[(X-μ)^2] = E[X^2] - 2μ E[X] + μ^2 = E[X^2] - μ^2
Binomial       X = B1 + ... + Bn, Bi ~ Bernoulli(p) independent
               E[Bi] = p, Var(Bi) = p - p^2 = p(1-p), so E[X] = np, Var(X) = np(1-p)
Poisson mean   sum of k e^(-λ) λ^k / k!  =  λ * sum of e^(-λ) λ^(k-1) / (k-1)!  =  λ
Poisson limit  C(n,k) (λ/n)^k (1-λ/n)^(n-k)
               = (λ^k / k!) * [n(n-1)...(n-k+1) / n^k] * (1-λ/n)^n * (1-λ/n)^(-k)
               -> (λ^k / k!) * 1 * e^(-λ) * 1          as n grows, k and λ fixed
Standardise    E[(X-μ)/σ] = 0 and Var((X-μ)/σ) = 1 by the shift/scale rules;
               a shifted, rescaled normal is still normal (a property of the family)
```

## 9. Run the identities

Each identity above, asserted on the series' own numbers with exact fractions. If an assertion fails, Python stops; if all hold it prints the last line.

```python
import math, itertools
from fractions import Fraction as F
from statistics import NormalDist

# 1. inclusion-exclusion on two dice
grid = list(itertools.product(range(1, 7), repeat=2))
A = {g for g in grid if g[0] == g[1]}; B = {g for g in grid if sum(g) == 8}
assert F(len(A | B), 36) == F(len(A), 36) + F(len(B), 36) - F(len(A & B), 36)

# 2. Bayes in odds form equals the fraction
prior, se, fp = F(1, 1000), F(99, 100), F(1, 100)
direct = se * prior / (se * prior + fp * (1 - prior))
odds = prior / (1 - prior) * (se / fp)
assert direct == odds / (1 + odds) == F(11, 122)

# 3. Binomial moments equal n p and n p (1-p), exactly
n, p = 10, F(3, 10)
pmf = [math.comb(n, k) * p**k * (1 - p)**(n - k) for k in range(n + 1)]
mean = sum(k * q for k, q in enumerate(pmf)); var = sum(k * k * q for k, q in enumerate(pmf)) - mean**2
assert sum(pmf) == 1 and mean == n * p and var == n * p * (1 - p)

# 4. Var(X+Y) = Var X + Var Y + 2 Cov, on the lucky tin; Cov(X,X) = Var X
tab = {0: F(5, 10), 5: F(3, 10), 10: F(1, 10), 20: F(1, 10)}
E_ = lambda f, d: sum(f(x) * q for x, q in d.items())
m = E_(lambda x: x, tab); v = E_(lambda x: x * x, tab) - m * m
joint = {(a, b): pa * pb for (a, pa), (b, pb) in itertools.product(tab.items(), repeat=2)}
cov = sum((a - m) * (b - m) * q for (a, b), q in joint.items())
assert cov == 0 and sum(((a + b) - 2 * m) ** 2 * q for (a, b), q in joint.items()) == 2 * v == F(149, 2)
assert E_(lambda x: (2 * x - 2 * m) ** 2, tab) == 4 * v == 149

# 4b. Poisson limit: total variation distance shrinks as n grows (lam = 4)
def tv(n, lam=4):
    pp = lambda k: math.exp(-lam) * lam**k / math.factorial(k)
    pb = lambda k: math.comb(n, k) * (lam / n)**k * (1 - lam / n)**(n - k)
    return 0.5 * sum(abs(pb(k) - pp(k)) for k in range(min(n, 150) + 1))
d = [tv(n) for n in (10, 100, 1000)]
assert d[0] > d[1] > d[2] and all(x <= n * (4 / n) ** 2 for x, n in zip(d, (10, 100, 1000)))

# 5. Standard normal tails and continuity correction
N = NormalDist()
assert round(N.cdf(1) - N.cdf(-1), 4) == 0.6827 and round(N.cdf(1.96) - N.cdf(-1.96), 3) == 0.95
exact = sum(math.comb(30, k) for k in range(13)) / 2**30
cc = N.cdf((12.5 - 15) / math.sqrt(7.5)); nocc = N.cdf((12 - 15) / math.sqrt(7.5))
assert abs(cc - exact) < abs(nocc - exact)
print("all checks passed", [round(x, 4) for x in d], round(exact, 5), round(cc, 5), round(nocc, 5))
```

```text
all checks passed [0.1253, 0.0102, 0.001] 0.1808 0.18066 0.13666
```

Run with Python 3 and the standard library only. If you use SciPy, the same objects are `scipy.stats.binom`, `poisson` and `norm` (`pmf`, `cdf`, `ppf`, `sf`); those names are not run on this page.

## References

- Series pages: [Counting the Ways](/fields/data-science/probability-statistics/probability/counting-the-ways.md), [The Test That Was 99% Accurate](/fields/data-science/probability-statistics/probability/the-test-that-was-99-percent-accurate.md), [What to Expect](/fields/data-science/probability-statistics/probability/what-to-expect.md), [Coins and Calls](/fields/data-science/probability-statistics/probability/coins-and-calls.md), [The Bell Curve](/fields/data-science/probability-statistics/probability/the-bell-curve.md).
- NIST/SEMATECH e-Handbook of Statistical Methods, *Binomial*, *Poisson* and *Normal Distribution* pages (mean, variance and density formulas).
- Python `statistics.NormalDist`, `math.comb`, `math.perm`, `fractions`.
- Le Cam's inequality for the Poisson approximation: total variation distance between a sum of independent Bernoulli(p_i) and Poisson(Σp_i) is at most Σp_i². Here only the numerical distances in the table were computed; the bound is quoted from the literature, not rederived.
- All figures above (11/122, 363/400, the distance table, the continuity-correction values, 68.27 / 95.45 / 99.73, 7.85 / 3.75) were recomputed with Python's standard library.
