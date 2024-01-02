# thisoldtoolbox-linux
This repo is part of my **This Old Toolbox** set of repos, which collectively host various system administration/management tools I've written over the years, for a variety of platforms and environments. I'm making them public so that others might find the ideas and/or the accumulated knowledge helpful to whatever they need to create.

# Documentation
These tools have extensive in-line documentation in the form of comments.

# Code Style
All over the place, really. In my newer BASH code, I try to follow the [Google BASH Style Guide](https://google.github.io/styleguide/shellguide.html). For Python, I make an effort to adhere to [PEP 8](https://peps.python.org/pep-0008/). However, [I value thorough and well-written comments](https://github.com/QuantumTux/thisoldtoolbox-linux/wiki/What-is-it-About-Documentation%3F) above following a specific code style.

# Warranty
Absolutely none at all. I stand by my work, yes, but I wrote these things for the environment in which I operated at the time. It probably isn't the same as any other environment. If someone tries to use any of my tools without taking the time to examine and understand the code, they're asking for trouble.

# The Library
Most of the tools written in BASH rely upon a BASH library that is part of this repo. It might seem to be a little overkill, but there's history behind it.

<details>

<summary>Why I Created a BASH Library</summary>

  I started developing tools in a PaaS environment hosting RHEL v2.1 through v4. As time went on, it included RHEL v5 through v7, and I typically had to support **N-3** (at one point, **N-4**!) versions of the OS. These issues were multiplied by the number of hardware vendors, which included IBM, HP, Sun (back when they sold X86-based hardware) and eventually VMware and Dell. When I moved to a SUSE environment, I had to deal with SLES v11 through v15, and added IBM Power9 LPARs (and even AIX v7) to the mix.

  The bottom line: it was hard to code a script that worked everywhere, and as part of easing that burden, I created a library that helped insulate me from the variations between OS versions and hardware platforms.

  Since leaving that older PaaS environment, I have slowly been re-factoring my tools to focus on modern OS versions and modern hardware, but the library proved helpful, so I generally still use it.

</details>

The library should be placed in **/usr/local/lib/bash_tools.sh**

# The Tools

Some of these tools are aimed at PowerPC LPARs, and those generally have names ending **-lpar**

## cpuecode
The earliest version I can find for this tool is January, 2011; but I know I started it several years prior to that.
<details>
<summary>Read more about cpudecode</summary>
  
  In the environment at that time, the host population was almost entirely physical, and there was a need to evaluate those systems, on the fly, during OS install. While the environment eventually shifted towards virtual hosts, the tool was still useful from time to time. It also became handy in the time of Spectre/Meltdown, and proved helpful in the PowerPC environment.

  Originally, the information on CPU flag meanings was in one huge **case** statement; I defend that by noting back in 2009, x86 CPUs had a lot fewer flags (dual-core was around, but quad-core wasn't yet common). In preparation for publishing it here, I took the vast majority of that information and moved it into the **cpudecode-data** file (a comment tells you where it needs to live), which basically just declares an array and populates it. The tools also depends on the BASH library.
  
</details>

## dell-query-array.py
Recently, an environment had about 30 Dell **PowerVault ME-{4,5}012 and ME-4084** Storage Arrays.
<details>
<summary>Read more about dell-query-array.py</summary>
  
  We didn't have a coherent monitoring/alerting strategy, so we weren't always aware of issues on a timely basis. While we were in the process of addressing that shortcoming, I developed this tool to meet dual needs. First, it provided a quick way for anyone in Operations to get a moment-in-time view of any Storage Array in the environment (quickly, without having to click around the GUI). Second, it provided a potential mechanism for the Monitoring Team (who were separate from Operations) to peek into a given Storage Array to gather detailed information when constructing an alert.

  **IMPORTANT!** This tool makes a number of assumptions about the environment in which it operates. These are detailed in the _Notes_ section of the comment header.

  One of my planned improvements was to provide a way for the tool to retrieve the password for the Management Controller login from a vault such as **1Password** or **LastPass** or whatever. That would be something very specific to the environment, and so I don't include it in this version. However, I have included a **man** page for the tool.

</details>

## ethreport
DESCRIPTION FORTHCOMING

## fscooler
I wrote this tool for SLES v15 VMs in a VMware environment.
<details>
<summary>Read more about fscooler</summary>
  
This tool automates XFS _Freeze_ and _Thaw_ operations during ESXi-mediated backups (basically, it "settles" the filesystems so the backup is "clean"). I designed it so invocation is controlled by the **open-vm-tools** configuration file `/etc/vmware-tools/tools.conf`, specifically the **[vmbackup]** stanza. Among other features, it allows definition of an "immune" Volume Group; that is, an LVM VG where no filesystem in that VG will be frozen. This is important, as freezing something like **/var** or **/tmp**, even for a second, can trigger catastrophic failures in other processes.

It's also important to note that this tool **_assumes_** that filesystems are all defined in/mounted by **/etc/fstab** and the entries use a "standard" syntax. Before deploying this tool in your environment, check my assumptions about that, and adjust the code if needed.

</details>

## hbareport
**hbareport-lpar** is designed specifically for PowerPC LPARs running SLES v12 or v15, and in particular those having HBAs provided by VIOs using NPIV.
<details>
<summary>Read more about hbareport-lpar</summary>
The impetus for this tool originated in the X86/physical hardware world, but I found it useful to modify it for **SLES for SAP** LPARs on IBM Power9 hardware. In that environment, I was building the Linux infrastructure underlying an SAP R3 migration, from DB2 atop AIX v7 on Power7 to HANA 2.0 atop SLES on Power9.

The LUN naming conventions, and expectations regarding the number of HBAs and names of the VIOs, are all derived from that specific environment. They may or may not be compatible with other places.

</details>

## nagios_downtime.py
I've designed and built several Nagios environments.
<details>
<summary>Read more about nagios_downtime.py</summary>
  
At one point, I developed this tool to integrate with other automation so those processes could exert a limited control over Nagios (specifically, the generation of alerts), generally during process flows that I noticed tended to generate false-positive notifications.

This tool expects to run as an **unprivileged** user (so don't try to run it as **root**); it also expects that user to be a member of a specific Group (identified by numeric **GID**). If you want to integrate it into your environment, then you'll need to tweak several variables, including **NAGIOS_URL_** and **REQUIRED_GROUP_**; of course, as currently engineered, the user ID under which it runs must also be recognized by your Nagios installation (and have control over the target objects).

</details>

## sumareport.py
Having a similar origin story to **vmreport.py**, this tool was also created with design choices, infrastructure expectations and a peculiar host naming convention all driven by the environment in which I was operating. The variables that will doubtless need tweaking for someone to use this tool somewhere else include **SUMAS_** and **CREDENTIALS_**.

## vmreport.py
This is a tool I wrote that was very specific to the environment where I was working; I've sanitized the code and tried to make it more-generic.
<details>
<summary>Read more about vmreport.py</summary>

That said, by design, it is limited to operating against, at most, two ESXi infrastructures (and assumes those are in different data centers, although that's not a critical distinction). There's logic to find a specific host (sort of a "Does a VM with this name exist in this place?" check); the code assumes a host naming convention that, again, was peculiar to the original environment. Bottom Line: You'll need to adapt this tool to **your** environment, don't try to use it as-is. Mainly, I'm publishing it because I found the existing examples of how to use the Python vSphere modules a bit wanting (I wrote this before VMware published the "Community examples"), and I think my code did a better job of demonstrating the basic functionality and making it easy for someone else to understand and adapt to their needs.

</details>
