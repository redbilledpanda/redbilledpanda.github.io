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

I've chosen v5.4 instead of the latest and greatest as it might (hopefully) be less complicated than the one at the top. Also, since I use source insight as the IDE of choice for C/C++ projects, I'll use winscp to share changes to files, as SI only runs on windows. However this requires some prepation that I outline below

1. We'll need to keep the local and remote linux repos in sync using WinSCP. However, windows by default is case in-sensitive, which is a problem as certain files under the source tree have exactly the same path but different case. Luckily, Windows now has a way to enable case sensivity on a [per folder basis](https://learn.microsoft.com/en-us/windows/wsl/case-sensitivity). Before doing this however, we need to [enable WSL](https://learn.microsoft.com/en-us/windows/wsl/install). If you are on an older version of Windows 10, then you need this [alternate method](https://linuxhint.com/enable-wsl-optional-component/) to install WSL. After installing WSL, reboot the host. Then, navigate to the folder on the windows host where you'd like to enable case sensitivity and issue `fsutil.exe file setCaseSensitiveInfo %cd% enable`. Make sure to do this **_before_** you get the source, since case sensitivity is inherited from the parent for new directories *NOT* applied recursively to an existing tree structure. 

2. Secondly, on windows, it is apparently ***illegal*** to have a file name that [starts with 'aux'](https://github.com/analogdevicesinc/linux/issues/111) and some of the driver files in Linux have exactly that name (OOPs). Due to this it is impossible to use git to checkout the tag directly. To workaround this annoying issue, make sure that git is added to your windows system path. Then, open up cygwin and keeping in mind that we just disabled case sensitivity on the aforementioned folder, navigate to it. We are now ready to clone the repo here. Additionally, since I do not want the entire history of the kernel (which is tbh humungous), I just clone tag v5.4 like so `git clone --depth 1 --branch $tagno git@github.com:torvalds/linux.git`.

After taking care of these windows peculiarities and cloning kernel v5.4, it's time to build it. We need a starting point for the kernel, and since I do not have anything particular in mind (vis-a-vis a board or a target configuration), I'll start with the default config for our architecture, x86_64. 
   ```
   $linux# make defconfig
   $linux# make localmodconfig
   ```
The build process fails like this:
   ```
   arch/x86/entry/thunk_64.o: warning: objtool: missing symbol table
   make[2]: *** [scripts/Makefile.build:357: arch/x86/entry/thunk_64.o] Error 1
   make[2]: *** Deleting file 'arch/x86/entry/thunk_64.o'
   make[1]: *** [scripts/Makefile.build:509: arch/x86/entry] Error 2
   make[1]: *** Waiting for unfinished jobs....
   ```
   A bit of googling tells me that the newer version of objtool (packaged as part of binutils) can now skip generating the symbol table for modules that are completely empty. However using an older version of the kernel (before this change went in) with this version of objtool is problematic. This is because, the kernel build process on older versions is not cognizant of the fact and expects a symbol table for each file that gets compiled (as part of the source or as a module). Here we see how tightly coupled the kernel build process is with various build tools.
   One way to solve this would be to downgrade binutils to somewhere before v2.35. But it is an arduous task and other system packages that assume a newer version of binutils might not work. Luckily, someone figured out a [much better way](https://www.spinics.net/lists/kernel/msg3797871.html) to fix this and we'll be using that instead. We apply that patch and move on. This time it fails at the very end (linking stage) like so:
   ```
   LD  arch/x86/boot/compressed/vmlinux
   ld: arch/x86/boot/compressed/pgtable_64.o:(.bss+0x0): multiple definition of `__force_order';
   arch/x86/boot/compressed/kaslr_64.o:(.bss+0x0): first defined here
   ```
   This is due to the fact that both pgtable_64 and kaslr_64 define `__force_order`. One of the ways to fix this is to declare one of the definitions as an extern as suggested [here](https://lkml.iu.edu/hypermail/linux/kernel/2001.3/05638.html). So that's what we do and carry on. Finally the build succeeds which we can tell as it says the bzImage for our architecture (x86) is ready.
   ```
   Kernel: arch/x86/boot/bzImage is ready  (#1)

   real    5m33.243s
   user    19m1.973s
   sys     2m30.680s
   ```
   As one can see above, it took me close to 5m33s to compile the kernel. However I had issued a parallel make command using 8 threads (on 4 vCPUs). Which is why we see that the total time it took across all cores was close to 20m (indicated by the user time above). Now this is multi-core in action.
   
   It also builds the uncompressed kernel (_vmlinux_) and generates the system.map file (symbol table) which can be used for debugging purposes.

   ![image](https://user-images.githubusercontent.com/46345560/225513195-41cd62b1-85f6-4344-8737-dcfc0302298e.png)
   
   We are ready to install loadable modules (if any)
   `$linux# make modules_install`
   It is advisable to shut down the VM and take a snapshot. So in case if things don't workout the way it should, we can always return to this point in time and reconfigure the kernel. The boot process can fail due to very many reasons, the most common being initial rootfs (initramfs) was [not installed properly](https://varunsaklani.wordpress.com/2019/08/01/kernel-panic-initramfs-image-not-found/). Once you've taken the snapshot, turn the VM on and navigate back to this directly. Obviously, the next step in the process is to install our (hopefully) shiny new kernel
   `#linux# sudo make install`
      We use `sudo` as installing the kernel implies copy the compress image, the system-map as well as the initramfs files to `/boot` which requires elevated privileges. We can now reboot the VM and it will attempt to boot from ur new kernel, failing which it will revert back to the original. However, since we'd like our kernel to show up in the list of kernels, we need to let GRUB know that we have a newer kernel. But first configure grub:
   ```
   sudo cp /etc/default/grub /etc/default/grub.orig
   sudo vi /etc/default/grub
   GRUB_HIDDEN_TIMEOUT_QUIET=false
   GRUB_TIMEOUT=10
   #GRUB_HIDDEN_TIMEOUT=1
   #GRUB_TIMEOUT_STYLE=hidden
   ```
   Lets reboot the VM now. This time, there's a 10s delay between the grub menu being displayed the kernel to boot being selected. So we select our kernel and right on cue something failed
![image](https://user-images.githubusercontent.com/46345560/225518150-63a4b904-1afa-4848-91cf-74bafe929204.png)
   <br/>
   Googling it a bit it [appears](https://bbs.archlinux.org/viewtopic.php?id=252429) that the default compression algorithm employed by `mkinitcpio` is now ZSTD which used to be lz4 earlier (before kernel v5.9 apparently). Ah the perils of compiling a (slightly) older kernel on a new Linux box! So now we boot into the earlier (original) kernel and configure mkinitcpio to compress the kernel using the `lz4` algorithm since our slightly older kernel doesn't understand _ZSTD_. On our ubuntu box, `mkinitcpio` is called `mminitramfs` and reading the man file (man 8 initramfs) tells us that it's configuration can be controlled by the  `/etc/initramfs-tools/initramfs.conf` file. 
   Then we (re)generate the initramfs and this time we see that it resorted to using `gzip` instead of lz4 as it seems we don't have it installed on our system
   ![image](https://user-images.githubusercontent.com/46345560/225524555-96686bcd-3bd1-4909-a096-c0c30658cd9f.png)
   <br/><br/>
   Upon rebooting, the kernel did boot but we land into the initramfs. So it was able to successfully extract the initial rootfs but apparently was not able to boot into the actual root filesystem. Let's type `exit` at the initramfs prompt and see what it says
   ![image](https://user-images.githubusercontent.com/46345560/225526935-e8c638ec-00b2-49b5-968e-91d7dcdae2d7.png)
   <br/>



   
   



