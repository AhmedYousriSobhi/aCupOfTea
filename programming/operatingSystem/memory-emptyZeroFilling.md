# Empty Memory Fill with Zeros ?!

The title of this blog is a question, but actually they are two separate questions!
- Why to set values to new free/empty memory? 
- Why to use Zero as a filling value?

You can say, it's for the purpose to *know this is a new empty memory*, but why so? 

In multi-user systems, where multiple users shares the same memory, but each one has a dedicated memory dedicated to, allocated/defined by the operating system. When a user ask the memory management controller to allocate new RAM memory, so it could take free-disk space that was belonging to other users who no longer uses them. in this case the user who asks for new memory, could simply go through the contents of the memory that no longer used by their users, which could contain important information. This is the need for filling the empty unused memory with some certain defined value (which will be zero).
- Note, without asking for new memory to allocate, any user could simply read (not write) any memory block in the system, that no longer belongs to certain users for now, so the user could simply know its last contents.

Why filling with zeros? Not very important questions, as it was the defined value in OS to set any free memory to zeros.

So over the years, the developers of OS in memory management section, they developed new techniques to how fill unused/free memory to zeros, they are interesting to search and take a look to the magnificent strategies they used.

# References
- The Insane Hackers Guild, Python sub-branch. Why your fresh new memory pages are zero-filled. Jan 2010. [https://utcc.utoronto.ca/~cks/space/blog/tech/WhyZeroMemoryPages?showcomments#comments](https://utcc.utoronto.ca/~cks/space/blog/tech/WhyZeroMemoryPages?showcomments#comments)
- Microsoft Learn. PDC10: Mysteries of Windows Memory Management Revealed: Part Two. 2010. [https://learn.microsoft.com/en-us/archive/blogs/tims/pdc10-mysteries-of-windows-memory-management-revealed-part-two](https://learn.microsoft.com/en-us/archive/blogs/tims/pdc10-mysteries-of-windows-memory-management-revealed-part-two)