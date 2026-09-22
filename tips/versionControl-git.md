# Tips - Version Control - Git

## Table of Contents
- [Tips - Version Control - Git](#tips---version-control---git)
  - [Table of Contents](#table-of-contents)
  - [Remove Commit from a Repo](#remove-commit-from-a-repo)
  - [.gitignore](#gitignore)

## Remove Commit from a Repo
- Our case is that, we want to remove an old commit from the repo, but to keep the main commit persists.
1. Get the git log using:
    ```bash
    git log --oneline

    # Output Example:
    abc1234 (HEAD -> main)   Your latest commit
    def5678                   Commit you want to delete
    ```
2. Use an interactive rebase to edit history. You want to rebase to two commits back (to edit the one before the latest):
    ```bash
    git rebase -i HEAD~2
    ```
3. In the interactive editor, it should be something like:
    ```bash
    pick def5678 Commit to delete
    pick abc1234 Your latest commit
    ```
    - Change it to:
        ```bash
        drop def5678 Commit to delete
        pick abc1234 Your latest commit
    ```
4. Force-push the new history to GitHub
    ```bash
    git push origin main --force
    ```
- Optional Backup Before Starting:
    ```bash
    git checkout -b backup-before-rebase
    git push origin backup-before-rebase
    ```

## .gitignore
A .gitignore should usually ignore:
- generated artifacts,
- caches,
- secrets,
- large binaries,
- environment-specific files.

An example for `.gitignore` file content:</br>
```bash
# =========================
# Python cache / bytecode
# =========================
__pycache__/
*.py[cod]
*$py.class

# =========================
# Virtual environments
# =========================
.env
.venv
venv/
ENV/
env/

# =========================
# Conda / Mamba environments
# =========================
conda-meta/
*.conda
*.tar.bz2

# =========================
# Jupyter Notebook
# =========================
.ipynb_checkpoints/

# =========================
# Logs
# =========================
*.log
logs/

# =========================
# Build / distribution
# =========================
build/
dist/
*.egg-info/
.eggs/

# =========================
# PyTorch model artifacts
# =========================
*.pth
*.pt
*.ckpt
checkpoints/
weights/

# =========================
# Dataset / generated data
# =========================
data/
datasets/
outputs/
results/
predictions/

# =========================
# IDE / Editor
# =========================
.vscode/
.idea/
*.swp
*.swo

# =========================
# OS files
# =========================
.DS_Store
Thumbs.db

# =========================
# Testing / coverage
# =========================
.pytest_cache/
.coverage
htmlcov/

# =========================
# Temporary files
# =========================
tmp/
temp/
*.tmp

# =========================
# Environment variables
# =========================
.env.*
!.env.example

# =========================
# FastAPI / Uvicorn
# =========================
*.pid

# =========================
# Mypy / Ruff / Pyright
# =========================
.mypy_cache/
.ruff_cache/
.pyright/

# =========================
# Ignore local secrets
# =========================
secrets/
credentials/
*.pem
*.key
```
