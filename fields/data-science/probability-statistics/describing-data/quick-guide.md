
<!-- related-block -->
<nav class="crumbs" aria-label="Breadcrumb"><a href="#/fields/">Fields</a> / <a href="#/fields/data-science/">Data Science</a> / <a href="#/fields/data-science/probability-statistics/">Probability &amp; Statistics, One Sip at a Time</a> / <a href="#/fields/data-science/probability-statistics/describing-data/">Describing Data</a></nav>

# Summarise a Data Set: Which Number, Which Picture

<!-- related-block -->
<div class="reading-time">Beginner · Guide · 3 min read · Updated 25 Nov 2026</div>
<!-- related-block -->
<div class="tag-chips"><a class="chip" href="#/.docs/generated/explore/tags/statistics">statistics</a></div>


> **Quick guide for** [Samples, Data Types and Tables](/fields/data-science/probability-statistics/describing-data/samples-data-types-and-tables.md) (parts 1 and 2), [Pictures and the Middle](/fields/data-science/probability-statistics/describing-data/pictures-and-the-middle.md) (parts 3 and 4) and [Spread and Position](/fields/data-science/probability-statistics/describing-data/spread-and-position.md) (parts 5 and 6).
> Python 3, standard library only. Formal statements: [technical reference](/fields/data-science/probability-statistics/describing-data/technical-reference.md).

## 1. Sample

| Two questions | Method |
|---|---|
| No groups, by chance | simple random |
| No groups, by pattern | systematic: `k = N / n`, random start |
| Groups, every group, some people | stratified: `n_h = n * N_h / N` |
| Groups, some groups, every person | cluster |

Bias does not shrink with `n`.

## 2. Classify and count

Same or different: nominal. Which first: ordinal. How far apart: discrete (counted) or continuous (measured). Digits used as labels are nominal.

Checks: `sum of f = n`, `sum of f/n = 1`, last cumulative frequency `= n`. Grouped: `h = Range / k`, rounded up.

## 3. Draw

| Question | Picture |
|---|---|
| How much lives here? | histogram (area = count) |
| How do two crowds compare? | frequency polygon |
| How many at or below here? | ogive: `(upper boundary, CF)` |

## 4. Middle and spread

| Data | Middle | Spread |
|---|---|---|
| Nominal | mode | none |
| Ordinal | median | IQR |
| Symmetric numbers | mean | SD |
| Skewed or outliers | median | IQR |

`mean > median` means a right tail. Grouped mean: `sum of (f * M) / sum of f`.

```python
import statistics as st
data = [2, 4, 9]
st.pvariance(data)   # divides by n: "this is everyone"
st.variance(data)    # divides by n - 1: "this is a sample" -> 13
```

## 5. Place one value

`percentile rank = (below + 0.5 * equal) / n * 100`; `z = (x - mean) / SD`.

```python
d = list(range(1, 10))
st.quantiles(d, n=4)                        # [2.5, 5.0, 7.5]
st.quantiles(d, n=4, method='inclusive')    # [3.0, 5.0, 7.0]
```

Box plot fences: `Q1 - 1.5 * IQR` and `Q3 + 1.5 * IQR`. Say which quartile method you used.

## Symptoms

| What you see | Likely cause | Fix |
|---|---|---|
| Average describes nobody | Two clumps | Histogram first, describe both |
| Mean and median far apart | Long tail or outlier | Report the median |
| Bigger sample, same wrong answer | Biased frame | Fix how you choose, not how many |
| Quartiles differ between tools | Different method | Pick one and say which |

> [!WARNING]
> Divide by `n` only if the data are everyone; divide by `n - 1` for a sample. Look at the picture before you trust any summary number.

## Try it

### Sampling methods lab

[Sampling methods lab](/fields/data-science/probability-statistics/labs/sampling-methods.html#embed ':ignore')

### Grouped tables lab

[Grouped tables lab](/fields/data-science/probability-statistics/labs/grouped-tables.html#embed ':ignore')

### Describing data lab

[Describing data lab](/fields/data-science/probability-statistics/labs/describing.html#embed ':ignore')

**Why it works:** the three story pages above (parts 1 to 6). Next: [Probability](/fields/data-science/probability-statistics/probability/README.md).

<!-- related-block -->
<div class="see-also">

**See also**

- [Describing Data, Technically: Definitions, Identities and Method Choices](/fields/data-science/probability-statistics/describing-data/technical-reference.md) — The formal layer under parts 1 to 6: scales of measurement, grouped-data formulas, what the mean and median minimise, n versus n-1, quartile methods, fences and sampling designs.
- [Pictures and the Middle: Histogram, Polygon, Ogive, and What 'Typical' Means](/fields/data-science/probability-statistics/describing-data/pictures-and-the-middle.md) — Draw the table before you summarise it: histogram for amount, polygon for comparison, ogive for up to here. Then "typical" is three questions, mean, median and mode, and none answers two clumps.
- [Samples, Data Types and Tables: Who You Asked, What Kind of Column, How to Count It](/fields/data-science/probability-statistics/describing-data/samples-data-types-and-tables.md) — A sample speaks for a crowd only if you chose it fairly. The kind of column decides which arithmetic is allowed, and a frequency table counts it without losing the shape, if the drawers touch.
- [Spread and Position: Variance, n − 1, Percentiles, Z-Scores and the Box Plot](/fields/data-science/probability-statistics/describing-data/spread-and-position.md) — Mean, median and mode are three attitudes to how a long walk hurts; spread is the walking left over. A value then has a position only in its crowd: rank (percentile) or distance (z-score).

</div>
<!-- related-block -->
<div class="mentioned-in">

**Mentioned in**

- [Describing Data, Technically: Definitions, Identities and Method Choices](/fields/data-science/probability-statistics/describing-data/technical-reference.md) — The formal layer under parts 1 to 6: scales of measurement, grouped-data formulas, what the mean and median minimise, n versus n-1, quartile methods, fences and sampling designs.

</div>
