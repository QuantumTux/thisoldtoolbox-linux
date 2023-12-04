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
DESCRIPTION FORTHCOMING

## dellhardwarereport
DESCRIPTION FORTHCOMING

## ethreport
DESCRIPTION FORTHCOMING

## hbareport
DESCRIPTION FORTHCOMING
