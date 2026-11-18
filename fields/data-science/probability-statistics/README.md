
<!-- related-block -->
<nav class="crumbs" aria-label="Breadcrumb"><a href="#/fields/">Fields</a> / <a href="#/fields/data-science/">Data Science</a></nav>

# Probability & Statistics, One Sip at a Time

<!-- related-block -->
<div class="reading-time">Beginner · Guide · 6 min read · Updated 12 Nov 2026</div>
<!-- related-block -->
<div class="tag-chips"><a class="chip" href="#/.docs/generated/explore/tags/statistics">statistics</a></div>


Most people do not struggle with statistics because the formulas are hard. They struggle because the **ideas** arrive before the reason for them. Why divide by `n − 1`? Why does a p-value not mean what it sounds like? Why is a 99% accurate test often wrong?

This series goes the other way. Every page starts with something that **goes wrong** for a small, invented tea shop, and the idea shows up as the fix. The formulas come last, when you already know what they are for.

## Feeling lost? Start here

If the series feels like too many numbers, too many graphs and too many steps, hold on to three ideas. Everything else is built from them.

1. **A summary is a stand-in for a crowd.** Mean, median and mode are not rival formulas. They are one question, *how much should a long walk hurt?*, asked three ways. Spread is how badly the stand-in still misses. ([Part 5](/fields/data-science/probability-statistics/how-far-from-the-middle.md))
2. **Graphs are one table seen three ways.** The histogram shows how much lives where. The ogive shows how many are at or below. The box plot is the ogive keeping only its landmarks. Look first, with the histogram. ([Part 6](/fields/data-science/probability-statistics/where-do-you-stand.md))
3. **A value has no meaning without its crowd.** Ask "better than what?", then place it with a rank (percentile) or a distance (z-score).

Then keep [The Map of Leaf & Kettle](/fields/data-science/probability-statistics/the-map-of-leaf-and-kettle.md) open as a reference. It lays every idea in the series out as rooms of one shop (nine downstairs, nine upstairs for chance), so you recall a room instead of a formula.

## How each page is built

1. **A scene.** Mira, who runs a tea shop called Leaf & Kettle, runs into a problem.
2. **The wrong instinct.** What most of us would do, and why it fails.
3. **One mental model.** The idea that repairs the story.
4. **The mechanics.** Definitions, formulas and worked tables, with numbers you can check by hand.
5. **Check yourself.** A few questions, with answers at the bottom.
6. **Back to the story.** The page returns to the opening scene and resolves it with what you have just learned, usually by handing the next question to the next page.
7. **A cheat sheet** you can read in thirty seconds before you need it.

## The pots on the shelf

| # | Page | The question it answers | Status |
|---|---|---|---|
| 1 | [Stir the Pot First](/fields/data-science/probability-statistics/stir-the-pot-population-and-sampling.md) | Why can a small, well-chosen sample beat a huge careless one? | Written |
| 2 | [Mira's Notebook](/fields/data-science/probability-statistics/data-types-and-frequency-tables.md) | What kind of data is this, and how do I count it honestly? | Written |
| 3 | [Draw It Before You Describe It](/fields/data-science/probability-statistics/draw-it-before-you-describe-it.md) | Which picture answers which question: histogram, polygon or ogive? | Written |
| 4 | [The Number on the Tin](/fields/data-science/probability-statistics/the-number-on-the-tin.md) | What does "typical" mean: mean, median or mode? | Written |
| 5 | [How Far From the Middle?](/fields/data-science/probability-statistics/how-far-from-the-middle.md) | Why are there three middles and so many spreads? Variance, SD, IQR and the mystery of `n − 1` | Written |
| 6 | [Where Do You Stand?](/fields/data-science/probability-statistics/where-do-you-stand.md) | How does one value find its place in a crowd? Percentiles, z-scores and the box plot | Written |
| 7 | [Counting the Ways](/fields/data-science/probability-statistics/counting-the-ways.md) | What is a probability, and why do "or" and "and" add and multiply? | Written |
| 8 | [The Test That Was 99% Accurate](/fields/data-science/probability-statistics/the-test-that-was-99-percent-accurate.md) | Why is an accurate test so often wrong? Conditional probability and Bayes' rule | Written |
| 9 | [What to Expect](/fields/data-science/probability-statistics/what-to-expect.md) | What does "expected" mean? Random variables, expected value and variance | Written |
| 10 | [Coins and Calls](/fields/data-science/probability-statistics/coins-and-calls.md) | Which recipe fits which question? The binomial and Poisson distributions | Written |
| 11 | [The Bell Curve](/fields/data-science/probability-statistics/the-bell-curve.md) | Where does the bell come from, and what is probability as area? The normal distribution | Written |
| 12 | [Why Averages Behave](/fields/data-science/probability-statistics/why-averages-behave.md) | Why does an average wobble less than a single value? Sampling distributions and the central limit theorem | Written |
| 13 | [How Sure Are You?](/fields/data-science/probability-statistics/how-sure-are-you.md) | How do you say "about this, give or take"? Confidence intervals and the bootstrap | Written |
| 14 | [The Courtroom for Numbers](/fields/data-science/probability-statistics/the-courtroom-for-numbers.md) | Could plain luck have done this? Hypothesis tests, p-values and how they get misused | Written |
| 15 | [Two Things Moving Together](/fields/data-science/probability-statistics/two-things-moving-together.md) | Do two columns rise and fall together, and what does that not prove? Correlation and regression | Written |
| Ref | [The Map of Leaf & Kettle](/fields/data-science/probability-statistics/the-map-of-leaf-and-kettle.md) | Every idea so far as a memory palace, a decision chart and a definitions sheet | Grows with the series |

The order is deliberate. Pages 1 to 6 are about **describing what you have**: where the data came from, what kind it is, what it looks like, where its middle is, how spread out it is, and where one value sits within it. Pages 7 to 11 build the language of **chance**: counting the ways, updating on evidence, what to expect, the common distributions and the bell curve. Pages 12 to 14 join the two: using a sample to make an honest statement about something you cannot fully see. Page 15 puts two columns side by side. Each chance page reuses an idea from the first half (the expected value is the mean again, the z-score finally meets the bell), so there is less new to memorize than the list suggests.

## Conventions

- Characters are invented. The numbers in the stories are chosen so you can do the arithmetic yourself.
- Where a story borrows a real event, the sources are listed at the bottom of that page.
- `x̄` is a sample mean, `μ` is a population mean, `n` is a sample size, `N` is a population size, `f` is a frequency and `M` is a class midpoint.
- The same small data sets come back from page to page, so a table you met earlier may turn out to have a surprise in it later.

<!-- related-block -->
<div class="see-also">

**See also**

- [Coins and Calls: Binomial and Poisson as Recipes](/fields/data-science/probability-statistics/coins-and-calls.md) — A named distribution is a recipe for who gets how much probability. Binomial fits "how many yeses in n tries", Poisson fits "how many events in a window". Know the question and the assumptions.
- [Counting the Ways: Probability as a Share of the List](/fields/data-science/probability-statistics/counting-the-ways.md) — Probability is the share of the equally likely ways. So "or" adds, "and" multiplies, and "at least one" is 1 minus none, because of what each does to the list of ways.
- [Draw It Before You Describe It: Three Pictures of the Same Fifty Days](/fields/data-science/probability-statistics/draw-it-before-you-describe-it.md) — Why a table of counts glazes eyes and a picture does not: the histogram, frequency polygon and ogive built from one table, and the mistakes that make them lie.
- [How Far From the Middle? One Question Behind Every Summary Number](/fields/data-science/probability-statistics/how-far-from-the-middle.md) — Mean, median and mode are one question asked with three rulers: how much should a long walk hurt? Spread is what is left over. Variance, SD, IQR and the n-1 mystery fall out of that.
- [How Sure Are You? Confidence Intervals](/fields/data-science/probability-statistics/how-sure-are-you.md) — A confidence interval is an honest "about this, give or take": the estimate plus or minus a margin built from the standard error. The 95% describes the method, not one interval.
- [Mira's Notebook: What Kind of Data Is This, and How Do You Count It?](/fields/data-science/probability-statistics/data-types-and-frequency-tables.md) — Why you cannot average a blend name: the four kinds of data, and how to turn raw numbers into honest category, ungrouped and grouped frequency tables.
- [Stir the Pot First: Population, Sample, and Why We Guess](/fields/data-science/probability-statistics/stir-the-pot-population-and-sampling.md) — Why a sip judges a pot of tea only if you stir it: population versus sample, four ways to draw a sample, the poll that asked 2.4 million and still erred.
- [The Bell Curve: Probability as Area, and One Ruler for Every Bell](/fields/data-science/probability-statistics/the-bell-curve.md) — Many small nudges add up to a bell. For continuous data probability is area, and the z-score makes every bell the same bell, so one table serves all of them, until the data are not a bell.
- [The Courtroom for Numbers: Could Plain Luck Do This?](/fields/data-science/probability-statistics/the-courtroom-for-numbers.md) — A hypothesis test asks one question: could plain luck have produced a difference this big? Shuffle the labels and count. What the p-value is, what it is not, and how testing twenty things fools you.
- [The Map of Leaf & Kettle: Every Idea So Far in One Walk Through the Shop](/fields/data-science/probability-statistics/the-map-of-leaf-and-kettle.md) — A concept map, decision chart and definitions sheet for the whole series, as a memory palace in one tea shop: nine rooms for describing data, an upstairs for chance.
- [The Number on the Tin: Mean, Median and Mode](/fields/data-science/probability-statistics/the-number-on-the-tin.md) — Why a perfectly computed average can describe nobody: "typical" is ambiguous, and mean, median and mode are three honest answers to three different questions. Look at the picture first.
- [The Test That Was 99% Accurate: Conditional Probability and Bayes' Rule](/fields/data-science/probability-statistics/the-test-that-was-99-percent-accurate.md) — Conditional probability is "shrink the crowd to those who match, then count again". Bayes' rule is that count read the other way; a tree of whole tins shows why a 99% test is often wrong.
- [Two Things Moving Together: Correlation and the Line](/fields/data-science/probability-statistics/two-things-moving-together.md) — Correlation is the average product of paired z-scores, a number about straight-line togetherness only. The regression line is least squared walking applied to a line. Graph first, always.
- [What to Expect: Random Variables and Expected Value](/fields/data-science/probability-statistics/what-to-expect.md) — A random variable is a number attached to each way things could turn out. Expected value and variance are the mean and the leftover walk of earlier parts, weighted by probability instead of frequency.
- [Where Do You Stand? Percentiles, Z-Scores and the Box Plot](/fields/data-science/probability-statistics/where-do-you-stand.md) — A score means nothing without its crowd. Two rulers give it a position: rank (percentile) and distance in spreads (z-score). The box plot is just the ogive read at four landmarks.
- [Why Averages Behave: The Sip You Could Take a Thousand Times](/fields/data-science/probability-statistics/why-averages-behave.md) — An average is itself random: every sample gives a different one. Their spread shrinks as sigma over root n, and whatever the crowd looks like, sample averages pile into a bell. Bias is not cured.

</div>
<!-- related-block -->
<div class="mentioned-in">

**Mentioned in**

- [Coins and Calls: Binomial and Poisson as Recipes](/fields/data-science/probability-statistics/coins-and-calls.md) — A named distribution is a recipe for who gets how much probability. Binomial fits "how many yeses in n tries", Poisson fits "how many events in a window". Know the question and the assumptions.
- [Counting the Ways: Probability as a Share of the List](/fields/data-science/probability-statistics/counting-the-ways.md) — Probability is the share of the equally likely ways. So "or" adds, "and" multiplies, and "at least one" is 1 minus none, because of what each does to the list of ways.
- [Draw It Before You Describe It: Three Pictures of the Same Fifty Days](/fields/data-science/probability-statistics/draw-it-before-you-describe-it.md) — Why a table of counts glazes eyes and a picture does not: the histogram, frequency polygon and ogive built from one table, and the mistakes that make them lie.
- [How Far From the Middle? One Question Behind Every Summary Number](/fields/data-science/probability-statistics/how-far-from-the-middle.md) — Mean, median and mode are one question asked with three rulers: how much should a long walk hurt? Spread is what is left over. Variance, SD, IQR and the n-1 mystery fall out of that.
- [How Sure Are You? Confidence Intervals](/fields/data-science/probability-statistics/how-sure-are-you.md) — A confidence interval is an honest "about this, give or take": the estimate plus or minus a margin built from the standard error. The 95% describes the method, not one interval.
- [Mira's Notebook: What Kind of Data Is This, and How Do You Count It?](/fields/data-science/probability-statistics/data-types-and-frequency-tables.md) — Why you cannot average a blend name: the four kinds of data, and how to turn raw numbers into honest category, ungrouped and grouped frequency tables.
- [Stir the Pot First: Population, Sample, and Why We Guess](/fields/data-science/probability-statistics/stir-the-pot-population-and-sampling.md) — Why a sip judges a pot of tea only if you stir it: population versus sample, four ways to draw a sample, the poll that asked 2.4 million and still erred.
- [The Bell Curve: Probability as Area, and One Ruler for Every Bell](/fields/data-science/probability-statistics/the-bell-curve.md) — Many small nudges add up to a bell. For continuous data probability is area, and the z-score makes every bell the same bell, so one table serves all of them, until the data are not a bell.
- and 7 more

</div>
