" ============================================================================
" File:        leaderf_oswindow.vim
" Description:
" Author:      Yggdroot <archofortune@gmail.com>
" Website:     https://github.com/Yggdroot
" Note:
" License:     Apache License, Version 2.0
" ============================================================================

command! -bar -nargs=* LeaderfOsWindow Leaderf osWindow <args>

" In order to be listed by :LeaderfSelf
call g:LfRegisterSelf("LeaderfOsWindow", "navigate windows")

let s:extension = {
            \   "name": "osWindow",
            \   "help": "navigate windows",
            \   "manager_id": "leaderf#OsWindow#managerId",
            \   "arguments": [
            \       {"name": ["--class"], "nargs": 1, "help": "filter by window class"},
            \       {"name": ["--exe"], "nargs": 1, "help": "filter by executable name"},
            \   ]
            \ }
call g:LfRegisterPythonExtension("osWindow", s:extension)
