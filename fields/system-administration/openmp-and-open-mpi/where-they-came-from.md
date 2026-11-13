
# Two Tribes, One Problem: Where OpenMP and MPI Came From

<!-- related-block -->
<div class="reading-time">6 min read</div>
<!-- related-block -->
<div class="related-strip">

**Read first:** [Not Twins, Not Even Cousins: OpenMP, MPI and Open MPI](/fields/system-administration/openmp-and-open-mpi/the-name-mixup.md)  ·  **Read next:** [Two Tickets About the Future: OpenMP 6, MPI 5 and What Never Expires](/fields/system-administration/openmp-and-open-mpi/where-they-are-going.md)

</div>


> **Part 2 of 8.** Two committees, one headache, and a standard that nearly died on the way in. By the end of this page you'll know why two parallel standards exist, who wrote each, and where Open MPI fits in the family tree.

## Contents

- [The problem: every vendor spoke its own dialect](#the-problem-every-vendor-spoke-its-own-dialect)
- [Tribe 1: the message passers (MPI)](#tribe-1-the-message-passers-mpi)
- [Try it before you scroll](#try-it-before-you-scroll)
- [Tribe 2: the shared-memory crowd (OpenMP)](#tribe-2-the-shared-memory-crowd-openmp)
- [Where Open MPI was born](#where-open-mpi-was-born)
- [The whole timeline on one screen](#the-whole-timeline-on-one-screen)

---

## The problem: every vendor spoke its own dialect

Picture the early 1990s. You spent a year writing a clever parallel program for one vendor's supercomputer. Then the machine was retired, and the replacement came from another vendor. Your year of work did not move. It had to be rewritten, because every vendor had invented its own way to say "split this work up". It was like a hotel chain where every hotel makes you learn a different way to switch on the light.

There were two kinds of machines, and so two kinds of dialect:

| Machine | How the processors see memory | How you program it |
|---------|-------------------------------|--------------------|
| **Shared-memory** | All processors see one memory | Mark loops for parallel execution; the compiler splits them |
| **Distributed-memory** | Each processor has its own memory | Send messages between processors |

Both tribes arrived at the same cure: stop inventing light switches, write the dialects down once as a standard, and let every vendor build to it. Then they went off and did it separately, which is the whole reason you are reading two stories.

Who went first, and who went at all?

---

## Tribe 1: the message passers (MPI)

The distributed-memory tribe moved first, and in the open. The [MPI-1.1 standard](https://www.mpi-forum.org/docs/mpi-1.1/mpi-11-html/node2.html) tells the story itself:

- **April 29-30, 1992:** a workshop on standards for message passing in a distributed-memory environment is held in Williamsburg, Virginia. It agrees that a standard is worth writing and sets up a working group.
- **November 1992:** Dongarra, Hempel, Hey and Walker put forward a first draft called MPI1, then a revised one in February 1993. The same month, in Minneapolis, the group decides to run itself by the procedures of the High Performance Fortran Forum. That group becomes the **MPI Forum**.
- **1993:** the Forum meets every six weeks for two days and shows its draft at Supercomputing 93 in November.
- **Who:** about 60 people from 40 organizations, spread over vendors, universities, government labs and industry.

MPI-1.0 was published in 1994 (per the [Open MPI FAQ](https://www.open-mpi.org/faq/?category=general)); MPI-1.1 followed on June 12, 1995.

Notice what MPI is: a **document**, finished by a committee of about 60 people who still managed to agree. The Forum writes the rules and, then, anyone may build software that follows them. That is the whole reason there is more than one MPI program (part 1).

Meanwhile, the shared-memory tribe tried the same trick in 1994, three years before OpenMP. It did not go well.

---

## Try it before you scroll

☕ Ten seconds. In 1994 a committee drafted a standard for shared-memory directives (it was called **ANSI X3H5**), and then **nobody adopted it**. Why do you think it was abandoned?

Hint: what was happening, at that exact moment, to the other kind of machine?

---

## Tribe 2: the shared-memory crowd (OpenMP)

The answer is in the sources. The shared-memory tribe had a false start. Per the [LLNL OpenMP tutorial](https://hpc-tutorials.llnl.gov/openmp/introduction/), makers of shared-memory machines had each offered "comparable Fortran extensions based on compiler directives", where you mark a loop and the compiler spreads it over the processors. In 1994 a draft from **ANSI X3H5** tried to standardize them. It was "never adopted, largely due to waning interest as distributed memory machines became popular".

Read that again: the rise of MPI-style machines is part of why the first shared-memory standard stalled. In short, the message-passing tribe accidentally knocked over the shared-memory tribe's first standard on the way in, and the shared-memory tribe came back three years later with a better plan.

It came back in **spring 1997**, when work on the OpenMP standard began, "continuing where X3H5 left off", led by the OpenMP Architecture Review Board (ARB). The first spec, **OpenMP Fortran 1.0, came out in October 1997**. The C/C++ version followed in October 1998 ([OpenMP specifications list](https://www.openmp.org/specifications/)).

| | MPI | OpenMP |
|---|---|---|
| Written by | The MPI Forum: vendors, universities, labs | The OpenMP ARB: a board of vendors and research bodies |
| First finished | MPI-1.0, 1994 | Fortran 1.0, October 1997 |
| Language it lives in | A library you call (C, Fortran) | Directives your compiler understands (C, C++, Fortran) |
| Failed predecessor | None needed: it started from a workshop | ANSI X3H5 (1994 draft, never adopted) |

> [!NOTE]
> The sources say the ARB led the 1997 work. They do not give an exact date for the board's founding, so this page doesn't either.

---

## Where Open MPI was born

MPI was a document, so implementations followed. By the [Open MPI FAQ](https://www.open-mpi.org/faq/?category=general), Open MPI "began as a merger" of three existing MPI implementations, with ideas from a fourth:

| Ancestor | From |
|----------|------|
| FT-MPI | University of Tennessee |
| LA-MPI | Los Alamos National Laboratory |
| LAM/MPI | Indiana University |
| PACX-MPI (contributed) | University of Stuttgart |

The project's copyright notice starts in 2004. Open MPI is therefore a **descendant of MPI implementations**, not of OpenMP. The name is "Open" because it is open source, the same way a hundred other projects are.

Open MPI is not alone. MPICH is another implementation, and vendors ship their own. Which is why, in part 1, installing "Open MPI" and "MPI" was never the same sentence.

---

## The whole timeline on one screen

| Year | Shared memory (OpenMP) | Message passing (MPI) |
|------|------------------------|-----------------------|
| 1992 | | Williamsburg workshop (April); first draft (November) |
| 1994 | ANSI X3H5 draft, never adopted | MPI-1.0 published |
| 1995 | | MPI-1.1 (June 12) |
| 1997 | Fortran 1.0 (October) | MPI-2.0 (July 18) |
| 1998 | C/C++ 1.0 (October) | |
| 2004 | | Open MPI project's copyright begins |

**Takeaway:** MPI and OpenMP are two answers from two tribes to the same 1990s headache, and Open MPI is a later, separate program that implements MPI.

You now know the cast and the history. Time to stop reading about them and run them: in [part 3](/fields/system-administration/openmp-and-open-mpi/threads-and-ranks.md) four threads count to 100 million, and two out of three times they get it wrong.

---

## References

- [MPI-1.1 standard, introduction: history of the MPI effort](https://www.mpi-forum.org/docs/mpi-1.1/mpi-11-html/node2.html)
- [MPI Forum: standards and release dates](https://www.mpi-forum.org/docs/)
- [Open MPI FAQ: MPI release history and Open MPI's ancestors](https://www.open-mpi.org/faq/?category=general)
- [LLNL OpenMP tutorial: history of OpenMP](https://hpc-tutorials.llnl.gov/openmp/introduction/)
- [OpenMP specifications: release dates](https://www.openmp.org/specifications/)
