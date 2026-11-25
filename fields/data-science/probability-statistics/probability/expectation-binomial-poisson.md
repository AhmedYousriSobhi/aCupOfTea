
<!-- related-block -->
<nav class="crumbs" aria-label="Breadcrumb"><a href="#/fields/">Fields</a> / <a href="#/fields/data-science/">Data Science</a> / <a href="#/fields/data-science/probability-statistics/">Probability &amp; Statistics, One Sip at a Time</a> / <a href="#/fields/data-science/probability-statistics/probability/">Probability</a></nav>

# Expectation and the Two Count Recipes: Binomial and Poisson

<!-- related-block -->
<div class="reading-time">Intermediate · Concept · 12 min read · Updated 25 Nov 2026</div>
<!-- related-block -->
<div class="tag-chips"><a class="chip" href="#/.docs/generated/explore/tags/statistics">statistics</a></div>
<!-- related-block -->
<div class="lab-line">Interactive lab: <a href="#/fields/data-science/probability-statistics/probability/expectation-binomial-poisson?id=try-it-expected-is-not-likely-edit-the-bag-and-see">Expected is not likely, edit the bag and see</a></div>
<!-- related-block -->
<div class="related-strip">

**Read first:** [Counting and Conditioning: Why a 99% Accurate Test Is Usually Wrong](/fields/data-science/probability-statistics/probability/counting-and-conditioning.md)  ·  **Read next:** [The Bell Curve: Probability as Area, and One Ruler for Every Bell](/fields/data-science/probability-statistics/probability/the-bell-curve.md)

</div>


> **Parts 9 and 10 of 15.** Part of the [Probability & Statistics](/fields/data-science/probability-statistics/README.md) series, after [Counting and Conditioning](/fields/data-science/probability-statistics/probability/counting-and-conditioning.md). The scenario numbers are invented; every figure was recomputed with Python 3.14.4 (exact fractions, enumeration, and one seeded simulation).

Before lunch on Saturday, Tala will give Mira three forecasts for the market stall. Each will be the most sensible number in the room. Each will be wrong in a way that costs money, and not one of them will be a calculation error.

**By the end of this page you will be able to:**

- Compute an expected value and a variance from a probability table, and say why the expected value is not the likeliest outcome.
- Apply the shift, scale and sum rules, and know when variances add.
- Pick binomial or Poisson from the shape of the question and write its table.
- Spot when a recipe's assumptions fail, from the variance.

* * *

## Three forecasts before lunch

Mira runs a stall with three things going on.

- **The lucky tin.** A customer pays 5 coins, pulls one card from a bag of ten and wins the prize printed on it: 5 cards say 0 (a sticker), 3 say 5 (a sachet), 1 says 10 and 1 says 20.
- **The smoky blend.** About 3 customers in 10 pick it. Ten are in the queue.
- **The walk-ins.** About 4 customers arrive every 10 minutes.

Tala forecasts. "Lucky tin: expect a sticker. Smoky: three of the ten. Walk-ins: about four per ten minutes, all day."

Ravi pulls once and wins the big tin. "Rigged," he says, in our favour.

* * *

## Where each forecast breaks

1. **"Expect a sticker."** The most likely single pull is the sticker (probability 0.5), but that is not what the stall pays out on average.
2. **"Three smoky."** She is right that three is the most likely count. It will still be wrong most of the time.
3. **"Four per ten minutes, all day."** Ravi tallies the lunch rush and mutters that a single average hides two shops. The stall is short-staffed at 12:30.

Each forecast answered "what is typical?" with a point. The stall needs the whole table of chances. Build it.

* * *

## From a table of chances to two recipes

### Random variables and the probability table

A **random variable** is a number attached to each way things could turn out. The card is the chance; the prize `X` printed on it is the random variable. List each value with its probability:

| Prize `x` | 0 | 5 | 10 | 20 |
|---|---|---|---|---|
| Probability `p` | 5/10 | 3/10 | 1/10 | 1/10 |

The probabilities add to 1. This is the frequency table of part 2 with one change: a frequency table is what a bag *did* produce, a probability table is what it *would* produce, in the model. **Relative frequency in the data; probability in the model.**

### Expected value is the seesaw

The mean was the balance point of values weighted by frequency. Weight by probability and it becomes the **expected value**:

```python
from fractions import Fraction as F
import statistics as st

table = {0: F(5, 10), 5: F(3, 10), 10: F(1, 10), 20: F(1, 10)}
print(sum(x * p for x, p in table.items()))              # E[X], exact

tray = [0] * 5 + [5] * 3 + [10] + [20]                   # the ten cards as data
print(st.fmean(tray), st.fmean(list(table), weights=[0.5, 0.3, 0.1, 0.1]))
```

```text
9/2
4.5 4.5
```

`0*0.5 + 5*0.3 + 10*0.1 + 20*0.1 = 4.5` coins per pull, against a 5-coin price: the customer is half a coin behind per pull. With a pile of cards you take the mean; with a table you weight. Same seesaw.

| Question | Answer |
|---|---|
| Most likely prize (the **mode**) | 0, with probability 0.5 |
| Expected value (the **balance point**) | 4.5 |
| Chance a pull pays exactly the expected value | 0 |

**Expected does not mean likely, it means balanced.** The 20-coin card is rare, but it sits far out on the seesaw and drags the balance point up. A fair die has expected value 3.5, and no face says that.

### Variance is the leftover walk

The variance is the probability-weighted average of `(x − 4.5)²`; a shortcut gives the same answer, `E[X²] − (E[X])²`:

```python
EX = sum(x * p for x, p in table.items())
EX2 = sum(x * x * p for x, p in table.items())
var = EX2 - EX**2
print(EX2, var, float(var), float(var) ** 0.5, st.pvariance(tray))
```

```text
115/2 149/4 37.25 6.103277807866851 37.25
```

Variance 37.25 coins², SD about **6.1 coins**: a typical pull misses 4.5 by more than 4.5, a lumpy game. `pvariance` agrees because the ten cards are the whole bag, so it divides by `n`.

### Expect, don't predict

The expected value is a **long-run average**. Simulated pulls (`random.seed(9)`):

```python
import random
random.seed(9)
for n in (10, 1000, 100000):
    xs = random.choices(list(table), weights=[0.5, 0.3, 0.1, 0.1], k=n)
    print(n, "pulls: mean", round(st.fmean(xs), 3), " share of zeros", round(xs.count(0) / n, 3))
```

```text
10 pulls: mean 3.5  share of zeros 0.5
1000 pulls: mean 4.365  share of zeros 0.512
100000 pulls: mean 4.485  share of zeros 0.502
```

Ten pulls are a full coin off; a hundred thousand are nearly 4.5. Why the average settles, and how fast, is [Averages and Intervals](/fields/data-science/probability-statistics/inference/averages-and-intervals.md).

### Shifting, scaling and adding

Every customer pays 5, so the net is `X − 5`; two customers' pulls added are `X + Y` (all 16 card pairs listed):

```python
from itertools import product
def moments(d):
    m = sum(x * p for x, p in d.items())
    return m, sum(x * x * p for x, p in d.items()) - m * m

print(moments({x - 5: p for x, p in table.items()}))
two = {}
for (a, pa), (b, pb) in product(table.items(), repeat=2):
    two[a + b] = two.get(a + b, 0) + pa * pb
print(moments(two))
```

```text
(Fraction(-1, 2), Fraction(149, 4))
(Fraction(9, 1), Fraction(149, 2))
```

```text
E[aX + b]  = a E[X] + b          Var(aX + b) = a^2 Var(X)
E[X + Y]   = E[X] + E[Y]         always
Var(X + Y) = Var X + Var Y       only if X and Y are independent
```

Net expected value is **−1/2** and the variance stays 149/4 (a shifted walk is the same walk). The two-pull total has expected value **9 = 4.5 + 4.5**, and variance 149/2 because the card is put back, so the pulls are independent. Contrast `2X`, one pull paid out twice: variance `4 × 37.25 = 149`.

### Try it: Expected is not likely, edit the bag and see

> **What to try:** Edit the cards in the bag, change the price and pull 10, 1,000 or 100,000 times: the average settles on the expected value, which is not a prize.  
> **Start with:** the preset *The lucky tin*.

[Expected value lab](/fields/data-science/probability-statistics/labs/expected-value.html#embed ':ignore')

### Binomial: count the ways, weigh each way

For **4** customers, each smoky with probability 0.3 independently, write every queue as a yes/no string: `2^4 = 16` strings, each with `k` yeses having probability `0.3^k × 0.7^(4−k)`. Group by `k` (the counting of the previous page):

| Smoky orders `k` | Ways (strings) | Chance of each way | P(X = k) |
|---|---|---|---|
| 0 | 1 | 0.7^4 | 0.2401 |
| 1 | 4 | 0.3 × 0.7^3 | 0.4116 |
| 2 | 6 | 0.3^2 × 0.7^2 | 0.2646 |
| 3 | 4 | 0.3^3 × 0.7 | 0.0756 |
| 4 | 1 | 0.3^4 | 0.0081 |

The whole recipe: **probability of `k` = (ways to place `k` yeses) × (probability of one such way)**. The ways column is a row of Pascal's triangle. For 10 customers there are 1024 strings; the shorthand `comb(10, k) × 0.3^k × 0.7^(10−k)` gave a table identical to the brute-force enumeration:

```python
import math
p, n = F(3, 10), 10
pmf = {k: math.comb(n, k) * p**k * (1 - p)**(n - k) for k in range(n + 1)}
print(sum(pmf.values()))                 # 1
```

| `k` | 0 | 1 | 2 | 3 | 4 | 5 | 6 | 7 | 8 |
|---|---|---|---|---|---|---|---|---|---|
| Ways | 1 | 10 | 45 | 120 | 210 | 252 | 210 | 120 | 45 |
| P(X = k) | 0.0282 | 0.1211 | 0.2335 | 0.2668 | 0.2001 | 0.1029 | 0.0368 | 0.0090 | 0.0014 |

(`k` = 9 and 10 are 0.0001 and below.) "Exactly 3" happens only **26.7%** of the time: Tala's three is the most likely count and still wrong nearly three times in four. Applying the two tools above:

```text
mean     = 3      = n × p
variance = 21/10  = n × p × (1 − p) = 10 × 0.3 × 0.7 = 2.1   (SD about 1.45)
```

Each customer is worth 0.3 of a smoky order on average and averages add; one customer's spread is biggest at p = 0.5 and independent spreads add. NIST gives both results and the catch: **`p` is fixed for all trials.** At least one smoky order is **not** `10 × 0.3 = 300%`: use the complement, `1 − 0.7^10 = 0.9718`. Assumptions: two outcomes, the same `p` every time, customers who do not influence one another.

### Poisson: many tiny chances

Customers arrive at an average of **4 per 10 minutes**. Cut the 10 minutes into `n` slices so thin that at most one person fits in each, chance `4/n` per slice: a binomial with `np = 4` fixed. As the slices thin the table settles:

| `k` | n = 10 | n = 100 | n = 1000 | Poisson, rate 4 |
|---|---|---|---|---|
| 0 | 0.0060 | 0.0169 | 0.0182 | 0.0183 |
| 1 | 0.0403 | 0.0703 | 0.0730 | 0.0733 |
| 2 | 0.1209 | 0.1450 | 0.1464 | 0.1465 |
| 3 | 0.2150 | 0.1973 | 0.1956 | 0.1954 |
| 4 | 0.2508 | 0.1994 | 0.1958 | 0.1954 |
| 5 | 0.2007 | 0.1595 | 0.1566 | 0.1563 |
| 6 | 0.1115 | 0.1052 | 0.1043 | 0.1042 |

```text
P(X = k) = e^(−λ) × λ^k / k!        mean = λ,  variance = λ
```

NIST gives this formula and its mean and variance; the "many tiny chances" link is shown by the numbers above, not proved. Poisson is a binomial with the `n` thrown away: all you need is the rate, and its signature is **variance equals mean**. At rate 4 an empty 10 minutes happens `e^(−4) =` 1.8% of the time, and ten or more customers 0.8%.

### Try it: Pick the recipe, turn the dials

> **What to try:** Pick the binomial or the Poisson, turn the dials, draw a random sample and compare it with the exact bars. Overlay Poisson(np) on a binomial to see when the two agree.  
> **Start with:** the preset *Smoky orders*.

[Distributions lab](/fields/data-science/probability-statistics/labs/distributions.html#embed ':ignore')

### When a recipe lies

Poisson assumes a **constant rate** and **independent arrivals**. Ravi's tally of 12 ten-minute windows: 8 quiet mid-morning windows `1, 2, 2, 3, 1, 2, 1, 3` and 4 lunchtime windows `7, 8, 6, 9`.

```text
mean over 12 windows        = 3.75
variance over 12 windows    = 7.85      (a true Poisson would give about 3.75)
windows with 7 or more      : observed 3, Poisson(3.75) predicts 12 × 0.0863 = 1.04
```

Variance twice the mean is the alarm: the rate was two rates (about 1.9 and 7.5) averaged into a number nobody lived at. The fix is one Poisson per period, not a cleverer formula.

The binomial breaks through dependence. If customers arrive as 5 couples who always order the same, the mean is still 3 but the variance jumps from 2.1 to 4.2, and "exactly 3 smoky" becomes **impossible** because counts come in twos. The formula would still print 26.7%.

> [!NOTE]
> A formula never checks its own assumptions. A distribution fits the world exactly as far as the story fits: independent, same `p`, same rate.

* * *

## The stall, with tables

Tala brings Mira the tables instead of three points.

- **Lucky tin:** 4.5 coins per pull on average against a 5-coin price, an SD of 6.1 per pull. Half a coin of margin per customer, earned the lumpy way. Ravi's big tin is one pull, not evidence.
- **Smoky:** exactly three is 26.7%; five or more is 15%, so to be safe 85% of the time brew five.
- **Walk-ins:** one Poisson for the quiet hours and one for lunch, because a single average hid two shops.

"Do the tables always look this lumpy?" asks Mira. Look back at the 10-customer row: it rises, peaks, falls. Make `n` huge and the lumps smooth into a curve. Next cup: [The Bell Curve](/fields/data-science/probability-statistics/probability/the-bell-curve.md).

* * *

## Never again

| Mistake | Symptom | Fix |
|---|---|---|
| Forecasting the mode or the mean as the answer | "A sticker", "exactly three" | State the table, or the mean **and** the spread |
| Treating E[X] as a possible value | A 4.5-coin prize that no card pays | It is the balance point; it need not be an outcome |
| Adding variances of dependent pulls | `Var(2X)` taken as 2 Var(X) | Variances add only for independent pulls |
| Adding overlapping chances | "10 × 0.3 = 300%" | `1 − (1 − p)^n` |
| One Poisson over two rates | Variance far above the mean | One Poisson per period |
| Binomial on clumped customers | Variance far from `np(1 − p)` | Model the clumps (couples) as the unit |

**Challenge:** ten customers at p = 0.3 give a lopsided table. Using `np` and `np(1 − p)`, guess its shape when `n` is 1000.

* * *

## Check yourself

1. A fair die: write the probability table and the expected value. Is it a possible roll?
2. The lucky tin charges 6 instead of 5. What are the customer's expected net and the new variance?
3. In 1,000 pulls, roughly how many coins of prizes are handed out, and how many pulls pay nothing?
4. Which recipe fits: (a) defective bulbs in a box of 12, (b) emails per hour, (c) heads in 8 flips?
5. What are the mean and variance for 20 customers at p = 0.1? A counter's counts have mean 5 and variance 14: does Poisson fit?

<details>
<summary>Answers</summary>

1. Faces 1 to 6, each 1/6, `E = 3.5`, not a possible roll.
2. `4.5 − 6 =` **−1.5**; the variance stays 37.25 because shifting does not change spread.
3. About `1000 × 4.5 =` **4,500 coins**, and about **500** pulls pay nothing (the simulation gave 512).
4. (a) binomial (12 tries), (b) Poisson (events in a window), (c) binomial (8 flips).
5. Mean `20 × 0.1 = 2`, variance `20 × 0.1 × 0.9 = 1.8`. No: Poisson needs variance close to the mean (5) and 14 is nearly three times that; look for mixed rates or clumped arrivals.

</details>

* * *

## 📜 The Scroll (keep this)

```text
Random variable : a number for each way things could turn out; p's add to 1
E[X]            : sum of x * p (the seesaw); NOT the likeliest value
Var(X)          : sum of (x - E[X])^2 * p = E[X^2] - E[X]^2;  SD = sqrt(Var)
Rules           : E[aX+b] = aE+b; Var(aX+b) = a^2 Var; E adds always; Var adds if independent
Binomial        : n tries, same p, independent. P(k) = comb(n,k) p^k (1-p)^(n-k); np, np(1-p)
Poisson         : events in a window, constant rate. P(k) = e^-lam lam^k / k!; mean = var = lam
Alarm           : variance far from the model's -> mixed rates or clumped, dependent counts
Do not          : add overlapping chances; trust a formula that never checked its assumptions
```

* * *

## References

- OpenStax, *Introductory Statistics 2e*, section 4.2 "Mean or Expected Value and Standard Deviation": the expected value as the long-term average, `mu = sum of x * P(x)`. <https://openstax.org/books/introductory-statistics-2e/pages/4-2-mean-or-expected-value-and-standard-deviation>
- NIST/SEMATECH e-Handbook of Statistical Methods, *Binomial Distribution* (pmf, mean `np`, standard deviation `sqrt(np(1 − p))`, `p` fixed across trials) and *Poisson Distribution* (pmf, mean and variance `λ`). <https://www.itl.nist.gov/div898/handbook/eda/section3/eda366i.htm>, <https://www.itl.nist.gov/div898/handbook/eda/section3/eda366j.htm>
- Python `fractions` (`Fraction` does rational arithmetic exactly), `statistics` (`fmean` with `weights`, `pvariance`) and `math` (`comb`, `exp`). <https://docs.python.org/3/library/fractions.html>, <https://docs.python.org/3/library/statistics.html>, <https://docs.python.org/3/library/math.html>
- Every number was recomputed with Python 3.14.4 (exact fractions, brute-force enumeration of all 16 and 1024 strings, a seeded simulation with `random.seed(9)`); the linearity claims were checked by enumeration for one table, not proved in general.

<!-- related-block -->
<div class="see-also">

**See also**

- [Pick and Compute the Right Probability Model](/fields/data-science/probability-statistics/probability/quick-guide.md) — A cheat sheet for parts 7 to 11 - the method, the code and the expected output for counting outcomes, flipping a test result, expected value, binomial or Poisson, and the normal curve.
- [Probability & Statistics, One Sip at a Time](/fields/data-science/probability-statistics/README.md) — A slow-brewed series on the ideas in probability and statistics that make people say "wait, why?", each one told as a small story in a tea shop.
- [Probability, Technically: Definitions, Identities and Assumptions](/fields/data-science/probability-statistics/probability/technical-reference.md) — The formal layer under parts 7 to 11: axioms, Bayes in odds form, pmf, cdf and density, moment rules, the Poisson limit, the normal approximation and each model's assumptions.

</div>
<!-- related-block -->
<div class="mentioned-in">

**Mentioned in**

- [Counting and Conditioning: Why a 99% Accurate Test Is Usually Wrong](/fields/data-science/probability-statistics/probability/counting-and-conditioning.md) — Probability is a share of the equally likely ways, so "or" adds, "and" multiplies and "at least one" is 1 minus none. Conditioning shrinks the crowd, and Bayes' rule reads that count backwards.
- [Pick and Compute the Right Probability Model](/fields/data-science/probability-statistics/probability/quick-guide.md) — A cheat sheet for parts 7 to 11 - the method, the code and the expected output for counting outcomes, flipping a test result, expected value, binomial or Poisson, and the normal curve.
- [Probability & Statistics, One Sip at a Time](/fields/data-science/probability-statistics/README.md) — A slow-brewed series on the ideas in probability and statistics that make people say "wait, why?", each one told as a small story in a tea shop.
- [Probability, Technically: Definitions, Identities and Assumptions](/fields/data-science/probability-statistics/probability/technical-reference.md) — The formal layer under parts 7 to 11: axioms, Bayes in odds form, pmf, cdf and density, moment rules, the Poisson limit, the normal approximation and each model's assumptions.
- [The Bell Curve: Probability as Area, and One Ruler for Every Bell](/fields/data-science/probability-statistics/probability/the-bell-curve.md) — Many small nudges add up to a bell. For continuous data probability is area, and the z-score makes every bell the same bell, so one table serves all of them, until the data are not a bell.
- [The Map of Leaf & Kettle: Every Idea So Far in One Walk Through the Shop](/fields/data-science/probability-statistics/the-map-of-leaf-and-kettle.md) — A concept map, decision chart and definitions sheet for the whole series, as a memory palace in one tea shop: nine rooms for describing data, an upstairs for chance.

</div>
