
<!-- related-block -->
<nav class="crumbs" aria-label="Breadcrumb"><a href="#/fields/">Fields</a> / <a href="#/fields/data-science/">Data Science</a> / <a href="#/fields/data-science/probability-statistics/">Probability &amp; Statistics, One Sip at a Time</a> / <a href="#/fields/data-science/probability-statistics/probability/">Probability</a></nav>

# Pick and Compute the Right Probability Model

<!-- related-block -->
<div class="reading-time">Beginner · Guide · 2 min read · Updated 25 Nov 2026</div>
<!-- related-block -->
<div class="tag-chips"><a class="chip" href="#/.docs/generated/explore/tags/statistics">statistics</a></div>


> **Quick guide for** [Counting and Conditioning](/fields/data-science/probability-statistics/probability/counting-and-conditioning.md) (parts 7 and 8), [Expectation and the Two Count Recipes](/fields/data-science/probability-statistics/probability/expectation-binomial-poisson.md) (parts 9 and 10) and [The Bell Curve](/fields/data-science/probability-statistics/probability/the-bell-curve.md).
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

### Expected value lab

[Expected value lab](/fields/data-science/probability-statistics/labs/expected-value.html#embed ':ignore')

### Bayes lab

[Bayes lab](/fields/data-science/probability-statistics/labs/bayes.html#embed ':ignore')

### Distributions lab

[Distributions lab](/fields/data-science/probability-statistics/labs/distributions.html#embed ':ignore')

**Why it works:** the three story pages above (parts 7 to 11). Next: [Inference](/fields/data-science/probability-statistics/inference/README.md).

<!-- related-block -->
<div class="see-also">

**See also**

- [Counting and Conditioning: Why a 99% Accurate Test Is Usually Wrong](/fields/data-science/probability-statistics/probability/counting-and-conditioning.md) — Probability is a share of the equally likely ways, so "or" adds, "and" multiplies and "at least one" is 1 minus none. Conditioning shrinks the crowd, and Bayes' rule reads that count backwards.
- [Expectation and the Two Count Recipes: Binomial and Poisson](/fields/data-science/probability-statistics/probability/expectation-binomial-poisson.md) — Expected value is the data's seesaw with probability as the weight, not the likeliest outcome. Binomial and Poisson are recipes for a count; each is right only as far as its assumptions hold.
- [Probability, Technically: Definitions, Identities and Assumptions](/fields/data-science/probability-statistics/probability/technical-reference.md) — The formal layer under parts 7 to 11: axioms, Bayes in odds form, pmf, cdf and density, moment rules, the Poisson limit, the normal approximation and each model's assumptions.
- [The Bell Curve: Probability as Area, and One Ruler for Every Bell](/fields/data-science/probability-statistics/probability/the-bell-curve.md) — Many small nudges add up to a bell. For continuous data probability is area, and the z-score makes every bell the same bell, so one table serves all of them, until the data are not a bell.

</div>
<!-- related-block -->
<div class="mentioned-in">

**Mentioned in**

- [Probability, Technically: Definitions, Identities and Assumptions](/fields/data-science/probability-statistics/probability/technical-reference.md) — The formal layer under parts 7 to 11: axioms, Bayes in odds form, pmf, cdf and density, moment rules, the Poisson limit, the normal approximation and each model's assumptions.

</div>
