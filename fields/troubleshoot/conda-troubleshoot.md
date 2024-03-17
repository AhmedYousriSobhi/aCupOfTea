# 102- Conda Troubleshooting

# Table of Content
- [102- Conda Troubleshooting](#102--conda-troubleshooting)
- [Table of Content](#table-of-content)
- [CondaError: Run 'conda init' before 'conda activate'](#condaerror-run-conda-init-before-conda-activate)
  - [Scenario](#scenario)
  - [Troubleshoot](#troubleshoot)
- [conda-libmambda-solver Point Error After conda Update](#conda-libmambda-solver-point-error-after-conda-update)
  - [Scenario](#scenario-1)
  - [Root Cause](#root-cause)
  - [Troubleshoot](#troubleshoot-1)
  - [Explanation](#explanation)
- [Tips](#tips)

# CondaError: Run 'conda init' before 'conda activate'
## Scenario
When running the command *"conda activate"*, this error was recieved telling me to run *conda init* first, which means that conda is not properly configured.

## Troubleshoot
First solution is to make sure that everything is configured correctly in the *.bashrc* & *.zshrc* shell files, by running the following commands:
```bash
conda init bash
conda init zsh

# In case conda is un defined command, 
# PATH-to/miniconda/miniconda-3/bin/conda init bash
# PATH-to/miniconda/miniconda-3/bin/conda init zsh
```

If the problem still exists, so let's continue.

The step worked for me is to run:
```bash
source activate base
```

Then reboot the machine.

This will make you login into base environment, but to check if it solved, run:
```bash
conda deactivate
# to logout conda base environment

conda activate
# it should login to base environment automatically
```

# conda-libmambda-solver Point Error After conda Update
## Scenario
Trying to update conda using *conda update conda*, then everything should be update sucessufly, but this error shows up when using *conda* command:
```bash
Error while loading conda entry point: conda-libmamba-solver (libarchive.so.19: cannot open shared object file: No such file or directory)
```

## Root Cause
There is a problem in the libmamba solver due to conflict in the libarchive package due to being installed from different channels.
  
## Troubleshoot
1. Remove .condarc file created.
2. Change the solver to *classic*, to do so from this [issue](https://github.com/conda/conda/issues/12868) in github:
    ```bash
    conda config --set solver classic
    ```
3. Let's install libarchieve one more time but in a clean way:
    ```bash
    conda install -n base libarchive -c main --force-reinstall
    ```
    - The output was: 
      ```
      Error while loading conda entry point: conda-libmamba-solver (libarchive.so.19: cannot open shared object file: No such file or directory)
      
      CondaValueError: You have chosen a non-default solver backend (libmamba) but it was not recognized. Choose one of: classic
      ```
4. Return the solver again to libmamba
    ```bash
    conda config --set solver libmamba
    ```

## Explanation
The command conda config "*--set solver classic*" is used to configure the solver behavior in Conda.

In Conda, the solver is responsible for resolving package dependencies when creating or updating environments. The solver determines which versions of packages to install, considering constraints such as dependencies, conflicts, and package versions specified in the environment configuration.

The classic solver is the default solver used in older versions of Conda. It uses an algorithm known as the "legacy" solver, which has been in use for many years. This solver is generally slower and less efficient compared to the newer, default mamba solver.
 
By running conda config "*--set solver classic*", you're instructing Conda to use the classic solver instead of the default mamba solver for environment resolution. This configuration might be necessary in certain cases, such as when compatibility issues arise with the mamba solver or when you prefer the behavior of the classic solver.

It's worth noting that unless you have specific reasons for doing so, it's generally recommended to stick with the default mamba solver, as it typically provides faster and more efficient environment resolution compared to the classic solver.


A gif from [libmamba](https://www.anaconda.com/blog/a-faster-conda-for-a-growing-community) in Anaconda docs
![libmamba speed test vs classic](https://www.anaconda.com/wp-content/uploads/2023/02/libmamba_classic_comparison.gif)

User guide for [***conda-libmamba-solver***](https://conda.github.io/conda-libmamba-solver/user-guide/).

# Tips
- The command *type* command_name always tells you exactly what is being run. This is better than which command_name, which ignores hashed commands and searches the PATH directly. 
  ```bash
  type install

  # install is /bin/install
  ```
- For every version of python required, create a seperate conda environment for it.
- Use [Anaconda.org](https://anaconda.org/), to search for specific package using the web interface.
