
# Two Things Moving Together: Correlation and the Line

<!-- related-block -->
<div class="reading-time">11 min read</div>
<!-- related-block -->
<div class="related-strip">

**Read first:** [The Courtroom for Numbers: Could Plain Luck Do This?](/fields/data-science/probability-statistics/the-courtroom-for-numbers.md)  ·  **See also:** [Draw It Before You Describe It: Three Pictures of the Same Fifty Days](/fields/data-science/probability-statistics/draw-it-before-you-describe-it.md), [How Far From the Middle? One Question Behind Every Summary Number](/fields/data-science/probability-statistics/how-far-from-the-middle.md), [Probability & Statistics, One Sip at a Time](/fields/data-science/probability-statistics/README.md), [Where Do You Stand? Percentiles, Z-Scores and the Box Plot](/fields/data-science/probability-statistics/where-do-you-stand.md)

</div>


> **Part 15 of 15.** Part of the [Probability & Statistics](/fields/data-science/probability-statistics/README.md) series. It continues from [The Courtroom for Numbers](/fields/data-science/probability-statistics/the-courtroom-for-numbers.md). By the end you will measure how two columns move together, draw the line through them, and know exactly when to distrust both. There is nothing new to memorize: two ideas you already own are reused. The scenario is invented, and every figure can be checked by hand.

## Table of Contents

- [Prologue: cold days, full cups](#prologue-cold-days-full-cups)
- [Draw it first](#draw-it-first)
- [Idea 1: do the z-scores rise and fall together?](#idea-1-do-the-z-scores-rise-and-fall-together)
- [Idea 2: the line is least squared walking](#idea-2-the-line-is-least-squared-walking)
- [Where it lies: four traps](#where-it-lies-four-traps)
- [Anscombe's quartet: four crowds, one set of numbers](#anscombes-quartet-four-crowds-one-set-of-numbers)
- [Check yourself](#check-yourself)
- [Back to the story](#back-to-the-story)
- [Cheat sheet](#cheat-sheet)
- [The series in three sentences](#the-series-in-three-sentences)
- [Answers](#answers)
- [References](#references)

* * *

## Prologue: cold days, full cups

Ravi has bought tea at Leaf & Kettle for months, and he has a theory. "The colder it is, the more you sell."

Mira shrugs. "Feels true." "Feels," says Ravi, and asks for the till book. Tala copies eight days into two columns: the temperature at opening, and the cups sold that day. (Invented numbers, small enough to check with a pencil.)

| Day | 1 | 2 | 3 | 4 | 5 | 6 | 7 | 8 |
|---|---|---|---|---|---|---|---|---|
| Temperature (°C) | 2 | 4 | 6 | 8 | 10 | 12 | 14 | 16 |
| Cups sold | 58 | 50 | 52 | 42 | 40 | 30 | 28 | 20 |

How do you put a number on "feels true"? And what would the number *not* tell you?

* * *

## Draw it first

Part 3 said it: draw before you describe. For two columns, the picture is a **scatter plot**, one dot per day, temperature across and cups up. Here it is as text, each row a band of 10 cups:

```text
cups
 60 |  *   *
 50 |    *   *
 40 |          *
 30 |            * *
 20 |                *
    +------------------
     0   4   8  12  16  (deg C)
```

The dots slide down as you go right. No clumps, no strays, roughly a line. This is the picture to check the number against, and later you will see why you must.

> ☕ **Try it before you scroll.** A perfectly downhill line should score one extreme, a shapeless cloud the middle. What numbers? *Hint: minus sign for "one rises as the other falls".*

* * *

## Idea 1: do the z-scores rise and fall together?

Temperature is in degrees, cups are in cups. Different units, different spreads. You already own the tool that makes them comparable: the **z-score** from [Where Do You Stand?](/fields/data-science/probability-statistics/where-do-you-stand.md), distance from the middle in typical distances.

Convert every day to two z-scores. Then ask one question: on a day when temperature is above its middle, is cups above or below *its* middle? Multiply the two z-scores of each day:

- both above, or both below: product **positive** (they agree);
- one above, one below: product **negative** (they disagree).

The **correlation coefficient** `r` is the average of those products. That is the whole definition. It lands between **-1** (perfect disagreement along a line) and **+1** (perfect agreement), with about 0 for no straight-line pattern.

Ravi's days (mean temperature 9, mean cups 40, SDs 4.58 and 12.33, the divide-by-`n` SD from part 5):

```text
z temperature: -1.53 -1.09 -0.65 -0.22  0.22  0.65  1.09  1.53
z cups:         1.46  0.81  0.97  0.16  0.00 -0.81 -0.97 -1.62
product:       -2.23 -0.88 -0.64 -0.04  0.00 -0.53 -1.06 -2.48
```

Every product is zero or negative. Their average is **-0.982**: nearly perfect disagreement. Python's `statistics.correlation` should say the same, and it does:

```python
import statistics as st

temp = [2, 4, 6, 8, 10, 12, 14, 16]          # degrees C at opening time
cups = [58, 50, 52, 42, 40, 30, 28, 20]      # cups sold that day

mt, mc = st.mean(temp), st.mean(cups)        # 9 and 40
sdt, sdc = st.pstdev(temp), st.pstdev(cups)  # the SD that divides by n, as in part 5
zt = [(x - mt) / sdt for x in temp]          # part 6: each day's z-score for temperature
zc = [(y - mc) / sdc for y in cups]          # and for cups
r = sum(a * b for a, b in zip(zt, zc)) / len(temp)   # average product of paired z-scores
print(round(r, 4), round(st.correlation(temp, cups), 4))
```

```text
-0.9823 -0.9823
```

Two honest notes: `r` says nothing about *how steep* the pattern is, only how tightly dots hug a **straight** line; and `statistics.correlation` (Python 3.10+) returns Pearson's `r`, while 3.12 added `method='ranked'` (Spearman, for any always-rising or always-falling pattern).

So `r = -0.98`. But Ravi wants to *predict*: how many cups tomorrow at 5 degrees?

* * *

## Idea 2: the line is least squared walking

You have met this problem in disguise. In [How Far From the Middle?](/fields/data-science/probability-statistics/how-far-from-the-middle.md), the mean was the spot that leaves the smallest total **squared** walk to the crowd. Now the crowd is eight dots and the thing we place is a **line**. The walk of each dot is the vertical gap between it and the line, called its **residual** (what is left over after the line has said its piece). The same rule applies: the line that leaves the smallest total squared residual wins. That is **least squares**, and it is the whole idea of regression.

```python
fit = st.linear_regression(temp, cups)
print(round(fit.slope, 3), round(fit.intercept, 2))
miss = [y - (fit.slope * x + fit.intercept) for x, y in zip(temp, cups)]
print([round(m, 2) for m in miss], round(sum(miss), 6), round(sum(m * m for m in miss), 2))
print(round(sum((y - mc) ** 2 for y in cups), 2))   # the miss if you ignore temperature
print(round(fit.slope * 5 + fit.intercept, 1), round(fit.slope * 40 + fit.intercept, 1))
```

```text
-2.643 63.79
[-0.5, -3.21, 4.07, -0.64, 2.64, -2.07, 1.21, -1.5] 0.0 42.57
1216.0
50.6 -41.9
```

Read each number in plain units:

| Number | Value | Meaning |
|---|---|---|
| Slope | -2.643 | Each extra degree goes with about **2.6 fewer cups** |
| Intercept | 63.79 | The line's height at 0 °C (a point on the line, not a promise) |
| Residuals | -0.5, -3.21, 4.07, ... | The leftover per day: actual minus the line. They add up to 0, the seesaw again |
| Squared miss | 42.57 | Left after the line, against 1216 if you guess the mean, 40, every day |

The line removed 96.5% of the total squared miss (1 - 42.57/1216), and that fraction equals `r²` (0.9823² = 0.965). The two ideas are one fact seen twice. They are tied by a formula too: `slope = r × (SD of cups) / (SD of temperature)`, which gives -0.9823 × 12.33 / 4.58 = -2.643.

The candidates `64 - 2.5x` and `67 - 3x` both miss by exactly 64.0, worse than 42.57.

At 5 degrees the line predicts **50.6 cups**. Sensible, since 5 degrees is inside the temperatures Tala wrote down. At 40 degrees it predicts **-41.9 cups**. A shop does not sell negative tea.

At 40 degrees a shop sells negative tea. Is `r = -0.98` any safer?

* * *

## Where it lies: four traps

Each trap below is a case where the numbers say one thing and the truth is another.

**1. Prediction outside the data.** The line was fitted on 2 to 16 degrees. At 40 it falls apart, as you just saw. A line describes the range it has seen; past that edge it is a guess in a confident voice.

**2. Correlation is not causation.** Two columns can move together because a *third* thing drives both. Simulated, seed 7: 200 days, each with a hidden amount of sun; iced-tea cups follow the sun, and so do sunburns. Neither follows the other.

```python
import random

random.seed(7)
sun = [random.gauss(0, 1) for _ in range(200)]             # hidden cause: hours of sun, standardised
iced = [s + random.gauss(0, 0.5) for s in sun]             # iced-tea cups follow the sun
burn = [s + random.gauss(0, 0.5) for s in sun]             # sunburns follow the sun; neither follows the other
print(round(st.correlation(iced, burn), 3))
same = [(i, b) for s, i, b in zip(sun, iced, burn) if abs(s) < 0.3]   # only days with about the same sun
print(len(same), round(st.correlation([i for i, b in same], [b for i, b in same]), 3))
```

```text
0.795
45 -0.075
```

Across all days, iced tea and sunburn correlate at **0.795**. Look only at days with about the same sun (45 of them) and it collapses to **-0.075**. Banning iced tea would not cure a single sunburn. The way to see this is to hold the third thing still, and when you cannot, `r` alone cannot tell you the direction of cause.

**3. A curve hides from `r`.** Take `y = x²` for x from -5 to 5: a perfect, noiseless pattern. `statistics.correlation` returns **0.0**. The left half falls, the right half rises, and the products cancel. `r` measures straight-line togetherness only.

**4. One outlier can move `r` a lot.** Add a ninth day to Ravi's book: a 30-degree heatwave festival, 60 cups.

```python
print(round(st.correlation(temp + [30], cups + [60]), 3))  # one heatwave festival day added
```

```text
-0.075
```

One day moved `r` from -0.982 to **-0.075**. (The same digits as the sunburn result by coincidence; it is a different data set.) Just as one far house wrecked the mean on Kettle Street, one far dot wrecks `r`, because z-scores are built from the mean and SD.

All four traps share a cure, and it is the one [Part 3](/fields/data-science/probability-statistics/draw-it-before-you-describe-it.md) gave you.

* * *

## Anscombe's quartet: four crowds, one set of numbers

In 1973 the statistician Francis Anscombe built four small data sets, 11 points each, to make exactly this point. The data is copied from the table in his paper (checked value by value against the JSTOR scan), and every summary below was recomputed in Python. Sets I to III share the same x values.

```python
x123 = [10, 8, 13, 9, 11, 14, 6, 4, 12, 7, 5]
sets = {
    "I":   (x123, [8.04, 6.95, 7.58, 8.81, 8.33, 9.96, 7.24, 4.26, 10.84, 4.82, 5.68]),
    "II":  (x123, [9.14, 8.14, 8.74, 8.77, 9.26, 8.10, 6.13, 3.10, 9.13, 7.26, 4.74]),
    "III": (x123, [7.46, 6.77, 12.74, 7.11, 7.81, 8.84, 6.08, 5.39, 8.15, 6.42, 5.73]),
    "IV":  ([8] * 7 + [19] + [8] * 3,
            [6.58, 5.76, 7.71, 8.84, 8.47, 7.04, 5.25, 12.50, 5.56, 7.91, 6.89]),
}
for name, (xs, ys) in sets.items():
    f = st.linear_regression(xs, ys)
    print(name, st.mean(xs), st.variance(xs), round(st.mean(ys), 2), round(st.variance(ys), 2),
          round(st.correlation(xs, ys), 3), round(f.intercept, 2), round(f.slope, 3))
```

```text
I 9 11 7.5 4.13 0.816 3.0 0.5
II 9 11 7.5 4.13 0.816 3.0 0.5
III 9 11 7.5 4.12 0.816 3.0 0.5
IV 9 11 7.5 4.12 0.817 3.0 0.5
```

Columns: mean of x, variance of x, mean of y, variance of y, `r`, intercept, slope. **Same mean, same spread, same `r` (0.816), same line `y = 3 + 0.5x`**, in all four. Now draw them (y rounded to whole units, one `*` per point, overlaps hidden):

```text
 I: a plain cloud         II: a smooth curve       III: a line plus one stray   IV: a stack plus one lever
11|         *             9|      *****             13|          *                12|                *
10|           *           8|     *     *             9|           *               9|     *
 9|      *                7|    *                    8|        **                 8|     *
 8|       ** *            6|   *                     7|     ***                   7|     *
 7|   * *                 5|  *                      6|  ***                      6|     *
 6|  *                    3| *                        5| *                         5|     *
 5|    *                                                                          
 4| *                                                                              
```

Set I is honest. II is a curve (trap 3). III is a line with one stray dot (trap 4). IV has ten dots at the same x and **one** far dot that alone creates the slope. Four crowds, one stand-in.

> [!NOTE]
> `r`, the slope and the line are all summaries. Like every summary in this series they throw information away. The picture is what gets it back: **graph first, number second.**

* * *

## Check yourself

1. Four days have z-scores for (temperature, cups) of (1, -1), (-1, 1), (0.5, -0.5), (-0.5, 0.5). What is `r`?
2. A fitted line is `cups = 64 - 2.5 × temp`. Predict cups at 10 degrees, and say what the slope means in words.
3. Towns with more fire engines at a fire have more fire damage (`r = 0.8`). Does sending fewer engines reduce damage? Name the hidden third thing.
4. Why is predicting at 40 degrees from data covering 2 to 16 a bad idea, even with `r = -0.98`?
5. Which one picture would have shown you that Anscombe's four sets differ?

* * *

## Back to the story

Ravi studies the scatter plot and the number. "So I was right. Cold days, more tea."

"On these eight days, in this range," says Mira. "Not a law, not a cause, and not at 40 degrees. But I would rather act on a picture and a number than on a feeling, and on a picture rather than a number."

**Takeaway:** correlation is the average product of paired z-scores, the line is least squared walking, and both describe a straight-line pattern in the range you saw, nothing more. Graph first.

* * *

## Cheat sheet

```text
r = average of (z of x) x (z of y)        -1 .. +1, straight-line togetherness only
LINE = the one with the smallest total squared residual (least squares)
slope = r x SD(y) / SD(x)       r squared = share of the squared miss the line removes
residual = actual - line         they add up to 0

NOT causation (look for a hidden third).  NOT curves (r = 0 can hide a perfect one).
ONE OUTLIER can swing r.   NO PREDICTION beyond the range of x you saw.
ALWAYS DRAW THE SCATTER FIRST: Anscombe's four sets share every summary.
```

* * *

## The series in three sentences

You made it to the last cup. The whole series was three ideas, retold in different costumes:

- A **summary is a stand-in for a crowd**: the mean, the spread, `r` and the slope each throw something away, so know the crowd.
- **Graphs are one table seen several ways**: histogram, ogive, box plot and scatter plot show the same numbers from different angles, and the picture always comes first.
- **A value needs its crowd**: a score, a test result, a correlation means nothing until you ask "compared to what?"

**Closing challenge.** Find two columns in your own life, steps and mood, spending and the weather, anything you can write down for ten days. Draw the scatter plot, compute `r`, and then try to break your own conclusion with the four traps above. If it survives, you have earned a claim. If not, you have learned something better.

Everything in one place: [The Map of Leaf & Kettle](/fields/data-science/probability-statistics/the-map-of-leaf-and-kettle.md), or back to the start of the series at the [series index](/fields/data-science/probability-statistics/README.md).

* * *

## Answers

1. Products: -1, -1, -0.25, -0.25. Sum -2.5, over 4 days: `r =` **-0.625**.
2. `64 - 2.5 × 10 =` **39 cups**. Each extra degree goes with 2.5 fewer cups sold, inside the range of temperatures the line was fitted on.
3. No. Both follow the **size of the fire**: bigger fires bring more engines and more damage. Hold the fire size still and the link largely disappears.
4. 40 degrees is far outside 2 to 16. The line is only evidence about the range seen, and there it predicts **-41.9 cups**, which is impossible.
5. The **scatter plot** of each set. The summary numbers are identical.

* * *

## References

- Python `statistics` module: `correlation` (added in 3.10; `method='ranked'` added in 3.12) and `linear_regression` (added in 3.10; `proportional` added in 3.11). All code on this page ran on Python 3.14.4, stdlib only. <https://docs.python.org/3/library/statistics.html>
- Anscombe, F. J. (1973), *Graphs in Statistical Analysis*, The American Statistician 27(1): 17-21. <https://doi.org/10.1080/00031305.1973.10478966>. The paper's table gives the four data sets and states the shared summaries (mean of x 9.0, mean of y 7.5, regression line y = 3 + 0.5x, multiple R² 0.667, so r = 0.816). The data on this page match that table value by value, and the summaries were recomputed above.
- The Ravi tea table and the simulated sun/iced-tea/sunburn data are invented for this page (fixed seed 7).
- Every other number on this page was recomputed with Python 3.14.4.
