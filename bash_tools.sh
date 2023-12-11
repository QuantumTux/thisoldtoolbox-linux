#!/bin/bash
#######################################################################
# bash_tools.sh - BASH Code Library for Scripting
#######################################################################
# IMPORTANT: Sourcing this file will set the PATH to a standard,
#   vanilla set of directories which are the same as on any unmolested
#   SLES system
#
# This is a collection of BASH code functions for use in other tools
#	It provides a standard library of functions that deal with specific
#   packages, configurations and tools
#
#######################################################################
# IMPORTANT NOTE
# This version of my library skews towards modern SLES/OpenSUSE
# I have an older version that skews towards RHEL
#
#######################################################################
# IMPORTANT NOTE
# The idea behind using "which" to find the full paths to various
#   executables is that a given program can live different places
#   on different OSes (e.g. Linux, Solaris, AIX) and/or distros, and it
#   can even vary wildly between different versions of the same Linux
#   distro (this has become less-true over time, but not that long ago
#   I found it to be a significant issue). I prefer to fully-specify an
#   executable, especially when it might be run with privilege, to
#   avoid shell built-ins, aliases and something like an oddball PATH
#   leading my tool to run something that behaves differently than
#   I expect.
#######################################################################
#
# PROVIDES:
#   _init_script_tool_names ()
#     Parameters: None
#     Global Variables: Populates a wide variety of global variable
#         names for various executable tools called by supported tools
#     Returns: Nothing
#     IMPORTANT: This  *MUST*  be called before any of the _get_*
#         functions will work!
#   _init_script_variables ()
#     Parameters: None
#     Global Variables: Populates a set of variables with SLES-specific
#         information; also populates _HOSTS_FILE
#     Returns: Nothing
#   _init_script_colors ()
#     Parameters: None
#     Global Variables: Populates variables that define ANSI color codes
#         which may be used to colorize output in BASH scripts
#     Returns: Nothing
#   _get_os_release ()
#     Parameters: None
#     Global Variables: None
#     Returns: 0=File Parse Error;Otherwise, the Release number
#   _get_os_update ()
#     Parameters: None
#     Global Variables: None
#     Returns: 255=Unable to determine;Otherwise, the Release number
#   _get_platform ()
#     Parameters: None
#     Global Variables: Populates _MY_PLATFORM
#     Returns: 0=PowerPC-based;1=VMware-based;255=Unable to determine
#   _get_tier ()
#     Parameters: None
#     Global Variables: Populates _MY_TIER
#     Returns: 0=Success;255=Unable to determine
#   _get_hostname ()
#     Parameters: None
#     Global Variables: Populates _MY_HOSTNAME
#     Returns: 0=Success;255=Unable to determine
#   _get_fqdn ()
#     Parameters: None
#     Global Variables: Populates _MY_HOSTNAME_FQDN
#     Returns: 0=Success;255=Unable to determine
#   _does_string_contain ()
#     Parameters: Expected sub-string, string for comparison
#     Global Variables: None
#     Returns: 0=Sub-string is NOT present in string
#             1=The sub-string is present in the string
#   _validate_email_address ()
#     Parameters: String for comparison
#     Global Variables: None
#     Returns: 0=String is NOT an RFC-compliant E-mail address
#             1=String is compliant with RFCs for E-mail
#   _log_script_message ()
#     Parameters: String of text to be sent to syslog (Facility local6)
#     Global Variables: If LOG_TAG is populated, then the syslog
#         entry is also tagged with the string
#     Returns: N/A
#   _render_wwpn_func
#     Parameters: String of text containing the WWPN without :
#         characters separating the octets
#     Global Variables: RAW_WWPN, WWPN
#     Returns: N/A
#
# REQUIRES:	Designed to be sourced by other BASH scripts - not intended
#     for stand-alone use (no output to screen or files)
#   Works by several methods; either it parses world-readable files,
#     or it uses UNAME_TOOL
#
# IMPORTANT: The file version is represented  *without*  the decimal to
#   aid comparison in tools; so "100" means "1.00"
readonly BASH_TOOLS_LIBRARY_VERSION='100'
#######################################################################
# Change Log (Reverse Chronological Order)
# Who When______ What__________________________________________________
# dxb 2018-12-10 Initial creation (v1.00)
#######################################################################
# Set a standard PATH for all scripts that source this library
#	This must be exported so it will be present in sub-shells
export PATH=/usr/local/sbin:/usr/local/bin:/sbin:/bin:/usr/sbin:/usr/bin:/root/bin

# The 'which' command is the same place for SLES v12-15, and the
#	behavior of the '--skip-alias' parameter is consistent
readonly WHICH_TOOL='/usr/bin/which'

# File names/paths used within this library
readonly _FSTAB_FILE='/etc/fstab'
if [[ -f /etc/os-release ]]; then
	readonly _RELEASE_FILE='/etc/os-release'
else
	# NOTE: /etc/SuSE-release is removed in SLES 15
	readonly _RELEASE_FILE='/etc/SuSE-release'
fi

# All hosts should have a file /etc/std that can be sourced
readonly STD_FILE='/etc/std'

#######################################################################
# Function: _init_script_tool_names                                   #
# Parameters: None                                                    #
# Local Variables: None                                               #
# Global Variables: See function for list                             #
# Purpose: Sets Global Variables for names of OS-provided             #
#     programs/tools that are used by various other                   #
#     internally-developed tools                                      #
#     The variable names are common across all tools                  #
# Returns: Nothing                                                    #
# NOTE: This function  *MUST*  be called before any of the _get_*     #
#       functions may be used                                         #
#######################################################################
_init_script_tool_names ()
{
	# NOTE: I append "2>&1" when calling "which" to suppress any
	#		error messages when a particular executable is
	#		not found (e.g. ps2pdf, enscript)

	# A
	readonly AWK_TOOL=$( ${WHICH_TOOL} --skip-alias awk 2>&1 )

	# B

	# C
	readonly CAT_TOOL=$( ${WHICH_TOOL} --skip-alias cat 2>&1 )
	readonly CALC_TOOL=$( ${WHICH_TOOL} --skip-alias bc 2>&1 )
  readonly CALENDAR_TOOL=$( ${WHICH_TOOL} --skip-alias cal 2>&1 )
	readonly CFG_TOOL=$( ${WHICH_TOOL} --skip-alias ifconfig 2>&1 )
	readonly CHGRP_TOOL=$( ${WHICH_TOOL} --skip-alias chgrp 2>&1 )
	readonly CHMODE_TOOL=$( ${WHICH_TOOL} --skip-alias chmod 2>&1 )
	readonly CHOWN_TOOL=$( ${WHICH_TOOL} --skip-alias chown 2>&1 )
	readonly CHRONY_CLIENT_TOOL=$( ${WHICH_TOOL} --skip-alias chronyc 2>&1 )
	readonly CP_TOOL=$( ${WHICH_TOOL} --skip-alias cp 2>&1 )
	readonly CPU_TOOL=$( ${WHICH_TOOL} --skip-alias lscpu 2>&1 )
	readonly CUT_TOOL=$( ${WHICH_TOOL} --skip-alias cut 2>&1 )

	# D
	readonly DATE_TOOL=$( ${WHICH_TOOL} --skip-alias date 2>&1 )
	readonly DD_TOOL=$( ${WHICH_TOOL} --skip-alias dd 2>&1 )
	readonly DECODE_TOOL=$( ${WHICH_TOOL} --skip-alias dmidecode 2>&1 )
	readonly DF_TOOL=$( ${WHICH_TOOL} --skip-alias df 2>&1 )
	readonly DNS_TOOL=$( ${WHICH_TOOL} --skip-alias host 2>&1 )

	# E
	readonly ETH_TOOL=$( ${WHICH_TOOL} --skip-alias ethtool 2>&1 )
	readonly ETHREPORT_TOOL=$( ${WHICH_TOOL} --skip-alias ethreport 2>&1 )
	readonly ENSCRIPT_TOOL=$( ${WHICH_TOOL} --skip-alias enscript 2>&1 )

	# F

	# G
	readonly GREP_TOOL=$( ${WHICH_TOOL} --skip-alias grep 2>&1 )

	# H
	readonly HBAREPORT_TOOL=$( ${WHICH_TOOL} --skip-alias hbareport 2>&1 )
	readonly HEAD_TOOL=$( ${WHICH_TOOL} --skip-alias head 2>&1 )
	readonly HOSTNAME_TOOL=$( ${WHICH_TOOL} --skip-alias hostname 2>&1 )

	# I
	readonly IP_TOOL=$( ${WHICH_TOOL} --skip-alias ip 2>&1 )
	readonly IPMI_TOOL=$( ${WHICH_TOOL} --skip-alias ipmitool 2>&1 )

	# J
	# K

	# L
	readonly LAST_TOOL=$( ${WHICH_TOOL} --skip-alias last 2>&1 )
	readonly LISTMOD_TOOL=$( ${WHICH_TOOL} --skip-alias lsmod 2>&1 )
	readonly LOGGER_TOOL=$( ${WHICH_TOOL} --skip-alias logger 2>&1 )
	readonly LS_TOOL=$( ${WHICH_TOOL} --skip-alias ls 2>&1 )
	readonly LSCFG_TOOL=$( ${WHICH_TOOL} --skip-alias lscfg 2>&1 )
	readonly LVREPORT_TOOL=$( ${WHICH_TOOL} --skip-alias lvreport 2>&1 )
	readonly LVS_TOOL=$( ${WHICH_TOOL} --skip-alias lvs 2>&1 )

	# M
	readonly MAIL_TOOL=$( ${WHICH_TOOL} --skip-alias sendmail 2>&1 )
	readonly MAIL_TOOL_CLIENT=$( ${WHICH_TOOL} --skip-alias mail 2>&1 )
	readonly MKDIR_TOOL=$( ${WHICH_TOOL} --skip-alias mkdir 2>&1 )
	readonly MKTEMP_TOOL=$( ${WHICH_TOOL} --skip-alias mktemp 2>&1 )
	readonly MODINFO_TOOL=$( ${WHICH_TOOL} --skip-alias modinfo 2>&1 )
	readonly MODPROBE_TOOL=$( ${WHICH_TOOL} --skip-alias modprobe 2>&1 )
	readonly MOUNT_TOOL=$( ${WHICH_TOOL} --skip-alias mount 2>&1 )
	readonly MPATHREPORT_TOOL=$( ${WHICH_TOOL} --skip-alias mpathreport 2>&1 )
	readonly MULTIPATH_TOOL=$( ${WHICH_TOOL} --skip-alias multipath 2>&1 )
	readonly MV_TOOL=$( ${WHICH_TOOL} --skip-alias mv 2>&1 )

	# N
	# O

	# P
	readonly PCI_TOOL=$( ${WHICH_TOOL} --skip-alias lspci 2>&1 )
	readonly PDF_TOOL=$( ${WHICH_TOOL} --skip-alias ps2pdf 2>&1 )
	readonly PING_TOOL=$( ${WHICH_TOOL} --skip-alias ping 2>&1 )
	readonly PKG_TOOL=$( ${WHICH_TOOL} --skip-alias rpm 2>&1 )
	readonly PS_TOOL=$( ${WHICH_TOOL} --skip-alias ps 2>&1 )
	readonly PVS_TOOL=$( ${WHICH_TOOL} --skip-alias pvs 2>&1 )

	# Q

	# R
	readonly RM_TOOL=$( ${WHICH_TOOL} --skip-alias rm 2>&1 )
	readonly ROUTE_TOOL=$( ${WHICH_TOOL} --skip-alias route 2>&1 )

	# S
	readonly SED_TOOL=$( ${WHICH_TOOL} --skip-alias sed 2>&1 )
	readonly SHUTDOWN_TOOL=$( ${WHICH_TOOL} --skip-alias shutdown 2>&1 )
	readonly SLEEP_TOOL=$( ${WHICH_TOOL} --skip-alias sleep 2>&1 )
	readonly SORT_TOOL=$( ${WHICH_TOOL} --skip-alias sort 2>&1 )
	readonly SSH_TOOL=$( ${WHICH_TOOL} --skip-alias ssh 2>&1 )
	readonly STAT_TOOL=$( ${WHICH_TOOL} --skip-alias stat 2>&1 )
	readonly STRINGS_TOOL=$( ${WHICH_TOOL} --skip-alias strings 2>&1 )
	readonly SUMINUS_TOOL=$( ${WHICH_TOOL} --skip-alias suminus 2>&1 )
	readonly SUBSCRIBE_TOOL=$( ${WHICH_TOOL} --skip-alias subscription-manager 2>&1 )
	readonly SVC_TOOL=$( ${WHICH_TOOL} --skip-alias service 2>&1 )
	readonly SYSCFG_NET_TOOL=$( ${WHICH_TOOL} --skip-alias system-config-network-cmd 2>&1 )
	readonly SYSCTL_TOOL=$( ${WHICH_TOOL} --skip-alias systemctl 2>&1 )

	# T
	readonly TAIL_TOOL=$( ${WHICH_TOOL} --skip-alias tail 2>&1 )
	readonly TOUCH_TOOL=$( ${WHICH_TOOL} --skip-alias touch 2>&1 )
	readonly TR_TOOL=$( ${WHICH_TOOL} --skip-alias tr 2>&1 )

	# U
	readonly UNAME_TOOL=$( ${WHICH_TOOL} --skip-alias uname 2>&1 )
	readonly UNLINK_TOOL=$( ${WHICH_TOOL} --skip-alias unlink 2>&1 )
	readonly UPTIME_TOOL=$( ${WHICH_TOOL} --skip-alias sles_uptime 2>&1 )

	# V
	readonly VGS_TOOL=$( ${WHICH_TOOL} --skip-alias vgs 2>&1 )

	# W
	readonly W_TOOL=$( ${WHICH_TOOL} --skip-alias w 2>&1 )
	readonly WC_TOOL=$( ${WHICH_TOOL} --skip-alias wc 2>&1 )
	WGET_TOOL=$( ${WHICH_TOOL} --skip-alias wget 2>&1 )
	readonly WGET_TOOL="${WGET_TOOL} -q -O"
	readonly WHO_TOOL=$( ${WHICH_TOOL} --skip-alias who 2>&1 )

	# X
	# Y
	# Z
}

#######################################################################
# Function: _init_script_variables                                    #
# Parameters: None                                                    #
# Local Variables: None                                               #
# Global Variables: See function for list                             #
# Purpose: Sets Global Variables that allow Linux-based BASH shell    #
#   scripts to parse SLES-specific information stored in              #
#   SLES-specific files; also populates _HOSTS_FILE                   #
# Notes: IMPORTANT! The _init_script_tool_names function  *MUST* be   #
#       invoked prior to invoking this function                       #
# Returns: Nothing                                                    #
#######################################################################
_init_script_variables ()
{
	# Helpfully, SLES (and OpenSuSE) format $_RELEASE_FILE as a set of
	#   variable statements I can source
	# If the file exists, source it, and other functions
  #   (like _get_os_release and _get_os_update) can reference the info
  #   instead of parsing the file
	# I expect the file to contain specific variables:
	#   NAME - This will be "SLES" or "openSUSE LEAP"
	#   VERSION - SLES hosts format this similar to "12-SP3"
	#		            but openSUSE looks like "15.0"
	#   VERSION_ID - Both SLES and openSUSE format this like "12.3"
	#   PRETTY_NAME - A string for humans like
  #     "SUSE Linux Enterprise Server 12 SP3" or "openSUSE Leap 15.0"
	#	  ID - A quick-reference string like "sles" or "opensuse-leap"
	#		    (looks as if it will always be all-lower-case as
	#		    compared to NAME)
	#	  CPE_NAME - A multi-variable colon-separated string like
  #       "cpe:/o:opensuse:leap:15.0" or "cpe:/o:suse:sles_sap:12:sp3"
	# There will probably be other variables like ANSI_COLOR,
  #       BUG_REPORT_URL, HOME_URL and ID_LIKE (the last is similar
  #       to ID) but for my purposes here I don't care about them
	# I'll initialize the ones I care about with a string that will make
  #       sure something is present even if the file didn't contain
  #       everything I expected
	NAME='X'
	VERSION='X'
	VERSION_ID='X'
	PRETTY_NAME='X'
	ID='X'
	CPE_NAME='X'
	if [[ -f ${_RELEASE_FILE} ]]; then
		source ${_RELEASE_FILE}
		# The variables should now be populated
	fi
	# If the file was missing or some were not populated, then I have the
	#	default values to let other functions know there was a problem
	readonly _HOSTS_FILE='/etc/hosts'
  readonly NAME
  readonly VERSION
  readonly VERSION_ID
  readonly PRETTY_NAME
  readonly ID
  readonly CPE_NAME
}

#################################################################################
# Function: _init_script_colors                                                 #
# Parameters: None                                                              #
# Local Variables: None                                                         #
# Global Variables: See function for list                                       #
# Purpose: Sets Global Variables for ASCII colors used by various other         #
#     internally-developed tools                                                #
#     The variable names are common across all tools                            #
# Returns: Nothing                                                              #
#################################################################################
_init_script_colors ()
{
	readonly INVERT_TEXT='\033[7m'
	readonly EOL='\033[0K'
	readonly UNDERLINE_TEXT='\033[4m'

	readonly SCREEN_HOME='\033[0;0H'

	# Colors for text output
	readonly GREEN_BLACK='\033[32;40m'
	readonly YELLOW_BLACK='\033[33;40m'
	readonly RED_BLACK='\033[31;40m'
	readonly BLUE_BLACK='\033[34;40m'
	readonly WHITE_BLACK='\033[37;40m'
	readonly CYAN_RED='\033[36;41m'
	readonly MAGENTA_BLACK='\033[35;40m'
	readonly BOLD_TEXT='\033[1m'
	readonly BLINK_ON='\033[5m'
	readonly ALL_OFF='\033[0m'
}

#########################
# Function Declarations #
#########################

#######################################################################
# Function: _get_os_release                                           #
# Security: No privilege required                                     #
# Parameters: None                                                    #
# Local Variables: _CHKSTR - Working string variable                  #
# Global Variables: None                                              #
# Purpose: Extracts the SLES (or even openSUSE) Release number from   #
#            variables initialized in _init_script_variables          #
# Returns: 0 - Unable to determine                                    #
#         Any other return value should be the Release number         #
#######################################################################
_get_os_release ()
{
	# If _init_script_variables found the file, then parse the Release
	#	number from $VERSION_ID
	if [[ "${VERSION_ID}" != 'X' ]]; then
		# The string should be in "XX.Y" format, where "XX" is the Release
		_CHKSTR=$( echo ${VERSION_ID} | ${AWK_TOOL} -F '.' '{ print $1 }' )
	else
		_CHKSTR=0
	fi
	# Validate that our data is numeric (return "0" if it isn't)
	case ${_CHKSTR} in
		*[!0-9]*|"")	return 0 ;;
		*)		        return ${_CHKSTR} ;;
	esac
}

#######################################################################
# Function: _get_os_update                                            #
# Security: No privilege required                                     #
# Parameters: None                                                    #
# Local Variables: _CHKSTR - Working string variable                  #
# Global Variables: None                                              #
# Purpose: Extracts the Update level of SLES (or even openSUSE) from  #
#          variables nitialized in _init_script_variables             #
# Returns: 255 - Unable to determine                                  #
#             Any other return value should be the Update number      #
#######################################################################
_get_os_update ()
{
  # If _init_script_variables found the file, then parse the Release
  #   number from $VERSION_ID
  if [[ "${VERSION_ID}" != 'X' ]]; then
    # The string should be in "XX.Y" format, where "Y" is the Release
    _CHKSTR=$( echo ${VERSION_ID} | ${AWK_TOOL} -F '.' '{ print $2 }' )
  else
    _CHKSTR=X
  fi
  # Validate that my data is numeric (return "255" if it isn't)
  case ${_CHKSTR} in
    *[!0-9]*|"")  return 255 ;;
    *)            return ${_CHKSTR} ;;
  esac
}

#######################################################################
# Function: _get_platform                                             #
# Security: No privilege required                                     #
# Parameters: None (uses Global Variables instead)                    #
# Local Variables: _CHKSTR - Working string variable                  #
# Global Variables: _MY_PLATFORM - Will contain string "PPC"          #
#                     or "VMware"                                     #
# Purpose: Uses UNAME_TOOL to extract the platform type               #
# Returns: 0 - Platform is an IBM PowerPC-based Virtual host          #
#          1 - Platform is a VMware-based Virtual Host                #
#         255 - Unable to determine                                   #
#######################################################################
_get_platform ()
{
  _CHKSTR=$( ${UNAME_TOOL} -p )
  # This should result in a string that is one of two (2) possible
  #   values (any other value is not supported)
  #     ppc64le - IBM PowerPC (little-endian) Guest (LPAR)
  #     x86_64 - VMware Guest
  if [[ "${_CHKSTR}" == 'x86_64' ]]; then
    readonly _MY_PLATFORM='VMware'
    return 1
  elif [[ "${_CHKSTR}" == 'ppc64le' ]]; then
	  readonly _MY_PLATFORM='PPC'
		return 0
  else
    readonly _MY_PLATFORM='Unknown'
    return 255
  fi
}

#######################################################################
# Function: _get_tier                                                 #
# Security: No privilege required                                     #
# Parameters: None (uses Global Variables instead)                    #
# Local Variables: _CHKSTR - Working string variable                  #
# Global Variables: _MY_TIER - Single character, one of:              #
#                         P,T,Q,R,D,S,E,A,B or X                      #
#           where "X" indicates a problem                             #
# Purpose: Discern the Tier from the host name                        #
# Returns: 0 - Success                                                #
#         255 - Unable to determine                                   #
#######################################################################
# IMPORTANT NOTE: This code is peculiar to an SAP environment for
#                 which I built the Linux infrastructure; it won't
#                 make much sense outside of that environment
#######################################################################
_get_tier ()
{
  _CHKSTR=$( ${UNAME_TOOL} -n )
  # Now get 3rd character - remember to use 0-index
  _CHKSTR="${_CHKSTR:2:1}"
  # Make it upper-case
  _CHKSTR=$( echo ${_CHKSTR} | ${TR_TOOL} "[:lower:]" "[:upper:]" )
  case ${_CHKSTR} in
    ['P','T','Q','R','D','S','E','A','B'])  readonly MY_TIER="${_CHKSTR}" ;;
    *)                                      readonly MY_TIER='X' ;;
  esac
  if [[ "${MY_TIER}" == 'X' ]]; then
    return 255
  else
    return 0
  fi
}

#######################################################################
# Function: _get_hostname                                             #
# Security: No privilege required                                     #
# Parameters: None (uses Global Variables instead)                    #
# Local Variables: _CHKSTR - Working string variable                  #
# Global Variables: _MY_HOSTNAME - The short hostname as reported by  #
#                           the "hostname" command                    #
# Purpose: Uses HOSTNAME_TOOL to populate a variable                  #
# Returns: 0 - Success                                                #
#         255 - Unable to determine                                   #
#######################################################################
_get_hostname ()
{
  readonly _MY_HOSTNAME=$( ${HOSTNAME_TOOL} )
  # Make sure it does NOT contain any "." characters
  _CHKSTR=$( echo "${_MY_HOSTNAME}" | ${AWK_TOOL} -F '.' '{ print NF }' )
  if [[ "${_CHKSTR}" -ne 1 ]]; then
    return 255
  else
    return 0
  fi
}

#######################################################################
# Function: _get_fqdn                                                 #
# Security: No privilege required                                     #
# Parameters: None (uses Global Variables instead)                    #
# Local Variables: _CHKSTR - Working string variable                  #
# Global Variables: _MY_HOSTNAME_FQDN - The short hostname as         #
#                       reported by the "hostname -f" command         #
# Purpose: Uses HOSTNAME_TOOL to populate a variable                  #
# Returns: 0 - Success                                                #
#         255 - Unable to determine                                   #
#######################################################################
_get_fqdn ()
{
  readonly _MY_HOSTNAME_FQDN=$( ${HOSTNAME_TOOL} -f )
  # Make sure it contains 2 "." characters
  _CHKSTR=$( echo "${_MY_HOSTNAME}" | ${AWK_TOOL} -F '.' '{ print NF }' )
  if [[ "${_CHKSTR}" -ne 3 ]]; then
    return 255
  else
    return 0
  fi
}

#######################################################################
# Function: _does_string_contain                                      #
# Parameters: Sub-string to match, string to be checked               #
# Local Variables: None                                               #
# Global Variables: None                                              #
# Purpose: Tests if a sub-string is present in another string         #
# Returns:  0 = The sub-string is NOT present in the string           #
#           1 = Found the sub-string in the other string              #
#                                                                     #
# Example Usage:  # Test if a string that is supposed to be a host    #
#                 #   name contains a certain string (like a SID)     #
#                 SUB_STR='tsta'                                      #
#                 HOSTNAME='dcabcnm0xyza2'                            #
#                 _does_string_contain "${SUB_STR}" "${HOSTNAME}"     #
#                 RET_CODE=$?                                         #
#                 if [[ "${RET_CODE}" -eq 1 ]]; then                  #
#                   echo "${HOSTNAME} includes ${SUB_STR}"            #
#                 else                                                #
#                   echo "${SUB_STR} is NOT in ${HOSTNAME}"           #
#                 fi                                                  #
#######################################################################
_does_string_contain ()
{
  [ -z "${2##*$1*}" ] && { [ -z "${1}" ] || [ -n "${2}" ] ;} ;
}

#######################################################################
# Function: _validate_email_address                                   #
# Parameters: String containing the prospective E-mail address        #
# Local Variables: REGEX (contains a BASH regex)                      #
# Global Variables: None                                              #
# Purpose: Tests if a string is an RFC-compliant E-mail address       #
# Returns:  0 = The sub-string is NOT a compliant E-mail address      #
#           1 = The E-mail address is compliant with RFCs             #
# NOTES: A string is "valid" if it meets the format of                #
#                 <recipient>@<domain>                                #
#     where:                                                          #
#         <recipient> is some combination of RFC-compliant characters #
#         <domain> is an RFC-compliant domain specification           #
#                                                                     #
# HOWEVER, only the structure of the string is validated; the E-mail  #
#   address is not guaranteed to be deliverable                       #
#######################################################################
_validate_email_address ()
{
  # Specify a BASH regex that will match for RFC-compliant E-mail
  # addresses (YES, the string should be in double-quotes)
  local _REGEX="^[a-z0-9!#\$%&'*+/=?^_\`{|}~-]+(\.[a-z0-9!#$%&'*+/=?^_\`{|}~-]+)*@([a-z0-9]([a-z0-9-]*[a-z0-9])?\.)+[a-z0-9]([a-z0-9-]*[a-z0-9])?\$"
  # Test the argument - note that "[[" and "]]" MUST be used
  #   as the "test" construct!
  if [[ ${1} =~ ${_REGEX} ]] ; then
    return 1
  else
    return 0
  fi
}

#######################################################################
# Function: _log_script_message                                       #
# Parameters: String of text message to be logged                     #
# Local Variables: TAG_STRING = Either holds '-t' and an argument, or #
#     is blank,	depending on the value of LOG_TAG                     #
# Global Variables: LOG_TAG - Optional string for argument to "-t"    #
#     parameter                                                       #
# Purpose: Generates a syslog entry to Facility "local6", the entry   #
#     includes the PID of the calling process; if the variable        #
#     LOG_TAG is populated, then the value is added as a tag to the   #
#     entry                                                           #
# Returns: N/A                                                        #
#######################################################################
_log_script_message ()
{
  # Only do something if I was passed a string
  if [[ "${#1}" -lt 1 ]]; then
    return
  fi
  # If LOG_TAG is not populated, then do not include the parameter
  if [[ "${#LOG_TAG}" -ne 0 ]]; then
    readonly TAG_STRING="-t ${LOG_TAG}"
  else
    readonly TAG_STRING=''
  fi
  # --id=$$ causes the PID of the parent process (that is, the script
  #	that called this function) to be logged, rather than the PID
  #	of the "logger" process itself
  ${LOGGER_TOOL} --id=$$ -p local6.info ${TAG_STRING} -- ${1}
}

#######################################################################
# Function: _render_wwpn_func                                         #
# Parameters: None (uses Global Variables instead)                    #
# Local Variables: NUMBER, OCTETS, START, THIS_OCTET                  #
# Global Variables: RAW_WWPN, WWPN                                    #
# Purpose: Takes a string containing a WWPN, but lacks : separating   #
#     the octets, and renders it with a : between each octet          #
# Returns: Nothing (all data stored in Global variables)              #
#######################################################################
_render_wwpn_func ()
{
  # RAW_WWPN should already contain the necessary string
  OCTETS=8
  START=0
  WWPN=''
  for NUMBER in $( seq ${OCTETS} ); do
    (( START = NUMBER - 1 ))
    (( START = START * 2 ))
    (( START = START + 1 ))
    THIS_OCTET=$( echo ${RAW_WWPN} | ${AWK_TOOL} -v start=${START} '{ print substr($1,start,2) }' )
    if [[ "${NUMBER}" -eq 1 ]]; then
      WWPN="${THIS_OCTET}"
    else
      WWPN="${WWPN}:${THIS_OCTET}"
    fi
  done
}

# Blank template for future use
#######################################################################
# Function:                                                           #
# Parameters: None (uses Global Variables instead)                    #
# Local Variables:                                                    #
# Global Variables:                                                   #
# Purpose:                                                            #
# Returns:                                                            #
#######################################################################

########################
# End of bash_tools.sh #
########################
