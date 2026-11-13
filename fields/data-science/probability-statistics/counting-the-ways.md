
# Counting the Ways: Probability as a Share of the List

<!-- related-block -->
<div class="reading-time">9 min read</div>
<!-- related-block -->
<div class="related-strip">

**Read first:** [Where Do You Stand? Percentiles, Z-Scores and the Box Plot](/fields/data-science/probability-statistics/where-do-you-stand.md)  ·  **See also:** [Coins and Calls: Binomial and Poisson as Recipes](/fields/data-science/probability-statistics/coins-and-calls.md), [Probability & Statistics, One Sip at a Time](/fields/data-science/probability-statistics/README.md)  ·  **Read next:** [The Test That Was 99% Accurate: Conditional Probability and Bayes' Rule](/fields/data-science/probability-statistics/the-test-that-was-99-percent-accurate.md)

</div>


> **Part 7 of 15.** Part of the [Probability & Statistics](/fields/data-science/probability-statistics/README.md) series. Parts 1 to 6 described data you **have**; from here on, chance. By the end you will see that most probability problems are counting problems in disguise, and that "or" adds and "and" multiplies because of what they do to a list. The scenario is invented, and every count was checked by listing the ways in Python.

## Table of Contents

- [Prologue: the lucky roll](#prologue-the-lucky-roll)
- [The list of ways](#the-list-of-ways)
- [Or adds, unless the ways overlap](#or-adds-unless-the-ways-overlap)
- [At least one: count the none](#at-least-one-count-the-none)
- [And multiplies, when the dice do not talk](#and-multiplies-when-the-dice-do-not-talk)
- [Counting without writing it all out](#counting-without-writing-it-all-out)
- [Back to the story](#back-to-the-story)
- [Check yourself](#check-yourself)
- [Cheat sheet](#cheat-sheet)
- [Answers](#answers)
- [References](#references)

* * *

## Prologue: the lucky roll

Mira puts two dice and a sign by the till: **"Roll a double, or a total of 8, and the biscuit is free."**

Ravi studies the sign like a man reading a contract. "A double is one in six. A total of 8 is five in thirty-six. So that's 6/36 plus 5/36, eleven in thirty-six. You'll go broke."

"Roll," says Mira.

Ravi rolls 4 and 4. A double, **and** a total of 8, in one throw. He cheers, then frowns: "Did that count twice?"

It did not, and that frown is the whole page. (Invented promotion; the counts below are exact.)

* * *

## The list of ways

Last pages gave you a crowd of **what happened**. Chance needs a crowd of **what could happen**, and you write it down before you do anything else.

- The **sample space** is the list of all possible outcomes.
- An **event** is any combination of outcomes: "a double", "total of 8".
- If every outcome is equally likely, the probability of an event is its share of the list:

```text
P(event) = (ways the event can happen) / (all ways)
```

OpenStax defines the sample space and event in exactly these words and gives this counting rule for equally likely outcomes. Two dice have 6 × 6 = **36** outcomes, and the picture is a grid, first die down the side, second across the top. Cells marked `D` are doubles, `8` are total-8, and `X` is both:

```text
         second die
          1  2  3  4  5  6
first  1  D  .  .  .  .  .
die    2  .  D  .  .  .  8
       3  .  .  D  .  8  .
       4  .  .  .  X  .  .
       5  .  .  8  .  D  .
       6  .  8  .  .  .  D
```

*The whole sample space. Probability is how many cells you shade, out of 36.*

Notice the link to part 2. A relative frequency is **what happened** divided by the number of throws; this is **what could happen** divided by the number of cells. They are twins: roll often enough and the first drifts toward the second.

> ☕ **Try it before you scroll.** Count the cells marked `D` or `8` on the grid. Is it 11?

* * *

## Or adds, unless the ways overlap

Count the shaded cells: 6 doubles, 5 eights, and the cell `X` is in **both** groups. Ravi added the two lists and counted `X` twice. The honest count is 6 + 5 − 1 = **10**, so the chance is 10/36, about 28%.

```text
P(A or B) = P(A) + P(B) − P(A and B)
```

When two events cannot happen together (a roll cannot be both 3 and 5 in one die), the overlap is empty and "or" is plain addition. The subtraction only repairs the double counting.

The failure is easy to repeat, so here is the sharper version. Chance of **at least one six** in two rolls? "One in six, twice, so 1/6 + 1/6 = 12/36." The grid says **11/36**, because (6, 6) is counted twice. Adding probabilities is adding lists, and you must not let one outcome sit on the list twice.

Now to a faster way to get 11. Why count cells that contain a six when it is easier to count the ones that do not?

* * *

## At least one: count the none

"At least one" hides a long list: a six on the first die, or the second, or both. The **complement**, no six at all, is one clean rectangle: 5 values for each die, 5 × 5 = 25 cells.

```text
P(not A) = 1 − P(A)          at least one six = 1 − 25/36 = 11/36
```

The sample space is split in two with nothing left over: the cells where it happens and the cells where it does not. So whenever the question says "at least one", flip it: **count the none, then subtract from the whole.** Ravi, take note: this is how a shop works out the chance that at least one order in a busy morning goes wrong.

* * *

## And multiplies, when the dice do not talk

"And" asks for the cells where both events hold. Take "first die is even" (3 rows of 6 = 18 cells) and "second die is 5 or 6" (6 rows of 2 columns = 12 cells). Where both hold, you get a block of 3 rows by 2 columns: **6 cells**.

```text
18/36 × 12/36 = 6/36            the block is exactly the product
```

That is **independence**, in plain words: knowing one tells you nothing about the other. Knowing the first die is even does not change the share of the second die that is 5 or 6; it is still 2 of 6. The grid shows it as a clean rectangle, and an area is a product.

Now an event that does talk. Let A be "first die is a 6" (6 cells) and S "total is at least 10" (6 cells: 4+6, 5+5, 5+6, 6+4, 6+5, 6+6). Both hold in 3 cells, not 6/36 × 6/36 = 1 cell. If the first die is a 6, you are much closer to 10, so the events are **not** independent, and multiplying would have been wrong.

```text
Independent:  P(A and B) = P(A) × P(B)      the shaded cells form a rectangle
Not so:       count the overlap directly
```

The same idea kills the gambler's fallacy. After three sixes in a row, surely a six is "due"? Write down all 6⁴ = 1296 four-roll sequences. Exactly 6 start with three sixes, and in only 1 of those 6 is the fourth roll a six: **1/6**, same as always. The dice have no memory, so the list does not shrink.

* * *

## Counting without writing it all out

Mira's second deal: **"Pick two free samples from six blends."** How many different picks are there?

If order matters (first pick, second pick), you have 6 choices, then 5 left: 6 × 5 = **30**. If only the pair matters, each pair was counted twice (A then B, B then A), so 30 / 2 = **15**. Python has both as functions, and `itertools` lists them so you can see:

```python
import itertools, math

grid = list(itertools.product(range(1, 7), repeat=2))   # every (first, second) pair
print(len(grid))                                         # the whole list of ways

double = {g for g in grid if g[0] == g[1]}
eight  = {g for g in grid if sum(g) == 8}
print(len(double), len(eight), len(double & eight))      # the overlap is one cell
print(len(double | eight))                               # the honest count of "or"

no_six = [g for g in grid if 6 not in g]
print(len(grid) - len(no_six))                           # "at least one six": 1 minus none

blends = range(6)
print(len(list(itertools.permutations(blends, 2))), math.perm(6, 2))
print(len(list(itertools.combinations(blends, 2))), math.comb(6, 2))
```

Output, as printed by Python 3.14.4:

```text
36
6 5 1
10
11
30 30
15 15
```

Mira keeps two blends secret. Ravi picks a pair at random. Chance he gets **both**? 1 pair in 15. Chance he gets **at least one**? Count the none: pairs from the 4 other blends, `math.comb(4, 2) = 6`, so 1 − 6/15 = **9/15 = 60%**. (Listing all 15 pairs confirms 1, 9 and 6.)

Only count this way when each pick is equally likely; if some outcomes are likelier than others, a share of the list is not a probability.

* * *

## Back to the story

Mira writes the real odds on the sign: 10 in 36, a free biscuit about once in 3.6 rolls. Ravi's 11/36 was wrong by one cell, and it was wrong in the direction that sounds scarier than it is.

"I added two lists with a shared name on them," he admits.

"Everyone does. Now go sit down," says Mira. "You rolled a double *and* an eight, and you still owe me for the tea."

**Takeaway:** probability is the share of equally likely ways. "Or" adds lists (minus the overlap), "and" multiplies when the events ignore each other, and "at least one" is easiest as 1 minus none.

**Challenge for next cup.** A rare thing affects 1 person in 1000. A test catches it 99% of the time, and wrongly flags 1% of healthy people. Ravi tests positive. Grid or no grid, write the list of 100,000 people and count who is flagged. Is he 99% likely to have it? Find out in [The Test That Was 99 Percent Accurate](/fields/data-science/probability-statistics/the-test-that-was-99-percent-accurate.md).

* * *

## Check yourself

1. Two dice: chance the total is 7? Count the cells.
2. Two dice: chance of **at least one** even number? Use the complement.
3. Why is P(A or B) = P(A) + P(B) wrong for "double" and "total of 8"? What is the fixed version?
4. Flip a fair coin four times, getting heads each time. What is the chance the fifth flip is heads, and why?
5. How many ways to pick 3 blends from 6 when order does not matter? (Check with `math.comb`.)
6. "A is independent of B" in your own words. Give one pair from the dice that is, and one that is not.

* * *

## Cheat sheet

```text
SAMPLE SPACE = list of all outcomes     EVENT = a group of outcomes
P(event) = ways it happens / all ways      (equally likely outcomes only)

NOT:   P(not A) = 1 - P(A)        "at least one" = 1 - none
OR:    P(A or B) = P(A) + P(B) - P(A and B)     (no overlap: just add)
AND:   P(A and B) = P(A) x P(B)    only if independent (a rectangle of cells)
       otherwise count the overlap directly

ORDERED picks:   math.perm(n, k)      UNORDERED picks:  math.comb(n, k)
Relative frequency = what happened;  probability = what could happen.
```

* * *

## Answers

1. The total is 7 in 6 cells (1+6, 2+5, 3+4, 4+3, 5+2, 6+1): **6/36 = 1/6**.
2. No even number means both dice odd: 3 × 3 = 9 cells. So 1 − 9/36 = **27/36 = 3/4**.
3. The cell (4, 4) is in both lists and gets counted twice. Fixed: 6/36 + 5/36 − 1/36 = **10/36**.
4. **1/2**. The tosses are independent, so the first four tell you nothing about the fifth. A streak does not make the next one "due".
5. `math.comb(6, 3)` = **20** (6 × 5 × 4 = 120 ordered picks, divided by the 6 orderings of each trio).
6. Independent means knowing one does not change the share of the other. "First die even" and "second die is 5 or 6" are independent (18/36 × 12/36 = 6/36). "First die is 6" and "total is at least 10" are not (3 cells, not 1).

* * *

## References

- OpenStax, *Introductory Statistics 2e*, Ch. 3 "Probability Topics", section 3.1 Terminology: sample space, event, and probability as a count for equally likely outcomes (quoted from the page). The chapter covers the addition and multiplication rules, but the page fetched here did not define independence, so the definition above is this page's own plain-words version. <https://openstax.org/books/introductory-statistics-2e/pages/3-1-terminology>
- Python `itertools`: `product`, `permutations`, `combinations`, and their lengths via `math.perm` and `math.comb`. <https://docs.python.org/3/library/itertools.html>
- Python `math`: `comb(n, k)` "without repetition and without order", `perm(n, k)` "without repetition and with order". Since 3.15 these are soft-deprecated aliases of `math.integer` versions; on 3.14.4 they work as shown. <https://docs.python.org/3/library/math.html>
- Every count on this page was recomputed by listing the outcomes with Python 3.14.4, including the 1296 four-roll sequences for the gambler's-fallacy count.
