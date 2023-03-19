---
layout: post
title:  "Linux Kernel Compilation: Part II"
date:   2023-03-19 14:42:48 +0530
tags: 
   - Kernel
   - Modules
   - Compilation
   - Linux
---
Hello.

To continue from [last time](https://redbilledpanda.github.io/2023/03/15/Linux-Kernel-Compilation-Part.html), lets have a quick recap on building kernel modules for the Linux kernel that we just installed. To get started, navigate to the kernel source directory and run the following command: `make prepare`. This will create a file called `autoconf.h` under `include/generated/`. When compiling modules that are out of tree, the build system will look for this file. This file contains a list of all config options for the kernel against which we are compiling our module.

Here's a sneak peek into it:
```
/*
 *
 * Automatically generated file; DO NOT EDIT.
 * Linux/x86 5.11.0 Kernel Configuration
 *
 */
#define CONFIG_RING_BUFFER 1
#define CONFIG_HAVE_ARCH_SECCOMP_FILTER 1
#define CONFIG_VFIO_PCI_MMAP 1
#define CONFIG_SCSI_DMA 1
#define CONFIG_TWL6040_CORE 1
#define CONFIG_INTEL_IDLE 1
#define CONFIG_TCP_MD5SIG 1
#define CONFIG_KERNEL_GZIP 1
#define CONFIG_CC_HAS_SANCOV_TRACE_PC 1
#define CONFIG_DEFAULT_INIT ""
#define CONFIG_MICROCODE 1
#define CONFIG_ARCH_HAS_DEBUG_VM_PGTABLE 1
#define CONFIG_NEED_PER_CPU_EMBED_FIRST_CHUNK 1
#define CONFIG_INPUT_KEYBOARD 1
#define CONFIG_ARCH_SUPPORTS_INT128 1
#define CONFIG_MEMORY_ISOLATION 1
#define CONFIG_SLUB_CPU_PARTIAL 1
#define CONFIG_RFS_ACCEL 1
#define CONFIG_SERIAL_8250_RT288X 1
#define CONFIG_ARCH_WANTS_THP_SWAP 1
#define CONFIG_CRC32 1
#define CONFIG_I2C_BOARDINFO 1
#define CONFIG_XEN_PV 1
#define CONFIG_MFD_WM831X_I2C 1
#define CONFIG_IMA_APPRAISE_BOOTPARAM 1
#define CONFIG_MEMREGION 1
#define CONFIG_X86_MCE 1
#define CONFIG_SIGNED_PE_FILE_VERIFICATION 1
#define CONFIG_UNICODE 1
#define CONFIG_BLK_SED_OPAL 1
#define CONFIG_FB_TILEBLITTING 1
#define CONFIG_KEY_DH_OPERATIONS 1
#define CONFIG_SECCOMP 1
#define CONFIG_CPU_FREQ_GOV_CONSERVATIVE 1
#define CONFIG_HIGH_RES_TIMERS 1
#define CONFIG_KGDB_HONOUR_BLOCKLIST 1
#define CONFIG_ARCH_HAS_SET_MEMORY 1
#define CONFIG_SECURITY_TOMOYO_MAX_AUDIT_LOG 102
```

Let's write a very simple module and as convention stands, let's call it helloworld. So here's how it looks:
```c
#include <linux/module.h>
#include <linux/init.h>

static int __init helloworld_init(void) {
    printk("\"Hello world initialization!\"\n");
    return 0;
}

static int init_wrapper(void) {
   // calling our init function here
   return helloworld_init();
}

static void __exit helloworld_exit(void) {
    printk("\"Hello world exit, let's try calling init here\"\n");
    init_wrapper();
}

module_init(helloworld_init);
module_exit(helloworld_exit);
MODULE_LICENSE("GPL");
MODULE_AUTHOR("AjB");
MODULE_DESCRIPTION("LKM skeleton");
```
Macros `module_init` and `module_exit` mark the corresponding functions as entry and exit functions respectively. These get executed only once when the driver registers (for a real/virtual device) regardless of whether any device has been enumerated yet or not. These merely place the init and exit code in some pre-defined sections of the kernel image. Remember the kernel image is just another [ELF](https://en.wikipedia.org/wiki/Vmlinux) binary albiet with some additional sections defined compared to your 'regular' *nix binary). It is important to remember that we're talking about built-in modules here. Once these modules have been loaded, the kernel [frees](https://lxr.missinglinkelectronics.com/linux/init/main.c#L1492) all such memory regions marked as`__init` since they'd never be called again until next reboot.

Let's grep for 'helloworld' on /proc/kallsyms. No mention of the __init function here:

```
0000000000000000 r _note_7      [helloworld]
0000000000000000 t helloworld_exit      [helloworld]
0000000000000000 d __this_module        [helloworld]
0000000000000000 t cleanup_module       [helloworld]
```
It gets [removed](https://stackoverflow.com/questions/63689045/init-function-not-present-in-kallsyms) once the module gets loaded. However, I am still able to call this function from within the `__exit` routine through a wrapper which seems strange to me. Although we don't see a matching symbol for `helloworld_init` in the list above, it is not unlikely that the relevant memory (more like cache lines) have not yet been invalidated. So it's possible that I'm just getting lucky here. To ascertain, let's drop them caches after the `__init` routine gets called and see if that causes a kernel panic (since the linked address or the offset should point to a section of memory that it shouldn't touch).
```
Mar 19 18:01:33 aijazVM kernel: [24795.884795] "Hello world initialization!"
Mar 19 18:02:01 aijazVM kernel: [24823.169160] echo (15514): drop_caches: 3
Mar 19 18:02:12 aijazVM kernel: [24834.528229] "Hello world exit, let's try calling init here"
Mar 19 18:02:12 aijazVM kernel: [24834.528232] "Hello world initialization!"
```
As we see above, everything seems A-ok. Perhaps the drop cache mechanism merely causes low level cache lines inside the kernel to get flushed and invalidated but does nothing to the architecure specific caches (think L1/L2/L3 caches) which is why we see what we see above. The only way to be sure would be to tell the underlying CPU to zero the cache lines that have been marked as invalid. But that's an investigation for another post (and day). We've [asked](https://stackoverflow.com/questions/75782076/init-and-exit-attributes-for-loadable-kernel-modules) help from the world wide web and hope to get some pointers.

As for exit, built in modules won't be unloaded so it's safe to have those functions removed. This concludes our (very) brief rejoinder on building Kernel modules. Until next time, adios!
