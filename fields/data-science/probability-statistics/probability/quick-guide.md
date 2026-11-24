---
id: probability-quick-guide
title: "Pick and Compute the Right Probability Model"
sidebar_label: "Quick guide: probability"
order: 13
summary: A cheat sheet for parts 7 to 11 - the method, the code and the expected output for counting outcomes, flipping a test result, expected value, binomial or Poisson, and the normal curve.
level: beginner
type:
  - guide
  - reference
domains:
  - statistics
tags:
  - statistics
relations:
  related:
    - counting-the-ways
    - the-test-that-was-99-percent-accurate
    - what-to-expect
    - coins-and-calls
    - the-bell-curve
    - probability-technical-reference
---

# Pick and Compute the Right Probability Model

> **Quick guide for** [Counting the Ways](/fields/data-science/probability-statistics/probability/counting-the-ways.md), [The Test That Was 99% Accurate](/fields/data-science/probability-statistics/probability/the-test-that-was-99-percent-accurate.md), [What to Expect](/fields/data-science/probability-statistics/probability/what-to-expect.md), [Coins and Calls](/fields/data-science/probability-statistics/probability/coins-and-calls.md) and [The Bell Curve](/fields/data-science/probability-statistics/probability/the-bell-curve.md).
> Python 3, standard library only. Formal statements: [technical reference](/fields/data-science/probability-statistics/probability/technical-reference.md).

## 1. Count outcomes

```python
import itertools
grid = list(itertools.product(range(1, 7), repeat=2))
double = {g for g in grid if g[0] == g[1]}
eight  = {g for g in grid if sum(g) == 8}
print(len(double | eight))        # 10  ->  P = 10/36
```

`P(A or B) = P(A) + P(B) - P(A and B)`. "At least one" is `1 - P(none)`: at least one six in two rolls is `1 - 25/36 = 11/36`.

## 2. Flip a test result

```python
from fractions import Fraction as F
sick = 100_000 * F(1, 1000); clean = 100_000 - sick
tp = sick * F(99, 100); fp = clean * F(1, 100)
print(tp, fp, tp / (tp + fp))     # 99 999 11/122  ->  about 9%
```

Count inside the positives. A second independent positive uses 11/122 as the new base rate: `363/400 = 90.75%`.

## 3. Expected value

`E[X] = sum of x * p`, `Var = E[X^2] - E[X]^2`. The lucky tin: `9/2`, variance `149/4`, SD about 6.1. `E[X + Y]` always adds; variances add only for independent pulls.

## 4. Binomial or Poisson

| The question counts | Recipe | Mean, variance |
|---|---|---|
| Yeses in `n` independent tries, same `p` | Binomial | `np`, `np(1-p)` |
| Events in a window, constant rate | Poisson | `λ`, `λ` |

```python
import math
print(math.comb(10, 3) * 0.3**3 * 0.7**7)   # about 0.2668
```

## 5. Normal curve

```python
from statistics import NormalDist
bag = NormalDist(100, 4)
print(bag.zscore(106), round(bag.cdf(106), 4), round(bag.inv_cdf(0.95), 2))   # 1.5 0.9332 106.58
```

Histogram first. Within 1, 2, 3 SD is 68.27%, 95.45%, 99.73%.

## Symptoms

| What you see | Likely cause | Fix |
|---|---|---|
| "or" answer too big | Shared outcome counted twice | Subtract the overlap |
| 99% for a rare thing | Flipped condition | Count inside the positives |
| Poisson variance far above mean | Two rates averaged | One Poisson per period |
| Bell gives wrong shares | Not one hump | Use percentiles |

> [!WARNING]
> Never add overlapping chances (`10 × 0.3 = 300%` is wrong; use `1 - 0.7^10 = 0.9718`). A repeated test helps only if its mistakes are independent.

## Try it

[Bayes lab](/fields/data-science/probability-statistics/labs/bayes.html#embed ':ignore')

[Distributions lab](/fields/data-science/probability-statistics/labs/distributions.html#embed ':ignore')

**Why it works:** the five story pages above. Next: [Inference](/fields/data-science/probability-statistics/inference/README.md).
