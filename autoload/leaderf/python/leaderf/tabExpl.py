#!/usr/bin/env python
# -*- coding: utf-8 -*-

import vim
import os
import os.path
from leaderf.utils import *
from leaderf.explorer import *
from leaderf.manager import *

#*****************************************************
# TabExplorer
#*****************************************************
class TabExplorer(Explorer):
    def __init__(self):
        self._content = []

    def getContent(self, *args, **kwargs):
        self._content = []
        for tab in vim.tabpages:
            tab_nr = tab.number
            win_count = len(tab.windows)
            try:
                # In some vim versions/configurations, accessing tab.window might fail if invalid
                active_win = tab.window
                buf_name = active_win.buffer.name
                if not buf_name:
                    buf_name = "[No Name]"
                else:
                    buf_name = os.path.basename(buf_name)
            except Exception:
                buf_name = "Unknown"

            # Format: Tab: {tabnr} | Wins: {window_count} | {active_buffer_name}
            line = "Tab: {:<3} | Wins: {:<3} | {}".format(tab_nr, win_count, buf_name)
            self._content.append(line)
        
        return self._content

    def getStlCategory(self):
        return "Tab"

    def getStlCurDir(self):
        return escQuote(lfEncode(lfGetCwd()))

    def supportsNameOnly(self):
        return True

#*****************************************************
# TabExplManager
#*****************************************************
class TabExplManager(Manager):
    def __init__(self):
        super(TabExplManager, self).__init__()

    def _getExplClass(self):
        return TabExplorer

    def _defineMaps(self):
        lfCmd("call leaderf#Tab#Maps()")

    def _acceptSelection(self, *args, **kwargs):
        if len(args) == 0:
            return
        line = args[0]
        # Line format: "Tab: 1   | Wins: 2   | buffer_name"
        try:
            parts = line.split('|')
            tab_part = parts[0].strip() # "Tab: 1"
            tab_nr = tab_part.split(':')[1].strip()
            
            lfCmd("tabnext %s" % tab_nr)
        except Exception:
            lfCmd("echoerr 'Invalid tab selection'")

    def _createHelp(self):
        help = []
        help.append('" <CR>/o : switch to selected tab')
        help.append('" q : quit')
        help.append('" i : switch to input mode')
        help.append('" <F1> : toggle this help')
        help.append('" ---------------------------------------------------------')
        return help

# Singleton
tabExplManager = TabExplManager()

__all__ = ["tabExplManager"]
