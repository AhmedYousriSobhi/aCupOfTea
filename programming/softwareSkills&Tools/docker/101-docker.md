# Software Skill: Docker
# 101 - Docker: Introduction to Docker

let's create a chapter to learn **Docker**. **Docker** is a popular containerization platform that allows you to package and run applications and their dependencies in isolated containers.

# Table of Content
- [Software Skill: Docker](#software-skill-docker)
- [101 - Docker: Introduction to Docker](#101---docker-introduction-to-docker)
- [Table of Content](#table-of-content)
- [Chapter Outline](#chapter-outline)
- [Section 1: Motivation and Objectives](#section-1-motivation-and-objectives)
  - [Motivation](#motivation)
  - [Challenges that need Solutions](#challenges-that-need-solutions)
  - [Objectives](#objectives)
  - [Workspace](#workspace)
    - [What is Containerization?](#what-is-containerization)
  - [Traditional Virtual Machines (VMs) vs. Containers](#traditional-virtual-machines-vms-vs-containers)
    - [Docker](#docker)
    - [Benefits of Docker](#benefits-of-docker)
    - [Example Usage](#example-usage)
    - [Key Features of Docker](#key-features-of-docker)
  - [KeyWords Term Definitions](#keywords-term-definitions)
- [Section: Docker Fundamentals](#section-docker-fundamentals)
  - [Info](#info)
  - [Commands Table](#commands-table)
  - [Key Concepts](#key-concepts)
  - [Docker Fundamental: Container Vs Image](#docker-fundamental-container-vs-image)
  - [When to Use Container \& Image](#when-to-use-container--image)
  - [Key Notes](#key-notes)
  - [Docker Container](#docker-container)
    - [Container LifeCycle](#container-lifecycle)
    - [Command: docker run](#command-docker-run)
  - [Docker Image](#docker-image)
    - [Command: docker pull](#command-docker-pull)
  - [Docker Registry](#docker-registry)
  - [Docker Client and Server](#docker-client-and-server)
    - [Command: docker --version and docker info](#command-docker---version-and-docker-info)
  - [Example Usage](#example-usage-1)
- [Section: Docker Installation](#section-docker-installation)
  - [Info](#info-1)
  - [Docker Installation on Linux](#docker-installation-on-linux)
  - [Docker Installation on Windows](#docker-installation-on-windows)
  - [Docker Installation on macOS](#docker-installation-on-macos)
  - [Key Features](#key-features)
  - [Example Usage](#example-usage-2)
  - [Docker Pull \& Run Images/Containers](#docker-pull--run-imagescontainers)
    - [Pulling Docker Images](#pulling-docker-images)
    - [Running Docker Containers](#running-docker-containers)
- [Section: Dockerfile and Building Images](#section-dockerfile-and-building-images)

# Chapter Outline
|Outline|Details|
|-|-|
Motivation|Explain the need for containerization and the challenges it addresses.</br>Introduce **Docker** as a leading containerization solution.</br>Highlight the benefits of using **Docker** for application deployment.
Objectives|Define the core concepts of **Docker**, including containers, images, and **Docker**file.</br>Provide an overview of **Docker**'s architecture and components.</br>Learn how to install **Docker** on a Linux system.
**Docker** Fundamentals|Explain the concept of containerization.</br>Understand the differences between containers and virtual machines.</br>Introduce **Docker** Hub as a repository for **Docker** images.
**Docker** Installation|Provide step-by-step instructions for installing **Docker** on various Linux distributions.</br>Explain how to verify the installation and check the **Docker** version.
**Docker** Images and Containers|Define **Docker** images and containers.</br>Explain how to pull and run **Docker** images.</br>Illustrate the life cycle of a **Docker** container.
**Dockerfile** and Building Images|Introduce **Docker**files as a means to define container configurations.</br>Explain the structure of **Docker**files and their instructions.</br>Walk through the process of building custom **Docker** images.
Container Networking and Storage|Describe how **Docker** handles networking for containers.</br>Explore container storage and data management.</br>Discuss container orchestration and **Docker** Compose.
**Docker** Security and Best Practices|Address security concerns in containerized environments.</br>Share best practices for securing **Docker** containers and images.</br>Discuss user and group management within containers.
**Docker** in Real-World Scenarios|Provide examples of how **Docker** is used in various industries.</br>Showcase use cases for deploying applications in **Docker** containers.
**Docker** Ecosystem|Explore **Docker** Compose for defining multi-container applications.</br>Introduce **Docker** Swarm for container orchestration.</br>Mention Kubernetes as a popular container orchestration platform.
Conclusion|Summarize key takeaways from the chapter.</br>Encourage further exploration and hands-on practice with **Docker**.</br>Provide additional resources for learning **Docker**.
Exercises and Projects|Offer hands-on exercises and mini-projects to reinforce learning.

This chapter will provide an introduction to **Docker**, covering its fundamental concepts, installation, usage, security, and real-world applications. It will equip you with the knowledge and skills to start working with **Docker** containers effectively.

# Section 1: Motivation and Objectives
## Motivation
In this section, we'll explore the motivation behind containerization and why **Docker** has become a popular choice for deploying applications. Understanding the challenges it addresses will help you appreciate the benefits of using ****Docker****.

## Challenges that need Solutions
Containerization emerged as a solution to the following challenges:
|Solution|Details|
|-|-|
Consistency| Ensuring that an application runs consistently across different environments, from development to production.
Isolation| Providing a way to isolate applications and their dependencies to prevent conflicts.
Portability| Allowing applications to run on any system without modification, promoting compatibility.
Resource Efficiency| Efficiently using system resources while keeping applications separate.
Scalability| Enabling easy scaling of applications and services as needed.

## Objectives
By the end of this section, you should:
- Understand the concept of containerization and its role in solving software deployment challenges.
- Comprehend the fundamental differences between traditional VMs and containers.
- Recognize **Docker** as a leading containerization solution.
- Gain insight into the benefits of using **Docker** for application deployment.

Now, let's dive into the details.

## Workspace
### What is Containerization?
**Containerization** is a technology that packages an application and its dependencies together into a single unit known as a container. This container can be easily moved, shared, and executed consistently across different environments. 

**Docker** is a leading platform for containerization that simplifies the process of creating, deploying, and managing containers.

## Traditional Virtual Machines (VMs) vs. Containers

To understand the significance of containerization, it's essential to distinguish it from traditional virtualization. 
|VMs|Containers|
|-|-|
In a VM-based environment, the physical hardware is virtualized to create multiple virtual machines, each with its own operating system. This approach is resource-intensive and can lead to overhead.|In contrast, containers share the host operating system, which means they are lightweight, start quickly, and consume fewer system resources. **They provide isolation at the process level**, allowing applications to run independently without interfering with each other.</br>In containsers, you don't actaully install whole operating systems, but only install the required packages that interact with the target kernal.</br>**Containers share the OS kernel of the host but run with their own file system, libraries, and configurations**

### Docker

**Docker** is a containerization platform that simplifies the development, deployment, and management of applications. It uses container technology to package an application and its dependencies, including libraries and configurations, into a single unit. **Docker** containers are consistent and portable, making it easier to move applications between development, testing, and production environments.

### Benefits of Docker
|Benefit|Details|
|-|-|
**Consistency**| **Docker** ensures that applications run consistently across different environments, eliminating the "it works on my machine" problem.
**Isolation**| Containers provide strong isolation, preventing conflicts between applications and dependencies.
**Portability**| **Docker** containers can run on any system that supports **Docker**, making it easy to move applications between environments.
**Resource Efficiency**| Containers share the host OS, leading to efficient resource utilization.
**Scalability**| **Docker** allows for easy scaling of applications and services as needed.

By using **Docker**, you can streamline the development process, reduce deployment issues, and manage your infrastructure more efficiently.

### Example Usage

Here's a basic example of using **Docker** to run a web server in a container:

```bash
Docker run -d -p 80:80 nginx
```

In this command, 
- We use **Docker** run to start a container based on the official Nginx image. 
- The -d flag runs the container in the background.
- The -p 80:80 maps port 80 on the host to port 80 in the container.

### Key Features of Docker
|Feature|Details|
|-|-|
Image-Based| **Docker** containers are created from images, which are snapshots of a file system and application. These images are versioned, making it easy to manage and distribute applications.
Container Orchestration| **Docker** offers tools like **Docker Compose** and **Kubernetes** for managing containerized applications at scale.
Security| Containers offer a level of isolation, and **Docker** provides security features to keep applications and data safe.
Community and Ecosystem| **Docker** has a large community and extensive ecosystem, including a hub for sharing and distributing container images.

Understanding **Docker** and **containerization** is essential for modern software development and system administration. It simplifies deployment, enhances consistency, and optimizes resource usage, ultimately saving time and reducing potential issues.

## KeyWords Term Definitions
The following is a breif of the some terms and keywords we will face in the coming section, so let's have an overhead info about them.
|Term|	Description|
|-|-|
Container|	A lightweight, executable package that includes an application and all its dependencies. Containers run isolated from the host system and other containers.</br>Container is an instance of an image.
Image|	A snapshot of a container, including the application code, runtime, system tools, and libraries. Images are used to create containers.
Docker|	A platform for developing, shipping, and running containers. Docker includes tools and services for building, managing, and deploying containers.
Virtual Machine (VM)|	A software-based emulation of a physical computer. VMs run a complete operating system, making them heavier and less efficient compared to containers.
Orchestration|	The process of automating the deployment, scaling, and management of containers. Tools like Kubernetes and Docker Swarm are used for container orchestration.
Isolation|	Containers provide process-level isolation, ensuring that applications do not interfere with each other. VMs offer hardware-level isolation with separate operating systems.
Portability|	Containers are highly portable, allowing applications to run consistently across different environments. VMs can be less portable due to varying configurations.
Overhead|	Containers have minimal overhead because they share the host OS. VMs can have higher overhead due to the need for multiple OS instances.
Resource Efficiency|	Containers are more resource-efficient compared to VMs, as they consume fewer system resources.
Image Repository|	A central storage location for container images. Docker Hub is a popular repository for Docker images.

# Section: Docker Fundamentals
## Info
|Info|Details|
|-|-|
Motivation| Understanding the fundamental concepts of Docker is essential for effective containerization and deployment.
Objective| To explore key Docker concepts and commands.
Workspace| We'll cover concepts like Docker containers, images, and registries, as well as basic Docker commands.
Illustration| We'll provide explanations, commands, and examples for each fundamental concept.

## Commands Table
|Command|	Description|
|-|-|
docker --version|	Check the Docker version.
docker info|	Display system-wide information.
docker run|	Run a container from an image.
docker pull|	Download an image from a registry.
docker images|	List available images.
docker ps|	List running containers.
docker ps -a|	List all containers (including stopped ones).
docker start|	Start a stopped container.
docker stop|	Stop a running container.
docker rm|	Remove a container.
docker rmi|	Remove an image.
docker logs|	View container logs.

## Key Concepts
|Concept|Details|
|-|-|
Docker Container| A runnable instance of a Docker image. Containers are isolated, lightweight, and can run various applications.
|Docker Image| A template for creating containers. Images include everything needed to run an application, such as code, libraries, and dependencies.
|Docker Registry| A centralized repository for Docker images. Docker Hub is a popular public registry, but you can set up private registries as well.
|Docker Client and Server| The Docker client communicates with the Docker server. The client can run on the same host as the server or connect to a remote Docker server.
|Dockerfile| A text file containing instructions for building a Docker image. Dockerfiles specify the base image, application code, and setup.

## Docker Fundamental: Container Vs Image
Feature|	Docker Container|	Docker Image|
|-|-|-|
|Definition|	Runnable instance of an image.|	A lightweight, standalone package containing application code, libraries, dependencies, and configuration.
Nature|	Dynamic and runnable.|	Static and read-only.|
Lifecycle|	Can be created, started, stopped, and deleted.|	Immutable; it's a template for containers.|
Storage|	Uses both base image and a writable layer for runtime changes.|	Stored as multiple layers, with each layer representing a filesystem change.|
Usage|	Ideal for running applications or services.|	Used to create containers that run specific applications.|
Portability|	Contains runtime environment; may vary based on the host.|	Highly portable; consistent across different hosts.|
Size|	Smaller in size.|	Larger in size (due to multiple layers).|
Recommended Use|	- For running and managing applications.</br>- Suitable for dynamic workloads.</br>- You can have multiple containers from one image, each with unique runtime configurations.|	- For distributing applications and ensuring consistent environments.</br>- Suitable for a consistent environment in various deployments.</br>- Images are shared across containers, ensuring consistency.

## When to Use Container & Image
|Use Docker Containers when|Use Docker Images when|
|-|-|
You want to run an application or service.</br>You need multiple instances of the same application with different configurations.</br>You want dynamic workloads that can be started, stopped, and scaled.|You need a consistent environment for running applications across different hosts.</br>You want to distribute applications and ensure they run with the same dependencies and configurations.</br>You're building a reproducible deployment pipeline.

In practice, Docker containers are often created from Docker images. Images provide the blueprint for containers, ensuring a consistent environment when deploying applications. This separation allows for efficient image sharing, easier version management, and rapid application deployment.

## Key Notes
- Images provide the foundation for containers but are not inherently executable.
- Containers are the actual instances where applications run and can be thought of as lightweight virtual machines.


## Docker Container
Containers are the primary units in Docker. They are lightweight, isolated, and can run applications in a consistent environment. **Containers share the OS kernel of the host but run with their own file system, libraries, and configurations**.

### Container LifeCycle
|Stage|Description|
|-|-|
1- Image Creation| The Docker container life cycle starts with the creation of a Docker image. The image acts as a template, containing the application code, libraries, configurations, and other dependencies required for the application to run. Images are created from a set of instructions defined in a Dockerfile. You can also pull pre-built images from Docker registries.
2- Container Initialization| When you run a Docker container from an image using the docker run command, a new container is initialized. The container inherits all the characteristics of the image. It starts in a clean state, and any changes made to the container are isolated from the image.
3- Application Execution| Once the container is up and running, the application inside the container is executed. This means the code within the container is executed according to the application's logic. Containers can run any application, from web servers to databases.
4- State Modification| While the application is running, it can modify its internal state. For instance, a web server container may serve web pages, a database container may store data, and so on. These changes are isolated within the container, ensuring that other containers and the host system are not affected.
5- Data and Configuration Persistence| Docker containers can have data volumes or use bind mounts to store data outside the container. This data can be shared across container instances, ensuring data persistence even if a container is removed or replaced.
6- Pause or Stop| At any point, a container can be paused or stopped using the docker pause or docker stop command. Pausing a container halts its execution without terminating it, while stopping a container gracefully shuts it down.
7- Termination| When you're done with a container, you can remove it with the docker rm command. This action effectively terminates the container, and any changes made to its file system are discarded.
8- Restart or Replacement| Containers can be restarted using the docker restart command or replaced by creating a new container from the same image. When replaced, a new container starts in the same state as the original image.
9- Scaling| Docker's flexibility allows you to scale your application by creating multiple containers from the same image. Each container runs independently but shares the same image and can communicate with each other.
10- Continuous Cycle| The life cycle of a Docker container can continue as you start, stop, and remove containers based on your application's requirements. This continuous cycle allows for scalability, flexibility, and efficient resource usage in a Docker environment.

### Command: docker run
|Info|Details|
|-|-|
Description| Create and run a new container based on an image.
Syntax| docker run [options] [image] [command] [args]
Key Features|-d: Run in detached mode (in the background).</br>-it: Start an interactive terminal session.</br>--name: Assign a name to the container.
Example Usage|docker run -d --name mycontainer nginx</br># Run an Nginx web server in detached mode with the name "mycontainer."

## Docker Image
Images are read-only templates for creating containers. They include the application code, libraries, dependencies, and configuration files.

### Command: docker pull
|Info|Details|
|-|-|
|Description| Download an image from a registry.
|Syntax| docker pull [image]
|Key Features|docker images: List available images on your system.</br>docker rmi [image]: Remove an image.
|Example Usage|docker pull ubuntu:20.04</br># Download the Ubuntu 20.04 image from Docker Hub.

## Docker Registry
In the context of Docker, "registries" refer to centralized servers or services that store and distribute Docker images. Registries are essential for sharing and managing container images across different systems and platforms. Here's what registries mean in the context of Docker:
|Concept|Details|
|-|-|
Storage for Docker Images| Registries act as storage repositories for Docker images. They store the image files, which include the application code, libraries, dependencies, and configuration needed to run a containerized application.
|Distribution| Docker images can be easily pushed (uploaded) to registries and pulled (downloaded) from them. This distribution mechanism allows users to share and deploy images across different hosts and environments.
|Access Control| Registries can have access control mechanisms to manage who can upload, download, or modify images. This is important for security and access management, especially in enterprise settings.
|Public and Private Registries| There are both public and private registries available. Public registries, like Docker Hub, allow anyone to access and use images. Private registries are used for proprietary or sensitive applications and offer more control over image access.
|Docker Hub| Docker Hub is the default and most widely used public registry for Docker images. It hosts a vast collection of pre-built images that can be used by the Docker community.

Overall, registries simplify the process of sharing, distributing, and managing Docker images, making containerization more practical for both individual developers and organizations.

## Docker Client and Server
Docker follows a client-server architecture. The Docker client communicates with the Docker server. The client can be on the same host as the server or connect to a remote server.

### Command: docker --version and docker info
|Info|Details|
|-|-|
Description| Check the Docker version and display system-wide information.
Syntax| docker --version and docker info
Key Features|docker version: Display more detailed version information.
Example Usage|docker --version: Check your Docker client version.</br>docker info: View system-wide Docker information.

## Example Usage
To start a new container from an image in detached mode (in the background), you can use:

```bash
docker run -d --name my_container ubuntu:20.04
```

To access a running container's shell, you can use:
```bash
docker exec -it my_container /bin/bash
```

# Section: Docker Installation
## Info
|Info|Details|
|-|-|
Motivation| Installing Docker is the first step towards leveraging the power of containerization. Docker provides a consistent environment for your applications across different systems, making it easier to develop, test, and deploy software.
Objective| By the end of this section, you will understand how to install Docker on your specific operating system and be ready to work with Docker containers.
Workspace| The installation process may vary based on your operating system. Below, I'll provide an overview of how to install Docker on Linux, Windows, and macOS. For specific details and updates, refer to the official Docker documentation.

## Docker Installation on Linux
Linux is a natural choice for Docker due to its close integration with the container technology. To install Docker on Linux, follow these general steps:
|Step|Details|
|-|-|
1- Check Prerequisites| Ensure that your Linux distribution is supported by Docker. Check for any specific prerequisites for your distribution.
2- Install Docker| Use your distribution's package manager to install Docker. For example, on Ubuntu, you can run:</br>sudo apt-get update</br>sudo apt-get install docker-ce
3-Start and Enable Docker| Start the Docker service and enable it to start at boot:</br>sudo systemctl start docker</br>sudo systemctl enable docker
Test Installation|Verify that Docker is correctly installed by running:</br>docker --version

## Docker Installation on Windows
On Windows, you can install Docker Desktop, which provides a convenient way to work with Docker containers. Follow these steps:
|Step|Details|
|-|-|
System Requirements| Ensure that your Windows version supports Docker Desktop and that virtualization is enabled in your BIOS settings.
|Download and Install| Download Docker Desktop from the official website and run the installer.
|Start Docker Desktop| After installation, start Docker Desktop. It will set up a Linux-based virtual machine to run Docker containers.
|Test Installation| Open a command prompt and run:</br>docker --version

## Docker Installation on macOS
Docker for Mac provides a user-friendly experience for macOS users. Here's how to install it:
|Step|Details|
|-|-|
System Requirements| Ensure your macOS version is supported, and virtualization is enabled in your system settings.
|Download and Install| Download Docker for Mac from the official website and follow the installation instructions.
|Start Docker| Launch Docker for Mac. It will set up a Linux-based virtual machine for Docker containers.
|Test Installation| Open a terminal and run:</br>docker --version

## Key Features
- Docker installation is platform-specific, so make sure to follow the official installation guides for your OS.
- Docker Desktop for Windows and Docker for Mac offer a user-friendly interface for managing containers.
- Ensure that virtualization is enabled on your system for optimal Docker performance.

## Example Usage
After successfully installing Docker, you can create, run, and manage containers using Docker commands, such as docker run, docker ps, and docker stop.

Now that you have an overview of Docker installation on different platforms, you can proceed with setting up Docker according to your specific operating system. Once Docker is installed, you can start working with containers and containerized applications.

## Docker Pull & Run Images/Containers
One of the fundamental concepts in Docker is the use of images. You can create your own images or pull pre-built images from Docker registries. Here's how to pull and run Docker images:

### Pulling Docker Images
**1- Search for an Image**: Before pulling an image, you can search for available Docker images using the docker search command. For example:
```bash
docker search ubuntu
```

**2- Pull an Image**: To pull an image from a Docker registry, use the docker pull command followed by the image name and optional tag (version). If you don't specify a tag, it will default to "latest." For example:
```bash
docker pull ubuntu
```
This command will download the official Ubuntu image from the Docker Hub.

**3- Check Available Images**: You can list all the images on your system using the docker images command. It will display a list of downloaded images.

### Running Docker Containers
Once you have the desired Docker image, you can run containers based on it.

**1- Run a Container**: To start a new container from a pulled image, use the docker run command. Specify the image name and any additional options you need. For example:
```bash
docker run -it ubuntu
```
This command creates an interactive (-it) Ubuntu container.

**2- Container Execution**: After running the container, you will be inside the container's shell, where you can interact with the Ubuntu environment. Any commands you run in this shell will execute within the container.

**3- Exiting a Container**: To exit the container's shell without stopping the container, you can use the exit command. This will return you to the host system's shell.

**4- Running in Detached Mode**: You can also run containers in detached mode (in the background) by adding the -d flag to the docker run command. For example:
```bash
docker run -d ubuntu
```
The container runs in the background, and you regain control of your terminal.

**5- Listing Running Containers**: To see a list of running containers, you can use the docker ps command. To view all containers (including stopped ones), add the -a flag:
```bash
docker ps
docker ps -a
```

**6- Stopping a Container**: To stop a running container, you can use the docker stop command followed by the container's ID or name. For example:
```bash
docker stop my_container
```

These are the basic steps to pull and run Docker images. Docker makes it easy to manage containers based on various images, allowing you to work with a wide range of applications and services. Remember that you can customize the behavior and configuration of containers by specifying different options when running them.

# Section: Dockerfile and Building Images
This section delves into the essential concepts of Dockerfile and image building. Dockerfiles are pivotal in Docker-based development, allowing you to define and configure containers systematically. The main topics covered in this section are as follows:
|Topic|Motivation|Objective|
|-|-|-|
Introduce Dockerfiles as a means to define container configurations|Dockerfiles provide a structured and repeatable way to create container images, making application deployment and scaling more efficient.|To understand the role of Dockerfiles in containerization and their significance in simplifying image creation and maintenance.
Explain the structure of Dockerfiles and their instructions|Dockerfiles follow a specific structure comprising instructions, each serving a unique purpose in defining container configuration.|To explore the anatomy of Dockerfiles, comprehend the role of instructions, and learn how to leverage them to design custom containers.
Walk through the process of building custom Docker images|Building custom Docker images enables you to tailor containers to your application's exact requirements.|To gain practical knowledge of creating custom Docker images using Dockerfiles, ensuring your applications run within the desired environment.

With an understanding of Dockerfiles and the image-building process, you'll have the foundation needed to develop and manage containers that perfectly match your application needs. The subsequent topics will dive into Dockerfile structure, instructions, and the step-by-step process of building custom images.
