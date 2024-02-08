# Packages - Conda

# Table of Content
- [Packages - Conda](#packages---conda)
- [Table of Content](#table-of-content)
- [1- Conda Environment](#1--conda-environment)
  - [1.1- What is Conda?](#11--what-is-conda)
  - [1.2- What is a **conda environment**?](#12--what-is-a-conda-environment)
  - [1.3- Base Environment](#13--base-environment)
  - [1.4- Create a New Environment](#14--create-a-new-environment)
  - [1.5- Check Envrionment List](#15--check-envrionment-list)
  - [1.5- Exit an Environment](#15--exit-an-environment)
  - [1.6- Question](#16--question)
  - [1.7- Remove an Environment](#17--remove-an-environment)
  - [1.8- A Note About Executing program](#18--a-note-about-executing-program)
- [2- Conda Channels](#2--conda-channels)
  - [2.1- Specifying Channels When Installing Packages](#21--specifying-channels-when-installing-packages)
  - [2.2- Conda .condarc file!](#22--conda-condarc-file)
    - [2.2.1- Where conda command search for .condarc?](#221--where-conda-command-search-for-condarc)
    - [2.2.2- Want to Configure Channels and Their Priority for a Single Env?](#222--want-to-configure-channels-and-their-priority-for-a-single-env)
  - [2.3- Managing Channels](#23--managing-channels)
- [3- Managing Packages](#3--managing-packages)
  - [3.1- Searching for Pacakges](#31--searching-for-pacakges)
  - [3.2- Installing Packages](#32--installing-packages)
    - [3.2.1- Install Packages on Created Environment](#321--install-packages-on-created-environment)
    - [3.2.2- Install Packages While Creating Environment](#322--install-packages-while-creating-environment)
  - [3.3- Update Conda](#33--update-conda)
- [Troubleshoot](#troubleshoot)
  - [conda-libmambda-solver Point Error After conda Update](#conda-libmambda-solver-point-error-after-conda-update)
- [Reference](#reference)

# 1- Conda Environment
## 1.1- What is Conda?
> The package and environment manager program bundled with Anaconda that installs and updates conda packages and their dependencies. Conda also lets you easily switch between conda environments on your local computer.

*Fetched from the documentation on [Glossary](https://conda.io/projects/conda/en/latest/glossary.html#conda)*.

## 1.2- What is a **conda environment**? 
> A folder or directory that contains a specific collection of conda packages and their dependencies, so they can be maintained and run separately without interference from each other.

*Fetched from the documentation on [Glossary](https://conda.io/projects/conda/en/latest/glossary.html#conda-environment)*.
## 1.3- Base Environment
It is the 'base' environment of conda, where everything gets start. We usually do not install a lot of complicated packages in this environment.

The most important thing we do in the base environment, is that we create other environments for different projects based on the task required, so we can install all required necessary packages and libraries.

## 1.4- Create a New Environment
The very simplest way to create an environment is through:
```bash
# Create the conda environment
# conda create -n <env-name>
conda create -n cupoftea_env

# Activate the environment to start using it
conda activate cupoftea_env
```
That's great, we have created our "cupoftea_env" environment.

> **Note**: Try to give your env a proper name, that describe what is used for, even this name is package related name, or project specific name.

> **Example**: if you have an env that is mainly for python v2.7 related projects, we could name it "python-v2.7"

> **Tip**: Try to know your working organization naming conventional format, and try to follow along with it.

## 1.5- Check Envrionment List
Wait!! you forgot what was the name of your created environment?! HOW COULD YOU? but it is not a big deal yes, we simply can list all the available environments created in conda using:
```bash
conda info --envs
```
- You will have an asterisk next to the one we are currently in.

The output should be like this:
```bash
conda environments:

   base           /home/username/Anaconda3
   myenvironment   * /home/username/Anaconda3/envs/myenvironment
```

## 1.5- Exit an Environment
and ofcourse, if you need to exit it, you can simply using the command "conda deactivate"
```bash
conda deactivate
```
- This will deactivate the current used environment, and gets you back to the "base" environmemt.
- The environment name is no longer shown in your prompt, and the asterisk(*) returns to 'base'

## 1.6- Question
Do you have to deactivate your current env to actiave other env? 

Actually, you don't have to do this, and simply "activate" your next target env to work on.

```bash
# Go back to 'base' env
conda activate
python --version

conda activate cupoftea_env
python --version
```
> **Note**: Yes you will get an error running the previous code, telling you "there is no python installed in cupoftea_env". That's because, we did not tell conda to install a python packages in our cupoftea_env during creating it.

## 1.7- Remove an Environment
```bash
# First you have to deactivate the environment
conda deactivate

# Remove the env
# conda create -n <env-name>
conda env remove -n cupoftea_env
```

## 1.8- A Note About Executing program
Even when an environment is deactivated, you can still execute programs in that environment by specifying their paths directly, as in *~/anaconda/envs/envname/bin/program_name*. When an environment is activated, you can execute the program in that environment with just *program_name*.

# 2- Conda Channels
What are Channels?! According to the [documentation](https://docs.conda.io/projects/conda/en/latest/user-guide/concepts/channels.html):
> Channels are the locations of the repositories where packages are stored. They serve as the base for hosting and managing packages.

So basically, Conda packages are downloaded from URLs to directories where the conda packages located, which are called "**remote Channels**".

So what is happening? when we want to search for a package to download, the *conda* command searches a set of channels. The [default channel](https://repo.anaconda.com/pkgs/) is the first one conda uses as its name describes. But this channel may require a paid license.

A free one you ask?! Sure, the [**conda-forge**](https://conda-forge.org/docs/index.html) channel is free for all to use.

This is not all!! you can also modify which remote channels are automatically searched;
- This is very usefull actually!! this feature is beneficial when maintaining a private or internal channel, try to visit ["*modify your channel lists*"](https://docs.conda.io/projects/conda/en/latest/user-guide/configuration/settings.html#config-channels) docs to have more info.

## 2.1- Specifying Channels When Installing Packages
- From the command line use *--channel*
  ```bash
  conda install scipy --channel conda-forge
  ```
- Specify multiple channels; note that priority decreases from left to right.
  ```bash
  conda install scipy --channel conda-forge --channel bioconda
  ```

A big note here!!
> The --channel parameter only make a pirority for the search, so if your package is not located in the channel you defined using --channel, it will automatically continue search for your package in all listed packates in **.condarc** file.
>
> Here "--override-channels" comes to the rescue.

- From the command line use *--override-channels* to only search  the specified channel(s) rather than any channels confgiured in *.condarc*. This also ignored conda's default channels
  ```bash
  conda search scipy --channel file:/<path to>/local-channel --override-channels
  ```
  
## 2.2- Conda .condarc file!
What is ***.condarc***? it is the file where are conda channels are configured.

Pronounced "Conda r-c" which stands for **The Conda Runtime Configuration file**, an optional .yaml file that allows you to configure many aspects of conda, such as which channels it searches for packages, proxy settings, and environment directories.

Refer to ["*Using the .condarc conda configuration file*"](https://conda.io/projects/conda/en/latest/user-guide/configuration/use-condarc.html) docs.

**Note**: the .condarc file is not included by default, but it is automatically created in your home directory the first time you run the ***conda config*** command.
```bash
# To create .condarc file.
conda config
```

- To list all available channels in conda's .condarc:
  ```bash
  conda config --show channels

  # The output should be like:
  # channels:
  #   - defaults
  ```
- To obtain information from .conda file
  ```bash
  # To get all keys and their values
  conda config --get

  # To get the value of a specific key, such as channels
  conda config --get channels

  # To show all the configuration file sources and their contents
  conda config --show-sources
  ```
- To edit the configuration file, there is two methods;
  - 1- Using the command line
    ```bash
    # Adding conda-forge channel to .condarc
    conda config --add channels conda-forge

    # Removing conda-forge channel to .condarc
    conda config --remove channels conda-forge

    # To remove a key, such as channels, and all of its values
    conda config --remove-key channels

    # To set configuration options using the "--set" key
    conda config --set auto_update_conda False
    ```
- **Note**: The order you add new channels is considered as priority from lowest to highest priority, so the recent added channel has the highest priority, according to [**bioconda**](https://bioconda.github.io/#usage), the order to add channels is important to avoid probles with solving dependencies.
   
- For all list of "conda config" parameters, check the [docs](https://conda.io/projects/conda/en/latest/commands/config.html).
  - 2- vim the file and write it manually using YAML syntax. Here is a [sample of .condarc file](https://conda.io/projects/conda/en/latest/user-guide/configuration/use-condarc.html#sample-condarc) from the documents, which you could simply download and edit it.
    ```yml
    # This is a sample .condarc file.
    # It adds the r Anaconda.org channel and enables
    # the show_channel_urls option.

    # channel locations. These override conda defaults, i.e., conda will
    # search *only* the channels listed here, in the order given.
    # Use "defaults" to automatically include all default channels.
    # Non-url channels will be interpreted as Anaconda.org usernames
    # (this can be changed by modifying the channel_alias key; see below).
    # The default is just 'defaults'.
    channels:
      - r
      - defaults

    # Show channel URLs when displaying what is going to be downloaded
    # and in 'conda list'. The default is False.
    show_channel_urls: True

    # For more information about this file see:
    # https://conda.io/docs/user-guide/configuration/use-condarc.html
    ```
### 2.2.1- Where conda command search for .condarc?
The conda looks in defined locations for .condarc file.

Refer to the [docs](https://conda.io/projects/conda/en/latest/user-guide/configuration/use-condarc.html#searching-for-condarc) for info.

### 2.2.2- Want to Configure Channels and Their Priority for a Single Env?
A simple answer: Make a .condarc file in the **root directory of that environment**.

So this [docs](https://conda.io/projects/conda/en/latest/user-guide/configuration/settings.html#config-channels) is a great place to start.

## 2.3- Managing Channels
For more details about how to manage the channels in conda, please refer to the [documentation](https://conda.io/projects/conda/en/latest/user-guide/tasks/manage-channels.html).


# 3- Managing Packages
Before diging into managing packages, we first need to give a hint about the available commands in Conda, which could be found in the [Commands docs](https://conda.io/projects/conda/en/latest/commands/index.html).

## 3.1- Searching for Pacakges
Hold your horses, before jumping into package installation, we should first make sure that the package is available in conda to be installed.

When searching for a package, we search in **Conda Channels**, what are these channels? please refer to [Conda Channels](#conda-channels) section above.

## 3.2- Installing Packages
That's what are created environments for, to install packages!!

We have two scenarios:
1. Installing packages on already created envrionments.
2. Installing packages along with creating the envrionment.
   
### 3.2.1- Install Packages on Created Environment
There are two ways to do so:

1.1. Via envrionment activation
```bash
conda activate cupoftea_env
conda install matplotlib
```

1.2 Via command line option
```bash
conda install --name cupoftea_env matplotlib
```

You can define the target specified package version, install multiple packages together, and specifying channels
```bash
# install scipy package version 0.15.0, and curl package
conda install scipy=0.15.0 curl conda-forge::numpy
```
- Tip: the documentation recommends that it is better to install multiple packages at once, so that all of the dependencies are installed at the same time.
- Tip: if you want to install a specific python version, it is best to use an environment with that version.
### 3.2.2- Install Packages While Creating Environment
Two methods actually!
1. While creating new environment using command line: *conda create -n <env-name>*
2. During [creating a project](https://conda.io/projects/conda/en/latest/user-guide/tasks/creating-projects.html), which will be configured through a YAML file.
    ```bash
    # To create new project env with its dependancies
    conda env create --file environment.yml

    # To update current project with new dependancies
    conda env update --file environment.yml
    ```
## 3.3- Update Conda
To update conda itself to the latest version use:
```bash
conda update conda
```

# Troubleshoot
## conda-libmambda-solver Point Error After conda Update
Scenario:
> Trying to update conda using *conda update conda*, then everything should be update sucessufly, but this error shows up when using *conda* command:
>
> Error while loading conda entry point: conda-libmamba-solver (libarchive.so.19: cannot open shared object file: No such file or directory)

Description:
- There is a problem in the libmamba solver due to conflict in the libarchive package due to being installed from different channels.
- 
Solution:
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
Explanation:
> The command conda config --set solver classic is used to configure the solver behavior in Conda.
>
> In Conda, the solver is responsible for resolving package dependencies when creating or updating environments. The solver determines which versions of packages to install, considering constraints such as dependencies, conflicts, and package versions specified in the environment configuration.
>
> The classic solver is the default solver used in older versions of Conda. It uses an algorithm known as the "legacy" solver, which has been in use for many years. This solver is generally slower and less efficient compared to the newer, default mamba solver.
> 
> By running conda config --set solver classic, you're instructing Conda to use the classic solver instead of the default mamba solver for environment resolution. This configuration might be necessary in certain cases, such as when compatibility issues arise with the mamba solver or when you prefer the behavior of the classic solver.
>
> It's worth noting that unless you have specific reasons for doing so, it's generally recommended to stick with the default mamba solver, as it typically provides faster and more efficient environment resolution compared to the classic solver.
>

A gif from [libmamba](https://www.anaconda.com/blog/a-faster-conda-for-a-growing-community) in Anaconda docs
![libmamba speed test vs classic](https://www.anaconda.com/wp-content/uploads/2023/02/libmamba_classic_comparison.gif)

User guide for [***conda-libmamba-solver***](https://conda.github.io/conda-libmamba-solver/user-guide/).

# Reference
- Conda documentation is a great getting-started source, located [here](https://conda.io/projects/conda/en/latest/user-guide/getting-started.html#managing-python).
- Tutorial "An introduction to Conda" from Happy Belly Bioinformatics could be found [here](https://astrobiomike.github.io/unix/conda-intro).
- Conda cheatsheet from the docs, found [here](https://conda.io/projects/conda/en/latest/_downloads/843d9e0198f2a193a3484886fa28163c/conda-cheatsheet.pdf).
- Conda troubleshooting from the docs, found [here](https://conda.io/projects/conda/en/latest/user-guide/troubleshooting.html).
- Conda basics course from Anaconda. found [here](https://learning.anaconda.cloud/conda-basics).
- **Bioconda** to install thousands of software packages related to biomedical research using the conda package manager, official docs found **here**.
- **Conda-Forge** channel which contains repositories of conda recipes and thus provbides conda packages, found [here](https://conda-forge.org/docs/index.html).
- Conda Recipes? checks for Anaconda learning Conda Essentials course, found [here](https://freelearning.anaconda.cloud/conda-essentials/75629).
- Conda Glossary for all keywords used, found [here](https://conda.io/projects/conda/en/latest/glossary.html).
