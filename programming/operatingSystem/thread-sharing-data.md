# Operating System - Thread Data Sharing

# Java - Without Notion of Global Data!
From reference Operating System Concepts 10th edition, chapter 4.4 - thread libraries:
```
For POSIX and Windows threading, any data declared globally—that is,
declared outside of any function—are shared among all threads belonging to
the same process. Because Java has no equivalent notion of global data, access
to shared data must be explicitly arranged between threads
```

Let's first get how Jave handles data sharing among threads compared to language that support global data!

**Global Data vs Shared Data in Java**
1. ***Global Data in other language***
    - In languages like C or C++, you can declare variables as global, which means they are accessible from any function of part of the program.
    - These global variables can be shared among different threads without any special arrangement.
2. ***Java's Approach***
    - Java does not support global variables in the same way. Instead, all data in java is encapsulated within classes. Variables that need to be shared among threads must be explicitly defined as field within a class.
    - To share data between threads, you need to make fields accessible to all threads that need to use them. This typically involves passing references to shared objects or using static fields within classes. 

- Because multiple threads can access shared data simultaneously, explicit synchronization is necessary to prevent race conditions and ensure data consistency. 

**Java Code Examples for Explicit Arrangement for Shared Data**
1. ***Instance variables***: define instance variables in an object and pass references to this object to all threads that need to share the data.
    ```java
    public class SharedData {
        public int counter = 0;
    }

    public class MyThread extends Thread {
        private SharedData sharedData;

        public MyThread(SharedData sharedData) {
            this.sharedData = sharedData;
        }

        public void run() {
            // Access and modify shared data
            synchronized(sharedData) {
                sharedData.counter++;
            }
        }
    }

    public class Main {
        public static void main(String[] args) {
            SharedData sharedData = new SharedData();
            Thread t1 = new MyThread(sharedData);
            Thread t2 = new MyThread(sharedData);
            t1.start();
            t2.start();
        }
    }
    ```
    - In this example, *SharedData* is an object with a shared variable *counter*. Both threads *t1* & *t2* can access and modify *counter*.
2. ***Static Variables***: define a static variable, which belong to the class rather than any particular instance.
    ```java
        public class SharedClass {
        public static int counter = 0;
    }

    public class MyThread extends Thread {
        public void run() {
            // Access and modify shared data
            synchronized(SharedClass.class) {
                SharedClass.counter++;
            }
        }
    }

    public class Main {
        public static void main(String[] args) {
            Thread t1 = new MyThread();
            Thread t2 = new MyThread();
            t1.start();
            t2.start();
        }
    }
    ```
    - *counter* is a static variable in *SharedClass*, shared by all instance of *MyThread*.
    - This code might suffer from an issue, that we need to ensure that changes to *counter* are visible to all threads immediately, this suggest adding the *volatile* keyword to *public static volatile int counter = 0;*
