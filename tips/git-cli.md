# Git Command Line Interface (CLI)

In the context of Git, "gh" refers to the GitHub CLI tool, which is a command-line interface for interacting with GitHub repositories. It provides a convenient way to manage GitHub-specific features, such as issues, pull requests, and releases, directly from your terminal. The GitHub CLI is available for macOS, Windows, and Linux, and it can be installed using a package manager or by downloading the binary from the GitHub CLI website.

## Table of Contents
- [Git Command Line Interface (CLI)](#git-command-line-interface-cli)
  - [Table of Contents](#table-of-contents)
  - [CLI Benefits](#cli-benefits)
  - [HTTP vs CLI Cloning](#http-vs-cli-cloning)
  - [Usage Examples](#usage-examples)
  - [How to Use?](#how-to-use)
  - [Steps - SSH Key Configuration](#steps---ssh-key-configuration)
  - [Steps to Manage Multiple Users](#steps-to-manage-multiple-users)
  - [How to Remove Last Pushed Commit ?](#how-to-remove-last-pushed-commit-)
  - [Classic GitHub Workflow (Fork -\> Modify -\> Pull Request -\> Merge)](#classic-github-workflow-fork---modify---pull-request---merge)
    - [Step-1: Fork](#step-1-fork)
    - [Step-2: Clone and Modify](#step-2-clone-and-modify)
    - [Step-3: Open a Pull Request (PR)](#step-3-open-a-pull-request-pr)
    - [Step-4: Merge (in repo A)](#step-4-merge-in-repo-a)
    - [Workflow Diagram](#workflow-diagram)
  - [Situation - Sync Repo-A/dev with Fork Repo-B/dev-updated](#situation---sync-repo-adev-with-fork-repo-bdev-updated)
    - [Objective](#objective)
    - [Should I Sync My Fork Before Opening a PR, or just create PR as-is?](#should-i-sync-my-fork-before-opening-a-pr-or-just-create-pr-as-is)
    - [Solution - Best Practice](#solution---best-practice)
  - [Handy Commands](#handy-commands)
  - [To be Cont....](#to-be-cont)

## CLI Benefits
Here are some of the benefits of using the GitHub CLI:
|Benefit|Details|
|-|-|
|Efficiency| It allows you to perform GitHub tasks without having to switch between the terminal and a web browser.
|Automation| You can use scripts to automate repetitive tasks, such as creating issues or updating pull requests.
|Customization| You can create custom aliases and extensions to personalize your GitHub CLI experience.

## HTTP vs CLI Cloning
Normal HTTP cloning and gh clone are both methods for cloning a Git repository, but there are some key differences between the two.

Normal HTTP cloning involves downloading the contents of the repository directly from the Git server using the HTTP protocol. This method is simple to use, but it can be slow and unreliable, especially for large repositories.

gh clone is a command provided by the GitHub CLI tool that uses GitHub-specific APIs to clone repositories. This method is more efficient and reliable than normal HTTP cloning, and it also supports additional features, such as cloning private repositories and using SSH authentication.

Here is a table summarizing the key differences between normal HTTP cloning and gh clone:
|Feature|	Normal HTTP cloning|	gh clone|
|-|-|-|
Protocol|	HTTP|	GitHub-specific APIs|
Speed|	Slow|	Efficient|
Reliability|	Unreliable|	Reliable|
Supported features|	Cloning public repositories|	Cloning public and private repositories, using SSH authentication

In general, it is recommended to use gh clone for cloning Git repositories whenever possible. It is a more efficient, reliable, and feature-rich method than normal HTTP cloning.

## Usage Examples
Here are some examples of how to use the GitHub CLI:
|Action|Command|
|-|-|
|Create an issue| gh issue create "Describe the issue here"
|List open pull requests| gh pr list
|Create a new release| gh release create "Version 1.0.0" -t "v1.0.0"

Here is an example of how to clone a repository using gh clone:
Bash
```
gh clone https://github.com/google/bard
```

This will clone the google/bard repository to the current directory. If you want to clone the repository to a different directory, you can specify the directory name as an argument to the gh clone command. For example, the following command will clone the google/bard repository to the directory named bard:
Bash
```
gh clone https://github.com/google/bard bard
```

## How to Use?
Here are the general steps on how to use the GitHub CLI:

1. Install the GitHub CLI:

    -  For macOS, download the binary from the GitHub CLI website or use Homebrew to install it.
    -  For Windows, download the installer from the GitHub CLI website or use Chocolatey to install it.
    -  For Linux, use your distribution's package manager to install the GitHub CLI package.

2. Authenticate with GitHub:
    - Open a terminal window and run the command gh auth login.
    - Follow the on-screen instructions to sign in to your GitHub account.
    - GitHub CLI will store your credentials securely.

3. Use GitHub CLI commands:
    - There are many different GitHub CLI commands available for managing issues, pull requests, repositories, and other GitHub features.
    - You can find a list of all available commands by running the command gh help.
    - For help with a specific command, run the command gh help <command>.

4. Customize your GitHub CLI experience:
    - You can create custom aliases for frequently used commands.
    - You can install extensions to add additional features to GitHub CLI.
    - You can configure GitHub CLI settings to personalize your experience.

Here are some examples of how to use GitHub CLI commands:
- Create an issue: gh issue create "Describe the issue here"
- List open pull requests: gh pr list
- Create a new release: gh release create "Version 1.0.0" -t "v1.0.0"
- Clone a repository: gh clone https://github.com/google/bard

For more information on the GitHub CLI, please refer to the official documentation: https://github.com/cli/cli

## Steps - SSH Key Configuration

1. In case of any unwanted SSH Key file, Start by removing them:
    - Open a terminal window and navigate to the directory where your SSH key files are stored.
    - Locate the id_rsa and id_rsa.pub files.
    - Delete both files using the rm command.
    - For example, to delete the id_rsa and id_rsa.pub files, you would run the following commands:
```
rm ~/.ssh/id_rsa
rm ~/.ssh/id_rsa.pub
```
2. Remove the SSH key from your GitHub account:
    - Go to your GitHub account settings.
    - Click on the "SSH and GPG keys" tab.
    - Find the SSH key that you want to remove and click on the "Delete key" button.

3. Re-generate the SSH key:
    - Open a terminal window and run the following command:
```bash
ssh-keygen
```

- When prompted, enter a filename for the key pair.
- Then, enter a passphrase for the key. This is optional, but it is recommended for security reasons.
- Your SSH key pair will be generated.
- The public key will be saved to a file called id_rsa.pub, and the private key will be saved to a file called id_rsa.

4. Add the public key to your GitHub account:
    - Copy the contents of the id_rsa.pub file to your clipboard.
    - Go to your GitHub account settings.
    - Click on the "SSH and GPG keys" tab.
    - Click on the "New SSH key" button.
    - Paste the contents of your clipboard into the "Key" field.
    - Give your key a title, such as "My new SSH key for GitHub".
    - Click on the "Add SSH key" button.

5. Re-configure GitHub CLI to use SSH:
    - Open a terminal window and run the following command:

```bash
git config --global core.sshCommand "ssh -o IdentityFile=$HOME/.ssh/yousri_per"
```
- This will configure GitHub CLI to use the id_rsa key for SSH authentication.

6. Retry the gh command:
    - Once you have completed these steps, you should be able to retry the gh command without any errors.

This process will ensure that you start with a fresh set of SSH keys and that your GitHub account is properly configured to use them.

## Steps to Manage Multiple Users
1. Create an SSH-Key for the target username and email with:
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
2. Add the ssh key to the ssh agent with:
    ```bash
    ssh-add ~/.ssh/id_ed25519_ahmedyousrisobhi
    ```
3. Copy the public key with:
    ```bash
    cat ~/.ssh/id_ed25519_ahmedyousrisobhi.pub
    ```
4. Add the ssh to the config file; This lets Git know which key to use per account:
    ```bash
    # GitHub account: AhmedYousriSobhi
    Host github.com-ahmedyousrisobhi
        HostName github.com
        User git
        IdentityFile ~/.ssh/id_ed25519_ahmedyousrisobhi
        IdentitiesOnly yes
    ```
5. Change your Git remote to use this Host with:
    ```bash
    git remote set-url origin git@github.com-ahmedyousrisobhi:ahmedyousrisobhi/<repo-name>.git
    ```
    - To validate using: git remote -v

- To validate the connection, use:
    ```bash
    ssh -T git@github.com-ahmedyousrisobhi

    # Expected output: Hi ahmedyousrisobhi! You've successfully authenticated, but GitHub does not provide shell access.
    # This confirms your SSH key is correctly mapped to that GitHub user.
    ```
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

## Classic GitHub Workflow (Fork -> Modify -> Pull Request -> Merge)
Role|Repo|Description
|-|-|-|
Repo A|github.com/original-owner/projectA|The original repository (upstream).
Repo B|github.com/your-username/projectA|Your **fork** -- a full copy of the Repo A under your account.

### Step-1: Fork
- Click Fork on github to fork Repo A into repo B
    ```css
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
    ```css
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
```css
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

## Handy Commands
- Visualize git branches, use:
    ```bash
    git log --oneline --graph --all --decorate
    ```
- Reset a repo from the origin branch, use:
    ```bash
    git reset --hard origin/<branch-name>
    ```

## To be Cont....