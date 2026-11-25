
<!-- related-block -->
<nav class="crumbs" aria-label="Breadcrumb"><a href="#/fields/">Fields</a> / <a href="#/fields/data-science/">Data Science</a> / <a href="#/fields/data-science/probability-statistics/">Probability &amp; Statistics, One Sip at a Time</a> / <a href="#/fields/data-science/probability-statistics/describing-data/">Describing Data</a></nav>

# Describing Data, Technically: Definitions, Identities and Method Choices

<!-- related-block -->
<div class="reading-time">Intermediate · Reference · 4 min read · Updated 24 Nov 2026</div>
<!-- related-block -->
<div class="tag-chips"><a class="chip" href="#/.docs/generated/explore/tags/statistics">statistics</a></div>
<!-- related-block -->
<div class="related-strip">

**Read first:** [Samples, Data Types and Tables: Who You Asked, What Kind of Column, How to Count It](/fields/data-science/probability-statistics/describing-data/samples-data-types-and-tables.md)

</div>


> The formal layer under parts 1 to 6. The stories give the intuition; this page gives statements you can check and reuse. Every number was recomputed with Python's standard library, and the script at the end asserts each identity.

## 1. Populations, samples and designs

```text
parameter   a number describing the population (μ, σ, p)
statistic   the same quantity computed from a sample (x̄, s, p̂)
frame       the list you actually draw from; frame ≠ population is a source of bias
```

| Design | Rule | Watch for |
|---|---|---|
| Simple random | every unit has the same chance, from the full list | needs a complete frame |
| Systematic | step `k = N / n` after a random start | a rhythm in the list that matches `k` |
| Stratified | proportional allocation `n_h = n × N_h / N` | strata must be known in advance |
| Cluster | randomly choose whole groups, then take everyone in them | units in a cluster resemble each other |

Example: `N = 1000`, `n = 50` gives `k = 20`, and strata of 600, 300, 100 get 30, 15, 5. **Bias is not cured by `n`:** a larger sample from a bad frame is a more precise wrong answer.

## 2. Scales and what they allow

| Scale | Order? | Distances? | Sensible summaries |
|---|---|---|---|
| Nominal | no | no | counts, mode |
| Ordinal | yes | no | median, percentiles |
| Discrete or continuous numeric | yes | yes | mean, SD, everything above |

Labels written as digits (IDs, postal codes) are nominal: averaging them is meaningless.

## 3. Frequency tables and grouped data

```text
checks         sum of f = n          sum of f / n = 1          last cumulative frequency = n
class count    k classes, width h = Range / k, rounded UP        Range = max - min
boundaries     limits -/+ half the measuring unit (0.5, 0.05, ...)
midpoint       M = (lower boundary + upper boundary) / 2
grouped mean   x̄ ≈ sum of (f × M) / sum of f
grouped median ≈ L + ((N/2 - cf) / f) × h     L: lower boundary of the median class, cf: frequency before it
histogram      area = count, so with unequal widths the height is f / width
ogive          plot (upper boundary, cumulative frequency); straight lines assume an even spread inside each class
```

Worked example: classes 0-10, 10-20, 20-30, 30-40 with `f = 4, 10, 8, 3` (`N = 25`) give a mean of `475 / 25 = 19.0` and a median of `10 + (12.5 - 4) / 10 × 10 = 18.5`. Both are estimates, because the classes hide where values sit.

## 4. Centre: what each one minimises

```text
mean     Σ(x - x̄) = 0                        minimises Σ(x - c)^2      (least squared walking)
median   any c between the two middle values  minimises Σ|x - c|        (least walking)
mode     the most frequent value              minimises nothing; may be absent or several
```

Robustness check on Kettle Street (`1, 2, 2, 3, 5, 9, 20`): mean 6, median 3. Replace the 20 by 200 and the mean passes 30 while the median stays 3 (**breakdown**: one value can drag the mean anywhere; the median needs half the data to be bad). Order by skew: `mean > median` suggests a right tail, `mean < median` a left tail; two clumps need both described.

## 5. Spread

```text
variance (population)  σ² = Σ(x - μ)² / N          SD = sqrt(variance)
variance (sample)      s² = Σ(x - x̄)² / (n - 1)
shortcut               Σ(x - x̄)² = Σx² - n x̄²
range = max - min      IQR = Q3 - Q1      (partner of the median)
linear change          mean(aX + b) = a·mean + b      SD(aX + b) = |a|·SD      (a shift does not change spread)
```

**Why `n - 1`.** Deviations are measured from `x̄`, which is fitted to the same sample and so sits closer to the data than `μ` does. Dividing by `n` is too small by exactly the factor `(n - 1) / n` on average. Exact check: population `2, 4, 9` has `σ² = 26/3`; averaging over all 9 draws of 2 with replacement, dividing by `n - 1` gives exactly `26/3`, dividing by `n` gives `13/3`. Python: `pvariance` and `pstdev` divide by `n`, `variance` and `stdev` by `n - 1`.

## 6. Position

```text
percentile rank   (count below + 0.5 × count equal) / n × 100        order only, resistant to outliers
z-score           z = (x - mean) / SD      a standardised set has mean 0 and SD 1
box plot          fences at Q1 - 1.5 IQR and Q3 + 1.5 IQR; whiskers end at the last point inside
```

**Quartile methods differ.** For `1 .. 9`, `statistics.quantiles(d, n=4)` (exclusive, the default) gives `2.5, 5.0, 7.5` and `method="inclusive"` gives `3.0, 5.0, 7.0`. Pick one, say which, do not mix. Kettle Street: `Q1 = 2`, `Q3 = 9`, upper fence `9 + 1.5 × 7 = 19.5`, so the house of 20 is an outlier. Percentile rank of 3 there: `(3 + 0.5) / 7 = 50%`.

## 7. Choosing a method

| Question | Use | Because |
|---|---|---|
| Typical, symmetric numbers | mean and SD | efficient, uses every value |
| Typical, skewed or with outliers | median and IQR | resistant |
| Typical, nominal | mode | the only one defined |
| Where does one value stand? | percentile (skewed) or z-score (bell-like) | rank versus distance |
| Compare groups | box plots; histograms for shape | landmarks versus shape |

Always draw first: two clumps average to a value nobody lives at, and no summary number shows that.

## 8. Run the identities

Each identity above, asserted with exact fractions or the series' own data (Mira's 20 scores, Kettle Street). If an assertion fails Python stops; otherwise it prints the last line.

```python
import itertools, statistics as st
from fractions import Fraction as F

scores = [52,55,55,58,58,58,62,62,62,71,71,89,89,89,93,93,94,94,95,104]
houses = [1, 2, 2, 3, 5, 9, 20]

# 1. The mean balances, minimises squared walking; the median minimises plain walking
m = st.fmean(scores)
assert abs(sum(x - m for x in scores)) < 1e-9
grid = [g / 10 for g in range(400, 1100)]
assert abs(min(grid, key=lambda c: sum((x - c) ** 2 for x in scores)) - m) <= 0.05
best = [c for c in grid if sum(abs(x - c) for x in scores) == min(sum(abs(x - g) for x in scores) for g in grid)]
assert min(best) <= st.median(scores) <= max(best)          # any c between the two middle values ties

# 2. Computing shortcut for the sum of squares, and n versus n - 1 (exact)
d = [F(2), F(4), F(9)]
mean = sum(d) / 3
assert sum((x - mean) ** 2 for x in d) == sum(x * x for x in d) - 3 * mean ** 2
pvar = sum((x - mean) ** 2 for x in d) / 3
assert pvar == F(26, 3) and sum((x - mean) ** 2 for x in d) / 2 == 13
# draw 2 with replacement: dividing by n - 1 is right on average, dividing by n is too small by (n-1)/n
def s2(pair, div): mu = sum(pair) / 2; return sum((x - mu) ** 2 for x in pair) / div
runs = list(itertools.product(d, repeat=2))
assert sum(s2(p, 1) for p in runs) / 9 == pvar              # n - 1 = 1
assert sum(s2(p, 2) for p in runs) / 9 == pvar / 2          # n = 2

# 3. z-scores: mean 0, SD 1 (population SD)
z = [(x - st.fmean(scores)) / st.pstdev(scores) for x in scores]
assert abs(st.fmean(z)) < 1e-9 and abs(st.pstdev(z) - 1) < 1e-9

# 4. Quartile methods differ
d9 = list(range(1, 10))
assert st.quantiles(d9, n=4) == [2.5, 5.0, 7.5] and st.quantiles(d9, n=4, method="inclusive") == [3.0, 5.0, 7.0]

# 5. Fences and robustness on Kettle Street
q1, q2, q3 = st.quantiles(houses, n=4)
fence = q3 + 1.5 * (q3 - q1)
assert (q1, q3, fence) == (2, 9, 19.5) and 20 > fence and st.median(houses) == 3 and st.fmean(houses) == 6
assert st.median(houses[:-1] + [200]) == 3 and st.fmean(houses[:-1] + [200]) > 30    # one wrong house moves the mean, not the median

# 6. Percentile rank
data = [1, 2, 2, 3, 5, 9, 20]
below, equal = sum(x < 3 for x in data), sum(x == 3 for x in data)
assert (below + 0.5 * equal) / len(data) * 100 == 50.0

# 7. Grouped data
f, M, L, h, N = [4, 10, 8, 3], [5, 15, 25, 35], 10, 10, 25
assert sum(a * b for a, b in zip(f, M)) / N == 19.0
assert L + (N / 2 - f[0]) / f[1] * h == 18.5

# 8. Allocation
assert [50 * n // 1000 for n in (600, 300, 100)] == [30, 15, 5] and 1000 // 50 == 20
print("all checks passed", round(st.fmean(scores), 1), round(st.stdev(scores), 2), (q1, q2, q3, fence))
```

```text
all checks passed 75.2 17.67 (2.0, 3.0, 9.0, 19.5)
```

Run with Python 3 and the standard library only.

## Try it

Pick a data set, add or move one value and watch the mean, median, SD and IQR react; change the bin width and see how the histogram's story changes. Short steps: [Describing data quick guide](/fields/data-science/probability-statistics/describing-data/quick-guide.md).

[Describing data lab](/fields/data-science/probability-statistics/labs/describing.html#embed ':ignore')

## References

- Series pages: [Samples, Data Types and Tables](/fields/data-science/probability-statistics/describing-data/samples-data-types-and-tables.md), [Pictures and the Middle](/fields/data-science/probability-statistics/describing-data/pictures-and-the-middle.md), [Spread and Position](/fields/data-science/probability-statistics/describing-data/spread-and-position.md).
- Python `statistics`: `fmean`, `median`, `pvariance`, `variance`, `pstdev`, `stdev`, `quantiles`.
- Every figure above was recomputed with Python's standard library. The stratified and grouped-data examples are this page's own small numbers, checked by the script.

<!-- related-block -->
<div class="see-also">

**See also**

- [Pictures and the Middle: Histogram, Polygon, Ogive, and What 'Typical' Means](/fields/data-science/probability-statistics/describing-data/pictures-and-the-middle.md) — Draw the table before you summarise it: histogram for amount, polygon for comparison, ogive for up to here. Then "typical" is three questions, mean, median and mode, and none answers two clumps.
- [Spread and Position: Variance, n − 1, Percentiles, Z-Scores and the Box Plot](/fields/data-science/probability-statistics/describing-data/spread-and-position.md) — Mean, median and mode are three attitudes to how a long walk hurts; spread is the walking left over. A value then has a position only in its crowd: rank (percentile) or distance (z-score).
- [Summarise a Data Set: Which Number, Which Picture](/fields/data-science/probability-statistics/describing-data/quick-guide.md) — A cheat sheet for parts 1 to 6 - choose a sampling method, classify the data, pick the picture, pick the middle and the spread, and place one value in its crowd.

</div>
<!-- related-block -->
<div class="mentioned-in">

**Mentioned in**

- [Summarise a Data Set: Which Number, Which Picture](/fields/data-science/probability-statistics/describing-data/quick-guide.md) — A cheat sheet for parts 1 to 6 - choose a sampling method, classify the data, pick the picture, pick the middle and the spread, and place one value in its crowd.

</div>
