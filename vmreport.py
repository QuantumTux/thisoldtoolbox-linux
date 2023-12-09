#!/usr/bin/python3
#######################################################################
# vmreport.py - VMware ESXi Guest Reporting Tool
#######################################################################
# This tool either displays information about all Linux VMs (in all Data
#       Centers, or in one Data Center), or generates a return code
#       for a query regarding one specific VM
#
# REQUIRES:
#   0) Python v3
#   1) Additional Python Modules: PyVmoni, Pyvim
#   2) Credentials for a valid vSphere/vCenter User ID that has at
#       least Read-Only access to the Linux VM objects in the VMware
#       environment
#
# NOTES:
#   0) IMPORTANT! This tool was designed for an environment with two
#       data centers, where the ESXi inventory was
#       separately-maintained and FT was used for selected VMs;
#       also, the credentials used for programmatic access were
#       limited (in vSphere) to only having access to the Linux
#       VMs (so I didn't have to worry about separating the wheat
#       from the chaff in terms of the OS on the VMs) and further
#       the logic for the "-c" parameter makes assumptions that
#       were peculiar to host naming convention in that environment;
#       ALL of these design decisions are likely to clash with your
#       environment, so review and modify the code before attempting
#       to use it!
#   1) The tool connects to an ESXi/Vcenter Server using the VMware
#       APIs, then retrieves (and potentially displays) the information
#       for individual Guests
#   2) This tool exits with the following return codes:
#       0 - If invoked WITHOUT the "-c" parameter, then the tool
#           completed normally; if invoked WITH the "-c" parameter,
#           then no VM was found with a matching name
#       1 - The tool was invoked with "-c" and a VM was found
#           matching the name provided
#       252-254 - An invalid host name was provided with the "-c"
#           parameter
#       255 - Invalid command-line parameter combination
#
# KNOWN BUGS:
#   0) There is no error-handling for comm failures when attempting
#       to contact the VMware environment
#   1) Hopefully I didn't munge anything when I sanitized this
#       code for publication; I don't have access to a vSphere
#       environment against which to test it now
#
# TO DO:
#   0) Explore handling comm issues that occur with VMware APIs
#   1) Re-implement using vSphere REST interface
#######################################################################
TOOL_VERSION_='100'
#######################################################################
# Change Log (Reverse Chronological Order)
# Who When______ What__________________________________________________
# dxb 2019-12-20 Initial creation
#######################################################################
# Module Imports #
##################
# System-specific functions/parameters
import sys
# OS-specific functions
import os
from os import system, name

# Command-line argument parser
import argparse
# Exit handlers
import atexit
# Low-level network functions
import socket
# TLS/SSL wrapper for socket objects
import ssl

# VMware-provided ESXi APIs
from pyVmomi import vmodl
from pyVmomi import vim
from pyVim import connect
from pyVim.connect import SmartConnect, Disconnect

# Declare a Class (instead of a dictionary or variable names)
#   of ANSI codes for screen control and Colors for text output
# Reference example --> ANSI_.BOLD_TEXT
class ANSI_:
  '''
  Defines ANSI screen and color control variables that can be
  referenced in print statements to highlight text
  '''
  INVERT_TEXT='\033[7m'
  EOL='\033[0K'
  UNDERLINE_TEXT='\033[4m'
  STRIKETHRU='\033[09m'
  SCREEN_HOME='\033[0;0H'
  GREEN_BLACK='\033[32;40m'
  YELLOW_BLACK='\033[33;40m'
  RED_BLACK='\033[31;40m'
  BLUE_BLACK='\033[34;40m'
  WHITE_BLACK='\033[37;40m'
  CYAN_RED='\033[36;41m'
  MAGENTA_BLACK='\033[35;40m'
  PINK_BLACK='\033[95m'
  BOLD_TEXT='\033[1m'
  BLINK_ON='\033[5m'
  ALL_OFF='\033[0m'

# Create a Dictionary containing IP addresses of vSpheres,
#   indexed by Data Center
VSPHERES_ = dict()
VSPHERES_['DC1'] = '10.2.4.30'
VSPHERES_['DC2'] = '10.2.4.60'

# Create a Dictionary containing User Credentials for vSphere, indexed
#   by username and password
CREDENTIALS_ = dict()
CREDENTIALS_['USER'] = 'service_id'
CREDENTIALS_['PASSWORD'] = 'password'

#######################################################################
# Function: vsphere_connect_func                                      #
# Local Variables: SSL_OBJECT_ = An SSL socket object                 #
# Global Variables: VSPHERE_TARGET_ = Hostname/IP of the target       #
#                     vSphere                                         #
#######################################################################
def vsphere_connect_func(**kwargs):
  '''
  Create a connection to a vSphere host, including an Exit Handler
  to close the connection at exit
    Arguments: **kwargs = Double pointer to keyword arguments
                referenced by socket methods
    Returns: vsphere_connect_func.ESX, an object referencing the
                connection to the vSphere host
  '''
  # Create an SSL socket object
  #   PROTOCOL_SSLv23 specifies both SSL and TLS support and is the
  #               most-interoperable option
  SSL_OBJECT_ = ssl.SSLContext(ssl.PROTOCOL_SSLv23)

  # Instruct methods to not require an SSL cert; if one is supplied
  #   by the remote host, then no validity check is made
  SSL_OBJECT_.verify_mode = ssl.CERT_NONE

  # Connect to the vSphere
  ESX_CONN_ = connect.SmartConnect(host=VSPHERE_TARGET_, user=CREDENTIALS_['USER'], pwd=CREDENTIALS_['PASSWORD'], sslContext=SSL_OBJECT_)

  # Put the vSphere connector object into the kwargs for this function
  vsphere_connect_func.ESX = ESX_CONN_

  # Register an exit handler that will disconnect from the vSphere
  #   when this tool exits
  atexit.register(connect.Disconnect, ESX_CONN_)

#######################################################################
# Function: print_vm_info_func                                        #
# Local Variables: SPHERE_CONTENT_                                    #
#                  ROOT_DATA_                 These are               #
#                  VIEW_TYPE_                 all variables           #
#                  IS_RECURSIVE_              to hold and             #
#                  VM_DATA_                   manipulate the          #
#                  VM_LIST_                   data extracted          #
#                  LINE_COUNT_                from the VMware         #
#                  FT_SKIP_COUNT_             environment             #
#                  THIS_VM_                                           #
#                  THIS_VM_DATA_          THIS_VM_NAME_               #
#                  THIS_VM_RAM_           THIS_VM_CPU_                #
#                  THIS_VM_STATE_         THIS_VM_TOOLS_              #
#                  THIS_VM_FT_                                        #
# Global Variables: vsphere_connect_func.ESX, the vSphere object      #
#######################################################################
def print_vm_info_func(SYSTEM_NAME_):
  '''
  Gather and display information retrieved by vSphere
    Arguments: SYSTEM_NAME_ - A string; if not blank, defining a
                specific host name which will cause this function to
                return "1" if the VM exists, "0" otherwise
    Returns: Two integer values
            If SYSTEM_NAME_ is blank, then the values are, in order,
              LINE_COUNT_ and FT_SKIP_COUNT_
            If SYSTEM_NAME_ is not blank, then the first value
              returned is "1" if a VM with that name exists, "0"
              otherwise; and the second value is always 0
  '''
  # Retrieve information from the ESX
  SPHERE_CONTENT_ = vsphere_connect_func.ESX.RetrieveContent()
  # Store all VMs that are available in the rootFolder of ESXi cluster
  ROOT_DATA_ = SPHERE_CONTENT_.rootFolder
  # Restrict View to only VMs
  VIEW_TYPE_ = [vim.VirtualMachine]
  # When looking in rootFolder, recurse
  IS_RECURSIVE_ = True
  # Get the data
  VM_DATA_ = SPHERE_CONTENT_.viewManager.CreateContainerView(ROOT_DATA_, VIEW_TYPE_, IS_RECURSIVE_)
  # Extract a list of VMs
  VM_LIST_ = VM_DATA_.view

  # Initalize a counter so I can put in a separator line
  LINE_COUNT_ = 0
  # Initalize a counter to track VMs I skip because they are FT images
  FT_SKIP_COUNT_ = 0

  # Cycle through the list of VMs
  for THIS_VM_ in VM_LIST_:
    # Get the block of info for this VM
    THIS_VM_DATA_ = THIS_VM_.summary

    # Get the name of the VM as it appears in the vCenter interface
    THIS_VM_NAME_ = THIS_VM_DATA_.config.name
    if ARGS_.d:
      print('\tTHIS_VM_NAME_ is ' + THIS_VM_NAME_)

    # If passed a host name to check against, then do so here; if the
    #   host doesn't match, then skip the rest of the loop
    if SYSTEM_NAME_ != '':
      if SYSTEM_NAME_ != THIS_VM_NAME_:
        continue
      else:
        # Match found - exit function here
        return(1,0)

    # This next if/else block is used to exclude FT images on the other
    #   Data Center (that is, it prevents this tool from displaying
    #   the FT image of a DC1-based VM when processing the DC2 VMs)
    if (THIS_VM_NAME_[0:3] == 'dc1' or THIS_VM_NAME_[0:3] == 'dc2') and THIS_VM_DATA_.runtime.powerState == 'poweredOn':
      pass
    else:
      FT_SKIP_COUNT_ += 1
      if ARGS_.d:
        print('\t\tSkipping ' + THIS_VM_NAME_ + 'FT_SKIP_COUNT_ is ' + str(FT_SKIP_COUNT_))
        continue

      # Get the RAM in MB
      THIS_VM_RAM_ = THIS_VM_DATA_.config.memorySizeMB
      # I want to display it in GB, so change units and round it
      THIS_VM_RAM_ = int( THIS_VM_RAM_ / 1024 )

      # Get the number of Virtual CPUs
      THIS_VM_CPU_ = THIS_VM_DATA_.config.numCpu

      # Determine if this is an FT
      if THIS_VM_DATA_.runtime.faultToleranceState == 'running':
        THIS_VM_FT_ = ANSI_.BOLD_TEXT + 'YES' + ANSI_.ALL_OFF
      else:
        THIS_VM_FT_ = ' NO'

      # Determine if it is powered on; if running, also get VMTools status
      if THIS_VM_DATA_.runtime.powerState == 'poweredOn':
        THIS_VM_STATE_ = " On"
        if THIS_VM_DATA_.guest.toolsStatus == 'toolsOk':
          THIS_VM_TOOLS_ = 'YES'
        else:
          if THIS_VM_FT_ == ' NO':
            THIS_VM_TOOLS_ = 'NO'
          else:
            continue
      else:
        THIS_VM_STATE_ = ANSI_.BOLD_TEXT + ANSI_.RED_BLACK + 'Off' + ANSI_.ALL_OFF
        # Since the VM is not running, I can't get a status of VMTools
        THIS_VM_TOOLS_ = '---'

        # Display the information
        print('\t\t' + THIS_VM_NAME_ + '\t   ' + THIS_VM_STATE_ + '\t\t' + ' ' + THIS_VM_TOOLS_ + '\t\t\t' + '  ' + str(THIS_VM_RAM_) + '\t\t\t' + '  ' + str(THIS_VM_CPU_) + '\t\t' + '  ' + THIS_VM_FT_)

        # If this is the 5th record, print a separator line
        if LINE_COUNT_ != 0 and (LINE_COUNT_ % 5 == 0):
          print('\t\t' + 105* '-')

        # Increment counter
        LINE_COUNT_ += 1

        # What I return depends on how script was invoked
        if SYSTEM_NAME_ != '':
          # I got done and did not match the host name
          return(0,0)
        else:
          # Return (in order) the count of VMs I displayed, and those skipped
          return(LINE_COUNT_,FT_SKIP_COUNT_)

#################
# Program Start #
#################
DESC_TEXT_ = '\n' + ANSI_.BOLD_TEXT + os.path.realpath(__file__) +  ' - '  + ANSI_.GREEN_BLACK + 'Virtual Machine Information Reporting Tool' + ANSI_.BLUE_BLACK + ' v' + TOOL_VERSION  + ANSI_.ALL_OFF
HELP_TEXT_ = DESC_TEXT_ + '\n\n\t' + ANSI_.BOLD_TEXT + 'Usage:' + ANSI_.ALL_OFF + ' %(prog)s [ [ ' + ANSI_.BOLD_TEXT + '-c' + ANSI_.BLUE_BLACK + ' <HOSTNAME>' + ANSI_.ALL_OFF + ' | ' + ANSI_.BOLD_TEXT + '-e' + ANSI_.ALL_OFF + ' | ' + ANSI_.BOLD_TEXT + '-w' + ANSI_.ALL_OFF + ' ] | ' + ANSI_.BOLD_TEXT + '-h' + ANSI_.ALL_OFF + ' ]'
EPILOG_TEXT_ = '\tThe ' + ANSI_.BOLD_TEXT + '-c' + ANSI_.ALL_OFF + ', ' + ANSI_.BOLD_TEXT + '-e' + ANSI_.ALL_OFF + ' and ' + ANSI_.BOLD_TEXT + '-w' + ANSI_.ALL_OFF + ' command-line flags conflict with each other\n \n'

# Create an argument parser object
#   usage=argparse.SUPPRESS - Prevents the normal "usage" header from
#           appearing; I build my in "description"
#   formatter_class=argparse.RawTextHelpFormatter - Allows me to
#           control help screen formatting
COMMAND_LINE_ = argparse.ArgumentParser(usage=argparse.SUPPRESS,description=HELP_TEXT_,epilog=EPILOG_TEXT_,formatter_class=argparse.RawTextHelpFormatter,add_help=True)
COMMAND_LINE_.add_argument('-c',action='store',default='',metavar=ANSI_.BOLD_TEXT+'<HOSTNAME>'+ANSI_.ALL_OFF+'\t\tLook up a specific host (use the "m" name, for example ' + ANSI_.BOLD_TEXT + 'wtdcsnm0dbw00' + ANSI_.ALL_OFF + ')',help='\tConflicts with ' + ANSI_.BOLD_TEXT + ANSI_.YELLOW_BLACK + '-e' + ANSI_.ALL_OFF + ' and ' + ANSI_.BOLD_TEXT + ANSI_.YELLOW_BLACK + '-w' + ANSI_.ALL_OFF + ' command-line parameters' + "\n\tExits with " + ANSI_.BOLD_TEXT + '1' + ANSI_.ALL_OFF + " if the host exists, " + ANSI_.BOLD_TEXT + '0' + ANSI_.ALL_OFF + " otherwise")
COMMAND_LINE_.add_argument('-d',action='store_true',help="Enable debugging messages to " + ANSI_.BOLD_TEXT + "stdout" + ANSI_.ALL_OFF)
COMMAND_LINE_.add_argument('-e',action='store_true',help='Limit output to ' + ANSI_.BOLD_TEXT + ANSI_.YELLOW_BLACK + 'EDC-based' + ANSI_.ALL_OFF + ' VMs (conflicts with ' + ANSI_.BOLD_TEXT + '-c' + ANSI_.ALL_OFF + ' and ' + ANSI_.BOLD_TEXT + '-w' + ANSI_.ALL_OFF + ')')
COMMAND_LINE_.add_argument('-w',action='store_true',help='Limit output to ' + ANSI_.BOLD_TEXT + ANSI_.YELLOW_BLACK + 'WDC-based' + ANSI_.ALL_OFF + ' VMs (conflicts with ' + ANSI_.BOLD_TEXT + '-c' + ANSI_.ALL_OFF + ' and ' + ANSI_.BOLD_TEXT + '-e' + ANSI_.ALL_OFF + ')')
# Parse the command-line based on the added arguments
ARGS_ = COMMAND_LINE_.parse_args()

if ARGS_.d:
  print('ARGS_.c is ' + ARGS_.c)
  print('ARGS_.d is ' + str(ARGS_.d))
  print('ARGS_.e is ' + str(ARGS_.e))
  print('ARGS_.w is ' + str(ARGS_.w))

# Validate command-line options
# -e and -w conflict
if ARGS_.e and ARGS_.w:
  print(DESC_TEXT_ + '\n\n\t' + ANSI_.BOLD_TEXT + ANSI_.MAGENTA_BLACK + 'FATAL ERROR: ' + ANSI_.BLUE_BLACK + '-e' + ANSI_.RED_BLACK + ' conflicts with ' + ANSI_.BLUE_BLACK + '-w' + ANSI_.ALL_OFF + '\n')
  sys.exit(255)

# -c conflicts with -e and -w
if (ARGS_.e or ARGS_.w) and ARGS_.c != '':
  print(DESC_TEXT_ + '\n\n\t' + ANSI_.BOLD_TEXT + ANSI_.MAGENTA_BLACK + 'FATAL ERROR: ' + ANSI_.BLUE_BLACK + '-c' + ANSI_.RED_BLACK + ' conflicts with ' + ANSI_.BLUE_BLACK + '-e' + ANSI_.RED_BLACK + ' and ' + ANSI_.BLUE_BLACK + '-w' + ANSI_.ALL_OFF + '\n')
  sys.exit(255)

# Was -c specified?
if ARGS_.c != '':
  # Yes, I need to validate the hostname

  #####################################################################
  # IMPORTANT NOTE                                                    #
  # This logic was designed around a naming convention specific to    #
  #   the environment I was in when I wrote this tool. It's almost a  #
  #   guarantee that your environment uses a vastly different naming  #
  #   convention for Linux hosts. Please adapt this code to work for  #
  #   your naming convention!                                         #
  #####################################################################

  if ARGS_.d:
    print('ARGS_.c is ' + ARGS_.c)
    print('ARGS_.c[0:1] is ' + ARGS_.c[0:1])
    print('ARGS_.c[0:2] is ' + ARGS_.c[0:2])
    print('ARGS_.c[4:6] is ' + ARGS_.c[4:6])
    print('ARGS_.c[6:8] is ' + ARGS_.c[6:8])

  # Must be 13 characters, no more or less
  if len(ARGS_.c) != 13:
    print(DESC_TEXT_ + '\n\n\t' + ANSI_.BOLD_TEXT + ANSI_.MAGENTA_BLACK + 'FATAL ERROR A: ' + ANSI_.ALL_OFF + ANSI_.BOLD_TEXT + ARGS_.c + ANSI_.RED_BLACK + ' is not a valid hostname (length)' + ANSI_.ALL_OFF + '\n')
    sys.exit(254)
  elif (ARGS_.c[0:2] != 'dc')
    # First two must be 'dc'
    print(DESC_TEXT_ + '\n\n\t' + ANSI_.BOLD_TEXT + ANSI_.MAGENTA_BLACK + 'FATAL ERROR B: ' + ANSI_.ALL_OFF + ANSI_.BOLD_TEXT + ARGS_.c + ANSI_.RED_BLACK + ' is not a valid hostname (' + ARGS_.c[0:2] + ')' + ANSI_.ALL_OFF + '\n')
    sys.exit(253)
  elif (ARGS_.c[4:6] != 'xx'):
    # The 5th and 6th characters must be 'xx'
    print(DESC_TEXT_ + '\n\n\t' + ANSI_.BOLD_TEXT + ANSI_.MAGENTA_BLACK + 'FATAL ERROR C: ' + ANSI_.ALL_OFF + ANSI_.BOLD_TEXT + ARGS_.c + ANSI_.RED_BLACK + ' is not a valid hostname (' + ARGS_.c[4:6] + ')' + ANSI_.ALL_OFF + '\n')
    sys.exit(252)
  elif (ARGS_.c[6:8] != '00'):
    # The 7th and 8th characters must be '00'
    print(DESC_TEXT_ + '\n\n\t' + ANSI_.BOLD_TEXT + ANSI_.MAGENTA_BLACK + 'FATAL ERROR D: ' + ANSI_.ALL_OFF + ANSI_.BOLD_TEXT + ARGS_.c + ANSI_.RED_BLACK + ' is not a valid hostname (' + ARGS_.c[6:8] + ')' + ANSI_.ALL_OFF + '\n')
    sys.exit(251)
  else:
    # Determine Data Center based on 3rd character
    if ARGS_.c[2:1] == '1':
      VSPHERE_LIST_ = [ VSPHERES_['DC1'] ]
    else:
      VSPHERE_LIST_ = [ VSPHERES_['DC2'] ]

else:
  #####################################################################
  # IMPORTANT NOTE                                                    #
  # This logic was designed around an environment with only two       #
  #   data centers (or two ESXi infrastructures); if your environment #
  #   is different, then this logic won't work for you unless you     #
  #   change it to match your environment                             #
  #####################################################################

  # -c was not used; check to see if -e or -w was specified
  if ARGS_.e or ARGS_.w:
    # Yes - I already know that BOTH -e and -c were
    #       not specified, so I only have to test for one
    if ARGS_.e:
      VSPHERE_LIST_ = [ VSPHERES_['DC1'] ]
    else:
      VSPHERE_LIST_ = [ VSPHERES_['DC2'] ]
    else:
      # No, so I'm getting the full listing (both DCs)
      VSPHERE_LIST_ = [ VSPHERES_['DC1'] , VSPHERES_['DC2'] ]

# VSPHERE_LIST_ is now populated with the list of vSphere
#       servers I'll be contacting

# If not invoked with -c, ID this script
if ARGS_.c == '':
  print(DESC_TEXT_)
# Debugging ouput
if ARGS_.d:
  print('VSPHERE_LIST_ is ' + str(VSPHERE_LIST_))

# Cycle through list of vSphere servers
for VSPHERE_TARGET_ in VSPHERE_LIST_:
  if ARGS_.d:
    print('VSPHERE_TARGET_ is ' + VSPHERE_TARGET_)
    # Connect to the vSphere
    vsphere_connect_func()
    # What I do with the connection depends on how script was invoked
    if ARGS_.c != '':
      # Look for a specific host
      (WAS_FOUND_,ALWAYS_ZERO_) = _print_vm_info_func(ARGS_.c)
      if ARGS_.d:
        print('WAS_FOUND_ is ' + str(WAS_FOUND_))
        # Exit with an RC or "1" if I found the system, or "0" otherwise
        sys.exit(WAS_FOUND_)
      else:
        # Print header
        print('\n\t\t' + ANSI_.BOLD_TEXT + ANSI_.GREEN_BLACK + '___VM_Name___\t__State__\t__Tools__\t\t__RAM(GB)__\t\t__CPU__\t\t__FT?__' + ANSI_.ALL_OFF)

        # Print the VM data
        (_THIS_DC_COUNT,_THIS_DC_SKIP) = _print_vm_info_func(ARGS_.c)
        # Display count of VMs listed, and those skipped
        print('\n\t\t' + ANSI_.BOLD_TEXT + str(_THIS_DC_COUNT) + ' VMs in this DC' + ANSI_.ALL_OFF + ' (' + str(_THIS_DC_SKIP) + ' skipped)\n')

if ARGS_.d:
  print('\nEXITING\n')

# If I get here, I was NOT invoked with -c, and so I always exit
#   with an RC of "0"
sys.exit(0)

# End of vmreport.py
####################
