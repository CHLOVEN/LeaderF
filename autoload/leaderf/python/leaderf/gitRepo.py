#!/usr/bin/env python
# -*- coding: utf-8 -*-

import vim
import os
import sys
import os.path
from .utils import *

#*****************************************************
# GitRepo
#*****************************************************
class GitRepo(object):
    def __init__(self):
        self._cache_dir = os.path.join(lfEval("g:Lf_CacheDirectory"),
                                       'LeaderF',
                                       'python' + lfEval("g:Lf_PythonVersion"),
                                       'gitRepo')
        self._cache_file = os.path.join(self._cache_dir, 'repos')
        self._initCache()

    def _initCache(self):
        if not os.path.exists(self._cache_dir):
            os.makedirs(self._cache_dir)
        if not os.path.exists(self._cache_file):
            with lfOpen(self._cache_file, 'w', errors='ignore'):
                pass

    def getCacheFileName(self):
        return self._cache_file

    def normalize(self, name):
        if '~' in name:
            name = os.path.expanduser(name)
        name = os.path.abspath(name)
        if sys.platform[:3] == 'win':
            if name[:4] == '\\\\?\\' and os.path.isabs(name):
                if os.path.isabs(name[4:]) and name[5:6] == ':':
                    name = name[4:]
            if name[1:3] == ':\\':
                name = name[:1].upper() + name[1:]
        elif sys.platform == 'cygwin':
            if name.startswith('/cygdrive/'):
                name = name[:11].lower() + name[11:]
        return name

    def record(self, path):
        path = self.normalize(path)
        if not os.path.isdir(path):
            return

        # Check if it is a git repo
        if not os.path.exists(os.path.join(path, '.git')):
            return

        with lfOpen(self._cache_file, 'r+', errors='ignore', encoding='utf-8') as f:
            lines = [line.strip() for line in f.readlines()]
            if path in lines:
                return

            lines.append(path)
            f.seek(0)
            f.truncate(0)
            f.writelines([line + '\n' for line in lines])

    def getRepos(self):
        with lfOpen(self._cache_file, 'r', errors='ignore', encoding='utf-8') as f:
            return [line.strip() for line in f.readlines()]

#*****************************************************
# gitRepo is a singleton
#*****************************************************
gitRepo = GitRepo()

__all__ = ['gitRepo']
