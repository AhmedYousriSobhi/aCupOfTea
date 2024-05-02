# This is a daily notes in our life

# Table of Notes
- [This is a daily notes in our life](#this-is-a-daily-notes-in-our-life)
- [Table of Notes](#table-of-notes)
- [17 Apr 2024 - Pytorch Deprecation for MacOS Intel X64](#17-apr-2024---pytorch-deprecation-for-macos-intel-x64)
- [17 Apr 2024 - The Zen of Python](#17-apr-2024---the-zen-of-python)

# 17 Apr 2024 - Pytorch Deprecation for MacOS Intel X64
According to latest [update](https://pytorch.org/blog/pytorch2-2/) in Pytorch 2.2, They are starting to deprecated pytorch starting from version 2.2.x for MacOS x64 support.

Investigating in [Apple announcement](https://discuss.circleci.com/t/macos-intel-support-deprecation-in-january-2024/48718), at the end of 28 June 2024, they will stop producing Mac with Intel processors, and instead they'll use their own Apple silicon resources.

So Pytorch sees no potential in investing the development in MacOS x64 binaries, as there will be lower resources in the future.

So the decision is made.

# 17 Apr 2024 - The Zen of Python
Tim Peters illustrate the [20 Python coding principles](https://peps.python.org/pep-0020/#the-zen-of-python) to follow for any developer, whoever a starter or coming from different language, and listed them in what are named as "[THE ZEN OF PYTHON](https://mail.python.org/pipermail/python-list/1999-June/001951.html)"

Want to know them? we are coders so let's run this easter egg code: 
```py
import this
```
