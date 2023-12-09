#!/usr/bin/python3
#######################################################################
# sumareport.py - A SuSE Manager Reporting Tool
#######################################################################
# This tool either displays information about all SLES hosts registered
#   to a SUMA, or prints a single integer value in response to a query
#   about a specific host name
#
# REQUIRES:
#   0) Python v3
#   1) Python support for XMLRPC
#   2) Credentials for a valid User ID on the SUMA that has at least
#       Read Only access to the proper Organization
#
# NOTES:
#   0) This tool connects to a SUMA using the XMLRPC interface and
#       retrieves (and potentially displays) information for a
#       registered SLES host or hosts
#   1) Invoking with "-n" is intended to provide a list of
#       SUMA-registered host as a simple text, one host per line
#       (using the host name, not the FQDN), written to stdout (but
#       easily re-directed to a file); the purpose is to provide data to
#       other tools
#
# KNOWN BUGS:
#   0) There is no error detection when attempting to contact the
#       SUMA; comm failure will cascade
#
# TO DO:
#   0) Explore error-handling SUMA comm issues
#
#######################################################################
TOOL_VERSION_='100'
#######################################################################
# Change Log (Reverse Chronological Order)
# Who When______ What__________________________________________________
# dxb 2020-10-06 Update LATEST_KERNEL_ to the "-47" version
# dxb 2019-11-15 Original creation
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
# Low-level network functions
import socket
# XMLRPC support
import xmlrpc.client as xc
# Additional date and time functions
import datetime
import time

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

# Create a Dictionary containing IP addresses of SuSE Managers, indexed
#       by Data Center
SUMAS_ = dict()
SUMAS_['ADC'] = '10.0.1.79'
SUMAS_['BDC'] = '10.0.2.79'

# Create a Dictionary containing User Credentials to access the SUMA API
CREDENTIALS_ = dict()
CREDENTIALS_['MANAGER_LOGIN'] = "YOUR_APP_ID"
CREDENTIALS_['MANAGER_PASSWORD'] = "APP_ID_PASSWORD"

# Date format string - used when calling date manipulation functions
DATE_FORMAT_ = '%Y%m%dT%H:%M:%S'

# Latest kernel version package name - when invoked without parameters,
#       and the SUMA-indicated running kernel version on a host does NOT
#       match this string, the table entry is highlighted
LATEST_KERNEL_ = '4.12.14-150.47-default'

# Maximum number of seconds since last host check-in to the SUMA
#       (7200 = 2 hours) before host is flagged when being displayed
CHECKIN_LIMIT_ = 7200

# Define how tool was invoked
OUR_TOOL_ = os.path.realpath(__file__)

#################
# Program Start #
#################
DESC_TEXT_=("\n \n"+ANSI_.BOLD_TEXT+OUR_TOOL_+' - '+ANSI_.GREEN_BLACK+
  "SuSE Manager Information Reporting Tool"+ANSI_.BLUE_BLACK+" v"+
  TOOL_VERSION_+ANSI_.ALL_OFF)
HELP_TEXT_=(DESC_TEXT_+"\n \n\t"+ANSI_.BOLD_TEXT+"Usage:"+ANSI_.ALL_OFF+
  " %(prog)s "+ANSI_.BOLD_TEXT+"-c"+ANSI_.BLUE_BLACK+" <HOSTNAME>"+
  ANSI_.ALL_OFF+" [ "+ANSI_.BOLD_TEXT+"-d"+ANSI_.ALL_OFF+" ] | "+
  ANSI_.BOLD_TEXT+"-n"+ANSI_.ALL_OFF+" [ "+ANSI_.BOLD_TEXT+"-d"+
  ANSI_.ALL_OFF+" ] | "+ANSI_.BOLD_TEXT+"-h"+ANSI_.ALL_OFF)
EPILOG_TEXT_=("\tIf no command-line parameters are given, a full listing of all hosts from both DCs is displayed\n"+
  "\t"+ANSI_.BOLD_TEXT+"SuSE Manager Login ID is "+ANSI_.BLUE_BLACK+
  CREDENTIALS_['MANAGER_LOGIN']+ANSI_.ALL_OFF+"\n \n")

# Create an argument parser object
#   usage=argparse.SUPPRESS - Prevents the normal "usage" header from
#                               appearing; I build my own in "description"
#   formatter_class=argparse.RawTextHelpFormatter - Allows me to control
#                               help screen formatting
COMMAND_LINE_ = argparse.ArgumentParser(usage=argparse.SUPPRESS,description=HELP_TEXT_,epilog=EPILOG_TEXT_,formatter_class=argparse.RawTextHelpFormatter,add_help=True)
COMMAND_LINE_.add_argument('-c',action='store',default='',metavar=ANSI_.BOLD_TEXT+'<HOSTNAME>'+ANSI_.ALL_OFF+'\t\tQuery if a specific host is registered (use the "m" name, for example '+ANSI_.BOLD_TEXT+'axdcsnm0abc00' + ANSI_.ALL_OFF + ')',help='\tWrites to ' + ANSI_.BOLD_TEXT + 'stdout' + ANSI_.ALL_OFF + ' a positive integer equal to the number of seconds since last\n\tcheck-in; or '+ANSI_.BOLD_TEXT+'0'+ANSI_.ALL_OFF+' if the host is not registered or a problem occurred')
COMMAND_LINE_.add_argument('-d',action='store_true',help='Enable debugging messages to '+ANSI_.BOLD_TEXT+'stdout'+ANSI_.ALL_OFF)
COMMAND_LINE_.add_argument('-n',action='store_true',help='Write a list of all hosts registered (in both Data Centers) to '+ANSI_.BOLD_TEXT+'stdout'+ANSI_.ALL_OFF+'\n\t(Conflicts with '+ANSI_.BOLD_TEXT+'-c'+ANSI_.ALL_OFF+')')
# Parse the command-line based on the added arguments
ARGS_=COMMAND_LINE_.parse_args()

if ARGS_.d:
  print("ARGS_.c is " + ARGS_.c)
  print("ARGS_.d is " + str(ARGS_.d))
  print("ARGS_.n is " + str(ARGS_.n))

# Validate command-line options
# The -n and -c arguments conflict (checked first so I don't waste time
#   validating -c)
if (ARGS_.c != '') and (ARGS_.n):
  print(DESC_TEXT_+'\n\n\t'+ANSI_.BOLD_TEXT+ANSI_.MAGENTA_BLACK+'FATAL ERROR: '+
    ANSI_.RED_BLACK+'The '+ANSI_.YELLOW_BLACK+'-c'+ANSI_.RED_BLACK+' and '+
    ANSI_.YELLOW_BLACK+'-n'+ANSI_.RED_BLACK+' command-line parameters conflict'+
    ANSI_.ALL_OFF+'\n')
  sys.exit(1)

# Was -c specified?
if ARGS_.c != '':
  # Yes, I need to validate the hostname
  if ARGS_.d:
    print("ARGS_.c is " + ARGS_.c)
    print("ARGS_.c[0:1] is " + ARGS_.c[0:1])
    print("ARGS_.c[0:2] is " + ARGS_.c[0:2])
    print("ARGS_.c[4:6] is " + ARGS_.c[4:6])
    print("ARGS_.c[6:8] is " + ARGS_.c[6:8])

    # Must be 13 characters, no more or less
    if len(ARGS_.c) != 13:
      print(DESC_TEXT_+"\n\n\t"+ANSI_.BOLD_TEXT+ANSI_.MAGENTA_BLACK+"FATAL ERROR A: "+
        ANSI_.ALL_OFF+ANSI_.BOLD_TEXT+ARGS_.c+ANSI_.RED_BLACK+
        " is not a valid hostname (length)"+ANSI_.ALL_OFF+"\n")
      sys.exit(1)
    elif (ARGS_.c[0:2] != 'at') and (ARGS_.c[0:2] != 'bt'):
      # First two must be 'at' or 'bt'
      print(DESC_TEXT_+"\n\n\t"+ANSI_.BOLD_TEXT+ANSI_.MAGENTA_BLACK+"FATAL ERROR B: "+
        ANSI_.ALL_OFF+ANSI_.BOLD_TEXT+ARGS_.c+ANSI_.RED_BLACK+" is not a valid hostname ("+
        ARGS_.c[0:2]+")"+ANSI_.ALL_OFF+"\n")
      sys.exit(1)
    elif (ARGS_.c[4:6] != 'sn'):
      # The 5th and 6th characters must be 'sn'
      print(DESC_TEXT_+"\n\n\t"+ANSI_.BOLD_TEXT+ANSI_.MAGENTA_BLACK+
        "FATAL ERROR C: "+ANSI_.ALL_OFF+ANSI_.BOLD_TEXT+ARGS_.c+
        ANSI_.RED_BLACK+" is not a valid hostname ("+ARGS_.c[4:6]+
        ")"+ANSI_.ALL_OFF+"\n")
      sys.exit(1)
    elif (ARGS_.c[6:8] != 'm0'):
      # The 7th and 8th characters must be 'm0'
      print(DESC_TEXT_+"\n\n\t"+ANSI_.BOLD_TEXT+ANSI_.MAGENTA_BLACK+
        "FATAL ERROR D: "+ANSI_.ALL_OFF+ANSI_.BOLD_TEXT+ARGS_.c+
        ANSI_.RED_BLACK+" is not a valid hostname ("+ARGS_.c[6:8]+
        ")"+ANSI_.ALL_OFF+"\n")
      sys.exit(1)
    else:
      if ARGS_.c[0:1] == 'e':
        SUMA_LIST_ = [ SUMAS_['DC1'] ]
      else:
        SUMA_LIST_ = [ SUMAS_['DC2'] ]
else:
  SUMA_LIST_ = [ SUMAS_['DC1'] , SUMAS_['DC2'] ]
  # If NOT invoked with -n, ID this tool
  if not ARGS_.n:
    print(DESC_TEXT_)

# SUMA_LIST_ is now populated with the list of SUMAs the tool will
#   be contacting

# I'll be calculating time differences between the current system
#   time and various timestamps I retrieve from SUMA - so get the
#   current time
_CURRENT_TIME = time.time()
if ARGS_.d:
  print("SUMA_LIST_ is " + str(SUMA_LIST_))
  print("_CURRENT_TIME is " + str(_CURRENT_TIME))

# Create a flag to catch when -c has been matched
#   If it gets set, then I need to exit both "for" loops
HOST_MATCH_FOUND_ = 0

# Cycle through list of SUMAs
for SUMA_TARGET_ in SUMA_LIST_:
  if ARGS_.d:
    print('SUMA_TARGET_ is ' + SUMA_TARGET_)

  MANAGER_URL_ = "http://" + SUMA_TARGET_ + "/rpc/api"
  # Create an XMLRPC object - this translates between conformable
  #   Python objects and XML
  SUMA_CLIENT_ = xc.ServerProxy(MANAGER_URL_, verbose=0)
  # Authenticate to the SUMA - I get back what amounts to a key that
  #       I'll attach to our subsequent queries so SUMA recognizes this
  #       tool as authenticated
  # NOTE: This tool does not login to the SUMA, per se - that is, no
  #       stateful session is created; as a result, using an Exit
  #       Handler is not appropriate
  SUMA_KEY_ = SUMA_CLIENT_.auth.login(CREDENTIALS_['MANAGER_LOGIN'], CREDENTIALS_['MANAGER_PASSWORD'])

  # Get a list of all systems registered in the SUMA
  REGISTERED_HOSTS_ = SUMA_CLIENT_.system.listSystems(SUMA_KEY_)

  # Counter for the number of host records I display
  HOST_COUNTER_ = 0

  # If not invoked with -n and not invoked with -c, print header
  if (not ARGS_.n) and (ARGS_.c == ''):
    print("\n\t\t"+ANSI_.BOLD_TEXT+ANSI_.GREEN_BLACK+
      "_Server_Name_\t__Last_Checkin__\t___Last_Boot____\t___System_Kernel______"+ANSI_.ALL_OFF)

    # Loop through the records of registered hosts
    for THIS_HOST_ in REGISTERED_HOSTS_:
      # SUMA stores the long FQDN of the host
      #   (e.g. atxusnm0abc00.blahblah.blah)
      THIS_HOST_LONGNAME_ = THIS_HOST_['name']
      # I only want the short name, so split the long name
      THIS_HOST_NAME_ = THIS_HOST_LONGNAME_.split('.')[0]

      # If invoked with -n, then write out the name and skip
      #   to next host
      if ARGS_.n:
        print(THIS_HOST_NAME_)
        continue

      # Print a separator line every 5 lines (not with -n)
      if (HOST_COUNTER_ != 0 and HOST_COUNTER_ % 5 == 0):
        print("\t\t" + 87* "-")

      if ARGS_.d:
        print("THIS_HOST_LONGNAME_ is " + THIS_HOST_LONGNAME_)
        print("THIS_HOST_NAME_ is " + THIS_HOST_NAME_)

      # Get a timestamp of the last time the host checked in
      THIS_HOST_LAST_CHECKIN_ = THIS_HOST_['last_checkin']
      # Get a timestamp of the last time the host was booted
      THIS_HOST_LAST_BOOT_ = THIS_HOST_['last_boot']
      # Convert the last checkin and last boot timestamps into my
      #   preferred display format
      CONVERTED_DATE_FRMT_CHECKIN_=datetime.datetime.strptime(str(THIS_HOST_LAST_CHECKIN_), DATE_FORMAT_)
      CONVERTED_DATE_FRMT_BOOT_=datetime.datetime.strptime(str(THIS_HOST_LAST_BOOT_), DATE_FORMAT_)
      # Get the running kernel version reported by the host
      THIS_HOST_KERNEL_ = SUMA_CLIENT_.system.getRunningKernel(SUMA_KEY_, THIS_HOST_['id'])
      # Convert the last checkin time to Epoch format so I can
      #   compare it
      EPOCH_LAST_CHECKIN_ = time.mktime(THIS_HOST_LAST_CHECKIN_.timetuple())
      # Determine # of seconds since last checkin
      SECONDS_SINCE_CHECKIN_ = int(_CURRENT_TIME - EPOCH_LAST_CHECKIN_)

      # NOTE: Since when invoked with "-c" I provide the number of
      #       seconds since last checkin, I test for match to the
      #       host name *after* all the computation
      # If the tool was passed a host name to check against, then
      #       do so here - if the host doesn't match, then skip the
      #       rest of the loop
      if ARGS_.c != '':
        if ARGS_.c != THIS_HOST_NAME_:
          # No match - skip to next record
          continue
        else:
          # Natch found - exit both loops by setting flag
          HOST_MATCH_FOUND_ = 1
          break

      # If I get here, I'll be printing out the host info

      # If the time since last checkin exceeds to limit, add color
      #   to that output
      if SECONDS_SINCE_CHECKIN_ > CHECKIN_LIMIT_:
        THIS_HOST_LAST_CHECKIN_=(ANSI_.BOLD_TEXT+ANSI_.MAGENTA_BLACK+
          CONVERTED_DATE_FRMT_CHECKIN_.strftime("%m-%d-%Y %H:%M")+ANSI_.ALL_OFF)
      else:
        THIS_HOST_LAST_CHECKIN_=CONVERTED_DATE_FRMT_CHECKIN_.strftime("%m-%d-%Y %H:%M")

      # If the kernel version is not equal to the latest, add color
      #   to that output
      if THIS_HOST_KERNEL_ != LATEST_KERNEL_:
        THIS_HOST_KERNEL_=(ANSI_.BOLD_TEXT+ANSI_.MAGENTA_BLACK+
          THIS_HOST_KERNEL_+ANSI_.ALL_OFF)

      # Print out the info for this host
      print("\t\t"+THIS_HOST_NAME_+"\t"+THIS_HOST_LAST_CHECKIN_+"\t"+
        CONVERTED_DATE_FRMT_BOOT_.strftime("%m-%d-%Y %H:%M")+
        "\t"+THIS_HOST_KERNEL_)

      # Increment counter of records I've displayed
      HOST_COUNTER_ += 1

      # Log out of the SUMA
      # What I'm really doing is telling the SUMA to no longer accept
      #   my key as valid
      SUMA_CLIENT_.auth.logout(SUMA_KEY_)

      # If invoked with -n, skip remainder of loop
      if ARGS_.n:
        continue

      # Am I exiting both loops?
      if HOST_MATCH_FOUND_ == 1:
        break

# Display total host entries printed out for this SUMA
#   Only do this if not invoked with "-c"
if ARGS_.c == '':
  print("\n\t\t"+ANSI_.BOLD_TEXT+"Server Count: "+ANSI_.ALL_OFF+
    str(HOST_COUNTER_)+"\n")

# If invoked with -n, exit here
if ARGS_.n:
  sys.exit(0)

# If invoked with "-c" and a match as found, print the number of
#   seconds since last check-in; or print 0 for any other situation
if ARGS_.c != '':
  # Did I find a match?
  if HOST_MATCH_FOUND_ == 1:
    # My only output is printing number of seconds since checkin
    print(SECONDS_SINCE_CHECKIN_)
  else:
    print("0")

# I always exit with a 0 return code
sys.exit(0)

########################
# End of sumareport.py #
########################
