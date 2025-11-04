# Git - Case Study

## Table of Contents
- [Git - Case Study](#git---case-study)
  - [Table of Contents](#table-of-contents)
  - [Situation - Sync Repo-A/dev with Fork Repo-B/dev-updated](#situation---sync-repo-adev-with-fork-repo-bdev-updated)
    - [Objective](#objective)
    - [Should I Sync My Fork Before Opening a PR, or just create PR as-is?](#should-i-sync-my-fork-before-opening-a-pr-or-just-create-pr-as-is)
    - [Solution - Best Practice](#solution---best-practice)
  - [Situation - Reviewing Merge PR to my Commit](#situation---reviewing-merge-pr-to-my-commit)
    - [Objective](#objective-1)
    - [Solution - Best Practice](#solution---best-practice-1)

## Situation - Sync Repo-A/dev with Fork Repo-B/dev-updated
### Objective
I’ve forked repo-b from repo-a and updated a specific branch, creating repo-b/dev-updated based on repo-a/dev. However, since then, several commits have been added to repo-a/dev, causing my repo-b/dev-updated branch to fall out of sync. As a result, merging a PR from repo-b/dev-updated into repo-a/dev will likely cause significant conflicts due to the large divergence.

This is a common situation when working with forks and multiple branches. 

### Should I Sync My Fork Before Opening a PR, or just create PR as-is?
Situation|	Recommended Action|
|-|-|
✅ Your branch (dev-uodated) is based on upstream/dev and only a few commits behind|	Continue without syncing — just open the PR. GitHub will handle showing the diff correctly.
⚠️ Your branch is significantly behind (many commits, structural changes, or conflicts likely)|	Sync first (merge or rebase from upstream/dev), then open the PR.
🚫 You accidentally synced with the wrong branch (upstream/main)|	Undo or ignore that sync (depending if it affected your branch) — then sync from the correct one later if needed.

### Solution - Best Practice
> CAUTION!! Do not use GitHub's Sync Fork button; it only syncs 'main'.

1. Add upstream remote (it not already)
    ```bash
    git remote add upstream https://github.com/<owner-of-repo-a>/<repo-a>.git
    ```
  
    > Note: In case you use ssh key, please use *'git remote set-url upstream git@\<ssh-key-name>:\<owner-of-repo-a>/\<repo-a>.git'*

2. Fetch all branches from upstream
    ```bash
    git fetch upstream
    ```
3. Checkout your working branch
    ```bash
    git checkout dev-updated
    ```
4. [Best-Practice] Create a new branch for the sync, let's call it dev-updated-synched, and it's starting from the current commit of branch A.
    ```bash
    git checkout -b dev-updated-synched
    ```
5. From this point, there are two options:
   1. Using Merge; this will keeps history.
        ```bash
        git merge upstream/dev
        ```
        - To undo, you can use: git reset --hard HEAD~1
   2. Using rebase; This will have cleaner history, and rewrite commits.
        ```bash
        git rebase upstream/dev
        ```
> From Here, We will choose the Rebase Approach. Rebase is used to push your commits on a top of the target branch. So once you did a rebase, it will place your commits on a top of the current branch.
> The issue you may face other than conflict, is that You will find all your commits (let's say 8) are a top of the synched branch. In this case we need to Squash them.
6. Squash the commits; Manually get the numbers of commits you need to squash, from command *git log*, then do a soft reset:
    ```bash
    git reset --soft HEAD~8
    
    # Check the latest staged modified files from the latest commit.
    git status
    ```
7. Commit the changes, and push it to the target branch in the repo-b:
    ```bash
    git commit -m "Your message, latest update in the commit"

    git push origin dev-updated-synched
    ```

## Situation - Reviewing Merge PR to my Commit
### Objective
A merge PR from another repo to my commit in a repo. I wanted to check the running the changes he requested locally to verify.

### Solution - Best Practice
```bash
git remote -v
# Add
git remote add <title> https://github.com/<username>/<repo-name>.git

# To verify adding the repo
git remote -v

# Fetching the repo
git fetch kadirc-docs 

# To be safe, create a separate branch to merge with the fetched external repo
git checkout -b review-kadirc-image

# Merge the external branch to the target branch
git merge <title>/<branch-name> 

# Check the changes
git status
```

> Note: you can commit the change in case of adding/removing modifications.

> Note: You can delete the created branch if the case if just reviewing the requested merged branch
