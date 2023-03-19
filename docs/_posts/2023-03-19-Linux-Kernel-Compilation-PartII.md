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

    This is rather perplexing to see why this would be the case. After a bit of help from the world wide web, it is likely that my (tiny) init function is getting inlined by the compiler which is why it never mattered to the wrapper function. Let's disassemble the binary and check what see:
    ```
    static void __exit helloworld_exit(void) {
       0:	55                   	push   %rbp
        printk("\"Hello world exit, let's try calling init here\"\n");
       1:	48 c7 c7 00 00 00 00 	mov    $0x0,%rdi
    static void __exit helloworld_exit(void) {
       8:	48 89 e5             	mov    %rsp,%rbp
        printk("\"Hello world exit, let's try calling init here\"\n");
       b:	e8 00 00 00 00       	call   10 <cleanup_module+0x10>
        printk("\"Hello world initialization!\"\n");
      10:	48 c7 c7 00 00 00 00 	mov    $0x0,%rdi
      17:	e8 00 00 00 00       	call   1c <cleanup_module+0x1c>
        init_wrapper();
    }    
    ```
   I'm only concerned with the disassenbly for the `__exit` function to check if our `init_wrapper` got inlined. As we can see from the above snippet, it indeed looks like the compiler inlined our `__init` function. Let's modify our source so it looks like this:

   ```C
   #include <linux/module.h>
   #include <linux/init.h>

   #ifdef NOINLINE
    static int  __init __attribute__ ((__noinline__)) helloworld_init(void)  {
   #else
    static int  __init helloworld_init(void)  {
   #endif
        // printk is the kernel's version of printf
        // and is completely defined and implemented
        // as part of the kernel, since it has no glibc 
        // the ubiquitous C library available to all and one
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
    MODULE_AUTHOR("Aijaz Baig");

    MODULE_DESCRIPTION("LKM skeleton");
   ```
   We can conditionally compile the code through the use of a pre-processor like so `make ccflags-y="-DNOINLINE"`. So we do just that and analyze the exit secion again. Here's the snippet below:
   ```asm
    static void __exit helloworld_exit(void) {
       0:	55                   	push   %rbp
        printk("\"Hello world exit, let's try calling init here\"\n");
       1:	48 c7 c7 00 00 00 00 	mov    $0x0,%rdi
    static void __exit helloworld_exit(void) {
       8:	48 89 e5             	mov    %rsp,%rbp
        printk("\"Hello world exit, let's try calling init here\"\n");
       b:	e8 00 00 00 00       	call   10 <cleanup_module+0x10>
       return helloworld_init();
      10:	e8 00 00 00 00       	call   15 <cleanup_module+0x15>
        init_wrapper();
    }   
   ```
   This time we see that although `init_wrapper` got inlined, our `__init` function was not inlined. Now that we know that inlining was causing our module removal to work, let's try to insert and then remove our module. This time, it should trigger a kernel panic.

   Let's tail on the kernel log:
   ```
   Mar 19 11:50:23 KernelVM kernel: [ 7352.434168] helloworld: loading out-of-tree module taints kernel.
    Mar 19 11:50:23 KernelVM kernel: [ 7352.434207] helloworld: module verification failed: signature and/or required key missing - tainting kernel
    Mar 19 11:50:23 KernelVM kernel: [ 7352.434711] "Hello world initialization!"


    Mar 19 11:50:49 KernelVM kernel: [ 7377.897246] "Hello world exit, let's try calling init here"
    Mar 19 11:50:49 KernelVM kernel: [ 7377.897256] BUG: unable to handle page fault for address: ffffffffa06ea000
    Mar 19 11:50:49 KernelVM kernel: [ 7377.897287] #PF: supervisor instruction fetch in kernel mode
    Mar 19 11:50:49 KernelVM kernel: [ 7377.897305] #PF: error_code(0x0010) - not-present page
    Mar 19 11:50:49 KernelVM kernel: [ 7377.897328] PGD 2815067 P4D 2815067 PUD 2816063 PMD 104060067 PTE 0
    Mar 19 11:50:49 KernelVM kernel: [ 7377.897352] Oops: 0010 [#1] SMP PTI
    Mar 19 11:50:49 KernelVM kernel: [ 7377.897365] CPU: 1 PID: 6925 Comm: rmmod Tainted: G           OE     5.11.0kaiwan #4
    Mar 19 11:50:49 KernelVM kernel: [ 7377.897392] Hardware name: VMware, Inc. VMware Virtual Platform/440BX Desktop Reference Platform, BIOS 6.00 02/27/2020
    Mar 19 11:50:49 KernelVM kernel: [ 7377.897425] RIP: 0010:0xffffffffa06ea000
    Mar 19 11:50:49 KernelVM kernel: [ 7377.897441] Code: Unable to access opcode bytes at RIP 0xffffffffa06e9fd6.
    Mar 19 11:50:49 KernelVM kernel: [ 7377.897462] RSP: 0018:ffffc9000455feb0 EFLAGS: 00010246
    Mar 19 11:50:49 KernelVM kernel: [ 7377.897478] RAX: 000000000000002f RBX: 0000000000000000 RCX: 0000000000000000
    Mar 19 11:50:49 KernelVM kernel: [ 7377.897499] RDX: 0000000000000000 RSI: ffff888139e58ac0 RDI: ffff888139e58ac0
    Mar 19 11:50:49 KernelVM kernel: [ 7377.897520] RBP: ffffc9000455feb8 R08: 0000000000000003 R09: 786520646c726f77
    Mar 19 11:50:49 KernelVM kernel: [ 7377.897541] R10: 6163207972742073 R11: 2774656c202c7469 R12: ffffffffa06e4000
    Mar 19 11:50:49 KernelVM kernel: [ 7377.897562] R13: 0000000000000000 R14: 0000000000000000 R15: 0000000000000000
    Mar 19 11:50:49 KernelVM kernel: [ 7377.897583] FS:  00007fba08fb4c40(0000) GS:ffff888139e40000(0000) knlGS:0000000000000000
    Mar 19 11:50:49 KernelVM kernel: [ 7377.897607] CS:  0010 DS: 0000 ES: 0000 CR0: 0000000080050033
    Mar 19 11:50:49 KernelVM kernel: [ 7377.897624] CR2: ffffffffa06e9fd6 CR3: 00000001062a2001 CR4: 00000000001706e0
    Mar 19 11:50:49 KernelVM kernel: [ 7377.897669] Call Trace:
    Mar 19 11:50:49 KernelVM kernel: [ 7377.897682]  ? helloworld_exit+0x15/0x1000 [helloworld]
    Mar 19 11:50:49 KernelVM kernel: [ 7377.897702]  __do_sys_delete_module.constprop.0+0x183/0x290
    Mar 19 11:50:49 KernelVM kernel: [ 7377.897723]  __x64_sys_delete_module+0x12/0x20
    Mar 19 11:50:49 KernelVM kernel: [ 7377.897739]  do_syscall_64+0x38/0x90
    Mar 19 11:50:49 KernelVM kernel: [ 7377.897752]  entry_SYSCALL_64_after_hwframe+0x44/0xa9
    Mar 19 11:50:49 KernelVM kernel: [ 7377.897772] RIP: 0033:0x7fba090dcc9b
    Mar 19 11:50:49 KernelVM kernel: [ 7377.897785] Code: 73 01 c3 48 8b 0d 95 21 0f 00 f7 d8 64 89 01 48 83 c8 ff c3 66 2e 0f 1f 84 00 00 00 00 00 90 f3 0f 1e fa b8 b0 00 00 00 0f 05 <48> 3d 01 f0 ff ff 73 01 c3 48 8b 0d 65 21 0f 00 f7 d8 64 89 01 48
    Mar 19 11:50:49 KernelVM kernel: [ 7377.897841] RSP: 002b:00007ffc38594b38 EFLAGS: 00000206 ORIG_RAX: 00000000000000b0
    Mar 19 11:50:49 KernelVM kernel: [ 7377.897864] RAX: ffffffffffffffda RBX: 000056412e7be760 RCX: 00007fba090dcc9b
    Mar 19 11:50:49 KernelVM kernel: [ 7377.897885] RDX: 000000000000000a RSI: 0000000000000800 RDI: 000056412e7be7c8
    Mar 19 11:50:49 KernelVM kernel: [ 7377.897907] RBP: 0000000000000000 R08: 0000000000000000 R09: 0000000000000000
    Mar 19 11:50:49 KernelVM kernel: [ 7377.897929] R10: 00007fba09174ac0 R11: 0000000000000206 R12: 00007ffc38594d90
    Mar 19 11:50:49 KernelVM kernel: [ 7377.898448] R13: 000056412e7be2a0 R14: 00007ffc385967d1 R15: 000056412e7be760
    Mar 19 11:50:49 KernelVM kernel: [ 7377.898967] Modules linked in: helloworld(OE-) rfcomm bnep intel_rapl_msr vmw_balloon intel_rapl_common rapl joydev input_leds serio_raw btusb btrtl btbcm btintel bluetooth ecdh_generic ecc binfmt_misc mac_hid vsock_loopback vmw_vsock_virtio_transport_common vmw_vsock_vmci_transport vsock vmw_vmci sch_fq_codel ipmi_devintf ipmi_msghandler msr parport_pc ppdev lp parport ramoops reed_solomon pstore_blk pstore_zone efi_pstore ip_tables x_tables autofs4 btrfs blake2b_generic libcrc32c xor zstd_compress raid6_pq dm_mirror dm_region_hash dm_log vmwgfx drm_kms_helper syscopyarea sysfillrect sysimgblt fb_sys_fops cec hid_generic rc_core ttm drm crct10dif_pclmul crc32_pclmul ghash_clmulni_intel aesni_intel usbhid glue_helper crypto_simd hid cryptd psmouse mptspi scsi_transport_spi pcnet32 i2c_piix4 ahci mptscsih libahci mii mptbase pata_acpi
    Mar 19 11:50:49 KernelVM kernel: [ 7377.904396] CR2: ffffffffa06ea000
    Mar 19 11:50:49 KernelVM kernel: [ 7377.905062] ---[ end trace a91eefd903d9976d ]---
    Mar 19 11:50:49 KernelVM kernel: [ 7377.905681] RIP: 0010:0xffffffffa06ea000
    Mar 19 11:50:49 KernelVM kernel: [ 7377.906273] Code: Unable to access opcode bytes at RIP 0xffffffffa06e9fd6.
    Mar 19 11:50:49 KernelVM kernel: [ 7377.906890] RSP: 0018:ffffc9000455feb0 EFLAGS: 00010246
    Mar 19 11:50:49 KernelVM kernel: [ 7377.907505] RAX: 000000000000002f RBX: 0000000000000000 RCX: 0000000000000000
    Mar 19 11:50:49 KernelVM kernel: [ 7377.908080] RDX: 0000000000000000 RSI: ffff888139e58ac0 RDI: ffff888139e58ac0
    Mar 19 11:50:49 KernelVM kernel: [ 7377.908650] RBP: ffffc9000455feb8 R08: 0000000000000003 R09: 786520646c726f77
    Mar 19 11:50:49 KernelVM kernel: [ 7377.909267] R10: 6163207972742073 R11: 2774656c202c7469 R12: ffffffffa06e4000
    Mar 19 11:50:49 KernelVM kernel: [ 7377.909836] R13: 0000000000000000 R14: 0000000000000000 R15: 0000000000000000
    Mar 19 11:50:49 KernelVM kernel: [ 7377.910429] FS:  00007fba08fb4c40(0000) GS:ffff888139e40000(0000) knlGS:0000000000000000
    Mar 19 11:50:49 KernelVM kernel: [ 7377.911031] CS:  0010 DS: 0000 ES: 0000 CR0: 0000000080050033
    Mar 19 11:50:49 KernelVM kernel: [ 7377.911608] CR2: ffffffffa06e9fd6 CR3: 00000001062a2001 CR4: 00000000001706e0
   ```
   As expected, we were able to get the kernel to panic and generate an OOPs message. There's a ton of information in this OOPs message, but that's for another day and post.                                                
