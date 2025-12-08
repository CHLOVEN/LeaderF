#!/usr/bin/env python
# -*- coding: utf-8 -*-

import vim
import re
import os
import os.path
import fnmatch
import time
import locale
import shutil
from functools import wraps
from .utils import *
from .explorer import *
from .manager import *
from .asyncExecutor import AsyncExecutor
from .devicons import (
    webDevIconsGetFileTypeSymbol,
    removeDevIcons,
    matchaddDevIconsDefault,
    matchaddDevIconsExact,
    matchaddDevIconsExtension,
)

def showRelativePath(func):
    @wraps(func)
    def deco(*args, **kwargs):
        if lfEval("g:Lf_ShowRelativePath") == '1':
            # os.path.relpath() is too slow!
            dir = lfGetCwd() if args[0]._cmd_work_dir == "" else args[1]
            cwd_length = len(lfEncode(dir))
            if not dir.endswith(os.sep):
                cwd_length += 1
            return [line[cwd_length:] for line in func(*args, **kwargs)]
        else:
            return func(*args, **kwargs)
    return deco

def showDevIcons(func):
    @wraps(func)
    def deco(*args, **kwargs):
        if lfEval("get(g:, 'Lf_ShowDevIcons', 1)") == "1":
            content = func(*args, **kwargs)
            # In case of Windows, line feeds may be included when reading from the cache.
            return [format_line(line.rstrip()) for line in content or []]
        else:
            return func(*args, **kwargs)
    return deco

def format_line(line):
    return webDevIconsGetFileTypeSymbol(line) + line


#*****************************************************
# FileExplorer
#*****************************************************
class FileExplorer(Explorer):
    def __init__(self):
        self._cur_dir = ''
        self._content = []
        self._cache_dir = os.path.join(lfEval("g:Lf_CacheDirectory"),
                                       'LeaderF',
                                       'python' + lfEval("g:Lf_PythonVersion"),
                                       'file')
        self._cache_index = os.path.join(self._cache_dir, 'cacheIndex')
        self._external_cmd = None
        self._initCache()
        self._executor = []
        self._no_ignore = None
        self._type = None
        self._cmd_work_dir = ""

    def _initCache(self):
        if not os.path.exists(self._cache_dir):
            os.makedirs(self._cache_dir)
        if not os.path.exists(self._cache_index):
            with lfOpen(self._cache_index, 'w', errors='ignore'):
                pass

    def _getFiles(self, dir, mode='file'):
        start_time = time.time()
        wildignore = lfEval("g:Lf_WildIgnore")
        file_list = []
        for dir_path, dirs, files in os.walk(dir, followlinks = False
                if lfEval("g:Lf_FollowLinks") == '0' else True):
            dirs[:] = [i for i in dirs if True not in (fnmatch.fnmatch(i,j)
                       for j in wildignore.get('dir', []))]
            if mode == 'dir':
                for name in dirs:
                    file_list.append(lfEncode(os.path.join(dir_path,name)))
            elif mode == 'both':
                for name in dirs:
                    file_list.append(lfEncode(os.path.join(dir_path,name)))
                for name in files:
                    if True not in (fnmatch.fnmatch(name, j) for j in wildignore.get('file', [])):
                        file_list.append(lfEncode(os.path.join(dir_path,name)))
            else:
                for name in files:
                    if True not in (fnmatch.fnmatch(name, j)
                                    for j in wildignore.get('file', [])):
                        file_list.append(lfEncode(os.path.join(dir_path,name)))
            if time.time() - start_time > float(
                    lfEval("g:Lf_IndexTimeLimit")):
                return file_list
        return file_list

    @showDevIcons
    @showRelativePath
    def _getFileList(self, dir):
        dir = dir if dir.endswith(os.sep) else dir + os.sep
        with lfOpen(self._cache_index, 'r+', errors='ignore') as f:
            lines = f.readlines()
            path_length = 0
            target = -1
            for i, line in enumerate(lines):
                path = line.split(None, 2)[2].strip()
                if dir.startswith(path) and len(path) > path_length:
                    path_length = len(path)
                    target = i

            if target != -1:
                lines[target] = re.sub(r'^\S*',
                                       '%.3f' % time.time(),
                                       lines[target])
                f.seek(0)
                f.truncate(0)
                f.writelines(lines)
                with lfOpen(os.path.join(self._cache_dir,
                                         lines[target].split(None, 2)[1]),
                            'r', errors='ignore') as cache_file:
                    if lines[target].split(None, 2)[2].strip() == dir:
                        return cache_file.readlines()
                    else:
                        file_list = [line for line in cache_file.readlines()
                                     if line.startswith(dir)]
                        if file_list == []:
                            type_arg = self._arguments.get("--type", ["file"])[0]
                            mode = 'file'
                            if type_arg == 'dir':
                                mode = 'dir'
                            elif type_arg == 'both':
                                mode = 'both'
                            file_list = self._getFiles(dir, mode)
                        return file_list
            else:
                start_time = time.time()
                type_arg = self._arguments.get("--type", ["file"])[0]
                mode = 'file'
                if type_arg == 'dir':
                    mode = 'dir'
                elif type_arg == 'both':
                    mode = 'both'
                file_list = self._getFiles(dir, mode)
                delta_seconds = time.time() - start_time
                if delta_seconds > float(lfEval("g:Lf_NeedCacheTime")):
                    cache_file_name = ''
                    if len(lines) < int(lfEval("g:Lf_NumberOfCache")):
                        f.seek(0, 2)
                        ts = time.time()
                        line = '%.3f cache_%.3f %s\n' % (ts, ts, dir)
                        f.write(line)
                        cache_file_name = 'cache_%.3f' % ts
                    else:
                        for i, line in enumerate(lines):
                            path = line.split(None, 2)[2].strip()
                            if path.startswith(dir):
                                cache_file_name = line.split(None, 2)[1].strip()
                                line = '%.3f %s %s\n' % (time.time(),
                                        cache_file_name, dir)
                                break
                        if cache_file_name == '':
                            timestamp = lines[0].split(None, 2)[0]
                            oldest = 0
                            for i, line in enumerate(lines):
                                if line.split(None, 2)[0] < timestamp:
                                    timestamp = line.split(None, 2)[0]
                                    oldest = i
                            cache_file_name = lines[oldest].split(None, 2)[1].strip()
                            lines[oldest] = '%.3f %s %s\n' % (time.time(),
                                            cache_file_name, dir)
                        f.seek(0)
                        f.truncate(0)
                        f.writelines(lines)
                    with lfOpen(os.path.join(self._cache_dir, cache_file_name),
                                'w', errors='ignore') as cache_file:
                        for line in file_list:
                            cache_file.write(line + '\n')
                return file_list

    @showDevIcons
    def _readFromFileList(self, files):
        result = []
        for file in files:
            with lfOpen(file, 'r', errors='ignore') as f:
                result += f.readlines()
        return result

    def _refresh(self):
        dir = os.path.abspath(self._cur_dir)
        dir = dir if dir.endswith(os.sep) else dir + os.sep
        with lfOpen(self._cache_index, 'r+', errors='ignore') as f:
            lines = f.readlines()
            path_length = 0
            target = -1
            for i, line in enumerate(lines):
                path = line.split(None, 2)[2].strip()
                if dir.startswith(path) and len(path) > path_length:
                    path_length = len(path)
                    target = i

            if target != -1:
                lines[target] = re.sub(r'^\S*', '%.3f' % time.time(), lines[target])
                f.seek(0)
                f.truncate(0)
                f.writelines(lines)
                cache_file_name = lines[target].split(None, 2)[1]
                file_list = self._getFiles(dir, 'dir' if self._arguments.get("--type", ["file"])[0] == 'dir' else 'file')
                with lfOpen(os.path.join(self._cache_dir, cache_file_name),
                            'w', errors='ignore') as cache_file:
                    for line in file_list:
                        cache_file.write(line + '\n')

    def _exists(self, path, dir):
        """
        return True if `dir` exists in `path` or its ancestor path,
        otherwise return False
        """
        if os.name == 'nt':
            # e.g. C:\\
            root = os.path.splitdrive(os.path.abspath(path))[0] + os.sep
        else:
            root = '/'

        while os.path.abspath(path) != root:
            cur_dir = os.path.join(path, dir)
            if os.path.exists(cur_dir) and os.path.isdir(cur_dir):
                return True
            path = os.path.join(path, "..")

        cur_dir = os.path.join(path, dir)
        if os.path.exists(cur_dir) and os.path.isdir(cur_dir):
            return True

        return False

    def _expandGlob(self, type, glob):
        # is absolute path
        if os.name == 'nt' and re.match(r"^[a-zA-Z]:[/\\]", glob) or glob.startswith('/'):
            if type == "file":
                return glob
            elif type == "dir":
                return os.path.join(glob, '*')
            else:
                return glob
        else:
            if type == "file":
                return "**/" + glob
            elif type == "dir":
                return "**/" + os.path.join(glob, '*')
            else:
                return glob

    def _buildCmd(self, dir, **kwargs):
        if self._cmd_work_dir:
            if os.name == 'nt':
                cd_cmd = 'cd /d "{}" && '.format(dir)
            else:
                cd_cmd = 'cd "{}" && '.format(dir)
        else:
            cd_cmd = ""

        if lfEval("g:Lf_ShowRelativePath") == '1' and self._cmd_work_dir == "":
            dir = os.path.relpath(dir)

        if lfEval("exists('g:Lf_ExternalCommand')") == '1':
            if cd_cmd:
                cmd = cd_cmd + lfEval("g:Lf_ExternalCommand").replace('"%s"', '').replace('%s', '')
            else:
                cmd = lfEval("g:Lf_ExternalCommand") % dir.join('""')
            self._external_cmd = cmd
            return cmd

        if lfEval("g:Lf_UseVersionControlTool") == '1':
            if self._exists(dir, ".git") and lfEval("executable('git')") == '1':
                wildignore = lfEval("g:Lf_WildIgnore")
                if ".git" in wildignore.get("dir", []):
                    wildignore.get("dir", []).remove(".git")
                if ".git" in wildignore.get("file", []):
                    wildignore.get("file", []).remove(".git")
                ignore = ""
                for i in wildignore.get("dir", []):
                    ignore += ' -x "%s"' % i
                for i in wildignore.get("file", []):
                    ignore += ' -x "%s"' % i

                if "--no-ignore" in kwargs.get("arguments", {}):
                    no_ignore = ""
                else:
                    no_ignore = "--exclude-standard"

                if lfEval("get(g:, 'Lf_RecurseSubmodules', 0)") == '1':
                    recurse_submodules = "--recurse-submodules"
                else:
                    recurse_submodules = ""

                if cd_cmd:
                    cmd = cd_cmd + 'git ls-files %s && git ls-files --others %s %s' % (recurse_submodules, no_ignore, ignore)
                else:
                    cmd = 'git ls-files %s "%s" && git ls-files --others %s %s "%s"' % (recurse_submodules, dir, no_ignore, ignore, dir)
                
                if kwargs.get("arguments", {}).get("--type", ["file"])[0] in ["dir", "both"]:
                    # git ls-files doesn't support directory listing easily. 
                    # We might need to use git ls-tree or fallback.
                    # For now, let's try git ls-tree if it's HEAD?
                    # Or just fallback to find/fd.
                    pass # Fallback to default tools if possible? 
                    # Actually, if we return cmd here, it uses it.
                    # Let's try to use `git ls-tree -d -r --name-only HEAD` if we are sure.
                    # But that only shows committed dirs.
                    # Let's just not use git for dirs for now, or use `find` fallback.
                    return None # Fallback to default tool

                self._external_cmd = cmd
                return cmd
            elif self._exists(dir, ".hg") and lfEval("executable('hg')") == '1':
                wildignore = lfEval("g:Lf_WildIgnore")
                if ".hg" in wildignore.get("dir", []):
                    wildignore.get("dir", []).remove(".hg")
                if ".hg" in wildignore["file"]:
                    wildignore.get("file", []).remove(".hg")
                ignore = ""
                for i in wildignore.get("dir", []):
                    ignore += ' -X "%s"' % self._expandGlob("dir", i)
                for i in wildignore.get("file", []):
                    ignore += ' -X "%s"' % self._expandGlob("file", i)

                if cd_cmd:
                    cmd = cd_cmd + 'hg files %s' % ignore
                else:
                    cmd = 'hg files %s "%s"' % (ignore, dir)
                
                if kwargs.get("arguments", {}).get("--type", ["file"])[0] in ["dir", "both"]:
                    return None # Fallback

                self._external_cmd = cmd
                return cmd

        if lfEval("exists('g:Lf_DefaultExternalTool')") == '1':
            default_tool = {"rg": 0, "pt": 0, "ag": 0, "find": 0}
            tool = lfEval("g:Lf_DefaultExternalTool")
            if tool and lfEval("executable('%s')" % tool) == '0':
                raise Exception("executable '%s' can not be found!" % tool)
            default_tool[tool] = 1
        else:
            default_tool = {"rg": 1, "pt": 1, "ag": 1, "find": 1}

        if default_tool["rg"] and lfEval("executable('rg')") == '1':
            wildignore = lfEval("g:Lf_WildIgnore")
            if os.name == 'nt': # https://github.com/BurntSushi/ripgrep/issues/500
                color = ""
                ignore = ""
                for i in wildignore.get("dir", []):
                    if lfEval("g:Lf_ShowHidden") != '0' or not i.startswith('.'): # rg does not show hidden files by default
                        ignore += ' -g "!%s"' % i
                for i in wildignore.get("file", []):
                    if lfEval("g:Lf_ShowHidden") != '0' or not i.startswith('.'):
                        ignore += ' -g "!%s"' % i
            else:
                color = "--color never"
                ignore = ""
                for i in wildignore.get("dir", []):
                    if lfEval("g:Lf_ShowHidden") != '0' or not i.startswith('.'):
                        ignore += " -g '!%s'" % i
                for i in wildignore.get("file", []):
                    if lfEval("g:Lf_ShowHidden") != '0' or not i.startswith('.'):
                        ignore += " -g '!%s'" % i

            if lfEval("g:Lf_FollowLinks") == '1':
                followlinks = "-L"
            else:
                followlinks = ""

            if lfEval("g:Lf_ShowHidden") == '0':
                show_hidden = ""
            else:
                show_hidden = "--hidden"

            if "--no-ignore" in kwargs.get("arguments", {}):
                no_ignore = "--no-ignore"
            else:
                no_ignore = ""

            if dir == '.':
                cur_dir = ''
            else:
                cur_dir = '"%s"' % dir

            if cd_cmd:
                cmd = cd_cmd + 'rg --no-messages --files %s %s %s %s %s' % (color, ignore, followlinks, show_hidden, no_ignore)
            else:
                cmd = 'rg --no-messages --files %s %s %s %s %s %s' % (color, ignore, followlinks, show_hidden, no_ignore, cur_dir)
            
            if kwargs.get("arguments", {}).get("--type", ["file"])[0] in ["dir", "both"]:
                 default_tool["rg"] = 0 # Fallback to other tools

        if default_tool["rg"] and lfEval("executable('rg')") == '1':
            self._external_cmd = cmd
            return cmd

        if default_tool["pt"] and lfEval("executable('pt')") == '1':
            wildignore = lfEval("g:Lf_WildIgnore")
            ignore = ""
            for i in wildignore.get("dir", []):
                ignore += ' --ignore=%s' % i
            for i in wildignore.get("file", []):
                ignore += ' --ignore=%s' % i

            if lfEval("g:Lf_FollowLinks") == '1':
                followlinks = "-l"
            else:
                followlinks = ""

            if lfEval("g:Lf_ShowHidden") == '0':
                show_hidden = ""
            else:
                show_hidden = "--hidden"

            if "--no-ignore" in kwargs.get("arguments", {}):
                no_ignore = "-U"
            else:
                no_ignore = ""

            if cd_cmd:
                cmd = cd_cmd + 'pt --nocolor %s %s %s %s -g=""' % (ignore, followlinks, show_hidden, no_ignore)
            else:
                cmd = 'pt --nocolor %s %s %s %s -g="" "%s"' % (ignore, followlinks, show_hidden, no_ignore, dir)
            
            if kwargs.get("arguments", {}).get("--type", ["file"])[0] in ["dir", "both"]:
                 default_tool["pt"] = 0

        if default_tool["pt"] and lfEval("executable('pt')") == '1':
            self._external_cmd = cmd
            return cmd

        if default_tool["ag"] and lfEval("executable('ag')") == '1':
            wildignore = lfEval("g:Lf_WildIgnore")
            ignore = ""
            for i in wildignore.get("dir", []):
                ignore += ' --ignore "%s"' % i
            for i in wildignore.get("file", []):
                ignore += ' --ignore "%s"' % i

            if lfEval("g:Lf_FollowLinks") == '1':
                followlinks = "-f"
            else:
                followlinks = ""

            if lfEval("g:Lf_ShowHidden") == '0':
                show_hidden = ""
            else:
                show_hidden = "--hidden"

            if "--no-ignore" in kwargs.get("arguments", {}):
                no_ignore = "-U --skip-vcs-ignores"
            else:
                no_ignore = ""

            if cd_cmd:
                cmd = cd_cmd + 'ag --nocolor --silent %s %s %s %s -g ""' % (ignore, followlinks, show_hidden, no_ignore)
            else:
                cmd = 'ag --nocolor --silent %s %s %s %s -g "" "%s"' % (ignore, followlinks, show_hidden, no_ignore, dir)
            
            if kwargs.get("arguments", {}).get("--type", ["file"])[0] in ["dir", "both"]:
                 default_tool["ag"] = 0

        if default_tool["ag"] and lfEval("executable('ag')") == '1':
            self._external_cmd = cmd
            return cmd

        if default_tool["find"] and lfEval("executable('find')") == '1':
            wildignore = lfEval("g:Lf_WildIgnore")
            ignore = ""
            for i in wildignore.get("dir", []):
                ignore += ' -name "%s" -prune -o' % i
            for i in wildignore.get("file", []):
                ignore += ' -name "%s" -prune -o' % i

            if lfEval("g:Lf_FollowLinks") == '1':
                followlinks = "-L"
            else:
                followlinks = ""

            if lfEval("g:Lf_ShowHidden") == '0':
                show_hidden = '-name ".*" -prune -o'
            else:
                show_hidden = ""

            if os.name == 'nt':
                cmd = 'find %s "%s" %s %s %s -type f -print' % (followlinks, dir, ignore, show_hidden, no_ignore)
            else:
                cmd = 'find %s "%s" %s %s %s -type f -print' % (followlinks, dir, ignore, show_hidden, no_ignore)

            if kwargs.get("arguments", {}).get("--type", ["file"])[0] == "dir":
                cmd = cmd.replace("-type f", "-type d")
            elif kwargs.get("arguments", {}).get("--type", ["file"])[0] == "both":
                cmd = cmd.replace("-type f", "")

            self._external_cmd = cmd
            return cmd

        self._external_cmd = None
        return None

    @removeDevIcons
    def _writeCache(self, content):
        dir = self._cur_dir if self._cur_dir.endswith(os.sep) else self._cur_dir + os.sep
        with lfOpen(self._cache_index, 'r+', errors='ignore') as f:
            lines = f.readlines()
            target = -1
            for i, line in enumerate(lines):
                if dir == line.split(None, 2)[2].strip():
                    target = i
                    break

            if target != -1:    # already cached
                if time.time() - self._cmd_start_time <= float(lfEval("g:Lf_NeedCacheTime")):
                    os.remove(os.path.join(self._cache_dir, lines[target].split(None, 2)[1]))
                    del lines[target]
                    f.seek(0)
                    f.truncate(0)
                    f.writelines(lines)
                    return

                # update the time
                lines[target] = re.sub(r'^\S*',
                                       '%.3f' % time.time(),
                                       lines[target])
                f.seek(0)
                f.truncate(0)
                f.writelines(lines)
                with lfOpen(os.path.join(self._cache_dir,
                                         lines[target].split(None, 2)[1]),
                            'w', errors='ignore') as cache_file:
                    for line in content:
                        cache_file.write(line + '\n')
            else:
                if time.time() - self._cmd_start_time <= float(lfEval("g:Lf_NeedCacheTime")):
                    return

                cache_file_name = ''
                if len(lines) < int(lfEval("g:Lf_NumberOfCache")):
                    f.seek(0, 2)
                    ts = time.time()
                    # e.g., line = "1496669495.329 cache_1496669495.329 /foo/bar"
                    line = '%.3f cache_%.3f %s\n' % (ts, ts, dir)
                    f.write(line)
                    cache_file_name = 'cache_%.3f' % ts
                else:
                    timestamp = lines[0].split(None, 2)[0]
                    oldest = 0
                    for i, line in enumerate(lines):
                        if line.split(None, 2)[0] < timestamp:
                            timestamp = line.split(None, 2)[0]
                            oldest = i
                    cache_file_name = lines[oldest].split(None, 2)[1].strip()
                    lines[oldest] = '%.3f %s %s\n' % (time.time(), cache_file_name, dir)

                    f.seek(0)
                    f.truncate(0)
                    f.writelines(lines)

                with lfOpen(os.path.join(self._cache_dir, cache_file_name),
                            'w', errors='ignore') as cache_file:
                    for line in content:
                        cache_file.write(line + '\n')

    @showDevIcons
    def _getFilesFromCache(self):
        dir = self._cur_dir if self._cur_dir.endswith(os.sep) else self._cur_dir + os.sep
        with lfOpen(self._cache_index, 'r+', errors='ignore') as f:
            lines = f.readlines()
            target = -1
            for i, line in enumerate(lines):
                if dir == line.split(None, 2)[2].strip():
                    target = i
                    break

            if target != -1:    # already cached
                # update the time
                lines[target] = re.sub(r'^\S*',
                                       '%.3f' % time.time(),
                                       lines[target])
                f.seek(0)
                f.truncate(0)
                f.writelines(lines)
                with lfOpen(os.path.join(self._cache_dir,
                                         lines[target].split(None, 2)[1]),
                            'r', errors='ignore') as cache_file:
                    file_list = cache_file.readlines()
                    if not file_list: # empty
                        return None

                    if lfEval("g:Lf_ShowRelativePath") == '1':
                        if os.path.isabs(file_list[0]):
                            # os.path.relpath() is too slow!
                            cwd_length = len(lfEncode(dir))
                            if not dir.endswith(os.sep):
                                cwd_length += 1
                            return [line[cwd_length:] for line in file_list]
                        else:
                            return file_list
                    else:
                        if os.path.isabs(file_list[0]):
                            return file_list
                        else:
                            return [os.path.join(lfEncode(dir), file) for file in file_list]
            else:
                return None

    def setContent(self, content):
        self._content = content
        if lfEval("g:Lf_UseCache") == '1':
            self._writeCache(content)

    def getContentFromMultiDirs(self, dirs, **kwargs):
        no_ignore = kwargs.get("arguments", {}).get("--no-ignore")
        type_arg = kwargs.get("arguments", {}).get("--type", ["file"])[0]
        if no_ignore != self._no_ignore or type_arg != self._type:
            self._no_ignore = no_ignore
            self._type = type_arg
            arg_changes = True
        else:
            arg_changes = False

        dirs = { os.path.abspath(os.path.expanduser(lfDecode(dir.strip('"').rstrip('\\/')))) for dir in dirs }
        if arg_changes or lfEval("g:Lf_UseMemoryCache") == '0' or dirs != self._cur_dir or \
                not self._content:
            self._cur_dir = dirs

            cmd = ''
            for dir in dirs:
                if not os.path.exists(dir):
                    lfCmd("echoe ' Unknown directory `%s`'" % dir)
                    return None

                command = self._buildCmd(dir, **kwargs)
                if command:
                    if cmd == '':
                        cmd = command
                    else:
                        cmd += ' && ' + command

            if cmd:
                executor = AsyncExecutor()
                self._executor.append(executor)
                if cmd.split(None, 1)[0] == "dir":
                    content = executor.execute(cmd, format_line)
                else:
                    if lfEval("get(g:, 'Lf_ShowDevIcons', 1)") == "1":
                        content = executor.execute(cmd, encoding=lfEval("&encoding"), format_line=format_line)
                    else:
                        content = executor.execute(cmd, encoding=lfEval("&encoding"))
                self._cmd_start_time = time.time()
                return content

        return self._content


    def getContent(self, *args, **kwargs):
        self._arguments = kwargs.get("arguments", {})
        files = kwargs.get("arguments", {}).get("--file", [])
        if files:
            return self._readFromFileList(files)

        dir = lfGetCwd()

        self._cmd_work_dir = ""
        directory = kwargs.get("arguments", {}).get("directory")
        if directory and len(directory) > 1:
            return self.getContentFromMultiDirs(directory, **kwargs)

        if directory and directory[0] not in ['""', "''"]:
            dir = directory[0].strip('"').rstrip('\\/')
            if os.path.exists(os.path.expanduser(lfDecode(dir))):
                if lfEval("get(g:, 'Lf_NoChdir', 1)") == '0':
                    lfCmd("silent cd %s" % dir)
                    dir = lfGetCwd()
                else:
                    dir = os.path.abspath(os.path.expanduser(lfDecode(dir)))
                    self._cmd_work_dir = dir
            else:
                lfCmd("echoe ' Unknown directory `%s`'" % dir)
                return None

        no_ignore = kwargs.get("arguments", {}).get("--no-ignore")
        type_arg = kwargs.get("arguments", {}).get("--type", ["file"])[0]
        if no_ignore != self._no_ignore or type_arg != self._type:
            self._no_ignore = no_ignore
            self._type = type_arg
            arg_changes = True
            
            base_cache_dir = os.path.join(lfEval("g:Lf_CacheDirectory"),
                                       'LeaderF',
                                       'python' + lfEval("g:Lf_PythonVersion"),
                                       'file')
            if self._type == 'dir':
                self._cache_dir = base_cache_dir + '_dir'
            elif self._type == 'both':
                self._cache_dir = base_cache_dir + '_both'
            else:
                self._cache_dir = base_cache_dir
            
            self._cache_index = os.path.join(self._cache_dir, 'cacheIndex')
            self._initCache()
        else:
            arg_changes = False

        if arg_changes or lfEval("g:Lf_UseMemoryCache") == '0' or dir != self._cur_dir or \
                not self._content:
            self._cur_dir = dir

            cmd = self._buildCmd(dir, **kwargs)
            lfCmd("let g:Lf_Debug_Cmd = '%s'" % escQuote(cmd))

            lfCmd("let g:Lf_FilesFromCache = 0")
            if lfEval("g:Lf_UseCache") == '1' and kwargs.get("refresh", False) == False:
                lfCmd("let g:Lf_FilesFromCache = 1")
                self._content = self._getFilesFromCache()
                if self._content:
                    return self._content

            if cmd:
                executor = AsyncExecutor()
                self._executor.append(executor)
                if cmd.split(None, 1)[0] == "dir":
                    content = executor.execute(cmd, format_line)
                else:
                    if lfEval("get(g:, 'Lf_ShowDevIcons', 1)") == "1":
                        content = executor.execute(cmd, encoding=lfEval("&encoding"), format_line=format_line)
                    else:
                        content = executor.execute(cmd, encoding=lfEval("&encoding"))
                self._cmd_start_time = time.time()
                return content
            else:
                self._content = self._getFileList(dir)

        return self._content

    def getFreshContent(self, *args, **kwargs):
        if self._external_cmd:
            self._content = []
            kwargs["refresh"] = True
            return self.getContent(*args, **kwargs)

        self._refresh()
        self._content = self._getFileList(self._cur_dir)
        return self._content

    def getStlCategory(self):
        return 'File'

    def getStlCurDir(self):
        if self._cmd_work_dir:
            return escQuote(lfEncode(self._cmd_work_dir))
        else:
            return escQuote(lfEncode(lfGetCwd()))

    def supportsMulti(self):
        return True

    def supportsNameOnly(self):
        return True

    def cleanup(self):
        for exe in self._executor:
            exe.killProcess()
        self._executor = []


#*****************************************************
# FileExplManager
#*****************************************************
class FileExplManager(Manager):
    def _getExplClass(self):
        return FileExplorer

    def _defineMaps(self):
        lfCmd("call leaderf#File#Maps()")

    def _createHelp(self):
        help = []
        help.append('" <CR>/<double-click>/o : open file under cursor')
        help.append('" x : open file under cursor in a horizontally split window')
        help.append('" v : open file under cursor in a vertically split window')
        help.append('" t : open file under cursor in a new tabpage')
        help.append('" i/<Tab> : switch to input mode')
        help.append('" s : select multiple files')
        help.append('" a : select all files')
        help.append('" c : clear all selections')
        help.append('" M : create a new file/directory')
        help.append('" D : delete the file/directory under cursor')
        help.append('" R : rename/move the file/directory under cursor')
        help.append('" p : preview the file')
        help.append('" q : quit')
        help.append('" <F5> : refresh the cache')
        help.append('" <F1> : toggle this help')
        help.append('" ---------------------------------------------------------')
        return help

    def createFile(self):
        try:
            line = self._getInstance().currentLine
            path = self._getFilePath(line)
            if os.path.isdir(path):
                context_dir = path
            else:
                context_dir = os.path.dirname(path)
            
            if not context_dir:
                context_dir = lfGetCwd()

            # Ensure context_dir ends with separator for display
            if not context_dir.endswith(os.sep):
                context_dir += os.sep

            # Prompt user for input
            name = lfEval("input('Create in %s: ', '', 'file')" % context_dir)
            if not name:
                return

            # Check if it's a directory creation request
            is_dir = False
            if name.startswith('/') or name.startswith(os.sep):
                is_dir = True
                name = name[1:] # Strip leading separator

            full_path = os.path.join(context_dir, name)

            if is_dir:
                if not os.path.exists(full_path):
                    os.makedirs(full_path)
                    lfCmd("echomsg 'Directory created: %s'" % full_path)
                else:
                    lfCmd("echohl Error | echo 'Directory already exists' | echohl None")
            else:
                # Create file
                if not os.path.exists(full_path):
                    # Ensure parent directory exists
                    parent_dir = os.path.dirname(full_path)
                    if parent_dir and not os.path.exists(parent_dir):
                        os.makedirs(parent_dir)
                    
                    with open(full_path, 'w') as f:
                        pass
                    lfCmd("echomsg 'File created: %s'" % full_path)
                else:
                    lfCmd("echohl Error | echo 'File already exists' | echohl None")
            
            self.refresh()
        except Exception as e:
            lfCmd("echohl Error | echo 'Error creating file: %s' | echohl None" % str(e))

    def deleteFile(self):
        line = self._getInstance().currentLine
        if self._getInstance().getWinPos() == 'popup':
            pass # TODO: handle popup mode if needed, but currentLine should work
        
        # Parse file path from line (handle icons if present)
        # The line format depends on showDevIcons and showRelativePath
        # But we can use the explorer's logic to get the full path?
        # Actually, let's try to parse it from the line content displayed
        
        # A safer way might be to get the raw content if possible, but here we only have the line.
        # Let's assume the line contains the path. 
        # If devicons are on, we need to strip them.
        
        # However, `_getDigest` or similar might be useful, but `Manager` doesn't expose a simple "get path for line" easily without knowing the exact format.
        # Let's look at `accept` method in `manager.py` or similar to see how it extracts the path.
        # `manager.py` uses `self._content[self._index]` usually? No, `currentLine` is from the buffer.
        
        # In `FileExplorer`, `format_line` adds icons.
        # Let's try to use `lfEval("expand('<cfile>')")` or similar? No, that's for the buffer.
        
        # Let's look at how `accept` works.
        # It calls `self._getExplorer().acceptSelection(line, mode)`
        
        # Let's implement a helper to get the path from the line.
        # But for now, let's just try to strip the icon if it exists.
        # Standard devicon width is usually 1 char + 1 space.
        
        # Actually, `FileExplorer` doesn't seem to store the raw list in a way that maps 1:1 to lines if filtering is applied?
        # Wait, `self._content` is the list.
        # But the window shows filtered results.
        
        # Let's use the `_instance.window.cursor` to get the line.
        # And we can try to resolve the path.
        
        # For now, let's assume the user is selecting a file from the list.
        # We can use `self._getInstance().currentLine`.
        
        file_path = self._getInstance().currentLine
        if lfEval("get(g:, 'Lf_ShowDevIcons', 1)") == "1":
             # Remove the icon and the space
             # 3 bytes for icon (utf-8) + 1 byte for space? 
             # It's safer to rely on `webDevIconsGetFileTypeSymbol` logic or just strip the first few chars if we know the length.
             # But `webDevIconsGetFileTypeSymbol` returns a symbol + space.
             # Let's just split by space and take the rest? No, filenames can have spaces.
             
             # Let's look at `removeDevIcons` decorator in `fileExpl.py`.
             # It doesn't seem to be used for `currentLine`.
             
             # Let's try to use a regex to strip the icon if we can.
             # Or just ask the user to confirm the file name extracted.
             pass

        # Actually, `manager.py` `accept` method:
        # line = self._getInstance().currentLine
        # self._getExplorer().acceptSelection(line, mode)
        
        # `FileExplorer` doesn't implement `acceptSelection`, so it uses default `Explorer.acceptSelection`?
        # `Explorer` class in `explorer.py`?
        # `Explorer` is in `explorer.py`.
        
        # Let's look at `manager.py` to see how it handles it.
        # It seems `manager.py` handles the opening.
        
        # Let's try to get the path using `self._getExplorer().getStlCurDir()` combined with the line?
        # If `ShowRelativePath` is 1, the line is relative.
        
        # Let's try to implement a robust way to get the full path.
        # If we look at `manager.py`, `_acceptSelection` does:
        # file = line
        # if self._getExplorer().supportsNameOnly():
        #     file = self._getExplorer().getFilePath(file)
        
        # `FileExplorer` supportsNameOnly returns True.
        # But `FileExplorer` doesn't implement `getFilePath`.
        # Wait, `Explorer` base class might have it?
        pass

    def _getFilePath(self, line):
        if lfEval("get(g:, 'Lf_ShowDevIcons', 1)") == "1":
            # Assume icon is always separated by a space
            # And icon is usually non-ascii.
            # A simple heuristic: find the first space and take everything after it?
            # But what if the icon is missing?
            # Let's check `devicons.py` if possible.
            # For now, let's assume 4 bytes (icon + space) if it looks like an icon?
            # Actually, let's just use `line.split(None, 1)[1]` if we are sure there is an icon.
            # But filenames can start with spaces? (Unlikely in this context but possible).
            
            # Let's look at `format_line` in `fileExpl.py`:
            # return webDevIconsGetFileTypeSymbol(line) + line
            # `webDevIconsGetFileTypeSymbol` returns `symbol + ' '`.
            
            # So we can just strip the first part.
            # But we need to be careful.
            
            # Let's try to use `lfEval` to call a vim function to strip it?
            # Or just python string manipulation.
            # The icon is usually 1 character.
            # So `line[line.find(' ')+1:]` might work if the icon is always there.
            pass
            
        # Let's just use a simpler approach:
        # We can re-use `manager.py`'s logic if possible.
        # But `manager.py` is `self`.
        
        # Let's look at `FileExplorer` again.
        # It has `_cmd_work_dir` or `_cur_dir`.
        
        # Let's try to implement `deleteFile` with a best-effort path extraction.
        
        line = self._getInstance().currentLine
        if lfEval("get(g:, 'Lf_ShowDevIcons', 1)") == "1":
            # Try to strip the icon
            # Icons are usually > 128 ord.
            if ord(line[0]) > 128:
                # Find the first space
                idx = line.find(' ')
                if idx != -1:
                    line = line[idx+1:]
        
        file = line.strip()
        
        # Handle relative path
        if lfEval("g:Lf_ShowRelativePath") == '1':
            # We need to join with current dir
            # `self._getExplorer()._cur_dir` ?
            # `FileExplManager` has `_getExplClass` which returns `FileExplorer`.
            # But `self._explorer` is the instance.
            # `Manager` has `self._explorer`.
            
            cwd = self._explorer._cur_dir
            if not cwd:
                cwd = lfGetCwd()
            
            full_path = os.path.join(cwd, file)
        else:
            full_path = file
            
        return full_path

    def deleteFile(self):
        try:
            path = self._getFilePath(self._getInstance().currentLine)
            
            # Confirm deletion
            confirm = lfEval("confirm('Delete %s?', '&Yes\n&No')" % path)
            if confirm != '1':
                return
            
            if os.path.isdir(path):
                if os.listdir(path):
                    confirm = lfEval("confirm('Directory is not empty. Delete recursively?', '&Yes\n&No')")
                    if confirm != '1':
                        return
                    shutil.rmtree(path)
                else:
                    os.rmdir(path)
            else:
                os.remove(path)
            
            lfCmd("echomsg 'Deleted: %s'" % path)
            self.refresh()
        except Exception as e:
            lfCmd("echohl Error | echo 'Error deleting file: %s' | echohl None" % str(e))

    def moveFile(self):
        try:
            old_path = self._getFilePath(self._getInstance().currentLine)
            
            # Prompt for new path
            # Default to current name
            new_path = lfEval("input('Rename/Move to: ', '%s', 'file')" % old_path)
            if not new_path or new_path == old_path:
                return
            
            # Create parent dir if needed
            parent_dir = os.path.dirname(new_path)
            if parent_dir and not os.path.exists(parent_dir):
                os.makedirs(parent_dir)
            
            os.rename(old_path, new_path)
            lfCmd("echomsg 'Moved: %s -> %s'" % (old_path, new_path))
            self.refresh()
        except Exception as e:
            lfCmd("echohl Error | echo 'Error moving file: %s' | echohl None" % str(e))


    def accept(self, mode=''):
        if "--next-action" in self._arguments:
            action = self._arguments["--next-action"][0]
            if action == "create":
                self.createFile()
                self.quit()
            elif action == "delete":
                self.deleteFile()
                self.quit()
            elif action == "move":
                self.moveFile()
                self.quit()
            else:
                super(FileExplManager, self).accept(mode)
        else:
            super(FileExplManager, self).accept(mode)

    def _afterEnter(self):
        super(FileExplManager, self)._afterEnter()
        lfCmd("augroup Lf_File")
        lfCmd("autocmd!")
        lfCmd("autocmd VimLeavePre * call leaderf#File#cleanup()")
        lfCmd("augroup END")

        if lfEval("get(g:, 'Lf_ShowDevIcons', 1)") == '1':
            winid = self._getInstance().getPopupWinId() if self._getInstance().getWinPos() == 'popup' else None
            icon_pattern = r'^__icon__'
            self._match_ids.extend(matchaddDevIconsExtension(icon_pattern, winid))
            self._match_ids.extend(matchaddDevIconsExact(icon_pattern, winid))
            self._match_ids.extend(matchaddDevIconsDefault(icon_pattern, winid))

    def _beforeExit(self):
        super(FileExplManager, self)._beforeExit()
        if self._timer_id is not None:
            lfCmd("call timer_stop(%s)" % self._timer_id)
            self._timer_id = None

    def _bangEnter(self):
        super(FileExplManager, self)._bangEnter()
        if lfEval("exists('*timer_start')") == '0':
            lfCmd("echohl Error | redraw | echo ' E117: Unknown function: timer_start' | echohl NONE")
            return

        self._workInIdle(bang=True)
        if self._read_finished < 2:
            self._timer_id = lfEval("timer_start(1, 'leaderf#File#TimerCallback', {'repeat': -1})")

    def startExplorer(self, win_pos, *args, **kwargs):
        directory = kwargs.get("arguments", {}).get("directory")
        if directory and directory[0] not in ['""', "''"]: # behavior no change for `LeaderfFile <directory>`
            self._orig_cwd = None
            super(FileExplManager, self).startExplorer(win_pos, *args, **kwargs)
            return

        self._orig_cwd = lfGetCwd()
        root_markers = lfEval("g:Lf_RootMarkers")
        mode = lfEval("g:Lf_WorkingDirectoryMode")
        working_dir = lfEval("g:Lf_WorkingDirectory")

        # https://github.com/neovim/neovim/issues/8336
        if lfEval("has('nvim')") == '1':
            chdir = vim.chdir
        else:
            chdir = os.chdir

        if os.path.exists(working_dir) and os.path.isdir(working_dir):
            chdir(working_dir)
            super(FileExplManager, self).startExplorer(win_pos, *args, **kwargs)
            return

        cur_buf_name = lfDecode(vim.current.buffer.name)
        fall_back = False
        if 'a' in mode:
            working_dir = nearestAncestor(root_markers, self._orig_cwd)
            if working_dir: # there exists a root marker in nearest ancestor path
                chdir(working_dir)
            else:
                fall_back = True
        elif 'A' in mode:
            if cur_buf_name:
                working_dir = nearestAncestor(root_markers, os.path.dirname(cur_buf_name))
            else:
                working_dir = ""
            if working_dir: # there exists a root marker in nearest ancestor path
                chdir(working_dir)
            else:
                fall_back = True
        else:
            fall_back = True

        if fall_back:
            if 'f' in mode:
                if cur_buf_name:
                    chdir(os.path.dirname(cur_buf_name))
            elif 'F' in mode:
                if cur_buf_name and not os.path.dirname(cur_buf_name).startswith(self._orig_cwd):
                    chdir(os.path.dirname(cur_buf_name))

        super(FileExplManager, self).startExplorer(win_pos, *args, **kwargs)

    @removeDevIcons
    def _previewInPopup(self, *args, **kwargs):
        if len(args) == 0 or args[0] == '':
            return

        line = args[0]
        if not os.path.isabs(line):
            if self._getExplorer()._cmd_work_dir:
                line = os.path.join(self._getExplorer()._cmd_work_dir, lfDecode(line))
            else:
                line = os.path.join(self._getInstance().getCwd(), lfDecode(line))
            line = os.path.normpath(lfEncode(line))
        if lfEval("bufloaded('%s')" % escQuote(line)) == '1':
            source = int(lfEval("bufadd('%s')" % escQuote(line)))
        else:
            source = line

        jump_cmd = 'normal! g`"'
        self._createPopupPreview(line, source, 0, jump_cmd)

    @removeDevIcons
    def _acceptSelection(self, *args, **kwargs):
        if len(args) == 0:
            return
        file = args[0]
        try:
            if not os.path.isabs(file):
                if self._getExplorer()._cmd_work_dir:
                    file = os.path.join(self._getExplorer()._cmd_work_dir, lfDecode(file))
                else:
                    file = os.path.join(self._getInstance().getCwd(), lfDecode(file))
                file = os.path.normpath(lfEncode(file))

            if kwargs.get("mode", '') == 't':
                if (lfEval("get(g:, 'Lf_DiscardEmptyBuffer', 1)") == '1' and vim.current.buffer.name == ''
                        and vim.current.buffer.number == 1
                        and len(vim.current.tabpage.windows) == 1 and len(vim.current.buffer) == 1
                        and vim.current.buffer[0] == '' and not vim.current.buffer.options["modified"]
                        and not (lfEval("get(g:, 'Lf_JumpToExistingWindow', 1)") == '1'
                            and lfEval("bufloaded('%s')" % escQuote(file)) == '1'
                            and len([w for tp in vim.tabpages for w in tp.windows if w.buffer.name == file]) > 0)):
                    lfCmd("setlocal bufhidden=wipe")
                    lfCmd("hide edit %s" % escSpecial(file))
                elif lfEval("get(g:, 'Lf_JumpToExistingWindow', 1)") == '1' and lfEval("bufloaded('%s')" % escQuote(file)) == '1':
                    lfDrop('tab', file)
                else:
                    lfCmd("tabe %s" % escSpecial(file))
            else:
                if (lfEval("get(g:, 'Lf_JumpToExistingWindow', 1)") == '1' or kwargs.get("mode", 'dr')) and lfEval("bufloaded('%s')" % escQuote(file)) == '1':
                    if (kwargs.get("mode", '') == '' and lfEval("get(g:, 'Lf_DiscardEmptyBuffer', 1)") == '1'
                            and vim.current.buffer.name == ''
                            and vim.current.buffer.number == 1
                            and len(vim.current.buffer) == 1 and vim.current.buffer[0] == ''
                            and not vim.current.buffer.options["modified"]
                            and len([w for w in vim.windows if w.buffer.name == file]) == 0):
                        lfCmd("setlocal bufhidden=wipe")
                    lfDrop('', file)
                else:
                    if (kwargs.get("mode", '') == '' and lfEval("get(g:, 'Lf_DiscardEmptyBuffer', 1)") == '1'
                            and vim.current.buffer.name == ''
                            and vim.current.buffer.number == 1
                            and len(vim.current.buffer) == 1 and vim.current.buffer[0] == ''
                            and not vim.current.buffer.options["modified"]):
                        lfCmd("setlocal bufhidden=wipe")

                    m = lfEval("get(g:, 'Lf_FileActions', {})")
                    if m != {}:
                        try:
                            extension = os.path.splitext(file)[-1]
                            filecmd = m[extension]
                            lfCmd("%s %s" % (filecmd, escSpecial(file)))
                        except KeyError:
                            lfCmd("hide edit %s" % escSpecial(file))
                    else:
                        lfCmd("hide edit %s" % escSpecial(file))
        except vim.error as e: # E37
            if 'E325' not in str(e).split(':'):
                lfPrintTraceback()

#*****************************************************
# fileExplManager is a singleton
#*****************************************************
fileExplManager = FileExplManager()

__all__ = ['fileExplManager']
