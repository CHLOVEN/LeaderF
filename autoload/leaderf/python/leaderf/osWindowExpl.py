#!/usr/bin/env python
# -*- coding: utf-8 -*-

import ctypes
import os
import sys
from ctypes import wintypes
from leaderf.utils import *
from leaderf.explorer import *
from leaderf.manager import *

# Windows API Definitions
user32 = ctypes.windll.user32
kernel32 = ctypes.windll.kernel32
psapi = ctypes.windll.psapi

WNDENUMPROC = ctypes.WINFUNCTYPE(wintypes.BOOL, wintypes.HWND, wintypes.LPARAM)

class OsWindowExplorer(Explorer):
    def __init__(self):
        self._content = []

    def getContent(self, *args, **kwargs):
        self._content = []
        
        def enum_windows_proc(hwnd, lParam):
            if not user32.IsWindowVisible(hwnd):
                return True
            
            length = user32.GetWindowTextLengthW(hwnd)
            if length == 0:
                return True
            
            title_buffer = ctypes.create_unicode_buffer(length + 1)
            user32.GetWindowTextW(hwnd, title_buffer, length + 1)
            title = title_buffer.value
            
            # Skip some common invisible/utility windows if needed
            if not title or title == "Default IME" or title == "MSCTFIME UI":
                return True

            class_buffer = ctypes.create_unicode_buffer(256)
            user32.GetClassNameW(hwnd, class_buffer, 256)
            class_name = class_buffer.value

            # Filter by Class Name
            target_class = kwargs.get("arguments", {}).get("--class", [None])[0]
            if target_class and target_class != class_name:
                return True

            pid = wintypes.DWORD()
            user32.GetWindowThreadProcessId(hwnd, ctypes.byref(pid))
            
            process_handle = kernel32.OpenProcess(0x0410, False, pid) # PROCESS_QUERY_INFORMATION | PROCESS_VM_READ
            exe_name = "Unknown"
            if process_handle:
                exe_buffer = ctypes.create_unicode_buffer(1024)
                if psapi.GetModuleBaseNameW(process_handle, 0, exe_buffer, 1024):
                    exe_name = exe_buffer.value
                kernel32.CloseHandle(process_handle)

            # Filter by Executable Name
            target_exe = kwargs.get("arguments", {}).get("--exe", [None])[0]
            if target_exe and target_exe.lower() != exe_name.lower():
                return True

            # Format: [PID] [ExeName] [Class] Title
            # We store HWND as a hidden field or just use the index if we cache it, 
            # but for simplicity let's put HWND in the string or just rely on finding it again? 
            # Actually, finding by title/pid is risky if duplicates. 
            # Let's store HWND in the line as a hidden hex? 
            # Leaderf lines are usually displayed as is. 
            # Let's put HWND at the start, maybe hidden or just visible.
            # Visible is fine for PoC.
            
            line = "{:<10} {:<8} {:<15} {:<20} {}".format(hwnd, pid.value, exe_name, class_name, title)
            self._content.append(line)
            return True

        user32.EnumWindows(WNDENUMPROC(enum_windows_proc), 0)
        return self._content

    def getStlCategory(self):
        return "OsWindow"

    def getStlCurDir(self):
        return escQuote(lfEncode(lfGetCwd()))

    def supportsNameOnly(self):
        return True

class OsWindowExplManager(Manager):
    def __init__(self):
        super(OsWindowExplManager, self).__init__()

    def _getExplClass(self):
        return OsWindowExplorer

    def _defineMaps(self):
        lfCmd("call leaderf#OsWindow#Maps()")

    def _acceptSelection(self, *args, **kwargs):
        if len(args) == 0:
            return
        
        line = args[0]
        # Extract HWND from the start of the line
        try:
            hwnd_str = line.split()[0]
            hwnd = int(hwnd_str)
            
            # Restore window if minimized
            if user32.IsIconic(hwnd):
                user32.ShowWindow(hwnd, 9) # SW_RESTORE
            
            # Try to bring to foreground
            # Windows 98/2000+ lock SetForegroundWindow. 
            # We might need to attach thread input or use SwitchToThisWindow (deprecated but works)
            
            # Method 1: SetForegroundWindow
            # user32.SetForegroundWindow(hwnd)
            
            # Method 2: SwitchToThisWindow (often bypasses restrictions)
            user32.SwitchToThisWindow(hwnd, True)
            
        except ValueError:
            lfCmd("echoerr 'Invalid HWND in selection'")

    def _createHelp(self):
        help = []
        help.append('" <CR>/o : activate selected window')
        help.append('" q : quit')
        help.append('" i : switch to input mode')
        help.append('" <F1> : toggle this help')
        help.append('" ---------------------------------------------------------')
        return help

# Singleton
osWindowExplManager = OsWindowExplManager()

__all__ = ["osWindowExplManager"]
