#!/usr/bin/python3
#######################################################################
# dell-query-array.py - Dell PowerVault Management CLI Query Tool
#######################################################################
# This tool programmatically accesses the Management Controller
#   interface of a Dell PowerVault ME-{4,5}012/4084 Storage
#   Array and retrieves specific information.
#
# REQUIRES:
#   0) Python v3
#   1) The password portion of the login credentials for the device;
#         it accepts this either from a prompt or by reading
#         them from a file (PW_FILENAME_)
#
# NOTES:
#   0) IMPORTANT! The design of this tool makes CRITICAL ASSUMPTIONS!
#
#       A) The User ID is assumed to be a standard value as defined
#           in the variable DEVICE_USER_
#       B) All of the Management Controllers are  >> directly <<
#           reachable via an IPv4 address, and the first two octets of
#           that address are defined in the NETWORK_BASE_ variable
#       C) The third octet of the IP address for the Management
#           Controller varies from "Site" to "Site"; a "Site" is
#           defined by a short string, and for each "Site" there
#           is a specific value for the third octet; these
#           associations are defined in the Dictionary
#           variable named SITE_INFO_
#       D) The last octet of the IP address for the Management
#           Controllers is always the same and is defined in the
#           variable MC_IP_ADDR_
#
#   1) This dumps out information without analysis; use other tools to
#         analyze the output
#   2) The original code was designed for/tested on specific models
#         of Dell PowerVault hardware, with specific Management
#         Controller configurations and code levels; it has not been
#         tested against other similar hardware
#
# KNOWN BUGS:
#   0) Does not validate the contents of PW_FILENAME_; just uses it
#         blindly
#   1) A lot of assumptions are made about networking, IP addresses,
#         and the ID for authentication
#   2) It's possible I introduced a bug when I sanitized the code
#         to remove information specific to the original environment,
#         but I don't have a way to really test it now (the parser
#         doesn't complain about anything, though)
#
# TO DO:
#   0) Improve logging
#   1) Re-factor to better-use functions
#######################################################################
TOOL_VERSION_='1.00'
#######################################################################
# Change Log (Reverse Chronological Order)
# Who When______ What__________________________________________________
# dxb 2020-06-04 Initial creation (v1.00)
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
# Password prompting
import getpass
# HTTP Request support
import requests
# NOTE: Suppress the insecure connection warning for
#       certificate verification
from requests.packages.urllib3.exceptions import InsecureRequestWarning
requests.packages.urllib3.disable_warnings(InsecureRequestWarning)
# JSON interpretation
import json
# Hashing for constructing authentication string
import hashlib

# Screen control and Colors for text output
# Reference example --> ANSI_.BOLD_TEXT_
class ANSI_:
  '''
  Defines ANSI screen and color control variables that can be
  referenced in print statements to highlight text
  '''
  INVERT_TEXT_='\033[7m'
  EOL_='\033[0K'
  UNDERLINE_TEXT_='\033[4m'
  STRIKETHRU_='\033[09m'
  SCREEN_HOME_='\033[0;0H'
  GREEN_BLACK_='\033[32;40m'
  YELLOW_BLACK_='\033[33;40m'
  RED_BLACK_='\033[31;40m'
  BLUE_BLACK_='\033[34;40m'
  WHITE_BLACK_='\033[37;40m'
  CYAN_RED_='\033[36;41m'
  MAGENTA_BLACK_='\033[35;40m'
  PINK_BLACK_='\033[95m'
  BOLD_TEXT_='\033[1m'
  BLINK_ON_='\033[5m'
  ALL_OFF_='\033[0m'

# Globals
TOOL_DESC_='Dell PowerVault Storage Array Query Tool'
# Standard User ID for authenticating to the Management Controller
DEVICE_USER_='<Your-Standard-Admin-ID-Here>'
# Filename where password might be founf
PW_FILENAME_='.dell-query-array'
# First two octets of IPv4 network where Management Controllers live
NETWORK_BASE_='192.168.'
# Standard last octet value of Management Controller IP address
MC_IP_ADDR_='.110'
# Min/Max values for numeric argument to -s
#   These could also be determined programmatically
MIN_SITE_INDEX_=11
MAX_SITE_INDEX_=17
# Min/Max values for string argument to -s
#   These could also be determined programmatically
MIN_SITE_LEN_=2
MAX_SITE_LEN_=6
# Define how tool was invoked
THIS_TOOL_=os.path.realpath(__file__)
# Create a dictonary that correlates Site Index to Site ID
# The numbers are the SITE_INDEX_ values and are used as the 3rd octet
#   in the IP address for the Management Controller
# The strings are the corresponding values for SITE_NAME_
SITE_INFO_={11:'DEV',12:'TST',13:'PRD',14:'HQ',15:'DR',16:'BACKUP1',17:'BACKUP2'}

def argument_parser_func_():
    """
    Creates and returns an ArgumentParser object

    Requires the Global TOOL_DESC_ string consisting of roughly four to
    eight words summarizing the script, for example
        Linux Frobish Renoberation Tool

    Also requires the Global TOOL_VERSION_ string holding the current
    version of the program in the format #.##

    Finally requires import of the argparse and os packages
    """

    # Redefine the ArgumentParser class so I can force it to print out
    # the Help screen if a required parameter is missing
    class MyParser(argparse.ArgumentParser):
        """
        Redefinition of the ArgumentParser Class
        """
        def error(self, message):
            print('\n'+ANSI_.BOLD_TEXT_+ANSI_.MAGENTA_BLACK_+
              'FATAL ERROR: '+ANSI_.RED_BLACK_+message+ANSI_.ALL_OFF_)
            self.print_help()
            sys.exit(2)

    # DESC_TEXT_ begins the creation of an output string that looks
    #   like /path/to/tool.py - Linux Frobish Renoberate Tool v1.00
    #    by relying on the TOOL_DESC_ and TOOL_VERSION_ strings
    DESC_TEXT_=('\n \n'+ANSI_.BOLD_TEXT_+THIS_TOOL_+' - '+
        ANSI_.GREEN_BLACK_+TOOL_DESC_+ANSI_.BLUE_BLACK_+' v'+
        TOOL_VERSION_+ANSI_.ALL_OFF_)

    # HELP_TEXT_ builds on DESC_TEXT_ by appending text like
    #   Usage : /path/to/tool.py -a -b <ARGUMENT> | -h
    HELP_TEXT_=(DESC_TEXT_+'\n \n\t'+ANSI_.BOLD_TEXT_+'Usage: '+
        ANSI_.ALL_OFF_+THIS_TOOL_+ANSI_.BOLD_TEXT_+'-s'+
        ANSI_.BLUE_BLACK_+' [ <SITE_INDEX> | <SITE_NAME> ] '+
        ANSI_.ALL_OFF_+' [ '+ANSI_.BOLD_TEXT_+'-a'+ANSI_.ALL_OFF_+
        ' ] [ '+ANSI_.BOLD_TEXT_+'-c'+ANSI_.ALL_OFF_+
        ' | '+ANSI_.BOLD_TEXT_+'-e'+ANSI_.ALL_OFF_+
        ' | '+ANSI_.BOLD_TEXT_+'-f'+ANSI_.ALL_OFF_+
        ' | '+ANSI_.BOLD_TEXT_+'-p'+ANSI_.ALL_OFF_+
        ' | '+ANSI_.BOLD_TEXT_+'-t'+ANSI_.ALL_OFF_+' ] ' +
        ' | '+ANSI_.BOLD_TEXT_+'-h'+ANSI_.ALL_OFF_)

    # EPILOG_TEXT_ defines a block of text that appears AFTER the Help
    #    screen when the script is invoked with the -h parameter; at
    #    minimum the string should look something like
    #       Using filename.txt
    EPILOG_TEXT_ = ('\t'+ANSI_.BOLD_TEXT_+'Using '+ANSI_.BLUE_BLACK_+
        PW_FILENAME_+ANSI_.ALL_OFF_+ANSI_.BOLD_TEXT_+ANSI_.ALL_OFF_
        +'\n \n')

    # Create an argument parser object (using my special Class)
    #   usage=argparse.SUPPRESS - Prevents the normal "usage" header from
    #        appearing; I built my own in HELP_TEXT_
    #   formatter_class=argparse.RawTextHelpFormatter - Allow me to
    #        control help screen formatting
    CLI_PARSER_ = (MyParser(usage=argparse.SUPPRESS,
        description=HELP_TEXT_,epilog=EPILOG_TEXT_,
        formatter_class=argparse.RawTextHelpFormatter,add_help=True) )
    CLI_PARSER_.add_argument('-a',action='store_true',default=False,
        required=False,help=ANSI_.BOLD_TEXT_+'Get authentication '+
        'password from file'+ANSI_.ALL_OFF_+'\nIf not specified, '+
        'you will be prompted for a password\n\tto the Storage '+
        'Array management interface\nIf specified, this tool will '+
        'look in your home directory\n\tfor a text file named '+
        ANSI_.BOLD_TEXT_+ANSI_.BLUE_BLACK_+PW_FILENAME_+ANSI_.ALL_OFF_+
        '\nThe file should contain a single line of text that is '+
        'the password for the Storage Array interface;\n\tif the file does '+
        'not exist, or is empty, then '+ANSI_.BOLD_TEXT_+
        '-a'+ANSI_.ALL_OFF_+' is ignored')
    CLI_PARSER_.add_argument('-s',action='store',required=True,
        metavar=ANSI_.BOLD_TEXT_+'<SITE_INDEX>'+ANSI_.ALL_OFF_+
        ' or '+ANSI_.BOLD_TEXT_+'<SITE_NAME>'+ANSI_.ALL_OFF_+'\n'+
        '\t\t\tEither the two-digit '+ANSI_.BOLD_TEXT_+
        'SITE_INDEX'+ANSI_.ALL_OFF_+' or the '+ANSI_.BOLD_TEXT_+
        'SITE_NAME'+ANSI_.ALL_OFF_+'; for example, '+ANSI_.BOLD_TEXT_+
        '14'+ANSI_.ALL_OFF_+' or '+ANSI_.BOLD_TEXT_+'HQ'+
        ANSI_.ALL_OFF_+' (the acronym is case-insensitive)',
        help='\t'+ANSI_.BOLD_TEXT_+ANSI_.MAGENTA_BLACK_+
        'This command-line option MUST be specified'+ANSI_.ALL_OFF_)
    CLI_PARSER_.add_argument('-j',action='store_true',default=False,
        required=False,help='Output results in '+ANSI_.BOLD_TEXT_+
        'json'+ANSI_.ALL_OFF_+' format instead of the default '+
        ANSI_.BOLD_TEXT_+'plain text'+ANSI_.ALL_OFF_+' as it would '+
        'appear on a console')
    CLI_PARSER_.add_argument('-q',action='store_true',default=False,
        required=False,help='Minimize output (useful if parsing the '+
        'output in another process)')
    # The -c, -e, -f, -p and -t arguments are mutually exclusive, and not
    #    required
    OPTION_GROUP_ = CLI_PARSER_.add_mutually_exclusive_group(required=False)
    OPTION_GROUP_.add_argument('-c',action='store_true',default=False,
        help='Limit output to information about the '+ANSI_.BOLD_TEXT_+
        'Controllers'+ANSI_.ALL_OFF_+'\n\tThis option is exclusive with '+
        ANSI_.BOLD_TEXT_+'-e'+ANSI_.ALL_OFF_+', '+
        ANSI_.BOLD_TEXT_+'-f'+ANSI_.ALL_OFF_+', '+
        ANSI_.BOLD_TEXT_+'-p'+ANSI_.ALL_OFF_+', and '+
        ANSI_.BOLD_TEXT_+'-t'+ANSI_.ALL_OFF_)
    OPTION_GROUP_.add_argument('-e',action='store_true',default=False,
        help='Limit output to information about the '+ANSI_.BOLD_TEXT_+
        'Enclosures'+ANSI_.ALL_OFF_+'\n\tThis option is exclusive with '+
        ANSI_.BOLD_TEXT_+'-c'+ANSI_.ALL_OFF_+', '+
        ANSI_.BOLD_TEXT_+'-f'+ANSI_.ALL_OFF_+', '+
        ANSI_.BOLD_TEXT_+'-p'+ANSI_.ALL_OFF_+', and '+
        ANSI_.BOLD_TEXT_+'-t'+ANSI_.ALL_OFF_)
    OPTION_GROUP_.add_argument('-f',action='store_true',default=False,
        help='Limit output to information about the '+ANSI_.BOLD_TEXT_+
        'Fan Modules'+ANSI_.ALL_OFF_+'\n\tThis option is exclusive with '+
        ANSI_.BOLD_TEXT_+'-c'+ANSI_.ALL_OFF_+', '+
        ANSI_.BOLD_TEXT_+'-e'+ANSI_.ALL_OFF_+', '+
        ANSI_.BOLD_TEXT_+'-p'+ANSI_.ALL_OFF_+', and '+
        ANSI_.BOLD_TEXT_+'-t'+ANSI_.ALL_OFF_)
    OPTION_GROUP_.add_argument('-p',action='store_true',default=False,
        help='Limit output to information about the '+ANSI_.BOLD_TEXT_+
        'Power Supplies'+ANSI_.ALL_OFF_+'\n\tThis option is exclusive with '+
        ANSI_.BOLD_TEXT_+'-c'+ANSI_.ALL_OFF_+', '+
        ANSI_.BOLD_TEXT_+'-e'+ANSI_.ALL_OFF_+', '+
        ANSI_.BOLD_TEXT_+'-f'+ANSI_.ALL_OFF_+', and '+
        ANSI_.BOLD_TEXT_+'-t'+ANSI_.ALL_OFF_)
    OPTION_GROUP_.add_argument('-t',action='store_true',default=False,
        help='Limit output to information about the '+ANSI_.BOLD_TEXT_+
        'Temperature and Voltage Sensors'+ANSI_.ALL_OFF_+
        '\n\tThis option is exclusive with '+
        ANSI_.BOLD_TEXT_+'-c'+ANSI_.ALL_OFF_+', '+
        ANSI_.BOLD_TEXT_+'-e'+ANSI_.ALL_OFF_+', '+
        ANSI_.BOLD_TEXT_+'-f'+ANSI_.ALL_OFF_+', and '+
        ANSI_.BOLD_TEXT_+'-p'+ANSI_.ALL_OFF_)
    return CLI_PARSER_

#################
# Program Start #
#################
def main():
    # Get and process command-line arguments
    COMMAND_LINE_=argument_parser_func_()
    ARGS_=COMMAND_LINE_.parse_args()
    # Init working variables
    SITE_NAME_=''
    PWFILE_=''
    SITE_INDEX_=0
    # USERNAME_ is used to contruct string referencing home
    #   directory of invoking user; it is not used to login
    #   to the Management Controller
    USERNAME_=''

    # Determine if the argument to -s is valid
    SITE_VALID_=False
    # First, is it an integer?
    if ARGS_.s.isdigit():
        # Yes, make sure it is in valid range
        if MIN_SITE_INDEX_ <= int(ARGS_.s) <= MAX_SITE_INDEX_:
          SITE_INDEX_=int(ARGS_.s)
          # Determine Site Name
          # This uses SITE_INFO_ to match a numeric argument to
          #   to the string identifying that site
          for key,value in SITE_INFO_.items():
            if key == SITE_INDEX_:
              SITE_VALID_=True
              SITE_NAME_=value
              break
    else:
        # No, should be a string of chars
        if MIN_SITE_LEN_ <= len(ARGS_.s) <= MAX_SITE_LEN_:
            # Determine if Site Name is valid
            SITE_NAME_=ARGS_.s.upper()
            for key,value in SITE_INFO_.items():
                if value == SITE_NAME_:
                    SITE_VALID_=True
                    SITE_INDEX_=key
                    break

    # At this point, SITE_NAME_ should contain a string and
    #    SITE_INDEX_ should be an positive integer
    # If not, then the argument to -s was not valid
    if not SITE_VALID_:
        print(ANSI_.BOLD_TEXT_+ANSI_.MAGENTA_BLACK_+'FATAL ERROR: '+
            ANSI_.RED_BLACK_+'The '+ANSI_.YELLOW_BLACK_+'-s'+
            ANSI_.RED_BLACK_+' parameter is invalid (must be '+
            ' a positive integer between '+ANSI_.MAGENTA_BLACK_+
            MIN_SITE_INDEX_+ANSI_.RED_BLACK_+' and '+
            ANSI_.MAGENTA_BLACK_+MAX_SITE_INDEX_+ANSI_.RED_BLACK+
            ', inclusive; or a string of '+ANSI_.MAGENTA_BLACK_+
            MIN_SITE_LEN_+ANSI_.RED_BLACK_+' to '+ANSI_.MAGENTA_BLACK_+
            MAX_SITE_LEN_+ANSI_.RED_BLACK_+' characters)'+
            ANSI_.ALL_OFF_+'\n')
        COMMAND_LINE_.print_help()
        sys.exit(1)
    else:
        # Get the user name
        USERNAME_=getpass.getuser()

    #print('\nSITE_NAME_ is '+SITE_NAME_)
    #print('\nPWFILE_ is '+PWFILE_)
    #print('\nUSERNAME_ is '+USERNAME_)
    #print('\nSITE_INDEX_ is '+str(SITE_INDEX_))
    # If invoked with -a, check that file exists
    if ARGS_.a:
        PWFILE_='/home/'+USERNAME_+'/'+PW_FILENAME_
        # Does file exist? If it does, read first line
        try:
            with open(PWFILE_,mode='r',buffering=-1,newline=None) as FILE_OBJECT_:
                LINES_=FILE_OBJECT_.readlines()
                # Ignore any lines beyond the first
                #   Also strip leading/trailing whitespace!
                USERPW_=LINES_[0].strip()
        except FileNotFoundError:
            # File does not exist, ignore -a
            USERPW_=''
            if not ARGS_.q:
                print('\n\t'+ANSI_.BOLD_TEXT_+'WARNING: Did not find '+
                    ANSI_.BLUE_BLACK_+PWFILE_+ANSI_.ALL_OFF_+
                    ANSI_.BOLD_TEXT_+'; ignoring '+ANSI_.MAGENTA_BLACK_+
                    '-a'+ANSI_.ALL_OFF_+'\n')
    else:
        USERPW_=''
        PWFILE_=''

    # Do I need to get a password from the user?
    if PWFILE_=='':
        if USERPW_=='':
            USERPW_=getpass.getpass(prompt='\n\tDell PowerVault in '+SITE_NAME_+' Storage Array Password: ')
    else:
        # I found a PWFILE_, make sure it had something
        if USERPW_=='':
            print(ANSI_.BOLD_TEXT_+ANSI_.MAGENTA_BLACK_+'FATAL ERROR: '+
                ANSI_.RED_BLACK_+'The password file '+ANSI_.BLUE_BLACK_+
                PWFILE_+ANSI_.RED_BLACK_+' did not contain anything'+
                ANSI_.ALL_OFF_+'\n')
            COMMAND_LINE_.print_help()
            sys.exit(1)
    # If invoked with -q, minimize output
    if not ARGS_.q:
        print('\n'+ANSI_.BOLD_TEXT_+THIS_TOOL_+' - '+
            ANSI_.GREEN_BLACK_+TOOL_DESC_+ANSI_.BLUE_BLACK_+' v'+
            TOOL_VERSION_+ANSI_.ALL_OFF_)
    #print('\nUSERPW_ is '+USERPW_)

    # The CLI parser took care of preventing conflicting parameters but I
    #    still need to figure out if one was given
    if ((ARGS_.c) or (ARGS_.e) or (ARGS_.f) or (ARGS_.p) or (ARGS_.t)):
        # Only one of these will "hit"
        if ARGS_.c:
            REPORT_LIST_=[ 'controllers' ]
        if ARGS_.e:
            REPORT_LIST_=[ 'enclosures' ]
        if ARGS_.f:
            REPORT_LIST_=[ 'fan-modules' ]
        if ARGS_.p:
            REPORT_LIST_=[ 'power-supplies' ]
        if ARGS_.t:
            REPORT_LIST_=[ 'sensor-status' ]
    else:
        # List all 5 reports
        REPORT_LIST_=[ 'controllers', 'enclosures', 'fan-modules', 'power-supplies', 'sensor-status' ]

    #print(REPORT_LIST_)
    # Construct the URL
    TARGET_URL_='https://'+NETWORK_BASE_+str(SITE_INDEX_)+MC_IP_ADDR_
    if not ARGS_.q:
        print('\n\tQuerying '+ANSI_.BOLD_TEXT_+SITE_NAME_+ANSI_.ALL_OFF_+' Storage Array at '+
            ANSI_.BOLD_TEXT_+TARGET_URL_+ANSI_.ALL_OFF_)
    AUTH_STRING_=hashlib.sha256(b''+DEVICE_USER_+str.encode(USERPW_)).hexdigest()
    #print('\nTARGET_URL_ is '+TARGET_URL_)
    #print('\nAUTH_STRING_ is '+AUTH_STRING_)

    # Login and obtain the session key
    HEADERS_={'datatype':'json'}
    QUERY_=requests.get(TARGET_URL_+'/api/login/'+AUTH_STRING_,headers=HEADERS_,verify=False)
    RESPONSE_=json.loads(QUERY_.content)
    SESSION_KEY_=RESPONSE_['status'][0]['response']
    #print('\nSESSION_KEY__ is '+SESSION_KEY_)

    # Generate requested report(s)
    for THIS_REPORT_ in REPORT_LIST_:
        if not ARGS_.q:
            print('\n\t\tQuerying '+ANSI_.BOLD_TEXT_+THIS_REPORT_+ANSI_.ALL_OFF_)

        if ARGS_.j:
            HEADERS_={'sessionKey': SESSION_KEY_, 'datatype':'json'}
        else:
            HEADERS_={'sessionKey': SESSION_KEY_, 'datatype':'console'}
        QUERY_=requests.get(TARGET_URL_+'/api/show/'+THIS_REPORT_,headers=HEADERS_,verify=False)
        if ARGS_.j:
            print(QUERY_.content)
        else:
            print('\n'+QUERY_.content.decode('UTF-8')+'\n')

if __name__ == "__main__":
    main()

##############################
# End of dell-query-array.py #
##############################
