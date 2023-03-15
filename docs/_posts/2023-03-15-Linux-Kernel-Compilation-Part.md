---
layout: post
title:  "Linux Kernel Compilation: Part I"
date:   2023-03-15 16:42:48 +0530
tags: 
   - Kernel
   - Compilation
   - Linux
---
Hello.

For our third post, let's revisit one of my favorite tech topics from earlier in my career viz. building the Linux kernel. Last time I worked with the kernel was during it's 3.x days. Quite a few things must have changed between then and now (obviously). It appears that even the process of building has some considerations that need to be kept in mind.

I've chosen v5.4 instead of the latest and greatest as it might (hopefully) be less complicated than the one at the top. Also, since I use source insight as the IDE of choice for C/C++ projects, I'll use winscp to share changes to files, as SI only runs on windows. However it appears that we have a couple of issues with this approach:

1. We'll need to keep the local and remote linux repos in sync using WinSCP. However, windows by default is case in-sensitive, which is a problem as certain files under the source tree have exactly the same path but different case. Secondly, on windows, it is apparently ***illegal*** to have a file name that [starts with 'aux'](https://github.com/analogdevicesinc/linux/issues/111) and some of the driver files in Linux have exactly that name (OOPs). 

   Luckily, for the earlier issue, Windows now has a way to enable case sensivity on a [per folder basis](https://learn.microsoft.com/en-us/windows/wsl/case-sensitivity). Before doing this however, we need to [enable WSL](https://learn.microsoft.com/en-us/windows/wsl/install). If you are on an older version of Windows 10, then you need this [alternate method](https://linuxhint.com/enable-wsl-optional-component/) to install WSL. After installing WSL, reboot the host. Then, navigate to the folder on the windows host where you'd like to enable case sensitivity and issue `fsutil.exe file setCaseSensitiveInfo %cd% enable`. Make sure to do this **_before_** you get the source, since case sensitivity is inherited from the parent for new directories *NOT* applied recursively to an existing tree structure. 

   For the second issue, make sure that git is added to your windows system path and then do the clone operation inside of the above folder (_for which you disabled case insensitivity_) under cygwin or cygwin like utilities for instance mobaxterm. Make sure to _never_ navigate to this path using anything windows related, like the windows terminal or file explorer. It's like we are using the fake unix environment provided by cygwin to sneak in those naughty 'aux' files. Additionally, since I do not want the entire history of the kernel (which is tbh humungous), I just clone tag v5.4 like so `git clone --depth 1 --branch $tagno git@github.com:torvalds/linux.git`.

2. Newer version of objtool (packaged as part of binutils) can now skip generating the symbol table for modules that are completely empty. However using an older version of the kernel (before this change went in) with this version of objtool is problematic. This is because, the kernel build process on older versions is not cognizant of the fact and expects a symbol table for each file that gets compiled (as part of the source or as a module). The build process thus fails like this:
   ```bash
   arch/x86/entry/thunk_64.o: warning: objtool: missing symbol table
   make[2]: *** [scripts/Makefile.build:357: arch/x86/entry/thunk_64.o] Error 1
   make[2]: *** Deleting file 'arch/x86/entry/thunk_64.o'
   make[1]: *** [scripts/Makefile.build:509: arch/x86/entry] Error 2
   make[1]: *** Waiting for unfinished jobs....
   ```
   One way to solve this would be to downgrade binutils to somewhere before v2.35. But it is an arduous task and other system packages that assume a newer version of binutils might not work. Luckily, someone figured out a [much better way](https://www.spinics.net/lists/kernel/msg3797871.html) to fix this and we'll be using that instead.

3. The build also breaks during the linking phase (while creating the vmlinux image) with the following error due to the fact that both pgtable_64 and kaslr_64 define `__force_order`. One of the ways to fix this is to declare one of the definitions as an extern as suggested [here](https://lkml.iu.edu/hypermail/linux/kernel/2001.3/05638.html) 
   ```
   LD  arch/x86/boot/compressed/vmlinux
   ld: arch/x86/boot/compressed/pgtable_64.o:(.bss+0x0): multiple definition of `__force_order';
   arch/x86/boot/compressed/kaslr_64.o:(.bss+0x0): first defined here
   ```
   



