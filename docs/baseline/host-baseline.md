# Host Baseline

This document captures the baseline system state of the machine hosting
the Enterprise Cloud Platform Simulator (ECPS).

All data below is generated directly from the host OS.

---

## OS Information
rohan@rohan-Nitro-AN515-56:~$ lsb_release -a
No LSB modules are available.
Distributor ID:	Ubuntu
Description:	Ubuntu 22.04.5 LTS
Release:	22.04
Codename:	jammy

## Kernel
rohan@rohan-Nitro-AN515-56:~$ uname -a
Linux rohan-Nitro-AN515-56 6.8.0-94-generic #96~22.04.1-Ubuntu SMP PREEMPT_DYNAMIC Fri Jan 16 13:19:05 UTC 2 x86_64 x86_64 x86_64 GNU/Linux

## Memory
rohan@rohan-Nitro-AN515-56:~$ free -h
               total        used        free      shared  buff/cache   available
Mem:            31Gi       1.7Gi        25Gi       722Mi       3.6Gi        28Gi
Swap:          2.0Gi          0B       2.0Gi


## CPU
rohan@rohan-Nitro-AN515-56:~$ lscpu
Architecture:             x86_64
  CPU op-mode(s):         32-bit, 64-bit
  Address sizes:          39 bits physical, 48 bits virtual
  Byte Order:             Little Endian
CPU(s):                   8
  On-line CPU(s) list:    0-7
Vendor ID:                GenuineIntel
  Model name:             11th Gen Intel(R) Core(TM) i5-11300H @ 3.10GHz
    CPU family:           6
    Model:                140
    Thread(s) per core:   2
    Core(s) per socket:   4
    Socket(s):            1
    Stepping:             1
    CPU max MHz:          4400.0000
    CPU min MHz:          400.0000
    BogoMIPS:             6220.80
    Flags:                fpu vme de pse tsc msr pae mce cx8 apic sep mtrr pge mca cmov pat pse36 clflush dts acpi
                           mmx fxsr sse sse2 ss ht tm pbe syscall nx pdpe1gb rdtscp lm constant_tsc art arch_perfm
                          on pebs bts rep_good nopl xtopology nonstop_tsc cpuid aperfmperf tsc_known_freq pni pclm
                          ulqdq dtes64 monitor ds_cpl vmx est tm2 ssse3 sdbg fma cx16 xtpr pdcm pcid sse4_1 sse4_2
                           x2apic movbe popcnt tsc_deadline_timer aes xsave avx f16c rdrand lahf_lm abm 3dnowprefe
                          tch cpuid_fault epb cat_l2 cdp_l2 ssbd ibrs ibpb stibp ibrs_enhanced tpr_shadow flexprio
                          rity ept vpid ept_ad fsgsbase tsc_adjust bmi1 avx2 smep bmi2 erms invpcid rdt_a avx512f 
                          avx512dq rdseed adx smap avx512ifma clflushopt clwb intel_pt avx512cd sha_ni avx512bw av
                          x512vl xsaveopt xsavec xgetbv1 xsaves split_lock_detect user_shstk dtherm ida arat pln p
                          ts hwp hwp_notify hwp_act_window hwp_epp hwp_pkg_req vnmi avx512vbmi umip pku ospke avx5
                          12_vbmi2 gfni vaes vpclmulqdq avx512_vnni avx512_bitalg avx512_vpopcntdq rdpid movdiri m
                          ovdir64b fsrm avx512_vp2intersect md_clear ibt flush_l1d arch_capabilities
Virtualization features:  
  Virtualization:         VT-x
Caches (sum of all):      
  L1d:                    192 KiB (4 instances)
  L1i:                    128 KiB (4 instances)
  L2:                     5 MiB (4 instances)
  L3:                     8 MiB (1 instance)
NUMA:                     
  NUMA node(s):           1
  NUMA node0 CPU(s):      0-7
Vulnerabilities:          
  Gather data sampling:   Mitigation; Microcode
  Itlb multihit:          Not affected
  L1tf:                   Not affected
  Mds:                    Not affected
  Meltdown:               Not affected
  Mmio stale data:        Not affected
  Reg file data sampling: Not affected
  Retbleed:               Not affected
  Spec rstack overflow:   Not affected
  Spec store bypass:      Mitigation; Speculative Store Bypass disabled via prctl
  Spectre v1:             Mitigation; usercopy/swapgs barriers and __user pointer sanitization
  Spectre v2:             Mitigation; Enhanced / Automatic IBRS; IBPB conditional; RSB filling; PBRSB-eIBRS SW seq
                          uence; BHI SW loop, KVM SW loop
  Srbds:                  Not affected
  Tsx async abort:        Not affected
  Vmscape:                Not affected




## Disk
rohan@rohan-Nitro-AN515-56:~$ df -h
Filesystem      Size  Used Avail Use% Mounted on
tmpfs           3.2G  2.6M  3.2G   1% /run
/dev/nvme1n1p4  196G   23G  163G  13% /
tmpfs            16G   28M   16G   1% /dev/shm
tmpfs           5.0M  4.0K  5.0M   1% /run/lock
efivarfs        248K  187K   57K  77% /sys/firmware/efi/efivars
/dev/nvme0n1p1   96M   63M   34M  65% /boot/efi
tmpfs           3.2G  124K  3.2G   1% /run/user/1000
