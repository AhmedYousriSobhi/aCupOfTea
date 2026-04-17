# 101 - Singularity

# Table of Content
- [101 - Singularity](#101---singularity)
- [Table of Content](#table-of-content)
- [1- Intro](#1--intro)
- [2- Installation](#2--installation)
- [3- Simple test - Docker alpine](#3--simple-test---docker-alpine)
- [4- Build sif for Adder App](#4--build-sif-for-adder-app)
- [5- More Deeper Singularity Tech](#5--more-deeper-singularity-tech)
  - [5.1- Two Ways to Build a Container](#51--two-ways-to-build-a-container)
  - [5.2- Converting Images from One Format to Another](#52--converting-images-from-one-format-to-another)
  - [5.3- Notice: Size Difference between \[SIF, Sandbox\] Formats](#53--notice-size-difference-between-sif-sandbox-formats)
  - [5.4- Immutable Images Modification?](#54--immutable-images-modification)
  - [5.5- Inspect Definition File of a Container](#55--inspect-definition-file-of-a-container)
  - [5.6- Running Container from Docker File](#56--running-container-from-docker-file)
  - [5.7- singularity.conf file](#57--singularityconf-file)
  - [5.8- System Bind](#58--system-bind)
    - [--mount](#--mount)
    - [SINGULARITY\_BIND](#singularity_bind)
  - [5.9- Variable in .def File](#59--variable-in-def-file)
    - [Setting Default Variables' Values](#setting-default-variables-values)
    - [Assign build-time Variables' Values](#assign-build-time-variables-values)
- [6- Tips, Notes \& Troubleshooting](#6--tips-notes--troubleshooting)
- [7- Apptainer](#7--apptainer)
- [References](#references)

# 1- Intro
Singularity is a rootless container solution, which means that we can bring up a container as user on a system, and the container process retains that user identity and cannot be used to gain additional privileges on the system.

Singularity uses image format called *Singularity Image Format* "SIF". This format is unique for only Singularity.

Singularity contains the ecosystem to integrate with other containers format like Docker.

Shared Working directory!
> It's also interesting to note that the current working directory within this container is the same as the current working directory outside the container on my host; This is possible because singularity mounts several directories from your host environment like /home into the container file by default; This gives the illusion of simply swapping the user space of your linux distrubtion while keeping all of your user data intact; this allows your containerized applications to read and write data within user owned locations just like they are being run natively on the host

A great 5-mins intro tutorial illustrated by CtrlQ channel on youtube, found [here](https://www.youtube.com/watch?v=UbxCwcreJqU&embeds_referring_euri=https%3A%2F%2Fapptainer.org%2F&source_ve_path=Mjg2NjY&feature=emb_logo).

# 2- Installation
Follow the steps in the INSTALL markdown file on [Singularity' Github](https://github.com/sylabs/singularity/blob/main/INSTALL.md).

when executing the ./mconfig to make the configuration file, some packages were not installed, so this error arise;
```bash
fuse / fuse3 (libfuse / libfuse3) headers are required to build squashfuse.
```

To solve this we need to install both libraries;
```bash
sudo yum install fuse-devel fuse3-devel
```
    - Note this also works with 'dnf'

# 3- Simple test - Docker alpine
To test, you can run a simple container of docker image for linux alpine
```bash
singularity shell docker://alpine

# will be inside the shell of linux alpine
# to check os
cat /etc/os-release
# The output should be linux alpine.
```
What is Alpine Linux?
> Alpine Linux is a security-focused, lightweight Linux distribution designed for power users who prioritize security, simplicity, and efficiency.

Why used with containers?
> Alpine's primary feature is its small size, which enables it to start quickly and run in environments very low in memory and storage, such as containers or embedded devices.
 
# 4- Build sif for Adder App
The script is provided in seperate file, go check it.

To create a go module, follow along with this tutorial from [go.dev docs](https://go.dev/doc/tutorial/create-module).

To start your module, first use go mod init command:
```bash
go mod init adder
# go: creating new go.mod: module adder
```
According to the docs:
> The go mod init command creates a go.mod file to track your code's dependencies. So far, the file includes only the name of your module and the Go version your code supports. But as you add dependencies, the go.mod file will list the versions your code depends on. This keeps builds reproducible and gives you direct control over which module versions to use. 

To test adder.go locally:
```bash
go run adder.go 5 10
# output: Result: 15
```

To build the app:
```bash
singularity build --fakeroot adder.sif adder.def
```

--fakeroot: 
> This allows us to build our container as a normal user without any elevated privileges. If you wanted to omit this flag you would need to use sudo before running singularity in order to have elevated privileges on your system.

> Doing this allows you to pretend to be the root user inside of your container without actually granting singularity elevated privilleges on host system.

![adder.sig](https://i.postimg.cc/L6nF9WvG/Screenshot-from-2024-02-18-14-09-28.png)
*Building Sif container for app adder*

To run the app:
```bash
singularity run adder.sif 5 10
```

# 5- More Deeper Singularity Tech
Now we have our first impression of using Singularity, let's go deeper and understand more.
## 5.1- Two Ways to Build a Container
||Sandbox|Image|
|-|-|-|
|Details|"Which is really just a directory"!! Singularity support create a directory with the entire OS and some Singularity metadata in your current working directory.| "Immutable Images"!! we can build an image where the container encapsulates everything that cannot be modified, so our developing environment becomes eternal.
Benefits|During testing and debugging you may want an image format that is writable, you can also use *shell*, *exec* & *run* commands|This ensures reproducible and verifiable images.
|Code|singularity build --fakeroot adder.sif adder.def|singularity build --fakeroot --sandbox adder_sandbox/ adder.def

![sandbox image format](https://i.postimg.cc/FK6XL5pM/Screenshot-from-2024-02-18-15-13-19.png)
*Sandbox format is a directory with 21 files included*

Check Singularity docs for [Sandbox Directories](https://docs.sylabs.io/guides/3.5/user-guide/quick_start.html#sandbox-directories) sections.

## 5.2- Converting Images from One Format to Another
Using the *build* command, you can build a container from an existing container.

```bash
# Convert from a sandbox format to sif image immutable format.
singularity build new-sif sandbox
```

Note:
> Becarefull of breaking the reproducibility if you have altered your sandbox outside of the context of definition file, so you are advised to exercise care.

## 5.3- Notice: Size Difference between [SIF, Sandbox] Formats
As notices in the image above showing the size of sif file format is much larger than the sandbox directory format!!

This should come from many different reasons:
- As SIF images typically include not only the filesystem layers but also metadata, including environment variables, labels, and other information associated with the container.
- Unlike Sandbox, refers to the directory-based container image format used Singularity, where the container image is represented as a directory containing the filesystem layers and associated metadate. So Singularity accesses the env variables, labels and other info needed directoly from local filesystem.

Let's see the size from converting sandbox format to SIF format:
![size](https://i.postimg.cc/RVn57Phk/Screenshot-from-2024-02-18-15-28-25.png)
*Converting from sandbox to sif format, and check the size*

## 5.4- Immutable Images Modification?
To modify the content of an image:
1. it should first be in the *sandbox* format.
2. Add the option *--writeable* to allow to modify the container, and the changes will actully be saved into the container and will presist across uses.
3. In case of root privillege required to install some apps, you will have to enter the container with *sudo* command from the start.
```bash
singularity shell --writable <sandbox>

sudo singularity shell --writable <sandbox>
```
## 5.5- Inspect Definition File of a Container
To inspect the definition file that was used to build the image [both sif & sandbox] formats;
```bash
singularity inspect --deffile adder.sig
```

![inspect def file](https://i.postimg.cc/fRwZjcdD/Screenshot-from-2024-02-18-16-12-46.png)
*Inspect definition file of a Singularity image*

## 5.6- Running Container from Docker File
You can directly [build a container from a DockerFile](https://docs.sylabs.io/guides/latest/user-guide/build_a_container.html#building-from-dockerfiles), with Singilarity starting version 4.1, using the [OCI Runtime Support](https://docs.sylabs.io/guides/latest/user-guide/oci_runtime.html#oci-runtime).
```bash
singularity build --oci adder.oci.sif ./Dockerfile
```
Notes:
- *--oci* Mode, does not mount a user's $HOME (similar to *--compat* in native mode); when tested it, there are no any mounted directories, so I have to do it manually using *--bind* .
    ```bash
    singularity exec --oci adder.oci.sif ls
    # no output
    ```
- To solve this, instead of using --bind, we could simply use *--no-compat* option according to the [docs](https://docs.sylabs.io/guides/latest/user-guide/oci_runtime.html#running-existing-non-oci-singularity-containers).
    ```bash
    singularity exec --oci --no-compat adder.oci.sif ls
    # output a directory contents
    ```

Older version, there are two option so far I know about:
1. Convert DockerFile to Definition file either manually, third-party tool, or even ChatGPT. Then build you container image normally.
2. Build a Docker image, then upload to the Docker server, then build the Singularity image from Docker image.
3. Build from Dockerfiles as regular (non-OCI-SIF) build

## 5.7- singularity.conf file
This file is used to edit all the configuration of singularity, could be found in directory **"/singularity/builddir/singularity.conf"**.

You can edit the mount directories when a singularity container is running (mainly the system administrator task).

For more info in the [docs: The Singularity Config File](https://singularity-admindoc.readthedocs.io/en/latest/the_singularity_config_file.html#the-singularity-config-file) 

Also it could edit the config from the command line using the [*singularity config* command](https://docs.sylabs.io/guides/latest/user-guide/cli/singularity_config.html).

## 5.8- System Bind
For [Bind Paths and Mounts](https://docs.sylabs.io/guides/latest/user-guide/bind_paths_and_mounts.html#bind-paths-and-mounts), we can control to un/mount a directory to the container using *--no-mount*/*--bind*, regarding the configuration defined in *singularity.confg* file.

Example to unmount /home directory from the container:
```bash
singularity shell --no-home adder.sif

# Equivalent to
singularity shell --no-mount home adder.sif
```
![unmount home](https://i.postimg.cc/wjwCGsND/Screenshot-from-2024-02-18-20-59-27.png)
*Unmount $HOME directory from Image*

```bash
# We only need to check if it's work, so we need to execute a simple command in the container, not running it all.

# General format: singularity exec --bind <target_dirs_to_mount, seperated_by_comma>:<target mount point> <Container.sif> Command to execute
singularity exec --bind ~/source:/mnt adder.sif ls /mnt

singularity exec adder.sif ls /mnt
```
![bind option](https://i.postimg.cc/HWFtWWwX/Screenshot-from-2024-02-18-20-40-44.png)
*Bind directory into /mnt directory*

### --mount
Starting from v3.9, they added [flag --mount](https://docs.sylabs.io/guides/latest/user-guide/bind_paths_and_mounts.html#mount-examples) with the following format:
```bash
--mount type=bind,src=<source>,dst=<destination>[,<option>]...
```
This could be useful in case of a path containing ":", which is not possible with --bind
```bash
# Mount a path containing ':' (not possible with --bind)
$ singularity run \
    --mount type=bind,src=/my:path,dst=/mnt \
    mycontainer.sif

# Mount a path containing a ','
$ singularity run \
    --mount type=bind,"src=/comma,dir",dst=/mnt \
    mycontainer.sif
```

### SINGULARITY_BIND
In case you have lots of directories we need to bind into our container, it's better and more advanced to use the Singularity variable "*SINGULARITY_BIND*", and set its value to all directories you want to bind.
```bash
# Outside the container
export SINGULARITY_BIND="${WORKDIR}/run:/run,${WORKDIR}/file:/file"
```
- Yes you could use and host environment variables, as you are executing this command in the local host not container.

According to the [documentation](https://docs.sylabs.io/guides/latest/user-guide/build_env.html#environment-variables):
> If a flag is represented by both a CLI option and an environment variable, and both are set, the CLI option will take precedence. This is true for all environment variables with the exception of SINGULARITY_BIND and SINGULARITY_BINDPATH, which are combined with the --bind option / argument pair, if both are present.

## 5.9- Variable in .def File
According to ["Templating: How to Pass Values into Definition file"](https://docs.sylabs.io/guides/latest/user-guide/definition_files.html#templating-how-to-pass-values-into-definition-files) docs, Variables could be supported in def file using the {{ placeholder }}, and define the variables in *%arguments* section in def file.

Let's take an example of def file:
```def
Bootstrap: docker
From: rockylinux:9.3

%startscript
        export PATH={{ arg4 }}:$PATH

%runscript
        echo "here is arg1:" {{ arg1 }}
        echo "here is arg2:" {{ arg2 }}
        echo "here is arg3:" {{ arg3 }}
        echo "here is my local host PATH:" {{ arg4 }}
        echo "here is path inside container:" {{ $PATH }}

%arguments
        arg1="ARGUMENT_1st"
        arg2="ARGUMETN_2nd"
        arg3=$AHMED
        arg4=$PATH
```

Let's build this image:
```bash
singularity build --fakeroot rocky9.3.sif rocky9.3.def
```

Running this container results in:
```bash
here is arg1: ARGUMENT_1st
here is arg2: ARGUMETN_2nd
here is arg3: he_is_ME
here is my local host PATH: /usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin
here is path inside container: {{ /usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin }}
```

### Setting Default Variables' Values
Using the 
### Assign build-time Variables' Values
Singularity gives you the capability to assign a new value to overwrite the default value defined in .def file during the build process of the container image.

This can be achieved by the option *--build-arg* :
```bash
singularity build --fakeroot --build-arg arg4=<SOME_VALUE> rocky9.3.sif rocky9.3.def
```

You can set any value you want even if it's a environment variable of the local host (e.g. $PATH, etc...). 

![--build-arg](https://i.postimg.cc/RVsyfhxJ/Screenshot-from-2024-02-29-13-18-30.png)

# 6- Tips, Notes & Troubleshooting
|Tip, Note, Troubleshoot|Details|
|-|-|
Troubleshoot| If you receive warnings from the Perl language about the locale being incorrect, you can usually fix them with export LC_ALL=C
Note| Starting with v3.4.0, the encrypted containers became a feature, and the decryption occurs at runtime completely within kernel space, so there is no intermediate, decrypted version of the container on disk. Check [Encrypted Containers](https://docs.sylabs.io/guides/latest/user-guide/encryption.html#encryption).
Tip| It is recommended by sylabs (Singularity creators), and Dockers to not build containers using the root user, in this [blog](https://medium.com/sylabs/a-note-on-cve-2019-14271-running-untrusted-containers-as-root-is-still-a-bad-idea-245d227d4e02) talking about the Common Vulnerabilities and Exposures [CVE-2019-5736](https://nvd.nist.gov/vuln/detail/CVE-2019-5736), and how this motivate to build Singularity.</br> This vulnerability is categorized as a "container escape" vulnerability, meaning an attacker who exploits it could potentially escape from a container and gain root access to the host system by overwriting the host runc binary, so consequently obtain host root access.
Tip|From the [docs](https://docs.sylabs.io/guides/latest/user-guide/bind_paths_and_mounts.html#using-bind-or-mount-with-the-writable-flag), binding paths to non-existent points within the container can result in unexpected behavior when used in conjunction with the --writable flag, and is therefore disallowed. If you need to specify bind paths in combination with the --writable flag, please ensure that the appropriate bind points exist within the container. If they do not already exist, it will be necessary to modify the container and create them.
Tip| You can export $SINGULARITY_BIND as env variable with all directories you want to mount inside your container.
Tip| Not highly recommended to build a OCI-SIF container from Dockerfile using --oci, It may break any runscripts or conda environments in the container!. That's because the Singularity is not fully optimized for OCI standard container format yet. "They basically don't speek the same language!!".
Tip|Try to add more info/description for def file, to be documented, using sections {%labels, %help}, so you can easily use commands {inspect, run-help} to get that documentation. "A good container tells the user how to interact with it"</br>![image](https://i.postimg.cc/52gzd9Rg/Screenshot-from-2024-02-29-09-37-09.png)

# 7- Apptainer
update: The new version of singularity is called [apptainer](https://apptainer.org/) one can install that easily on rockylinux.

# References
- Official Docs, located [here](https://docs.sylabs.io/guides/latest/user-guide/index.html).
- Apptainer (formerly Singularity), located [here](https://apptainer.org/).
- Tutorial of Singularity by hackmd, located [here](https://hackmd.io/@yihu3230/By1ipSiWF).
- Singularity Tutorial github, located [here](https://singularity-tutorial.github.io/03-building/).
- Usefull create a systemd file for container in local machine, located [here](https://ciq.com/blog/managing-containerized-services-with-apptainer-and-systemd/).
