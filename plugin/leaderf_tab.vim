" ============================================================================
" File:        leaderf_tab.vim
" Description:
" Author:      Yggdroot <archofortune@gmail.com>
" Website:     https://github.com/Yggdroot
" Note:
" License:     Apache License, Version 2.0
" ============================================================================

command! -bar -nargs=0 LeaderfTab Leaderf tab

" In order to be listed by :LeaderfSelf
call g:LfRegisterSelf("LeaderfTab", "navigate tab pages")

let s:extension = {
            \   "name": "tab",
            \   "help": "navigate tab pages",
            \   "manager_id": "leaderf#Tab#managerId",
            \   "arguments": []
            \ }
call g:LfRegisterPythonExtension("tab", s:extension)
