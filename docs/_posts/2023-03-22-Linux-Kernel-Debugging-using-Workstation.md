---
layout: post
title:  "Linux Kernel Debugging using Workstation"
date:   2023-03-22 10:30:48 +0530
tags:
   - Debugging
   - Linux
   - Kernel
---

Hello there fellas!

Let's [continue](https://redbilledpanda.github.io/2023/03/19/Linux-Kernel-Compilation-PartII.html) our (mis)adventure(😁) with the Linux kernel. We ran into an OOPs but due to lack of time (and inclination 😃), we had to delay the task. Well, this time around, we'll try to get it addressed or at least have our debugging setup fixed.

Our Linux Kernel debugging setup consists of two virtual machines, quite similar to our [FreeBSD kernel debugging](https://redbilledpanda.github.io/2023/03/11/Kernel-Debugging-using-workstation.html). One of them would drive the debug process, we'll call that VM as the debugger VM, also called the Master. It's peer VM will host the kernel that would be debugged; we'll call that the debugee or the slave VM. We'll have them connected using a windows named pipe, similar to what we did with our FreeBSD setup. Refer to that post for pictures explaining this.

Once that has been setup, start the master VM first, this will create the named pipe. Add the user to the `dialout` group like so: `usermod -a -G dialout $USER`. Repeat the process for the slave VM. Linux unlike FreeBSD, mandates access to the serial port via the `dialout` group. In Linux, you can't access the serial port, even as root. Only a user from the `dialout` group has access to it. Having added ourselves to this `dialout` group, restart the master and then the slave VM. Once both the VMs are up, try to use the (virtual) serial connection between them for simple communication. This is to make sure that our serial port is indeed behaving the way it should.

On the master, grep the startup kernel log to check the device node for our serial port:
```
sudo dmesg | grep -i tty
```
Most likely it would be `/dev/ttyS0`. Check on the slave and most likely you'll find that it's the same node. Then establish a connection between the VMs using the `cu` utility like so: `cu -l $your-serial-device-node -s 115200`. Run this on both the VMs. Type something on the master and you should see it on the slave and vice versa. There's no echo by default so make sure your test strings are different. Having confirmed the connection issue a `~.` on both the ends to disconnect. Finally our VMs are connected!

We now turn our attention on the slave VM. We'll need to make sure the kernel is properly configured to supported debugging over a serial console. It's important to pause here and think about the setup. Since we are debugging the kernel, we'll need another machine to debug it. A surgeon cannot perform surgery on himself and needs another one to operate on him. So does the kernel (🙂). On the slave VM, we need to set the following kernel config options:

```
CONFIG_FRAME_POINTER=Y
CONFIG_KGDB=Y
CONFIG_KGDB_SERIAL_CONSOLE=Y
CONFIG_KGDB_KDB=Y
CONFIG_KDB_KEYBOARD=Y (optional)
CONFIG_KALLSYMS=Y
CONFIG_CONSOLE_POLL=Y
CONFIG_MAGIC_SYSRQ=Y
CONFIG_PANIC_ON_OOPS=Y
```
If your current kernel has the `CONFIG_IKCONFIG` and `CONFIG_IKCONFIG_PROC` config options set, you may grep for a config parameter on the currently running kernel like so `zcat /proc/config.gz | grep $configname`. If all these parameters are already set on your kernel, you're good to go. Else, we need a (re)compile and a (re)install as explained [previously](https://redbilledpanda.github.io/2023/03/15/Linux-Kernel-Compilation-Part.html). 

In my case, the only config option that was ***not*** set was `CONFIG_PANIC_ON_OOPS` and luckily, this can be passed on the kernel command line like so `oops=panic`. In addition, one needs to append the following to the kernel command line: `console=tty0 kgdboc=ttyS0,115200 nokaslr`. We need to disable [KASLR](https://www.ibm.com/docs/en/linux-on-systems?topic=shutdown-kaslr) to allow gdb to properly translate addressesses into symbols. One crude way to modify the kernel command line precisely for a given GRUB menu entry is to directly modify the `/boot/grub/grub.cfg` file. Locate the corresponding menuentry here and make modifications as you need. I prefer it to the rather convoluted (IMHO) way of creating custom grub2 entries (which somehow never work for me anyways). So after modifying the menu-entry, we restart the client VM.

On the server VM, navigate to the kernel source directory. While at the top, fire up gdb passing the uncompressed kernel binary `vmlinux` as an argument as such `sudo gdb vmlinux`. Now, on the client, force a sysrq like so `echo g > /proc/sysrq-trigger` which will drop the kernel to the debugger. For this to work, write a 1 to this proc entry `/proc/sys/kernel/sysrq`. Additionally, make sure that we are indeed configured to panic on oops like so:
   ```
   sysctl kernel.panic_on_oops
   ```
If it gives a value of 0 change it to 1 like so `sudo sysctl kernel.panic_on_oops=1`. In addition, sometimes, the systemd service timeout might cause the system to freeze. This is because the systemd daemon will kill the service if it's watchdog encounters a timeout (which by default is set at 3m on Ubuntu 22). Typically, you'll see messages like these:

![image](https://user-images.githubusercontent.com/46345560/230270093-0536505e-9462-4fb6-bd71-cd1596deee28.png)

If that happens, then your debugger might not get the input it needs so your debugging environment is no longer useful. One easy way to disable the timeout is by adding `RuntimeWatchdogSec=0` to `/etc/systemd/system.conf` and rebooting the system. More info [here](https://0pointer.de/blog/projects/watchdog.html). Assuming we've done all this we are now ready to start the debugging session. Since our master is already connected via the serial port and we've enabled serial console based debugging (via the `CONFIG_KGDB_SERIAL_CONSOLE` option), we can now ask the gdb instance on the master to connect to the serial port like so `target remote /dev/ttyS0`. Once connected, it will connect to the thread that fired the sysrq trigger. Issue the `backtrace` command to check the backtrace within that thread.

```
(gdb) target remote /dev/ttyS0
Remote debugging using /dev/ttyS0
warning: multi-threaded target stopped without sending a thread-id, using first non-exited thread
[Switching to Thread 4294967294]
kgdb_breakpoint () at kernel/debug/debug_core.c:1224
1224            wmb(); /* Sync point after breakpoint */
(gdb) bt
#0  kgdb_breakpoint () at kernel/debug/debug_core.c:1224
#1  0xffffffff811aa27e in sysrq_handle_dbg (key=<optimized out>) at kernel/debug/debug_core.c:967
#2  0xffffffff81c73280 in __handle_sysrq (key=103, check_mask=check_mask@entry=false) at drivers/tty/sysrq.c:598
#3  0xffffffff817c4ea8 in write_sysrq_trigger (file=<optimized out>, buf=<optimized out>, count=2, ppos=<optimized out>) at drivers/tty/sysrq.c:1157
#4  0xffffffff813ecb3a in pde_write (ppos=<optimized out>, count=<optimized out>, buf=<optimized out>, file=<optimized out>, pde=0xffff88800eb42840) at fs/proc/inode.c:345
#5  proc_reg_write (file=<optimized out>, buf=<optimized out>, count=<optimized out>, ppos=<optimized out>) at fs/proc/inode.c:357
#6  0xffffffff81340bf2 in vfs_write (file=file@entry=0xffff88800c1a7d00, buf=buf@entry=0x558115c00cb0 <error: Cannot access memory at address 0x558115c00cb0>, count=count@entry=2, pos=pos@entry=0xffffc900035e3ef0) at fs/read_write.c:603
#7  0xffffffff813410a7 in ksys_write (fd=<optimized out>, buf=0x558115c00cb0 <error: Cannot access memory at address 0x558115c00cb0>, count=2) at fs/read_write.c:658
#8  0xffffffff81341139 in __do_sys_write (count=<optimized out>, buf=<optimized out>, fd=<optimized out>) at fs/read_write.c:670
#9  __se_sys_write (count=<optimized out>, buf=<optimized out>, fd=<optimized out>) at fs/read_write.c:667
#10 __x64_sys_write (regs=<optimized out>) at fs/read_write.c:667
#11 0xffffffff81cba708 in do_syscall_64 (nr=<optimized out>, regs=0xffffc900035e3f58) at arch/x86/entry/common.c:46
#12 0xffffffff81e0008c in entry_SYSCALL_64 () at arch/x86/entry/entry_64.S:120
#13 0x00007fe884ecea00 in ?? ()
#14 0x00007fe884ecf600 in ?? ()
#15 0x00007fe884ed3780 in ?? ()
#16 0x0000000000000002 in fixed_percpu_data ()
#17 0x0000558115c00cb0 in ?? ()
#18 0x0000000000000002 in fixed_percpu_data ()
#19 0x0000000000000246 in ?? ()
#20 0x00007fe884ed2d20 in ?? ()
#21 0x0000558115c00cb0 in ?? ()
#22 0x0000000000000000 in ?? ()
```
While the debugger has control, the debugee would be stalled. SSH connection(s) to the client will get disconnected after a while. We can now examine the backtrace as shown here or switch to another task of our interest. So this officially completes our rather quick and dirty introduction to Linux kernel debugging using windows workstation.
