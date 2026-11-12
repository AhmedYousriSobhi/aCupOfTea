---
id: draw-it-before-you-describe-it
title: "Draw It Before You Describe It: Three Pictures of the Same Fifty Days"
sidebar_label: Draw it first
summary: 'Why a table of counts glazes eyes and a picture does not: the histogram, frequency polygon and ogive built from one table, and the mistakes that make them lie.'
level: beginner
type: concept
domains:
  - statistics
tags:
  - statistics
relations:
  related:
    - probability-statistics-series
    - data-types-and-frequency-tables
    - the-number-on-the-tin
---

# Draw It Before You Describe It: Three Pictures of the Same Fifty Days

> **Part of the [Probability & Statistics](https://github.com/AhmedYousriSobhi/aCupOfTea/blob/main/fields/data-science/probability-statistics/README.md) series.** It builds on the grouped tables from [Mira's Notebook](https://github.com/AhmedYousriSobhi/aCupOfTea/blob/main/fields/data-science/probability-statistics/data-types-and-frequency-tables.md). The shop, the people and the counts are invented, and every number can be checked by hand.

## Table of Contents

- [Prologue: Ravi's blank stare](#prologue-ravis-blank-stare)
- [The table behind the pictures](#the-table-behind-the-pictures)
- [Picture 1: the histogram](#picture-1-the-histogram)
- [Picture 2: the frequency polygon](#picture-2-the-frequency-polygon)
- [Picture 3: the ogive](#picture-3-the-ogive)
- [Which picture for which question](#which-picture-for-which-question)
- [Ways these pictures lie](#ways-these-pictures-lie)
- [Check yourself](#check-yourself)
- [Back to the story](#back-to-the-story)
- [Cheat sheet](#cheat-sheet)
- [Answers](#answers)

* * *

## Prologue: Ravi's blank stare

Mira has counted the customers who came into Leaf & Kettle on each of the last 50 days, and grouped the counts into classes. She slides the table across the counter to her business partner Ravi, who is deciding how many baristas to schedule.

| Customers per day | Days |
|---|---|
| 100 to 104 | 2 |
| 105 to 109 | 8 |
| 110 to 114 | 18 |
| 115 to 119 | 13 |
| 120 to 124 | 7 |
| 125 to 129 | 1 |
| 130 to 134 | 1 |

Ravi reads the table. He reads it again. Then he looks up and says, "So... is that a lot?"

The table is correct, and it is useless to him. It holds every number he needs, and it makes him do the work of seeing the shape himself. A person looking at seven rows of numbers cannot easily feel where the bulk of the days sits, or how lopsided the tail is.

So Mira picks up a pen, turns the napkin over, and draws.

* * *

## The table behind the pictures

All three pictures come from one table. Because the counts are whole numbers, the class boundaries sit half a unit beyond the limits, as described in the previous page.

| Class boundaries | Frequency `f` | Midpoint `M` | Relative frequency | Cumulative frequency `CF` |
|---|---|---|---|---|
| 99.5 to 104.5 | 2 | 102 | 0.04 | 2 |
| 104.5 to 109.5 | 8 | 107 | 0.16 | 10 |
| 109.5 to 114.5 | 18 | 112 | 0.36 | 28 |
| 114.5 to 119.5 | 13 | 117 | 0.26 | 41 |
| 119.5 to 124.5 | 7 | 122 | 0.14 | 48 |
| 124.5 to 129.5 | 1 | 127 | 0.02 | 49 |
| 129.5 to 134.5 | 1 | 132 | 0.02 | 50 |
| **Total** | **50** | | **1.00** | |

Two new columns appear. The **midpoint** is the middle of the class, `(lower boundary + upper boundary) / 2`, so the first class gives `(99.5 + 104.5) / 2 = 102`. The **cumulative frequency** is the running total of the frequencies. Both checks from before still apply: the frequencies add to `n = 50`, and the last cumulative value equals `n`.

Each picture uses a different pair of columns:

| Picture | Plots | Uses |
|---|---|---|
| Histogram | frequency against **class boundaries** | `f` |
| Frequency polygon | frequency against **midpoints** | `M` and `f` |
| Ogive | cumulative frequency against **upper boundaries** | `CF` |

* * *

## Picture 1: the histogram

Mira draws one bar for each class. The bar stands on the **class boundaries**, from 99.5 to 104.5, from 104.5 to 109.5, and so on, and its height is the frequency. Sideways, in text, it looks like this:

```
 99.5 - 104.5 | ██ 2
104.5 - 109.5 | ████████ 8
109.5 - 114.5 | ██████████████████ 18
114.5 - 119.5 | █████████████ 13
119.5 - 124.5 | ███████ 7
124.5 - 129.5 | █ 1
129.5 - 134.5 | █ 1
```

Ravi's eyebrows go up on the first glance. The days pile up in the 110s and thin out gently on the left and more slowly on the right, with a thin tail of busy days stretching toward 134. He has seen the shape of the fifty days without reading a single number.

The rules for a histogram:

- **The bars touch.** The data are measurements on a continuous scale, and the classes touch because the boundaries are shared. A gap between bars would suggest a range of values that cannot occur. A bar chart of favorite blends is different: the categories are separate things, so those bars have gaps.
- **The axis shows boundaries, not limits.** If you label the bars with limits (100 to 104, 105 to 109), a reader sees a hole between 104 and 105 that does not exist.
- **Equal widths let height mean frequency.** Here every class is 5 wide, so a taller bar means more days. If you ever draw classes of different widths, height alone misleads. The usual fix is to plot frequency divided by class width, so that the **area** of each bar represents the count.

* * *

## Picture 2: the frequency polygon

On a second napkin, Mira puts a dot above the **midpoint** of each class, at the height of its frequency, then joins the dots with straight lines.

| Midpoint | 102 | 107 | 112 | 117 | 122 | 127 | 132 |
|---|---|---|---|---|---|---|---|
| Frequency | 2 | 8 | 18 | 13 | 7 | 1 | 1 |

The dots rise to a peak at 112, fall away to 122, and then crawl along the bottom. A polygon should be a **closed** shape, so the line goes back down to the axis at each end. There are two common conventions for the end points:

- Add an empty class on each side, with midpoints 97 and 137 and frequency 0, and run the line down to those.
- Bring the line down at the outer boundaries, 99.5 and 134.5.

Either is fine as long as you say which one you used.

The polygon holds the same information as the histogram, so why bother? Because **lines overlay better than bars**. If Ravi wants to compare this summer with last summer, two histograms side by side are hard to compare. Two polygons drawn on the same axes show at a glance whether this year's peak sits to the left, to the right, or higher.

* * *

## Picture 3: the ogive

The third picture answers a different kind of question. Ravi asks, "On how many days did we have 114 or fewer customers?" The histogram makes him add bars in his head. The **cumulative frequency curve**, or **ogive** (pronounced "OH-jive"), does the adding in advance.

Each point is an **upper class boundary** paired with the cumulative frequency up to it. The first point is the lower edge of the first class, where nothing has happened yet.

| Boundary (x) | Cumulative frequency (y) |
|---|---|
| 99.5 | 0 |
| 104.5 | 2 |
| 109.5 | 10 |
| 114.5 | 28 |
| 119.5 | 41 |
| 124.5 | 48 |
| 129.5 | 49 |
| 134.5 | 50 |

Join them with straight lines. The curve starts at 0, **never goes down**, and ends at `n = 50`. Its steepest stretch is where the data are thickest, which here is between 109.5 and 114.5.

Why the **upper** boundary? Because the cumulative count at 114.5 means "this many days had values **up to** 114.5", and that only becomes true at the top of the class. Plot it at the midpoint or the lower boundary and the count claims days that have not yet happened.

**How to read it:**

- *From x to y:* find a value on the horizontal axis, go up to the curve, then across to read how many days were at or below it.
- *From y to x:* pick a count on the vertical axis, go across to the curve, then down to read the value.

The first direction answers Ravi. Because the counts are whole numbers, "114 or fewer" reaches exactly the boundary 114.5, and the curve reads **28 days**, which is `28 / 50 = 56%` of the days.

The second direction finds the middle of the data. Half of 50 is 25, so go across at height 25 and drop down. The curve at height 25 sits on the straight stretch between (109.5, 10) and (114.5, 28), so

```
x = 109.5 + (25 − 10) / (28 − 10) × 5 = 109.5 + 0.833 × 5 ≈ 113.7
```

Half the days had about 113.7 customers or fewer. This is the **median**, and the next page shows that the formula for it is exactly this ruler-reading in disguise.

A note on the straight lines. Joining boundary points with straight lines quietly assumes the days are spread **evenly** within each class. The curve is an estimate between the boundary points. It is exact at the boundaries and an approximation in between.

The same ogive gives **percentiles**, the idea that "a value is above X% of the data". The point (114.5, 28) says that 114.5 sits above 56% of the days. A later page builds on this.

* * *

## Which picture for which question

| The question | The picture |
|---|---|
| What does the distribution look like? Where is the bulk, and is there a long tail? | **Histogram** |
| How does this data set compare with another one? | **Frequency polygon**, overlaid |
| How many values are at or below this number, or what share? | **Ogive** |
| What value splits the data in half, or marks the lowest 25%? | **Ogive**, read from y to x |

* * *

## Ways these pictures lie

| Trap | What goes wrong | The fix |
|---|---|---|
| Gaps between histogram bars | Suggests impossible values in between | Let bars touch, use boundaries |
| Axis labelled with limits | A phantom gap between classes | Label with boundaries |
| Ogive plotted at midpoints or lower boundaries | Counts values that have not yet been reached | Plot at **upper boundaries** |
| Polygon left open at the ends | Does not return to zero, so the area is unclear | Close it with empty classes or at the outer boundaries |
| Unequal class widths with plain frequency as height | The wider class looks bigger than it is | Plot frequency density, so area shows the count |
| Reading an ogive between points as exact | The straight lines assume an even spread inside each class | Treat in-between readings as estimates |

* * *

## Check yourself

Use the table of 50 days above.

1. On how many days were there 119 customers or fewer, and what share is that?
2. Which two numbers make the first ogive point after (99.5, 0)?
3. You want to compare this summer's days with last summer's on one chart. Which picture, and why?
4. A bar chart of favorite blends has gaps between its bars, but a histogram of daily customers does not. Why?
5. Estimate the value below which the lowest 25% of days fall.

* * *

## Back to the story

Ravi holds the napkin up to the light.

"The tallest bar is the 110s," he says. "That's my normal day."

"Right," says Mira. "Eighteen of the fifty days."

"And I can plan for 114 or fewer on over half of them," he says, tracing the third drawing with his finger. "Twenty-eight days, you said. So the other twenty-two are busier than that." He frowns. "How many of those are the really busy ones, over 119?"

Mira reads it off the curve: 41 days at or below 119, so **9 days**, a bit under one day in five.

Ravi nods slowly. Ten minutes earlier he could not tell whether the numbers were large. Now he is asking his own questions, which is what a good picture is for: it gets the reader to the *next* question.

"Okay," he says, putting down the napkin. "Two baristas on ordinary days, a third on call for the busy ones. But what's the *typical* day, exactly? One number."

That is a harder question than it sounds, and it is the next cup.

* * *

## Cheat sheet

```
Midpoint M = (lower boundary + upper boundary) / 2

Histogram          : bars on class BOUNDARIES, height = f, bars touch
Frequency polygon  : dots at (midpoint, f), joined, closed at both ends; good for overlays
Ogive (CF curve)   : points at (UPPER boundary, CF), start at (lowest boundary, 0), ends at n
  read x -> y : how many values are at or below x
  read y -> x : the value below which y values fall (median at y = n/2)

Unequal class widths -> plot frequency density (area = count)
Lines between points assume values are spread evenly inside each class
```

* * *

## Answers

1. The cumulative frequency at the boundary 119.5 is **41**, so 41 days, which is `41 / 50 = 82%`.
2. The upper boundary **104.5** and its cumulative frequency **2**.
3. The **frequency polygon**. Lines for the two summers can share one set of axes, and the eye compares peaks and shifts easily. Two sets of bars would overlap and hide each other.
4. Blends are separate **categories**, so their bars are separate. Daily customers are measured on a continuous scale where the classes share boundaries, so the bars touch.
5. 25% of 50 is 12.5. That height lies between (109.5, 10) and (114.5, 28), so `x = 109.5 + (12.5 − 10) / 18 × 5 = 109.5 + 0.694 ≈ 110.2`. About a quarter of the days had roughly 110 customers or fewer.
