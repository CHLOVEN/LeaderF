#!/usr/bin/env python
# -*- coding: utf-8 -*-

import ctypes
import json
import os
import sys
import tempfile
from ctypes import wintypes
from leaderf.utils import *
from leaderf.explorer import *
from leaderf.manager import *

user32 = ctypes.windll.user32
kernel32 = ctypes.windll.kernel32
psapi = ctypes.windll.psapi

WNDENUMPROC = ctypes.WINFUNCTYPE(wintypes.BOOL, wintypes.HWND, wintypes.LPARAM)



class SendToAGMExplorer(Explorer):
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

      if not title or title == "Default IME" or title == "MSCTFIME UI":
        return True

      class_buffer = ctypes.create_unicode_buffer(256)
      user32.GetClassNameW(hwnd, class_buffer, 256)
      class_name = class_buffer.value

      target_class = kwargs.get("arguments", {}).get("--class", [None])[0]
      if target_class and target_class != class_name:
        return True

      pid = wintypes.DWORD()
      user32.GetWindowThreadProcessId(hwnd, ctypes.byref(pid))

      process_handle = kernel32.OpenProcess(0x0410, False, pid)
      exe_name = "Unknown"
      if process_handle:
        exe_buffer = ctypes.create_unicode_buffer(1024)
        if psapi.GetModuleBaseNameW(process_handle, 0, exe_buffer, 1024):
          exe_name = exe_buffer.value
        kernel32.CloseHandle(process_handle)

      target_exe = kwargs.get("arguments", {}).get("--exe", [None])[0]
      if target_exe and target_exe.lower() != exe_name.lower():
        return True

      line = "{:<10} {:<8} {:<15} {:<20} {}".format(hwnd, pid.value, exe_name, class_name, title)
      self._content.append(line)
      return True

    user32.EnumWindows(WNDENUMPROC(enum_windows_proc), 0)
    return self._content

  def getStlCategory(self):
    return "SendToAGM"

  def getStlCurDir(self):
    return escQuote(lfEncode(lfGetCwd()))

  def supportsNameOnly(self):
    return True



class SendToAGMExplManager(Manager):
  def __init__(self):
    super(SendToAGMExplManager, self).__init__()
    self._selection_content = ""

  def _getExplClass(self):
    return SendToAGMExplorer

  def _defineMaps(self):
    lfCmd("call leaderf#SendToAGM#Maps()")

  def setSelectionContent(self, content):
    self._selection_content = content

  def _acceptSelection(self, *args, **kwargs):
    if len(args) == 0:
      return

    line = args[0]
    try:
      parts = line.split()
      if len(parts) < 5:
        lfCmd("echoerr 'Invalid window line format'")
        return

      title = " ".join(parts[4:])

      self._sendToAPI(title, self._selection_content)

    except Exception as e:
      lfCmd("echoerr 'Error: {}'".format(str(e).replace("'", "''")))

  def _sendToAPI(self, title, message):
    try:
      import urllib.request
      import urllib.error

      payload = json.dumps({"title": title, "message": message})
      req = urllib.request.Request(
        "http://localhost:3848/send",
        data=payload.encode("utf-8"),
        headers={"Content-Type": "application/json"},
        method="POST"
      )

      response = urllib.request.urlopen(req, timeout=5)
      result = response.read().decode("utf-8")
      lfCmd("echo '{}'".format(result.replace("'", "''")))

    except urllib.error.URLError as e:
      lfCmd("echoerr 'Failed to connect to AGM: {}'".format(str(e).replace("'", "''")))
    except Exception as e:
      lfCmd("echoerr 'Error sending to AGM: {}'".format(str(e).replace("'", "''")))

  def _createHelp(self):
    help = []
    help.append('" <CR>/o : send selection to selected AGM window')
    help.append('" q : quit')
    help.append('" i : switch to input mode')
    help.append('" <F1> : toggle this help')
    help.append('" ---------------------------------------------------------')
    return help



sendToAGMExplManager = SendToAGMExplManager()

__all__ = ["sendToAGMExplManager"]
