#!/usr/bin/python3
#######################################################################
# nagios_downtime.py - Host-based Nagios Downtime Scheduling Tool
#######################################################################
# This tool allows a User (who must already possess valid credentials
#   to access the Nagios web interface) to schedule a downtime period
#   for the host on which this tool executes.
#
# REQUIRES:
#   0) Python v3
#   1) SLES v12 or later
#   2) Valid login credentials to the Nagios web interface
#   3) Execution by an UNPRIVILEGED ID that is a member of the Group
#       with the GID specified in REQUIRED_GROUP_
#
# NOTES:
#   0) This tool connects to the Nagios web interface and submits a
#		    processing request via the CGIs; the URL for the Nagios
#       server is specified in NAGIOS_URL_
#
# KNOWN BUGS:
#   0) Does not validate the contents of PW_FILENAME_; just uses them
#		    blindly
#   1) If run on a host that has a clock that is more than 1 minute
#       out-of-sync with the Nagios host, then otherwise valid
#		    operations may fail if the downtime request starts before the
#		    current time on the Nagios host
#
# TO DO:
#   0) Improve logging
#   1) Re-factor to use functions
#   2) python_tools library needs to be re-engineered, which will impact
#       this tool
##########################################################################
TOOL_VERSION_='100'
##########################################################################
# Change Log (Reverse Chronological Order)
# Who When______ What_____________________________________________________
# dxb 2020-06-04 Initial creation
##########################################################################
# Module Imports #
##################
# System-specific functions/parameters
import sys
# OS-specific functions
import os
from os import system, name
# Command-line argument parser
import argparse
# Regular expressions when checking Group membership
import re
# Time manipulation functions
import time
# Password prompting
import getpass
# Needed for log_tool_message_()
import syslog

# HTTP Request module
import requests
# I want to supress warnings that will occur when I do not verify the
#	SSL cert of the Nagios server
from requests.packages.urllib3.exceptions import InsecureRequestWarning
requests.packages.urllib3.disable_warnings(InsecureRequestWarning)

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

# Globals
TOOL_DESC_ = 'Host-based Nagios Downtime Scheduling Tool'
NAGIOS_URL_ = 'https://<PUT YOUR NAGIOS SERVER HERE>/nagios/cgi-bin/cmd.cgi'
# The User running this tool must be a member of the Group with
#   this GID
REQUIRED_GROUP_ = '12345'
# File name (in the home directory of the User ID executing the tool)
#   where the password is located
PW_FILENAME_ = '.nagios_downtime'
# Define how tool was invoked
OUR_TOOL_ = os.path.realpath(__file__)

###################
# Initialization  #
###################
# In the case of logging, I need to initialize the module
#   and tell it to include the PID and set the Facility
#   (the Priority will be "INFO" by default)
syslog.openlog(logoption=syslog.LOG_PID,facility=syslog.LOG_LOCAL6)

#######################################################################
# Function: log_tool_message_                                         #
# Parameters: String of text message to be logged                     #
# Local Variables: LOG_MESSAGE_                                       #
# Global Variables: None                                              #
# Purpose: Generates a syslog entry to Facility "local6"              #
# Returns: N/A                                                        #
#######################################################################
def log_tool_message_(LOG_MESSAGE_):
  '''
  Write a message to syslog using the LOCAL6 Facility
    and INFO Priority

  Arguments: String of text message to be logged
  Returns: N/A
  '''
  # Only do something if a messages was provided
  if len(LOG_MESSAGE_) > 0:
    syslog.syslog(LOG_MESSAGE_)
  else:
    return

def argument_parser_func_():
  """
  Creates and returns an ArgumentParser object

  Requires the Global TOOL_DESC_ string consisting of roughly four to
  eight words summarizing the tool, for example
        Linux Renoberation Fromish Reporting Tool

  Also requires the Global TOOL_VERSION_ string holding the current
  version of the program in the format ###

  Finally, requires import of the argparse and os modules
  """

  # Redefine the ArgumentParser class so I can force it to print out
  #	the Help screen if a required parameter is missing
  class MyParser(argparse.ArgumentParser):
    """
    Redefinition of the ArgumentParser Class
    """
    def error(self, message):
      print('\n'+ANSI_.BOLD_TEXT+ANSI_.MAGENTA_BLACK+
        'FATAL ERROR: '+ANSI_.RED_BLACK+message+ANSI_.ALL_OFF)
      self.print_help()
      sys.exit(2)

  # DESC_TEXT_ begins the creation of an output string that looks
  #   like /path/to/tool.py - Linux Frobish and Renoberate Tool v1.00
  # by relying on the TOOL_DESC_ and TOOL_VERSION_ strings
  DESC_TEXT_ = ('\n \n'+ANSI_.BOLD_TEXT+OUR_TOOL_+' - '+
    ANSI_.GREEN_BLACK+TOOL_DESC_+ANSI_.BLUE_BLACK+' v'+
    TOOL_VERSION_+ANSI_.ALL_OFF)

  # HELP_TEXT_ builds on DESC_TEXT_ by appending text like
  #   Usage : /path/to/tool.py -b -c <ARGUMENT> | -h
  HELP_TEXT_ = (DESC_TEXT_+'\n \n\t'+ANSI_.BOLD_TEXT+'Usage: '+
    ANSI_.ALL_OFF+OUR_TOOL_+ANSI_.BOLD_TEXT+' -c '+
    ANSI_.BLUE_BLACK+'"Comment"'+ANSI_.ALL_OFF+' [ '+
    ANSI_.BOLD_TEXT+'-d HH:MM'+ANSI_.ALL_OFF+' | '+
    ANSI_.BOLD_TEXT+'-f MMM'+ANSI_.ALL_OFF+' ]'+
    ' [ '+ANSI_.BOLD_TEXT+'-p'+ANSI_.ALL_OFF+' ]'+
    ' [ '+ANSI_.BOLD_TEXT+'-v'+ANSI_.ALL_OFF+' ] '+
    '| '+ANSI_.BOLD_TEXT+'-h'+ANSI_.ALL_OFF)

  # EPILOG_TEXT_ defines a block of text that appears AFTER the Help
  #   screen when the tool is invoked with the -h parameter; at
  #   minimum the string should look like
  #       Found python_tools.py
  EPILOG_TEXT_ = ('\t'+ANSI_.BOLD_TEXT+'Nagios Host URL is '+ANSI_.BLUE_BLACK+
    NAGIOS_URL_+ANSI_.ALL_OFF+'\n'+'\t'+ANSI_.BOLD_TEXT+'Required Group ID is '+
    ANSI_.BLUE_BLACK+REQUIRED_GROUP_+ANSI_.ALL_OFF+'\n'+'\t'+ANSI_.BOLD_TEXT+
    'Using credential file '+ANSI_.BLUE_BLACK+PW_FILENAME_+ANSI_.ALL_OFF+'\n \n')

  # Create an argument parser object (using my special Class)
  #   usage=argparse.SUPPRESS - Prevents the normal "usage" header from
  #       appearing; I built my own in HELP_TEXT_
  #   formatter_class=argparse.RawTextHelpFormatter - Allow me to control
  #       help screen formatting
  CLI_PARSER_ = (MyParser(usage=argparse.SUPPRESS,
    description=HELP_TEXT_,epilog=EPILOG_TEXT_,
    formatter_class=argparse.RawTextHelpFormatter,add_help=True) )
  CLI_PARSER_.add_argument('-c',action='store',required=True,
    metavar=ANSI_.BOLD_TEXT+'"Comment"'+ANSI_.ALL_OFF+'\t\t'+
    ANSI_.BOLD_TEXT+'Short text comment that will be included '+
    'in the Downtime Schedule'+ANSI_.ALL_OFF,
    help='\t'+ANSI_.BOLD_TEXT+ANSI_.MAGENTA_BLACK+
    'MUST be enclosed in quotes'+ANSI_.ALL_OFF)
  CLI_PARSER_.add_argument('-p',action='store_true',default=False,
    required=False,help=ANSI_.BOLD_TEXT+'Get password from file'+
    ANSI_.ALL_OFF+'\n\tIf not specified, you will be prompted '+
    'for your password\n\tto the Nagios web interface'+
    '\n\tIf specified, this tool will look in your home directory '+
    '\n\tfor a text file named '+ANSI_.BOLD_TEXT+ANSI_.BLUE_BLACK+
    PW_FILENAME_+ANSI_.ALL_OFF+
    '\n\tThe file should contain a single line of text that is\n\t'+
    'your password to the Nagios web interface;\n\tif the file does '+
    'not exist, or is empty, then '+ANSI_.BOLD_TEXT+
    ANSI_.BLUE_BLACK+'-p'+ANSI_.ALL_OFF+' is ignored')
  CLI_PARSER_.add_argument('-v',action='store_true',default=False,
    required=False,help=ANSI_.BOLD_TEXT+'Verbose mode'+ANSI_.ALL_OFF+
    '\n\tIf specified, this tool will generate output to '+
    ANSI_.BOLD_TEXT+ANSI_.BLUE_BLACK+'stdout'+ANSI_.ALL_OFF+
    '\n\tas it runs; if not specified, there is no screen output')
  # The -d and -f arguments are mutually exclusive, but require one
  OPTION_GROUP_ = CLI_PARSER_.add_mutually_exclusive_group(required=True)
  OPTION_GROUP_.add_argument('-d',action='store',default='',
    metavar=ANSI_.BOLD_TEXT+'HH:MM'+ANSI_.ALL_OFF+'\t\t'+
    ANSI_.BOLD_TEXT+'Schedule a '+ANSI_.MAGENTA_BLACK+
    'Floating'+ANSI_.ALL_OFF+ANSI_.BOLD_TEXT+
    ' downtime of this duration'+ANSI_.ALL_OFF,
    help='\tSpecified as hours and minutes; both values must be'+
    '\n\tnon-negative integers; the hours cannot exceed 23 and'+
    '\n\tthe minutes cannot exceed 59')
  OPTION_GROUP_.add_argument('-f',action='store',type=int,default=0,
    choices=range(5,999),metavar=ANSI_.BOLD_TEXT+'MMM'+
    ANSI_.ALL_OFF+'\t\t'+ANSI_.BOLD_TEXT+'Schedule a '+
    ANSI_.MAGENTA_BLACK+'Fixed'+ANSI_.ALL_OFF+
    ANSI_.BOLD_TEXT+' downtime of this duration'+ANSI_.ALL_OFF,
    help='\tSpecified as a number of minutes, minumum 5, maximum 999'+
    '\n\tThe downtime begins 1 minute from the current system'+
    '\n\ttime and ends '+ANSI_.BOLD_TEXT+ANSI_.MAGENTA_BLACK+
    'MMM'+ANSI_.ALL_OFF+' minutes later')
  return CLI_PARSER_

#################
# Program Start #
#################
def main():
  log_tool_message_(OUR_TOOL_+' Started execution')
  # Get and process command-line arguments
  COMMAND_LINE_ = argument_parser_func_()
  ARGS_ = COMMAND_LINE_.parse_args()

  # Get the Group memberships of the User ID under which this tool is
  #	running - the list must include REQUIRED_GROUP_
  EGID_LIST_ = os.getgroups()
  # Also get the Effective UID
  EUID_ = os.geteuid()
  try:
    re.search(REQUIRED_GROUP_,str(EGID_LIST_))
  except:
    # Oops! Group not in the list of Groups for this User!
    if ARGS_.v:
      print(ANSI_.BOLD_TEXT+ANSI_.MAGENTA_BLACK+'FATAL ERROR: '+
        ANSI_.RED_BLACK+'This tool must be executed by a User'+
        ' who has access to '+ANSI_.MAGENTA_BLACK+'Nagios'+
        ANSI_.ALL_OFF+'\n')
      COMMAND_LINE_.print_help()
      sys.exit(1)
    else:
      # OK, as long as the EUID is not 0, get the text User name
      if (EUID_ != 0):
        USERNAME_ = getpass.getuser()
      else:
        if ARGS_.v:
          print(ANSI_.BOLD_TEXT+ANSI_.MAGENTA_BLACK+'FATAL ERROR: '+
            ANSI_.RED_BLACK+'This tool must be executed by an '+
            ANSI_.MAGENTA_BLACK+'UNPRIVILEGED'+ANSI_.RED_BLACK+
            ' User ID'+ANSI_.ALL_OFF+'\n')
          COMMAND_LINE_.print_help()
          sys.exit(1)

    #print('USERNAME_ is '+USERNAME_)
    if ARGS_.p:
      PWFILE_ = '/home/'+USERNAME_+'/'+PW_FILENAME_
      # Does file exist? If it does, read first line
      try:
        with open(PWFILE_,mode='r',buffering=-1,newline=None) as FILE_OBJECT_:
          LINES_ = FILE_OBJECT_.readlines()
          # Ignore any lines beyond the first
          #   Must strip leading/trailing whitespace!
          USERPW_ = LINES_[0].strip()
      except FileNotFoundError:
        # File does not exist, ignore -p
        USERPW_ = ''
        if ARGS_.v:
          print('\n\t'+ANSI_.BOLD_TEXT+'WARNING: Did not find '+
            ANSI_.BLUE_BLACK+PWFILE_+ANSI_.ALL_OFF+
            ANSI_.BOLD_TEXT+'; ignoring '+ANSI_.MAGENTA_BLACK+
            '-p'+ANSI_.ALL_OFF+'\n')
    else:
      USERPW_ = ''

    # Do I need to get a password from the user?
    if USERPW_ == '':
      print('\n\t')
      USERPW_ = getpass.getpass(prompt='Nagios Web UI Password: ')
      print('\n')

    # If -d was specified, validate it (the logic is too complex for
    #   the parser object)
    if ARGS_.d != '':
      # I expect a string in the form HH:MM
      #   Both values must be non-negative integers
      #   HH cannot exceed 23, MM cannot exceed 59
      # Total string length must between 3 and 5 inclusive
      CHKSTR_ = len(ARGS_.d)
      if ( CHKSTR_ > 5 ) or ( CHKSTR_ < 3 ):
        if ARGS_.v:
          print(ANSI_.BOLD_TEXT+ANSI_.MAGENTA_BLACK+'FATAL ERROR: '+
            ANSI_.RED_BLACK+'The '+ANSI_.YELLOW_BLACK+'-d'+
            ANSI_.RED_BLACK+' parameter has an invalid length ('+
            str(CHKSTR_)+')'+ANSI_.ALL_OFF+'\n')
          COMMAND_LINE_.print_help()
          sys.exit(1)

      # The string must contain :
      try:
        CHKINDEX_ = ARGS_.d.index(':')
      except:
        if ARGS_.v:
          print(ANSI_.BOLD_TEXT+ANSI_.MAGENTA_BLACK+'FATAL ERROR: '+
            ANSI_.RED_BLACK+'The '+ANSI_.YELLOW_BLACK+'-d'+
            ANSI_.RED_BLACK+' parameter invalid (missing '+
            ANSI_.MAGENTA_BLACK+':'+ANSI_.RED_BLACK+' )'+
            ANSI_.ALL_OFF+'\n')
          COMMAND_LINE_.print_help()
          sys.exit(1)
        else:
          CHKHOUR_ = ARGS_.d[0:CHKINDEX_]
          CHKMIN_ = ARGS_.d[CHKINDEX_+1:CHKSTR_]

        if (CHKHOUR_.isdigit()) and (CHKMIN_.isdigit()):
          # CHKHOUR_ needs to be in the range 0-23
          # CHKMIN_ needs to be in the range 0-59
          # isdigit accepts negative numbers
          if ( ( ( int(CHKHOUR_) < 0 ) or ( int(CHKMIN_) < 0 ) ) or
            ( ( int(CHKHOUR_) == 0 ) and ( int(CHKMIN_) == 0 ) ) or
            ( ( int(CHKHOUR_) > 23 ) or ( int(CHKMIN_) > 59 ) ) ):
            if ARGS_.v:
              print(ANSI_.BOLD_TEXT+ANSI_.MAGENTA_BLACK+
                'FATAL ERROR: '+ANSI_.YELLOW_BLACK+'-d '+
                ARGS_.d+ANSI_.RED_BLACK+' is invalid'+
                ANSI_.ALL_OFF+'\n')
              COMMAND_LINE_.print_help()
              sys.exit(1)
        else:
          if ARGS_.v:
            print(ANSI_.BOLD_TEXT+ANSI_.MAGENTA_BLACK+'FATAL ERROR: '+
              ANSI_.RED_BLACK+'The '+ANSI_.YELLOW_BLACK+'-d'+
              ANSI_.RED_BLACK+' parameter invalid (missing '+
              ANSI_.MAGENTA_BLACK+':'+ANSI_.RED_BLACK+' )'+
              ANSI_.ALL_OFF+'\n')
            COMMAND_LINE_.print_help()
            sys.exit(1)
    else:
      CHKHOUR_ = ''
      CHKMIN_ = ''
    # End of if ARGS_.d != ''

    # At this point, if -d was specified, it is valid, and the duration
    #	data is in the strings CHKHOUR_ and CHKMIN_
    # If -f was specified, then those strings are initialized empty
    #   and the argument parser already validated ARGS_.f

    # If -c was not specified, then argparse would have bombed out
    COMMENT_ = ('Auto-scheduled for ' + ARGS_.c)

    # I need the host's name
    D_HOSTNAME_ = os.uname()[1]
    # It is likely to be the "d" name of the host, and I need
    #   the "m" name
    if D_HOSTNAME_[6:7] == 'd':
      M_HOSTNAME_ = D_HOSTNAME_[0:6]+'m'+D_HOSTNAME_[7:]
    else:
      M_HOSTNAME_ = D_HOSTNAME_

    # If -d was specified, then CHKHOUR_ will not be blank
    if (CHKHOUR_ == ''):
      # OK, -f was specified - Downtime is Fixed
      FIXED_ = '1'
      DOWNTIME_TYPE_ = 'Fixed'
      CHKHOUR_ = '2'
      CHKMIN_ = '0'
      # Get current system time in Epoch format and add 60 seconds
      START_TIME_EPOCH_ = (int(time.time()) + 60)
      # Now express in proper format
      CHKTIME_ = time.gmtime(START_TIME_EPOCH_)
      START_TIME_ = (str(CHKTIME_[1])+'-'+str(CHKTIME_[2])+'-'+
        str(CHKTIME_[0])+' '+str(CHKTIME_[3])+':'+
        str(CHKTIME_[4])+':00')
      # To calculate end time, multiply the argument by 60 (to get
      #   number of seconds) and add it to the start time
      TIME_OFFSET_ = ARGS_.f * 60
      END_TIME_EPOCH_ = START_TIME_EPOCH_ + TIME_OFFSET_
      CHKTIME_ = time.gmtime(END_TIME_EPOCH_)
      END_TIME_ = (str(CHKTIME_[1])+'-'+str(CHKTIME_[2])+'-'+
        str(CHKTIME_[0])+' '+str(CHKTIME_[3])+':'+
        str(CHKTIME_[4])+':00')
    else:
      FIXED_ = '0'
      DOWNTIME_TYPE_ = 'Floating'
      # This is a Floating downtime
      # Multiply the argument by 60 to get number of seconds
      TIME_OFFSET_ = ( ( CHKHOUR_ * 60 ) * 60 ) + ( CHKMIN_ * 60 )
      # Get current system time in Epoch format and add 60 seconds
      START_TIME_EPOCH_ = (int(time.time()) + 60)
      # Now express in proper format
      CHKTIME_ = time.gmtime(START_TIME_EPOCH_)
      START_TIME_ = (str(CHKTIME_[1])+'-'+str(CHKTIME_[2])+'-'+
        str(CHKTIME_[0])+' '+str(CHKTIME_[3])+':'+
        str(CHKTIME_[4])+':00')
      # To calculate end time, multiply the argument by 60 (to get
      #   number of seconds) and add it to the start time
      END_TIME_EPOCH_ = START_TIME_EPOCH_ + TIME_OFFSET_
      CHKTIME_ = time.gmtime(END_TIME_EPOCH_)
      END_TIME_ = (str(CHKTIME_[1])+'-'+str(CHKTIME_[2])+'-'+
        str(CHKTIME_[0])+' '+str(CHKTIME_[3])+':'+
        str(CHKTIME_[4])+':00')

    # If invoked with -v, then output info to stdout
    if ARGS_.v:
      print('\n'+ANSI_.BOLD_TEXT+OUR_TOOL_+' - '+
        ANSI_.GREEN_BLACK+TOOL_DESC_+ANSI_.BLUE_BLACK+
        ' v'+TOOL_VERSION_+ANSI_.ALL_OFF+'\n')
      print('\tScheduling '+ANSI_.BOLD_TEXT+DOWNTIME_TYPE_+
        ANSI_.ALL_OFF+' downtime for '+ANSI_.BOLD_TEXT+
        M_HOSTNAME_+ANSI_.ALL_OFF+'\n')
      if FIXED_ == '1':
        print('\t\t'+ANSI_.BOLD_TEXT+'Start Time: '+
          ANSI_.ALL_OFF+START_TIME_)
        print('\t\t'+ANSI_.BOLD_TEXT+'  End Time: '+
          ANSI_.ALL_OFF+END_TIME_)
      else:
        if (CHKHOUR_ == 1):
          HOUR_NOUN_ = 'hour'
        else:
          HOUR_NOUN_ = 'hours'
          if (CHKMIN_ == 1):
            MIN_NOUN_ = 'minute'
          else:
            MIN_NOUN_ = 'minutes'

          print('\t\t'+ANSI_.BOLD_TEXT+'  Duration: '+ANSI_.ALL_OFF+
            CHKHOUR_+' '+HOUR_NOUN_+' '+CHKMIN_+' '+MIN_NOUN_)

      print('\n')

    log_tool_message_('Preparing command')

    # First 5 values are consistent
    # If "fixed" is "1" then "start_time" and "end_time" are used;
    #   "hours" and "minutes" are ignored
    # If "fixed" is "0" then a floating outage is scheduled with a
    #   maximum duration of "hours" and "minutes"; "start_time" and
    #   "end_time" are ignored
    # "com_data" is the text comment
    # "host" is the long (FQDN) hostname as defined in Nagios
    # "com_author" is User ID recognized by Nagios - generally should
    #   match the User ID submitted in the "auth" stanza
    # NOTES:  0) A valid "start_time" MUST be specified no matter what
    #         1) To be "valid", the "start_time" must be after the
    #             current time (ON THE NAGIOS HOST!)
    #         2) Even if the Downtime type is "floating"
    #             ("fixed": '0'), a valid "end_time" MUST be specified
    #         3) To be "valid", the "end_time" MUST be later than the
    #             "start_time", even if just by 1 second
    #         4) Times are expressed using    MM-DD-YYYY HH:MM:SS
    #                   MM may be expressed as M, DD as D
    payload = {
        'cmd_mod': '2',
        'cmd_typ': '55',
        'trigger': '0',
        'childoptions': '0',
        'btnSubmit': 'Commit',
        'fixed': FIXED_,
        'hours': CHKHOUR_,
        'minutes': CHKMIN_,
        'start_time': START_TIME_,
        'end_time': END_TIME_,
        'com_data': COMMENT_,
        'host': M_HOSTNAME_,
        'com_author': USERNAME_
    }
    #print('response = (requests.post('+NAGIOS_URL_+',data='+str(payload)+
    #    ',verify=False,auth=('+USERNAME_+', '+USERPW_+'))))')
    response = (requests.post(NAGIOS_URL_,data=payload,verify=False,
        auth=(USERNAME_, USERPW_)))
    #print(response.text)
    log_tool_message_(OUR_TOOL_+' Execution completed')

if __name__ == "__main__":
    main()

#############################
# End of nagios_downtime.py #
#############################
