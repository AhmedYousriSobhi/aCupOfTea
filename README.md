# aCupOfTea
# AI Tea Lounge: Sipping Knowledge in AI Domains
![aCupOfTea logo: a yellow Pac-Man shape beside a steaming cup of tea on a saucer](https://github.com/AhmedYousriSobhi/aCupOfTea/assets/66730765/4a033ba8-5aac-475d-9b27-ec13e68746ba)

> **Knowledge, served in short sips.** Notes on AI, machine learning, software engineering and the business around them. Each page is short enough to finish before your tea goes cold.

## ☕ What's brewing

aCupOfTea is a personal knowledge base built during day-to-day work in data science and engineering. It collects:

- **Concepts**: the ideas behind ML, deep learning, statistics and generative AI.
- **Engineering**: clean code, design patterns, version control, parallel programming and systems.
- **Problems and projects**: reusable problem write-ups and the projects that solved them.
- **Business context**: how the technical work connects to real decisions.

It is written for practitioners who want the core of a topic quickly, and for anyone who likes to learn something new on a coffee break.

## 🍵 The menu

| Section | What you'll find | Best with |
|---|---|---|
| [Fields](/fields/README.md) | Deep learning, generative AI, statistics, recommender systems, RL, tabular data, benchmarks, schedulers, sysadmin | A long black |
| [Programming](/programming/README.md) | Python, clean code, OOP, data structures, decorators, OS, parallel programming, Git | A flat white |
| [Problems](/problems/README.md) | Interview and assessment problems, problem formulations, problem solving | A double espresso |
| [Projects](/projects/README.md) | End-to-end projects: customer segmentation, used-car pricing, campaign impact, BEV, face-off | A full pot |
| [Experiments](/experiments/README.md) | Small, exploratory work that isn't a project (yet) | A tasting flight |
| [Business](/business/README.md) | Data science in business, industry notes (HPC) | A board-meeting latte |
| [Tips](/tips/README.md) | Linux tricks, Git, Markdown, Kaggle, interview prep | A quick sip |
| [Journal](/journal/README.md) | Running notes and reflections | Whatever's in the pot |

## ☕ Start here: short sips

Not sure where to begin? Each of these takes one cup, roughly the reading time shown.

| Time | Page | Why read it |
|---|---|---|
| ~4 min | [The accuracy paradox](/fields/tabular-data/data-evaluation/classification/accuracy-paradox.md) | Why a model can score 95% and still be useless |
| ~6 min | [Sequence models](/fields/deep-learning/concepts/sequence-models.md) | How models handle ordered data like text, from RNNs onward |
| ~3 min | [Encoder-decoder for translation](/fields/generative-ai/machine-translator/encoder-decoder.md) | The architecture behind machine translation, in a few paragraphs |
| ~7 min | [Bias and variance](/fields/tabular-data/data-evaluation/model-behavior/bias-variance-trade-off.md) | The trade-off behind overfitting and underfitting |
| ~6 min | [Customer segmentation](/problems/customer-segmentation.md) | A business problem, framed the way a data scientist would |
| ~7 min | [Schedulers, the traffic controller](/fields/schedulers/intro.md) | What a cluster scheduler does and why it matters |

<!-- recent:start -->

## 🆕 Recently added

- 2026-10-20 · [The Curtain, the Locksmith and the Door Already Built](/programming/local-app-accounts/lock-recovery-and-going-online.md)
- 2026-10-20 · [The Orphans Come Home: Old Data and Background Work](/programming/local-app-accounts/old-data-and-background-work.md)
- 2026-10-20 · [Reviewing the Design: Where Would You Push Back?](/programming/local-app-accounts/reviewing-the-design.md)
- 2026-10-20 · [Who's Home, and What May They Touch? Sessions and Two Walls](/programming/local-app-accounts/sessions-and-two-walls.md)
- 2026-10-20 · [Sign-In Hygiene: How the Clerk Says "No" Without Giving Anything Away](/programming/local-app-accounts/sign-in-hygiene.md)
- 2026-10-20 · [Two People, One Laptop: What Accounts Should (and Shouldn't) Promise](/programming/local-app-accounts/threat-model-and-first-launch.md)

<!-- recent:end -->

## 🗺️ How to read it

- **On the website:** use the sidebar. It is generated from the folder structure, so it always matches the repo.
- **On GitHub:** every folder has a `README.md` that lists its pages.
- **Projects** marked ↗ are separate repositories, linked as git submodules. Clone with `git clone --recursive` to get them locally.

<details>
<summary><b>Repository layout</b></summary>

```bash
.
├── business
│   └── hpc-industry
├── experiments
│   └── wandb-sklearn-project
├── fields
│   ├── benchmarks
│   ├── computer-science-engineering  (submodule)
│   ├── data-collection
│   ├── deep-learning
│   ├── design-patterns
│   ├── generative-ai
│   ├── libraries-frameworks-containers
│   ├── recommender-systems
│   ├── reinforcement-learning
│   ├── schedulers
│   ├── statistics
│   ├── system-administration
│   └── tabular-data
├── journal
├── problems
│   ├── interview-assessment-problems
│   └── problem-solving  (submodule)
├── programming
│   ├── data-structure
│   ├── decorators
│   ├── oop
│   ├── operating-system
│   ├── parallel-programming
│   ├── python
│   ├── python-clean-code
│   ├── software-goals
│   ├── software-skills-and-tools
│   └── version-control
├── projects
│   ├── bev-project  (submodule)
│   ├── customer-segmentation  (submodule)
│   ├── face-off  (submodule)
│   ├── market-campaign-impact  (submodule)
│   └── used-cars-price-estimation  (submodule)
├── tips
├── index.html   (Docsify entry point)
└── README.md
```

</details>

## 🤝 Pull up a chair

Contributions are welcome: a correction, a clearer explanation or a whole new topic.

1. Branch from `dev` and keep one topic per branch.
2. Put the page where it belongs. [`SPEC.md`](/SPEC.md) describes the structure, and folder and page names use `kebab-case`.
3. Open a pull request against `dev`.

The step-by-step guide, with the script that creates a page and the checks to run, is in [CONTRIBUTING.md](https://github.com/AhmedYousriSobhi/aCupOfTea/blob/main/.github/CONTRIBUTING.md).

Found something off but no time to fix it? [Open an issue](https://github.com/AhmedYousriSobhi/aCupOfTea/issues). That helps too.

## 📜 License

© 2023–2026 Ahmed Yousri Sobhi and aCupOfTea contributors.

- **Writing and diagrams** (the pages) are licensed under [CC BY 4.0](https://github.com/AhmedYousriSobhi/aCupOfTea/blob/main/LICENSE). You may share and adapt them, including commercially, as long as you credit **aCupOfTea** and link back to the page.
- **Code** (scripts, notebooks and the site tooling in `.docs/`) is licensed under the [MIT License](https://github.com/AhmedYousriSobhi/aCupOfTea/blob/main/LICENSE-CODE).
- **Not covered:** material that already carries its own license or belongs to someone else keeps it:
  - `fields/generative-ai/machine-translator/nmt_with_attention.ipynb` (TensorFlow Authors, Apache 2.0)
  - the linked project repositories (git submodules)
  - the CSV datasets
  - images and quotes taken from other sites

By contributing, you agree that your contribution is licensed under the same terms.

## 💬 Sip and support

If a page saved you some time, ⭐ the repo or share it with someone who'd enjoy it. Feedback and ideas are always welcome.

<div align="center">
  <img src="https://media.giphy.com/media/KZMRyVjEtdv8AU6mIr/giphy.gif" width="300" alt="Cheers"/>
  <p><b>Cheers to knowledge, growth, and a well-brewed cup. 🍵</b></p>
</div>
