---
layout: post
title:  "Linux Kernel Compilation: Part I"
date:   2023-03-13 16:42:48 +0530
tags: 
   - Kernel
   - Compilation
   - Linux
---
Hello.

For our third post, let's revisit one of my favorite tech topics from earlier in my career viz. building the Linux kernel. Last time I worked with the kernel was during it's 3.x days. Quite a few things must have changed between then and now (obviously). It appears that even the process of building has some considerations that need to be kept in mind.

We'll be building the code on a shared folder, that is shared between a Linux VM and windows host. I've chosen v5.4 instead of the latest and greatest as it might (hopefully) be less complicated than the one at the top. However it appears that we have a couple of issues with this approach:

1. Newer version of objtool (packaged as part of binutils) can now skip generating the symbol table for modules that are completely empty. However using an older version of the kernel (before this change went in) with this version of objtool is problematic. This is because, the kernel build process on older versions is not cognizant of the fact and expects a symbol table for each file that gets compiled (as part of the source or as a module). The build process thus fails like this:
```bash
arch/x86/entry/thunk_64.o: warning: objtool: missing symbol table
make[2]: *** [scripts/Makefile.build:357: arch/x86/entry/thunk_64.o] Error 1
make[2]: *** Deleting file 'arch/x86/entry/thunk_64.o'
make[1]: *** [scripts/Makefile.build:509: arch/x86/entry] Error 2
make[1]: *** Waiting for unfinished jobs....
```
One way to solve this would be to downgrade binutils to somewhere before v2.35. But it is an arduous task and other system packages that assume a newer version of binutils might not work. Luckily, someone figured out a [much better way](https://www.spinics.net/lists/kernel/msg3797871.html) to fix this and we'll be using that instead.

2. Sharing an exFAT or NTFS folder with a Linux VM is fine but not if you intend to build the kernel on it. Now why would I want to share such a folder? That's because I wish to disable GUI on the VM and hence cannot use an IDE like Source Insight or Visual Studio to browse the code. Luckily, Windows now has a way to enable case sensivity on a [per folder basis](https://learn.microsoft.com/en-us/windows/wsl/case-sensitivity). Before doing this however, we need to [enable WSL](https://learn.microsoft.com/en-us/windows/wsl/install). If you are on an older version of Windows 10, then you need this [alternate method](https://linuxhint.com/enable-wsl-optional-component/) to install WSL. 

After installing WSL, reboot the host. Then enable case sensitivity as discussed above. Make sure to do this before you get the source. I prefer using GitHub to only get v5.4 like so `git clone --depth 1 --branch $tagno git@github.com:torvalds/linux.git`. Make sure that you clone this repo *_after_* enabling case sensitivity on the shared folder.  
