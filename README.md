# thisoldtoolbox-linux
This repo is part of my **This Old Toolbox** set of repos, which collectively host various system administration/management tools I've written over the years, for a variety of platforms and environments. I'm making them public so that others might find the ideas and/or the accumulated knowledge helpful to whatever they need to create.

# Documentation
These tools have extensive in-line documentation in the form of comments.

# Code Style
All over the place, really. In my newer BASH code, I try to follow the [Google BASH Style Guide](https://google.github.io/styleguide/shellguide.html). For Python, I make an effort to adhere to [PEP 8](https://peps.python.org/pep-0008/). However, I value thorough and well-written comments above following a specific code style.

# Warranty
Absolutely none at all. I stand by my work, yes, but I wrote these things for the environment in which I operated at the time. It probably isn't your environment. If you try to use any of my tools without taking the time to examine and understand the code, you're asking for trouble.

# The Library
Most of these tools rely upon a BASH library that is part of this repo. It might seem to be a little overkill, but there's history behind it.

<details>

<summary>Why I Created a BASH Library</summary>

  I started developing tools in a PaaS environment hosting RHEL v2.1 through v4. As time went on, it included RHEL v5 through v7, and I typically had to support **N-3** (at one point, **N-4**!) versions of the OS. This issues were multiplied by the number of hardware vendors, which included IBM, HP, Sun (back when they sold X86-based hardware) and eventually VMware and Dell. When I moved to a SUSE environment, I had to deal with SLES v11 through v15, and added IBM Power9 LPARs (and even AIX v7) to the mix.

  The bottom line: it was hard to code a script that worked everywhere, and as part of easing that burden, I created a library that helped insulate me from the variations between OS versions and hardware platforms.

  Since leaving that older PaaS environment, I have slowly been re-factoring my tools to focus on modern OS versions and modern hardware, but the library proved helpful, so I generally still use it.

</details>

The library should be placed in **/usr/local/lib/bash_tools.sh**

# The Tools

Some of these tools are aimed at PowerPC LPARs, and those generally have names ending **-lpar**

## cpuecode
<details>
<summary>History of this tool</summary>
  The earliest version I can find for this tool is January, 2011; but I know I started it several years prior to that. In the environment at that time, the host population was almost entirely physical, and there was a need to evaluate those systems, in the fly, during OS install. While the environment eventually shifted towards virtual hosts, the tool was still useful from time to time. It also became handy when in the time of Spectre/Meltdown, and proved helpful in the PowerPC environment.
</details>

Originally, the information on CPU flag meanings was in one huge **case** statement; I defend that by noting back in 2009, x86 CPUs had a lot fewer flags (dual-core was around, but quad-core wasn't yet common). In preparation for publishing it here, I took the vast majority of that information and moved it into the **cpudecode-data** file (a comment tells you where it needs to live), which basically just declares an array and populates it. The tools also depends on the BASH library.

## dell-query-array.py
Recently, an environment had about 30 Dell **PowerVault ME-{4,5}012 and ME-4084** Storage Arrays. We didn't have a coherent monitoring/alerting strategy, so we weren't always aware of issues on a timely basis. While we were in the process of addressing that shortcoming, I developed this tool to meet dual needs. First, it provided a quick way for anyone in Operations to get a moment-in-time view of any Storage Array in the environment. Second, it provided a potential mechanism for the Monitoring Team (who were separate from Operations) to peek into a given Storage Array to gather detailed information when constructing an alert.

**IMPORTANT** This tool makes a number of assumptions about the environment in which it operates. These are detailed in the _Notes_ section of the comment header.

One of my planned improvements was to provide a way for the tool to retrieve the password for the Management Controller login from a vault such as **1Password** or **LastPass** or whatever. That would be something very specific to the environment, and so I don't include it in this version.

## ethreport
DESCRIPTION FORTHCOMING

## fscooler
I wrote this tool for SLES v15 VMs in a VMware environment. It automates XFS _Freeze_ and _Thaw_ operations during backups (basically, it "settles" the filesystems so the backup is "clean"). Invocation is controlled by the **open-vm-tools** configuration file `/etc/vmware-tools/tools.conf`, specifically the **[vmbackup]** stanza. Among other features, it allows definition of an "immune" Volume Group; that is, an LVM VG where no filesystem in that VG will be frozen. This is important, as freezing something like **/var** or **/tmp**, even for a second, can trigger catastrophic failures in other processes.

It's also important to note that this tool **_assumes_** that filesystems are all defined in/mounted by **/etc/fstab** and the entries use a "standard" syntax. Before deploying this tool in your environment, check my assumptions about that, and adjust the code if needed.

## hbareport
**hbareport-lpar** is designed specifically for PowerPC LPARs running SLES v12 or v15, and in particular those having HBAs provided by VIOs using NPIV. The LUN naming assumed by the tool comes from the SLES-for-SAP environment I built for a R3-to-HANA migration.
