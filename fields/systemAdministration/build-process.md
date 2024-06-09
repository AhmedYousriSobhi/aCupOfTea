# System Administration - Build Process

# Mystic Map
- [System Administration - Build Process](#system-administration---build-process)
- [Mystic Map](#mystic-map)
- [Why Configure the Build Process for Applications or Packages in Linux?](#why-configure-the-build-process-for-applications-or-packages-in-linux)
- [Key Steps in the Build Configuration Process](#key-steps-in-the-build-configuration-process)
- [Common Tools and Commands](#common-tools-and-commands)
- [CMake](#cmake)
  - [Overview and History](#overview-and-history)
  - [How CMake Works Internally](#how-cmake-works-internally)
  - [Cmake follows a two-phase process](#cmake-follows-a-two-phase-process)
  - [How to configure using CMake](#how-to-configure-using-cmake)
    - [1- Basic Structure of CMakeLists.txt](#1--basic-structure-of-cmakeliststxt)
    - [2- Running CMake](#2--running-cmake)
    - [3- Common Default Parameters](#3--common-default-parameters)
  - [Cleaning the Build Directory](#cleaning-the-build-directory)
    - [1- Using *--build* with *--target clean* option](#1--using---build-with---target-clean-option)
    - [2- Using *-E rm* Command](#2--using--e-rm-command)
    - [3- Using CMake Scripting with a Clean Target](#3--using-cmake-scripting-with-a-clean-target)
  - [Advanced Tips and Tricks for CMake Command Line](#advanced-tips-and-tricks-for-cmake-command-line)
  - [Using find\_package and Config Modules](#using-find_package-and-config-modules)
    - [Common Issues and Solutions with find\_package](#common-issues-and-solutions-with-find_package)
      - [1. *Package Not Found*](#1-package-not-found)
      - [2. *Version Mismatch*](#2-version-mismatch)
      - [3. *Incorrect Find.cmake Module*](#3-incorrect-findcmake-module)
      - [4. *Missing Dependencies*](#4-missing-dependencies)
      - [5. *Incorrect Package Config File Location*](#5-incorrect-package-config-file-location)
      - [6. *Case Sensitivity Issues*](#6-case-sensitivity-issues)
      - [7. *Incorrect Usage of find\_package Options*](#7-incorrect-usage-of-find_package-options)
      - [8. *Custom Installation Locations*](#8-custom-installation-locations)


# Why Configure the Build Process for Applications or Packages in Linux?
Configuring the build process for applications or packages in Linux is crucial for several reasons:
1. Customization: Allows tailoring the software to specific needs by enabling or disabling features, optimizing for particular hardware, or integrating with other software components.
2. Performance Optimization: Adjusting compiler flags and options can enhance performance and efficiency, making the application run faster or use fewer resources.
3. Dependency Management: Ensures that all required libraries and dependencies are correctly identified and linked, preventing runtime errors and ensuring smooth operation.
4. Security: Custom builds can apply specific security patches, enforce stricter security policies, and remove unnecessary components that might introduce vulnerabilities.
5. Compatibility: Configuring the build process ensures compatibility with the specific environment, such as the operating system version, library versions, and hardware architecture.
6. Automated Deployment: Facilitates automated deployment processes, allowing consistent and reproducible builds, essential for continuous integration and delivery pipelines.
7. Debugging and Testing: Custom configurations can include debug symbols, enabling more effective debugging and more thorough testing processes.

# Key Steps in the Build Configuration Process
1. Obtaining the Source Code: Usually from repositories like GitHub, or by downloading tarballs.
2. Preparing the Build Environment: Installing necessary tools and libraries, such as compilers, build systems, and dependencies.
3. Configuring the Build Options: Using tools like ./configure, CMake, or Meson to set options and preferences.
4. Compiling the Code: Running make or another build command to compile the source code.
5. Installing the Application: Using make install or equivalent to install the built software.
6. Post-Installation Configuration: Adjusting runtime configurations and environment variables if necessary.

# Common Tools and Commands
- Autoconf and Automake: Tools for generating configure scripts.
- CMake: A cross-platform tool for managing the build process.
- Meson: A modern build system focused on speed and ease of use.
- make: A build automation tool that uses Makefiles to control the build process.

They both differ in their design, usage, and capabilities.

Let's explore some of them.

# CMake
## Overview and History
CMake (short for "Cross-Platform Make") is an open-source tool designed to manage the build process of software in a compiler-independent manner. It was created by Kitware in 2000 to address the limitations of make and other build tools in cross-platform environments. CMake generates native build files (like Makefiles on Unix or project files for IDEs like Visual Studio) based on platform-specific configurations.

## How CMake Works Internally
1. CMakeLists.txt: The primary configuration file where build instructions are written.
2. Configuration Phase: When you run cmake command, it reads the CMakeLists.txt files and generates native build system files.
3. Build Phase: Using the generated files (e.g., Makefiles), the actual build process is executed by running the appropriate build tool (like make).

## Cmake follows a two-phase process
1. **Configuration Phase**
    - Parses *CmakeLists.txt*.
    - Resolves dependencies.
    - Generates cache entries in *CMakeCache.txt*.
2. **Generation Phase**
    - Produces native build system files.
    - Configures includes directories, library dependencies, and compilation options.

## How to configure using CMake
### 1- Basic Structure of CMakeLists.txt
    ```cmake
    cmake_minimum_required(VERSION 3.10)
    project(AdvancedProject)

    # Set project version
    set(PROJECT_VERSION_MAJOR 1)
    set(PROJECT_VERSION_MINOR 0)

    # Specify C++ standard
    set(CMAKE_CXX_STANDARD 17)
    set(CMAKE_CXX_STANDARD_REQUIRED True)

    # Add executable
    add_executable(AdvancedExecutable main.cpp)

    # Add include directories
    target_include_directories(AdvancedExecutable PUBLIC include)

    # Link libraries
    find_package(Boost 1.65 REQUIRED COMPONENTS system)
    target_link_libraries(AdvancedExecutable Boost::system)

    # Add custom build step
    add_custom_command(TARGET AdvancedExecutable POST_BUILD
                    COMMAND ${CMAKE_COMMAND} -E copy
                    "${PROJECT_SOURCE_DIR}/config.cfg"
                    $<TARGET_FILE_DIR:AdvancedExecutable>)
    ```
    - This example shows a more advanced configuration, specifying the C++ standard, linking Boost libraries, and adding custom build steps.

### 2- Running CMake
   
2.1. ***Approach-01- Manually creating build directory***
- Create build directory:
    ```sh
    mkdir build
    cd build
    ```
- Run Cmake to generate the build system files:
    ```sh
    cmake ..
    # Note you must specify the location of the binaries of the source.
    # specifies the source directory, which is the parent directory ('..'). 
    ```
- Build the project:
    ```sh
    make
    ```
- Install the project
    ```sh
    make install
    ```

2.2. ***Approach-02- Without manually creating the build directory***
- Running Cmake with the specified build directory: instead of creating the build directory and manually navigating to it, you can run CMake in a single command, specifying the build directory.
    ```sh
    cmake -S . -B build
    ```
    - ***-s .*** : specifies the source directory, which is the current directory ('.').
    - ***-B build** : specifies the build directory, which will be created if it doesn't exists.
- Building the project: Once the build directory is specified, you can invoke the build system from the source directory.
    ```sh
    cmake --build build
    ``` 
- Install the project
    ```sh
    cmake --install build
    ```

### 3- Common Default Parameters
- ***Installation directories specific***
    ```sh
    -DCMAKE_INSTALL_PREFIX=/path/to/install/directory
    # Specifies the installation directory

    -DCMAKE_RUNTIME_OUTPUT_DIRECTORY=/path/to/bin
    # Specifies the directory where runtime files (executables) will be placed.

    -DCMAKE_LIBRARY_OUTPUT_DIRECTORY=/path/to/lib
    # Specifies the directory where library files will be placed.

    -DCMAKE_ARCHIVE_OUTPUT_DIRECTORY=/path/to/lib
    # Specifies the directory where archive files (static libraries) will be placed.
    ```
- ***Compiler specific parameters***
    ```sh
    -DCMAKE_BUILD_TYPE=Release
    # Specifies the build type (e.g, Debug, Release, RelWithDebInfo, MinSizeRel).

    -DCMAKE_C_COMPILER=gcc
    -DCMAKE_CXX_COMPILER=g++
    -DCMAKE_Fortran_COMPILER=gfortran
    # Specifies the C, C++, Fortran compilers.
    
    -DCMAKE_C_FLAGS="-Wall -02"  
    -DCMAKE_CXX_FLAGS="-Wall -02"
    -DCMAKE_Fortran_FLAGS="-Wall -02"
    # Specifies the Additional compiler flags for C, C++, Fortran files.
    ```
- ***Dependencies specific paramters***
    ```sh
    -DCMAKE_PREFIX_PATH=/path/to/dependencies
    # Lists of directories specifying where to search for dependencies.

    -DCMAKE_FIND_ROOT_PATH=/path/to/root
    # Specifies one or more directories to be prepended to all other search directories.

    -DCMAKE_TOOLCHAIN_FILE=/path/to/toolchain.cmake
    # Specifies the path to a toolchain file to use for cross-compilation.
    ```
- ***Additional info paramters***
    ```sh
    -DBUILD_SHARED_LIBS=ON
    # Controls whether shared libraries are build [ON, OFF].

    -DCMAKE_INSTALL_MESSAGE=ALWAYS
    # Specifies the install message level [ALWAYS, LAZY, NEVER]

    -DCMAKE_EXPORT_COMPILE_COMMANDS=ON
    # Generates a compile_commands.json file. [ON, OFF]
    ```

## Cleaning the Build Directory
### 1- Using *--build* with *--target clean* option
```sh
cmake --build build --target clean
# This removes the files generated during the build process but does not clear the entire build directory.

# Recreate the build directory and configure the project
cmake -S . -B build

# Build the project
cmake --build build
```
### 2- Using *-E rm* Command
```sh
cmake -E rm -rf build
# The -E rm command can be used to completely remove files or directories

# Recreate the build directory and configure the project
cmake -S . -B build

# Build the project
cmake --build build
```

### 3- Using CMake Scripting with a Clean Target
You can create a custom clean target in your CMakeLists.txt that removes the build directory contents. This is useful if you want to integrate this functionality directly into your build configuration.
```cmake
add_custom_target(clean-all
    COMMAND ${CMAKE_COMMAND} -E remove_directory ${CMAKE_BINARY_DIR}
    COMMAND ${CMAKE_COMMAND} -E make_directory ${CMAKE_BINARY_DIR}
    COMMENT "Cleaning all build files"
)
```
Then, you can run:
```sh
cmake --build build --target clean-all
```

## Advanced Tips and Tricks for CMake Command Line
|Title|objective|Command|
|-|-|-|
Out-of-Source Builds|Always use out-of-source builds to keep your source directory clean.|***cmake -S . -B build***
Parallel Builds|Use the --parallel option to speed up builds by utilizing multiple CPU cores.|***cmake --build build --parallel $(nproc)***
Reconfigure with cmake --fresh|Reconfigure the project with fresh cache values.|***cmake -S . -B build -DCMAKE_BUILD_TYPE=Release --fresh***
Using Ninja for Faster Builds|Ninja is a small build system with a focus on speed. Use the Ninja generator for faster builds.|***cmake -S . -B build -G Ninja</br>cmake --build build***
Build and Install in One Step|Build and install the project in one step using the --target and --install options.|***cmake --build build --target install***
Using Environment Variables|You can set environment variables to customize the build process.|***CXX=g++ CC=gcc cmake -S . -B build***
Clearing the Cache|If you need to clear the cache without deleting the entire build directory, you can remove the CMakeCache.txt file.|**rm build/CMakeCache.txt</br>cmake -S . -B build**
Custom Build Commands|Add custom build commands directly from the command line|***cmake --build build --target my_custom_target***
Install Only Specific Components|If your project has multiple install components, you can install specific ones.|***cmake --install build --component MyComponent***
Test and Package Your Build|Use CTest and CPack for testing and packaging.|***cmake --build build --target test</br>cmake --build build --target package***

One final tip is CMake Presets:
- Use CMakePresets.json to define and manage build configurations more easily.
    ```json
        {
    "version": 3,
    "cmakeMinimumRequired": {
        "major": 3,
        "minor": 19,
        "patch": 0
    },
    "configurePresets": [
        {
        "name": "default",
        "hidden": true,
        "generator": "Ninja",
        "binaryDir": "${sourceDir}/build",
        "cacheVariables": {
            "CMAKE_EXPORT_COMPILE_COMMANDS": "YES"
        }
        },
        {
        "name": "release",
        "inherits": "default",
        "description": "Release build",
        "cacheVariables": {
            "CMAKE_BUILD_TYPE": "Release"
        }
        }
    ]
    }
    ```
- Then use
    ```sh
    cmake --preset release
    ```

## Using find_package and Config Modules
Find Modules: Use find_package() to locate and configure external dependencies. Prefer using package config files provided by libraries over writing custom find modules.

Using find_package in CMake can sometimes lead to issues, especially when dealing with external dependencies. Here are some common issues and their solutions:

### Common Issues and Solutions with find_package
#### 1. *Package Not Found*
     - Issue: CMake cannot locate the package.
     - Solution: Ensure the package is installed and its paths are correctly set. Use CMAKE_PREFIX_PATH or CMAKE_MODULE_PATH to help CMake find the package.

        ```sh
        cmake -DCMAKE_PREFIX_PATH=/path/to/package ..
        ```

#### 2. *Version Mismatch*
    - Issue: The specified version of the package is not found.
    - Solution: Check the installed version of the package and specify the correct version in the find_package command.

    ```cmake
    find_package(PackageName 1.2 REQUIRED)
    ```

#### 3. *Incorrect Find<Package>.cmake Module*
    * Issue: The Find<Package>.cmake module provided by CMake is incorrect or outdated.
    * Solution: Write your own Find<Package>.cmake module or use the package config file provided by the library.

    ```cmake
    set(CMAKE_MODULE_PATH "${CMAKE_CURRENT_SOURCE_DIR}/cmake")
    find_package(PackageName REQUIRED)
    ```

#### 4. *Missing Dependencies*
    - Issue: The package depends on other libraries that are not found.
    - Solution: Ensure all dependencies are installed and their paths are set correctly. You may need to manually specify paths for these dependencies.

    ```sh
    cmake -DCMAKE_PREFIX_PATH="/path/to/dependency1;/path/to/dependency2" ..
    ```

#### 5. *Incorrect Package Config File Location*
    - Issue: CMake cannot find the package config file (<Package>Config.cmake or <package>-config.cmake).
    - Solution: Specify the directory containing the config file using CMAKE_PREFIX_PATH.

    ```sh
    cmake -DCMAKE_PREFIX_PATH="/path/to/package" ..
    ```
#### 6. *Case Sensitivity Issues*
    - Issue: Case sensitivity issues on case-sensitive file systems (e.g., Linux).
    - Solution: Ensure the case matches exactly as CMake is case-sensitive when looking for files and directories.

    ```cmake
    find_package(PackageName REQUIRED)
    ```

#### 7. *Incorrect Usage of find_package Options*
    - Issue: Misuse of find_package options like REQUIRED, QUIET, and COMPONENTS.
    - Solution: Correctly use find_package options based on your requirements.

    ```cmake
    find_package(PackageName REQUIRED COMPONENTS component1 component2)
    ```

#### 8. *Custom Installation Locations*
    - Issue: Packages installed in non-standard locations.
    - Solution: Use environment variables or specify paths directly.

    ```sh
    export CMAKE_PREFIX_PATH=/custom/path/to/package
    cmake ..
    ```
