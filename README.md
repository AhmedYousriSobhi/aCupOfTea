# aCupOfTea
# AI Tea Lounge: Sipping Knowledge in AI Domains
![image](https://github.com/AhmedYousriSobhi/aCupOfTea/assets/66730765/4a033ba8-5aac-475d-9b27-ec13e68746ba)

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

Found something off but no time to fix it? [Open an issue](https://github.com/AhmedYousriSobhi/aCupOfTea/issues). That helps too.

## 💬 Sip and support

If a page saved you some time, ⭐ the repo or share it with someone who'd enjoy it. Feedback and ideas are always welcome.

<div align="center">
  <img src="https://media.giphy.com/media/KZMRyVjEtdv8AU6mIr/giphy.gif" width="300" alt="Cheers"/>
  <p><b>Cheers to knowledge, growth, and a well-brewed cup. 🍵</b></p>
</div>
