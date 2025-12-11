#!/usr/bin/env python
# -*- coding: utf-8 -*-

import vim
import os
import os.path
from .utils import *
from .explorer import *
from .manager import *
from .gitRepo import *
import ctypes
from ctypes import wintypes

user32 = ctypes.windll.user32
kernel32 = ctypes.windll.kernel32
psapi = ctypes.windll.psapi

WNDENUMPROC = ctypes.WINFUNCTYPE(wintypes.BOOL, wintypes.HWND, wintypes.LPARAM)

def getWindowTitles(target_exe=None, target_class=None):
    titles = set()
    def enum_windows_proc(hwnd, lParam):
        if not user32.IsWindowVisible(hwnd):
            return True

        length = user32.GetWindowTextLengthW(hwnd)
        if length == 0:
            return True

        title_buffer = ctypes.create_unicode_buffer(length + 1)
        user32.GetWindowTextW(hwnd, title_buffer, length + 1)
        title = title_buffer.value

        if target_class:
            class_buffer = ctypes.create_unicode_buffer(256)
            user32.GetClassNameW(hwnd, class_buffer, 256)
            class_name = class_buffer.value
            if class_name != target_class:
                return True

        if target_exe:
            pid = wintypes.DWORD()
            user32.GetWindowThreadProcessId(hwnd, ctypes.byref(pid))

            process_handle = kernel32.OpenProcess(0x0410, False, pid)
            exe_name = "Unknown"
            if process_handle:
                exe_buffer = ctypes.create_unicode_buffer(1024)
                if psapi.GetModuleBaseNameW(process_handle, 0, exe_buffer, 1024):
                    exe_name = exe_buffer.value
                kernel32.CloseHandle(process_handle)

            if exe_name.lower() != target_exe.lower():
                return True

        titles.add(title)
        return True

    user32.EnumWindows(WNDENUMPROC(enum_windows_proc), 0)
    return titles

#*****************************************************
# GitRepoExplorer
#*****************************************************
class GitRepoExplorer(Explorer):
    def __init__(self):
        pass

    def getContent(self, *args, **kwargs):
        repos = sorted(gitRepo.getRepos())
        arguments = kwargs.get("arguments", {})
        def strip_quotes(s):
            if s and len(s) >= 2 and ((s.startswith('"') and s.endswith('"')) or (s.startswith("'") and s.endswith("'"))):
                return s[1:-1]
            return s

        target_exe = strip_quotes(arguments.get("--detect-exe", [None])[0])
        target_class = strip_quotes(arguments.get("--detect-class", [None])[0])
        fmt = strip_quotes(arguments.get("--detect-fmt", ["{} - Antigravity"])[0])

        if target_exe or target_class:
            titles = getWindowTitles(target_exe, target_class)
            result = []
            # lfCmd("echoerr 'Debug: expected_title: %s'" % str(list(titles)).replace("'", "''"))
            for repo in repos:
                basename = os.path.basename(repo)
                if not basename:
                  continue

                expected_title = fmt.format(basename)
                # lfCmd("echoerr 'Debug: expected_title: %s'" % str(expected_title))
                if any(expected_title in title for title in titles):
                    result.append(repo + " [Open]")
                else:
                    result.append(repo)

            # Prioritize [Open] repos
            result.sort(key=lambda x: (not x.endswith(" [Open]"), x))
            return result
        return repos

    def getStlCategory(self):
        return 'GitRepo'

    def getStlCurDir(self):
        return escQuote(lfEncode(lfGetCwd()))

    def supportsMulti(self):
        return False

    def supportsNameOnly(self):
        return True

#*****************************************************
# GitRepoExplManager
#*****************************************************
class GitRepoExplManager(Manager):
    def __init__(self):
        super(GitRepoExplManager, self).__init__()

    def _getExplClass(self):
        return GitRepoExplorer


    def _defineMaps(self):
        lfCmd("call leaderf#GitRepo#Maps()")

    def _acceptSelection(self, *args, **kwargs):
        if len(args) == 0:
            return
        line = args[0]
        if line.endswith(" [Open]"):
            line = line[:-7]
        lfCmd("cd %s" % escSpecial(line))

        # Open a file inside .git as requested
        git_files = ["HEAD", "config", "description", "index"]
        for name in git_files:
            target = os.path.join(line, ".git", name)
            if os.path.exists(target):
                lfCmd("edit %s" % escSpecial(os.path.join(".git", name)))
                return

    def _getDigest(self, line, mode):
        if line.endswith(" [Open]"):
            return line[:-7]
        return line

    def _getDigestStartPos(self, line, mode):
        return 0

    def _createHelp(self):
        help = []
        help.append('" <CR>/<double-click>/o : jump to the repository')
        help.append('" q : quit')
        help.append('" <F1> : toggle this help')
        help.append('" ---------------------------------------------------------')
        return help

#*****************************************************
# gitRepoExplManager is a singleton
#*****************************************************
gitRepoExplManager = GitRepoExplManager()

__all__ = ['gitRepoExplManager']
