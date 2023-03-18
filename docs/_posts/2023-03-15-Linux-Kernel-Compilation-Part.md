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

For our third post, let's revisit one of my favorite topics from earlier in my career viz. building the Linux kernel. Last time I worked with the kernel was during it's 3.x days. Quite a few things must have changed between then and now (obviously). It appears that even the process of building has some considerations that need to be kept in mind.

I've chosen v5.10 of the linux kernel. Also, since I use source insight as the IDE of choice for C/C++ projects, I'll use winscp to share changes to files, as SI only runs on windows. However this requires some prepation that I outline below

1. We'll need to keep the local and remote linux repos in sync using WinSCP. However, windows by default is case in-sensitive, which is a problem as certain files under the source tree have exactly the same path but different case. Luckily, Windows now has a way to enable case sensivity on a [per folder basis](https://learn.microsoft.com/en-us/windows/wsl/case-sensitivity). Before doing this however, we need to [enable WSL](https://learn.microsoft.com/en-us/windows/wsl/install). If you are on an older version of Windows 10, then you need this [alternate method](https://linuxhint.com/enable-wsl-optional-component/) to install WSL. After installing WSL, reboot the host. Then, navigate to the folder on the windows host where you'd like to enable case sensitivity and issue `fsutil.exe file setCaseSensitiveInfo %cd% enable`. Make sure to do this **_before_** you get the source, since case sensitivity is inherited from the parent for new directories *NOT* applied recursively to an existing tree structure. 

2. Secondly, on windows, it is apparently ***illegal*** to have a file name that [starts with 'aux'](https://github.com/analogdevicesinc/linux/issues/111) and some of the driver files in Linux have exactly that name (ouch). Due to this it is impossible to use git to checkout the source code directly on the terminal. To workaround this annoying issue, use it from git-bash or cygwin. Make sure that you are in the folder for which you've enabled case sensitivity as shown above. We are now ready to clone the repo here. Additionally, since I do not want the entire history of the kernel (which is tbh humungous), I just clone tag v5.10 like so `git clone --depth 1 --branch $tagno git@github.com:torvalds/linux.git`.

After taking care of these windows peculiarities and cloning kernel v5.10, it's time to build it. We need a starting point for the kernel, and since I do not have anything particular in mind (vis-a-vis a board or a target configuration), I'll use the currently loaded modules to create a config file and then make changes to it.
   ```
   $linux# lsmod > ../lsmod_running
   $linux# make LSMOD=../lsmod_running localmodconfig
   $linux# make menuconfig
   ```   
The make the following changes to the options:
   ```
   -KVM n
   -STACKPROTECTOR_STRONG y
    DEBUG_INFO_BTF y -> n
    IKCONFIG m -> y
    IKCONFIG_PROC n -> y
    KERNEL_GZIP n -> y
    KERNEL_ZSTD y -> n
    LOCALVERSION "" -> "Test"
    STACKPROTECTOR y -> n
    VIRTUALIZATION y -> n
   ```
Start the build process like so `make -j ($nproc * 2) all` where `nproc` indicates the total number of cores as indicated by `nproc`. After a while it fails like so:
   ```
   make[1]: *** No rule to make target 'debian/canonical-revoked-certs.pem', needed by 'certs/x509_revocation_list'.  Stop.
   make[1]: *** Waiting for unfinished jobs....
   ```
   
   A bit of googling tells me [how](https://stackoverflow.com/questions/67670169/compiling-kernel-gives-error-no-rule-to-make-target-debian-certs-debian-uefi-ce) to fix this. I install the canonical certificates as indicated and continue the build. The build completes by creating an uncompressed vmlinux kernel image, the symbol file (System.map) and a bootable compressed kernel image, which for the x86_64 arch is referred to as a bZimage (big zImage).
   
   We then proceed to install the modules and complete the final installation. But it is advisable to shut down the VM and take a snapshot. So in case if things don't workout the way it should, we can always return to this point in time and reconfigure the kernel. The boot process can fail due to very many reasons, the most common being initramfs (initramfs) [not installed properly](https://varunsaklani.wordpress.com/2019/08/01/kernel-panic-initramfs-image-not-found/). Once you've taken the snapshot, turn the VM on and navigate back to this directory. Obviously, the next step in the process is to install our (hopefully) shiny new kernel <br/>
   
   `$linux# make modules && sudo make modules_install && sudo make install`
   
   We use `sudo` as installing the kernel implies copying the compressed image, the system-map as well as the initramfs files to `/boot` which requires elevated privileges. We can now reboot the VM and it will attempt to boot into our new kernel, failing which it will revert back to the original. However, since we'd like our kernel to show up in the list of kernels, we need to let GRUB know that we have a newer kernel. But first, we need to configure grub itself so it pauses for a while to give us a chance to select the kernel to boot into.
   ```
   sudo cp /etc/default/grub /etc/default/grub.orig
   sudo vim /etc/default/grub
   ```
   Make the following changes in the file and issue `sudo update-grub` once done.
   ```
   GRUB_HIDDEN_TIMEOUT_QUIET=false
   GRUB_TIMEOUT=10
   #GRUB_HIDDEN_TIMEOUT=1
   #GRUB_TIMEOUT_STYLE=hidden
   ```
   Lets reboot the VM now. This time, there's a 10s delay between the grub menu being displayed and the kernel to boot being auto selected. Press the down arrow key, selecting 'advanced options for ubuntu'. Press return and select our kernel from the list hoping for the best. So we do that and voila! Things are finally looking good. We can check if we've indeed booted into the kernel we compiled using `uname -r` and it should show the 'test' string we appended to the local version. We are finally ready to roll with kernel module experimentation. But that's for another post!
