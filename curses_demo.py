#!/usr/bin/python3
#######################################################################
# curses_demo.py - A Simple Demo of Python ncurses
#######################################################################
# This tool demonstrates a simple curses-style menu in Python v3
#
# REQUIRES:
#   0) Python v3
#   1) The "python3-curses" (or equivalent) package
#
# NOTES:
#   0) This is just code I slapped together, based on some examples,
#       mainly as a proof-of-concept for the environment I was in
#       at the time
#
# KNOWN BUGS:
#   0) Needs clean-up and better documentation
#
# TO DO:
#   0)
#
#######################################################################
TOOL_VERSION_='100'
#######################################################################
# Change Log (Reverse Chronological Order)
# Who When______ What__________________________________________________
# dxb 2019-08-14 Original creation
#######################################################################
# Module Imports #
##################
# System-specific functions/parameters
import sys
# OS-specific functions
import os
# ncurses library
import curses

# Define how tool was invoked
OUR_TOOL_=os.path.realpath(__file__)

class CursesMenu(object):

  INIT = {'type' : 'init'}

  def __init__(self, menu_options):
    self.screen=curses.initscr()
    self.menu_options=menu_options
    self.selected_option=0
    self._previously_selected_option=None
    self.running=True

    # Initialize curses, and curses input
    curses.noecho()
    curses.cbreak()
    curses.start_color()
    # Hide the cursor
    curses.curs_set(0)
    # Enable the numeric keypad
    self.screen.keypad(1)

    # Define a color pair to designate the highlighted option
    curses.init_pair(1, curses.COLOR_BLACK, curses.COLOR_WHITE)
    self.hilite_color = curses.color_pair(1)
    self.normal_color = curses.A_NORMAL

  def prompt_selection(self, parent=None):
    if parent is None:
      lastoption = "Exit"
    else:
      lastoption = "Return to previous menu ({})".format(parent['title'])

    option_count = len(self.menu_options['options'])

    input_key = None

    ENTER_KEY = ord('\n')
    while input_key != ENTER_KEY:
      if self.selected_option != self._previously_selected_option:
        self._previously_selected_option = self.selected_option

        self.screen.border(0)
        self._draw_title()
        for option in range(option_count):
          if self.selected_option == option:
            self._draw_option(option, self.hilite_color)
          else:
            self._draw_option(option, self.normal_color)

        if self.selected_option == option_count:
          self.screen.addstr(5 + option_count, 4, "{:2} - {}".format(option_count+1,lastoption), self.hilite_color)
        else:
          self.screen.addstr(5 + option_count, 4, "{:2} - {}".format(option_count+1,lastoption), self.normal_color)

        max_y, max_x = self.screen.getmaxyx()
        if input_key is not None:
          self.screen.addstr(max_y-3, max_x - 5, "{:3}".format(self.selected_option))
        self.screen.refresh()

        input_key = self.screen.getch()
        down_keys = [curses.KEY_DOWN, ord('j')]
        up_keys = [curses.KEY_UP, ord('k')]
        exit_keys = [ord('q')]

        if input_key in down_keys:
          if self.selected_option < option_count:
            self.selected_option += 1
          else:
            self.selected_option = 0

        if input_key in up_keys:
          if self.selected_option > 0:
            self.selected_option -= 1
          else:
            self.selected_option = option_count

        # If exit was selected, then return
        if input_key in exit_keys:
          self.selected_option = option_count
          break

    return self.selected_option

  def _draw_option(self, option_number, style):
    self.screen.addstr(5 + option_number,
                           4,
                           "{:2} - {}".format(option_number+1, self.menu_options['options'][option_number]['title']),
                           style)

  def _draw_title(self):
    self.screen.addstr(2, 2, self.menu_options['title'], curses.A_STANDOUT)
    self.screen.addstr(4, 2, self.menu_options['subtitle'], curses.A_BOLD)

  def display(self):
    selected_option = self.prompt_selection()
    i, _ = self.screen.getmaxyx()
    curses.endwin()
    os.system('clear')
    if selected_option < len(self.menu_options['options']):
      selected_opt = self.menu_options['options'][selected_option]
      return selected_opt
    else:
      self.running = False
      return {'title' : 'Exit', 'type' : 'exitmenu'}

menu = {'title' : 'Curses Menu',
        'type' : 'menu',
        'subtitle' : 'A Curses menu in Python'}

option_1 = {'title' : 'Hello World',
            'type' : 'command',
            'command' : 'echo Hello World!'}

menu['options'] = [option_1]

m = CursesMenu(menu)
selected_action = m.display()

if selected_action['type'] != 'exitmenu':
    os.system(selected_action['command'])

# End of curses_demo.py
#######################
