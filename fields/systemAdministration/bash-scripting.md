# System Administration - Bash Scripting
# Table of Content
- [System Administration - Bash Scripting](#system-administration---bash-scripting)
- [Table of Content](#table-of-content)
- [Introduction](#introduction)
  - [Bash Scripting Definition](#bash-scripting-definition)
  - [Advantages](#advantages)
- [Creating a bash script](#creating-a-bash-script)
  - [Script naming conventions](#script-naming-conventions)
  - [Shebang](#shebang)
  - [Executing the Bash Script](#executing-the-bash-script)
    - [Make Script Executable](#make-script-executable)
    - [Execute](#execute)
- [Basics](#basics)
  - [1- Comments](#1--comments)
  - [2- Variables \& Data Types](#2--variables--data-types)
    - [Define a Varialbe](#define-a-varialbe)
    - [Access a Varialbe](#access-a-varialbe)
    - [Naming Convention](#naming-convention)
      - [Tips](#tips)
  - [3- Inputs](#3--inputs)
    - [Read User Input](#read-user-input)
    - [Reading from File](#reading-from-file)
    - [Command Line Arguments](#command-line-arguments)
  - [4- Outputs](#4--outputs)
    - [Prinitng to the Terminal](#prinitng-to-the-terminal)
    - [Writing to a File](#writing-to-a-file)
    - [Appending to a File](#appending-to-a-file)
    - [Redirecting Output](#redirecting-output)
  - [5- Conditional Statements (if/else)](#5--conditional-statements-ifelse)
    - [If](#if)
    - [Multiple Conditions](#multiple-conditions)
    - [Case Statements](#case-statements)
    - [If Flags](#if-flags)
  - [6- Looping](#6--looping)
    - [While Loop](#while-loop)
    - [For Loop](#for-loop)
  - [7- Functions](#7--functions)
  - [8- Schedule Scripts using cron](#8--schedule-scripts-using-cron)
    - [Cron](#cron)
    - [Steps to Shcedule a Bash Script](#steps-to-shcedule-a-bash-script)
      - [1. Understand Cron Syntax](#1-understand-cron-syntax)
      - [2. Edit the User's Cron Jobs](#2-edit-the-users-cron-jobs)
      - [3.Schedule the Bash Script](#3schedule-the-bash-script)
      - [4. Save and exit](#4-save-and-exit)
      - [5. Check Shceduled Scripts](#5-check-shceduled-scripts)
      - [Additional Tips:](#additional-tips)
- [Debug \& Troubleshoot](#debug--troubleshoot)
  - [1. Using 'set -x'](#1-using-set--x)
  - [2. echo Statements:](#2-echo-statements)
  - [3. Redirecting Output and Errors](#3-redirecting-output-and-errors)
  - [4. set -e](#4-set--e)
  - [5. trap Command](#5-trap-command)
  - [6. Shellcheck](#6-shellcheck)
  - [7. Debugging with bash -x](#7-debugging-with-bash--x)
  - [8. Logging](#8-logging)
- [Tips \& Tricks](#tips--tricks)
  - [Braces Expansion](#braces-expansion)
  - [Braces for Variables](#braces-for-variables)
  - [Command Substitution](#command-substitution)
  - [Aliases](#aliases)
  - [The Watch Command](#the-watch-command)
  - [History Expansion](#history-expansion)
- [References](#references)

# Introduction
## Bash Scripting Definition
Working in UNIX operating system, we will face this type of a file which contain a sequence of commands that are executed by the bash program line by line to perfrom a series of actions. These actions performed by commands can be repeated multiple times and execute them by running the script.

## Advantages
Adv|Description|
|-|-|
Automation| Bash scripting allows you to automate repetitive tasks, making it incredibly useful for tasks like file manipulation, system maintenance, backups, and more. This automation can significantly save time and reduce human error.
Accessibility| Bash is the default shell for most Unix-like operating systems, ensuring its widespread availability. It's pre-installed on macOS and most Linux distributions, making it easily accessible without the need for additional installations.
Customization| Users can customize and tailor scripts according to their needs, making it a flexible tool for various tasks. With conditional statements, loops, and functions, it's possible to create complex and specific workflows.
Integration| Bash scripts can integrate with other command-line utilities and programs seamlessly. This integration allows for powerful scripting by combining the functionality of multiple tools into a single script.
System Administration| Bash scripting is extensively used in system administration tasks. It helps in automating system configurations, user management, log analysis, and other administrative tasks.
Portability| Bash scripts are often portable across different Unix-like systems. However, it's essential to consider the differences in commands and functionalities across different versions of Bash and other shells.
Rapid Development| Writing scripts in Bash is relatively quick and straightforward due to its simple syntax. For quick solutions or prototyping, it provides a fast development environment.
Learning Curve| Compared to more complex programming languages, Bash scripting has a relatively lower learning curve, making it accessible for beginners. It's a good starting point for those new to scripting or programming concepts.
Debugging Tools| Bash provides debugging options like tracing execution, setting breakpoints, and displaying error messages, aiding in identifying and fixing issues in scripts.
Community Support| There's a large community of Bash scripters and developers, resulting in an abundance of online resources, forums, and tutorials to seek help from and learn.

Note: It is important to note that, bash scripting might not always be the most suitable tool for every task, for complex projects or tasks requiring extensive data manupulation or advanced data structures.

# Creating a bash script
Let's start creating our own script!! 

## Script naming conventions
Bash scripts ends with **.sh**, However, they can run fine without the **sh** extention.

An Important Observation! In Unix system, a file extention is useless for Unix system, and has no any importants except for the user, to know what is the file type working on. So how does the system knows it is a bash script?

## Shebang
A shebang, also known as a hashbang (hash **#** + bang **!**) or a pound-bang, refers to the first line in a script file in Unix-like operating systems. It begins with the characters "#!" followed by the path to the interpreter that should execute the script. For example:
```bash
#!/bin/bashc
```

Shebang is simply an absoulte path to the bash interpreter

To find the bash shell path:
```bash
which bash
```

## Executing the Bash Script
In Unix system, any created file by default is not executable, which means user can not execute it.

### Make Script Executable
To make a file executable:
```bash
chmod u+x my_script.sh
```
|Command|Description|
|-|-|
chmod|Modifies the ownership of a file
u|Modify this ownership for the current user
x| adds the execution rights
u+x|This means that the user who is the owner can now run the script
my_script.sh| The file which the user want to run
### Execute
there are several methods to execute the scirpt
```bash
sh my_script.sh
bash my_script.sh
./my_script.sh
```

# Basics
There are some basics in the bash scripting any user should know
## 1- Comments
A neat bash script is the one that you could understand what is happening inside. To make a script readable, we should add comments.

Comments starts with **#**, so any line begins with **#** is a comment and will be ignored by the interpreter. There is exception in the **shebang**!!
```bash
#!/bin/bash

# This line is a comment, and will not be executed
# So try to say something usefull to illustrate the mess you are doing.
```

## 2- Variables & Data Types
To easily store, read, and access the data, variables knows how to get this job done.There are no data types in Bash, so variables can easily store any type of data.

### Define a Varialbe
```bash
#!/bin/bash

# this is a variable to store a string
firstname=ahmed
lastname="yousri"
```
- You can enclose the string with quots or just leave it without them, but in case of not using the quotes, make sure the string does not have any spaces
### Access a Varialbe
To access the value in a variable, use **$**
```bash
#!/bin/bash

echo $firstname
```
### Naming Convention
In Bash scripting, variable names should follow certain conventions for readability and consistency. Here are the commonly recommended naming conventions for variables:
- Should start with a letter or an underscore
- Can contains letters, numbers, and underscores
- Case-senstive
- Should not contain spaces or special characters

#### Tips
- Avoid using reserved keywords, such as if, then, else, fi, and so on.
- Avoid using system or Bash reserved variables names like PATH, HOME, PWD, ...
- Use descriptive names that reflect the purpose of the variables.
- Uppercase for Environment Variables
- Lowercase or CamelCase for Local Variables
- Underscores for Multi-word Variable Names
- Constants in Uppercase

## 3- Inputs
### Read User Input
You can read user input using the **read** command
```bash
#!/bin/bash

# Print a message for the user
echo "What's your name?"

# Read input from user, and store it in varialbe called usernamne
read username

# print user input
echo "Hello, $username! Welcome"
```
### Reading from File
```bash
#!/bin/bash

# Reading line by line from user
while read line
do
  echo $line
done < input.txt
```
|Command|Details|
|-|-|
while read line| This line starts a while loop. The read command reads a line from the input and stores it in the variable line. This loop continues until there are no more lines to read.
do| Marks the beginning of the loop body. Commands placed after do and before done will be executed repeatedly as long as the read command successfully reads a line from the file.
echo $line| This command prints the content of the variable line to the terminal.
done| Marks the end of the loop body.
< input.txt| Redirects the contents of the file input.txt as input to the while loop. So, the read command reads each line of input.txt sequentially, assigns it to the variable line, and then echo $line prints each line to the terminal.
### Command Line Arguments
In many cases, we add arugments along side with the bash script during the execution, like:
```bash
./my_script.sh ahmed
```
So in the bash script, we can access this using the **$** operator.
```bash
#!/bin/bash

echo "Hello, $1!"
```
so the expected output will be: "Hello, Ahmed!"

The number notation, indecate the argument position, so in our case, **ahmed** was the first arguments in the command line, so we can read it using **$1**. So in case there are other arguments, we can access them using their index number in the command line.

What about **$0** you may ask?
- This holds the bash script name itself!!.

## 4- Outputs
### Prinitng to the Terminal
Using Command **echo**
```bash
#!/bin/bash

echo "Hello Bash!"
```
### Writing to a File
Using redirect operator **>**
```bash
#!/bin/bash

echo "This is bash text." > my_output.txt
```
### Appending to a File
Using the appending operator **>>** :
```bash
#!/bin/bash

echo "More bash text" >> my_output.txt
```
### Redirecting Output
You can redirect the output of a command to a file using the redirect operator
```bash
ls > my_file.txt
```
## 5- Conditional Statements (if/else)
TO have a boolean results, with a true or false. this is what is called conditions. To do so using if, if-else, if-elif-else, and nested conitionals.

### If
```bash
#!/bin/bash

if [[ condition ]]; then 
  statement
elif [[ condition ]]; then
  statement
else
  do this by default
fi
```

### Multiple Conditions
You can combine multiple conditions using AND **-a** and OR **-o** to make comparisons that have more significance:
```bash
#!/bin/bash

if [ $a -gt 60 -a $b -lt 100]
# To check if varialbe a is greater than 60 AND variable b is less than 100
```
### Case Statements
```bash
case expression in
    pattern1)
        # code to execute if expression matches pattern1
        ;;
    pattern2)
        # code to execute if expression matches pattern2
        ;;
    pattern3)
        # code to execute if expression matches pattern3
        ;;
    *)
        # code to execute if none of the above patterns match expression
        ;;
esac

```
### If Flags
Refer to **man if** manual page to get more about the supported flags used in the conitions.
```bash
 -a    file exists  This is identical in effect to -e. It has been "deprecated," [1] and its use is discouraged.
 -b    file is a block device
 -c    file is a character device  [ -b "/dev/sda2" ]
 -d    file is a directory
 -e    file exists
 -f    file is a regular file (not a directory or device file)
 -G    group-id of file same as yours
 -g    set-group-id (sgid) flag set on file or directory
          If a directory has the sgid flag set, then a file created within that directory belongs to the group
          that owns the directory, not necessarily to the group of the user who created the file.
 -h    file is a symbolic link
 -k    sticky bit1 set
 -L    file is a symbolic link
 -N    file modified since it was last read
 -O    you are owner of file
 -p    file is a pipe  [ -p /dev/fd/0 ]
 -r    file has read permission (for the user running the test)
 -S    file is a socket
 -s    file is not zero size
 -t    file (descriptor) is associated with a terminal device.
 -u    set-user-id2 (suid) flag set on file
 -w    file has write permission (for the user running the test)
 -x    file has execute permission (for the user running the test)

 -nt   file f1 is newer than f2   f1 -nt f2
 -ot   file f1 is older than f2   f1 -ot f2
 -ef   files f1 and f2 are hard links to the same file   f1 -ef f2
    
 !     "not" -- reverses the sense of the tests above (returns true if condition absent).
```
## 6- Looping
To repeatily doing same instructions commands as long as a condition is valid (true), you can easily use looping, until a condition become invalid (false) and break the loop.

### While Loop
It is used in case you want to repeat some commands as long a condition is valid
```bash
#!/bin/bash

i=1
while [[ $i -ls 10]]; do
  echo $i
  (( i +=1 ))
done
```
### For Loop
It is more used in case if you know how many times you need to iterate and repeatly do the same commands, so this even used in case of reading a file line by line.
```bash
#!/bin/bash

for i in [1..5]
do
  echo $i
done
```
## 7- Functions
In Bash scripting, functions are blocks of code that can be defined once and executed multiple times within a script. They offer modularity, reusability, and help organize code. Here's an overview of using functions in Bash:
```bash
function function_name {
    # Commands or code block
    # Within the function
}
```
Example for a cslculator:

```bash
#!/bin/bash

# Define functions to perform calculations
function add {
echo $(($1 + $2))
}

function subtract {
echo $(($1 - $2))
}

function multiply {
echo $(($1 * $2))
}

function divide {
echo $(($1 / $2))
}

# Get input numbers from command-line arguments
num1=$1
num2=$2

# Call the functions with input numbers
echo "Addition: $(add $num1 $num2)"
echo "Subtraction: $(subtract $num1 $num2)"
echo "Multiplication: $(multiply $num1 $num2)"
echo "Division: $(divide $num1 $num2)"
```

## 8- Schedule Scripts using cron
Not all scripts are meant to be immediatly run to do their task, some time we need to set a schedule to automate their work on a specific time. We will use cron to do this schedule feature.

### Cron
Cron is a time-based job scheduler in Unix-like operating systems, including Linux and macOS. It allows users to schedule tasks, commands, or shell scripts to run automatically at predefined intervals or specific times without manual intervention.

### Steps to Shcedule a Bash Script
#### 1. Understand Cron Syntax
Cron uses a specific syntax to define the schedule. It comprises five fields followed by the command/script to be executed. The fields represent minute, hour, day of the month, month, and day of the week. Here's the syntax:
```plaintext
* * * * * command_to_execute
- - - - -
| | | | |
| | | | +----- Day of the week (0 - 7) (Sunday is 0 or 7)
| | | +------- Month (1 - 12)
| | +--------- Day of the month (1 - 31)
| +----------- Hour (0 - 23)
+------------- Minute (0 - 59)
```
#### 2. Edit the User's Cron Jobs
Use the **crontab -e** command to open the cron job editor for the current user. This command opens the user's crontabe file for editting in the default text editor.
```bash
crontab -e
```

#### 3.Schedule the Bash Script
Add an entry to schedule your bash script by specifying the schedule and the command to execute:
```bash
# Schdule a script to run every 0 mins, 4 hours, for every day, month, day of week
0 4 * * * /path/to/your/script.sh
```
#### 4. Save and exit
After adding the entry, save the changes and exit the editor

#### 5. Check Shceduled Scripts
```bash
crontab -l
```

#### Additional Tips:
- Ensure that the script has executable permissions (chmod +x script.sh).
- Specify absolute paths for files, as cron might not use the same environment variables as your interactive shell.
- Redirect output (if necessary) to a specific file within the script itself to capture any output or errors that might occur during execution.

# Debug & Troubleshoot
"Do it work just fine? then do not touch it!!", we need to be able to debug our script, and can catch the error, so we need to be able to deubg our script.

Debugging Bash scripts involves identifying and resolving issues or errors that occur during script execution. There are several techniques and tools available to debug Bash scripts effectively:

## 1. Using 'set -x'
Add '**set -x**' at the beginning of your script to enable debugging mode. This mode displays each command before executing it, allowing you to see the sequence of commands executed.

```bash
#!/bin/bash

set -x
# Your script commands here
```
## 2. echo Statements:
Use '**echo**' statements within the script to print variables, messages, or checkpoints to the terminal. This helps track the flow of the script and identify where issues might occur.

```bash
#!/bin/bash

echo "Starting script..."
# Your script commands here
echo "Script completed."
```
## 3. Redirecting Output and Errors
Redirect standard output and errors to separate files to capture any issues or messages that might not be displayed in the terminal.
```bash
#!/bin/bash

# Redirect standard output to a file
exec > output.log

# Redirect errors to a file
exec 2> error.log

# Your script commands here
```

## 4. set -e
Use '**set -e**' to exit immediately if any command returns a non-zero exit status. This helps in catching errors early in the script execution.
```bash
#!/bin/bash

set -e
# Your script commands here
```

## 5. trap Command
Use trap to catch and handle signals or errors that occur during script execution. This helps perform specific actions when an error occurs.

```bash
#!/bin/bash

trap 'echo "Error occurred"; exit 1' ERR

# Your script commands here
```
## 6. Shellcheck
Use external tools like Shellcheck to statically analyze your Bash script for common issues, syntax errors, and pitfalls

## 7. Debugging with bash -x
Run your script with bash -x script.sh to debug it directly from the command line, enabling debugging mode only for that execution.

## 8. Logging
Implement logging mechanisms within your script to track the execution flow, variable values, and errors encountered during script execution.

# Tips & Tricks
## Braces Expansion
You can use brace expansion feature to allow user to generate list of words or commands.

To use it, enclose a comma-seperated list of workds or command in curly braces.
```bash
touch file.{txt,doc,pdf}

mkdir /var/tmp/{one,two,three}
```
## Braces for Variables
Using braces around a variable name can help to avoid ambiguity and improve readability.
```bash
output_dir=/path/to/directory

echo "The output file is: ${output_dir}"
```
## Command Substitution
It is a good programming tip to use variables for commands substitution instead of 
```bash
current_time=$(date +%Y-%m-%d_%H:%M:%S)
echo "The current time is: $current_time"
```
## Aliases
You can use aliases as shortcuts for commands or command sequences. This could save time and typing by allowing user to use a shorter or more intuitive command.

To create an alias, use the alias command followed by the name of the alias and the command or command sequence you want to alias.

```bash
alias ll="ls -la"
```
## The Watch Command
Use watch command to allows you to execute a command periodically and display the output in real-time.

Useful for monitoring system resources or processess.

To use watch command:
```bash
# display the output of ps aux command every second.
watch -n 1 ps aux
```

## History Expansion
History expansion allows user to reuse commands from your command history.

To use it:
```bash
# return the last command
!!

# return the command two commands ago
!-2
```

# References
- freeCodeCamp - Bash Scripting Tutorial – Linux Shell Script and Command Line for Beginners: [link](https://www.freecodecamp.org/news/bash-scripting-tutorial-linux-shell-script-and-command-line-for-beginners/)
- 10 must-known Bash shell scripting tips and tricks for beginners - [Foos Linux](https://www.fosslinux.com/105140/10-must-know-bash-shell-scripting-tips-and-tricks-for-beginners.htm)
- 10 Bash Tricks Every Developer Should Know - [tecadmin](https://tecadmin.net/bash-tricks-every-developer-should-know/#google_vignette)
- Chatgpt - openAI: [link](https://chat.openai.com)
  