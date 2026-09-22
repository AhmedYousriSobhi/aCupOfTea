# Git - Know How?

Daily works never ends, learning never gets old, so every new day requires a new thing to do, here let's know the how to do for git and github.

## Table of Contents
- [Git - Know How?](#git---know-how)
  - [Table of Contents](#table-of-contents)
  - [Classic GitHub Workflow (Fork -\> Modify -\> Pull Request -\> Merge)](#classic-github-workflow-fork---modify---pull-request---merge)
    - [Step-1: Fork](#step-1-fork)
    - [Step-2: Clone and Modify](#step-2-clone-and-modify)
    - [Step-3: Open a Pull Request (PR)](#step-3-open-a-pull-request-pr)
    - [Step-4: Merge (in repo A)](#step-4-merge-in-repo-a)
    - [Workflow Diagram](#workflow-diagram)
  - [How to Manage Multiple Users ?](#how-to-manage-multiple-users-)
    - [1. Who Makes the Commits ? (Global vs Local Git User)](#1-who-makes-the-commits--global-vs-local-git-user)
    - [2. Commits Vs Pull/Push](#2-commits-vs-pullpush)
    - [3. Steps to Manage Multiple Users](#3-steps-to-manage-multiple-users)
  - [How to Remove Last Pushed Commit ?](#how-to-remove-last-pushed-commit-)
  - [How to Start New Branch from an Upstream Branch?](#how-to-start-new-branch-from-an-upstream-branch)
    - [Example Setup](#example-setup)
    - [Steps](#steps)
  - [Enable and Deploy Pages](#enable-and-deploy-pages)
    - [BrainStorming](#brainstorming)
    - [Steps](#steps-1)
    - [Notes](#notes)
  - [Handy Commands](#handy-commands)

## Classic GitHub Workflow (Fork -> Modify -> Pull Request -> Merge)
Role|Repo|Description
|-|-|-|
Repo A|github.com/original-owner/projectA|The original repository (upstream).
Repo B|github.com/your-username/projectA|Your **fork** -- a full copy of the Repo A under your account.

### Step-1: Fork
- Click Fork on github to fork Repo A into repo B
    ```
    GitHub
    │
    ├── Repo A (original)
    │    ├── commit1
    │    └── commit2
    │
    └── Repo B (your fork, copied from A)
        ├── commit1
        └── commit2
    ```

### Step-2: Clone and Modify
1. Clone the forked repo B locally, with:
    ```bash
    git clone https://github.com/your-username/projectA.git
    ```
2. Make the changes, then commit and push:
    ```bash
    git add .
    git commit -m "add feature X"
    git push origin main
    ```
- Diagram:
    ```
    Repo A (original)
    ├── commit1
    └── commit2

    Repo B (your fork)
    ├── commit1
    ├── commit2
    └── commit3 ← your new commit
    ```

### Step-3: Open a Pull Request (PR)
- On GitHub, you go to Repo B -> click **Compare & pull request**.
- This creates a **pull request** targeting Repo A's main branch e.g:
    ```
    your-username:main  →  original-owner:main
    ```
- This Pull Request (PR) says: Please merge my commit from Repo B into Repo A.

### Step-4: Merge (in repo A)
- When the repo A maintainer clicks “Merge Pull Request”:
    - GitHub merges commit3 from Repo B into Repo A.
    - The new commit now physically lives inside Repo A’s history.

```
Repo A (after merge)
  ├── commit1
  ├── commit2
  └── commit3 ← now part of Repo A!

Repo B (fork)
  ├── commit1
  ├── commit2
  └── commit3
```
### Workflow Diagram
```
        ┌──────────────────────────┐
        │      Repo A (Original)   │
        │  commit1 → commit2       │
        └────────────┬─────────────┘
                     │  (fork)
                     ▼
        ┌──────────────────────────┐
        │      Repo B (Forked)     │
        │  commit1 → commit2 → ✨commit3✨ │
        └────────────┬─────────────┘
                     │  (pull request)
                     ▼
        ┌──────────────────────────┐
        │ Repo A after merge       │
        │  commit1 → commit2 → commit3 │
        └──────────────────────────┘
                     │
                     ▼
              Repo B deleted ❌
          (but commit3 remains in A)
```

## How to Manage Multiple Users ?
This is a classic multi-user / multi-repo Git setup problem.

Before jumping to the steps, there are two main points should be understood first:
1. Who makes the commits?
2. What is the difference between commits and pull/push?

### 1. Who Makes the Commits ? (Global vs Local Git User)
- When you run:
    ```bash
    git config --global user.name "Alice"
    git config --global user.email "alice@example.com"
    ```
    - **--global user =** default identity for all repos for this system user.
    - It’s stored in `~/.gitconfig`.
    - If you don’t override it, Git will always use this identity for commits.
- But Git also supports per-repository identity:
    ```bash
    cd /path/to/repo
    git config user.name "Bob"
    git config user.email "bob@example.com"
    ```
    - Local **user =** identity for this repo only.
    - It’s stored in `.git/config` inside that repo.
    - It overrides the global settings.

### 2. Commits Vs Pull/Push
- **Commit identity** is set by `user.name` and `user.email`.
- **Pull/Push authentication** depends on credentials (SSH keys, HTTPS tokens).

So you need to handle two layers:
- Git identity (`user.name`, `user.email`)
- GitHub authentication (SSH key or HTTPS token)

### 3. Steps to Manage Multiple Users
1. Create an SSH-Key for the target username and email using *ssh-keygen* command:
    ```bash
    ssh-keygen -t ed25519 -C 'ahmedyousrisobhi@gmail.com'

    # Expected output:
    Generating public/private ed25519 key pair.
    Enter file in which to save the key (/home/asobhy/.ssh/id_ed25519): /home/asobhy/.ssh/id_ed25519_ahmedyousrisobhi
    Enter passphrase (empty for no passphrase): 
    Enter same passphrase again: 
    Your identification has been saved in /home/asobhy/.ssh/id_ed25519_ahmedyousrisobhi
    Your public key has been saved in /home/asobhy/.ssh/id_ed25519_ahmedyousrisobhi.pub
    ```
    - The generated keys are: [id_ed25519_ahmedyousrisobhi.pub, id_ed25519_ahmedyousrisobhi]

    > 📝 Note: the keys are generated under `*~/.ssh*` directory.
    
    > 📝 Note: Running ssh-keygen command without any additional options gets you id_rsa and id_rsa.pub

    > 📝 Note: You can use option `-f <key-name>` instead of using -C for comment, e.g: ***ssh-keygen -f work_id_rsa***, this will create keys: [work_id_rsa, work_id_rsa.pub].

2. For account #2: Let's create another key for work account:
    ```bash
    ssh-keygen -f work_id_rsa
    ```
    - Same if you want to set passphrase you can do it, but using default here.
    - Generated keys are: [work_id_rsa, work_id_rsa.pub].

    > 💡 Pro Tip: Try to choose a descriptive naming for the key, like define the which work mail your refer to.

3. Add the ssh key to the ssh agent with:
    ```bash
    ssh-add ~/.ssh/id_ed25519_ahmedyousrisobhi
    ssh-add ~/.ssh/work_id_rsa
    ```

    > 📝 Note: You can verify the keys listed using command: ***ssh-add -l***

    > 📝 Note: ssh-add is used in the cases: The key is not the default one (~/.ssh/id_rsa or ~/.ssh/id_ed25519), and you use a custom SSH config with multiple IdentityFiles.

4. Add the ssh to the config file; This lets Git know which key to use per account:
    ```bash
    # GitHub account: AhmedYousriSobhi
    Host github.com-ahmedyousrisobhi
        HostName github.com
        User git
        IdentityFile ~/.ssh/id_ed25519_ahmedyousrisobhi
        IdentitiesOnly yes
    
    # my work account
    Host github.com-work
        HostName github.com
        IdentityFile ~/.ssh/work_id_rsa
        IdentitiesOnly yes
    ```
    - Using of `IdentitiesOnly yes`: 
      - Tells ssh to use only the key(s) explicitly listed under IdentityFile for this host — and ignore all other keys in the agent or defaults.
      - In case of removing it; When you connect to GitHub, SSH may try all keys loaded under `~/.ssh` in order until one matches. That’s inefficient and sometimes leads to `Too many authentication failures` error. 
      - Using it ensures no cross-contamination.

    > 📝 Note: this can work with gitlab, you need to change github to gitlab, can work with both at the same time too.

4. Copy the public key with to be added as a key in Github account:
    ```bash
    cat ~/.ssh/id_ed25519_ahmedyousrisobhi.pub
    ```

5. To validate the connection, use:
    ```bash
    ssh -T git@github.com-ahmedyousrisobhi

    # Expected output: Hi ahmedyousrisobhi! You've successfully authenticated, but GitHub does not provide shell access.
    # This confirms your SSH key is correctly mapped to that GitHub user.
    ```

6. If you want to clone from personal, you use default ssh you copy from github
    ```bash
    git clone git@github.com-ahmedyousrisobhi:AhmedYousriSobhi/aCupOfTea.git
    ```

    - If you want to use your work then:
        ```bash
        git clone git@github.com-work:AhmedYousriSobhi/aCupOfTea.git
        ```

    > 📝 Note: You can clone the repo normally using its http url, then update the git remote url to the correct host. Illustrated in step #8.

7. When you clone a repo for the first time using this method you need to set the name and email so it won't use the default name and email which here is personal
    ```bash
    git config user.name "github account name"
    git config user.email "github email"
    ```

8. Change your Git remote to use this Host:
    ```bash
    git remote set-url origin git@github.com-ahmedyousrisobhi:ahmedyousrisobhi/<repo-name>.git
    ```
    - To validate using: git remote -v

## How to Remove Last Pushed Commit ?
```bash
# 1. Remove last commit but keep the changes (so you can fix and recommit)
# This moves the branch pointer back by one commit, but your changes stay staged.
git reset --soft HEAD~1

# If you want them unstaged
# git reset HEAD

# 2. Remove last commit and discard the changes completely
# This rewinds history by one commit and throws away those changes.
git reset --hard HEAD~1

# 3. Push the corrected history to remote
# Since the commit is already pushed, you need to force push
git push origin HEAD --force
```

## How to Start New Branch from an Upstream Branch?
### Example Setup
- Your fork: origin
- The main/original repo: upstream
- You want to create a new branch (say feature-x) from an upstream branch (say dev)

### Steps
1. Make sure you have the latest refs from upstream; This updates your local knowledge of all upstream branches without modifying your working directory:
    ```bash
    git fetch upstream
    ```
2. Check which upstream branches exist:
    ```bash
    git branch -r
    ```
3. Create your new branch from the upstream branch:
    ```bash
    git checkout -b feature-x upstream/dev
    ```
    - This means:
        - Create a new branch called feature-x
        - Start it from the state of upstream/dev

4. Verify:
    ```bash
    git status
    git branch -vv
    ```

## Enable and Deploy Pages
This guide to enable and deploy pages in Github using Github actions.
1. Define Github action yml file.
2. Create the Sphinx quick start. 

### BrainStorming
The roles of each branch:

Branch|Role|
|-|-|
main|This is your source of truth: all your Markdown files, scripts, and configuration live here.</br>You edit docs here, commit, and push changes.</br>You never manually edit HTML or built artifacts here (those are generated).
gh-pages|This branch is purely for the generated output — the final HTML site that GitHub Pages serves publicly.</br>GitHub Pages doesn’t build your docs itself (except for simple Jekyll setups).
It just hosts whatever static files it finds in gh-pages (or /docs in the same branch, if configured that way).

So, the GitHub Actions workflow’s job is:
1. Build the documentation using Sphinx from main.
2. Push the resulting _build/html/ directory to the gh-pages branch.
3. GitHub Pages then serves that branch directly at:
https://<username>.github.io/<repo>/

That’s the reason the gh-pages branch must exist even if your actual source is somewhere else.

So the current structure will be:
```bash
── tips/
├── README.md
└── docs/
    ├── source/
    │   ├── conf.py
    │   ├── index.rst
    │   └── ...
    └── build/
```

> Issue: Referring the markdown guides to the be visible under `docs/source` directory, which will be solved by defining the abs path in the conf.py file.

> Tip: Best-practice to create a temp branch to develop the solution, then merge it with the main. But note there will be some modifications in the deploy-docs.yml below which creates the Github action.

### Steps
1. mkdir the docs directory, where it will be keeps using: `mkdir docs`
2. Initiate the Sphinx quick start using: `sphinx-quickstart`
    ```bash
    sphinx-quickstart 

    # Expected output:
    Welcome to the Sphinx 8.2.3 quickstart utility.

    Please enter values for the following settings (just press Enter to
    accept a default value, if one is given in brackets).

    Selected root path: .

    You have two options for placing the build directory for Sphinx output.
    Either, you use a directory "_build" within the root path, or you separate
    "source" and "build" directories within the root path.
    > Separate source and build directories (y/n) [n]: y

    The project name will occur in several places in the built documentation.
    > Project name: aCupOfTea
    > Author name(s): Ahmed Yousri Sobhi
    > Project release []: 1.0

    If the documents are to be written in a language other than English,
    you can select a language here by its language code. Sphinx will then
    translate text that it generates into that language.

    For a list of supported codes, see
    https://www.sphinx-doc.org/en/master/usage/configuration.html#confval-language.
    > Project language [en]: 

    Creating file ~/workspace/aCupOfTea/docs/source/conf.py.
    Creating file ~/workspace/aCupOfTea/docs/source/index.rst.
    Creating file ~/workspace/aCupOfTea/docs/Makefile.
    Creating file ~/workspace/aCupOfTea/docs/make.bat.

    Finished: An initial directory structure has been created.

    You should now populate your master file /home/asobhy/workflow/workspace/aCupOfTea/docs/source/index.rst and create other documentation
    source files. Use the Makefile to build the docs, like so:
    make builder
    where "builder" is one of the supported builders, e.g. html, latex or linkcheck.
    ```
3. Add the `docs/build` to `.gitignore` to avoid committing the build html.
    ```bash
    touch .gitignore

    vi .gitignore

    # Ignore Sphinx build output
    docs/build/

    # Save and exit
    :wq!
    ```
4. Create the Github workflows directory for Github action definition:
    ```bash
    mkdir -p .github/workflows
    ```
5. Create the Github action using `deploy-docs.yml` file configuration:
    ```yml
    name: Deploy Docs to GitHub Pages

    on:
    push:
        branches:
        - main
    workflow_dispatch:

    permissions:
    contents: write

    jobs:
    deploy:
        runs-on: ubuntu-latest
        steps:
        - name: Checkout repository
            uses: actions/checkout@v4

        - name: Set up Python
            uses: actions/setup-python@v5
            with:
            python-version: '3.11'

        - name: Install dependencies
            run: |
            python -m pip install --upgrade pip
            pip install sphinx sphinx-rtd-theme

        - name: Build documentation
            run: |
            make html

        - name: Deploy to gh-pages branch
            uses: peaceiris/actions-gh-pages@v4
            with:
            github_token: ${{ secrets.GITHUB_TOKEN }}
            publish_branch: gh-pages
            publish_dir: ./docs/_build/html
            force_orphan: true

    ```
6. Add the abs path to the markdown documentation in the docs/source/conf.py file:
    ```py
    # Imports
    import os
    import sys

    # Add project root to sys.path so we can reference top-level folders
    sys.path.insert(0, os.path.abspath('../..'))
    ```
7. To include a sample markdown in the webpage use:
    ```bash
    # inside the docs/source/index.rst file:
    .. include:: ../../README.md
       :parser: myst_parser.sphinx_
    ```
8. Verify by local html build inside the docs directory
    ```bash
    cd docs

    make html
    ```
    - Note: make sure that myst-parser package is installed with pip. (Best practice to build a conda env for Sphinx to use.)

### Notes
1. In deploy-docs.yml file, This tells GitHub when to run the workflow.
    - push → run the workflow whenever someone pushes commits to a branch.

    ```yml
    on:
    push:
        branches:
        - main
    ```
2. In deploy-docs.yml, This tells Github which branch to fetch the docs from:
    ```yml
    jobs:
    deploy:
        runs-on: ubuntu-latest
        steps:
        - name: Checkout repository
            uses: actions/checkout@v4
            with:
                ref: main
    ```

## Handy Commands
- Visualize git branches, use:
    ```bash
    git log --oneline --graph --all --decorate
    ```
- Reset a repo from the origin branch, use:
    ```bash
    git reset --hard origin/<branch-name>
    ```
