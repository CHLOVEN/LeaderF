" ============================================================================
" File:        Tab.vim
" Description:
" Author:      Yggdroot <archofortune@gmail.com>
" Website:     https://github.com/Yggdroot
" Note:
" License:     Apache License, Version 2.0
" ============================================================================

if leaderf#versionCheck() == 0  " this check is necessary
    finish
endif

exec g:Lf_py "from leaderf.tabExpl import *"

function! leaderf#Tab#managerId()
    exec g:Lf_py "from leaderf.tabExpl import tabExplManager"
    return g:Lf_PyEval("id(tabExplManager)")
endfunction

function! leaderf#Tab#Maps()
    nmapclear <buffer>
    nnoremap <buffer> <silent> <CR>          :exec g:Lf_py "tabExplManager.accept()"<CR>
    nnoremap <buffer> <silent> o             :exec g:Lf_py "tabExplManager.accept()"<CR>
    nnoremap <buffer> <silent> q             :exec g:Lf_py "tabExplManager.quit()"<CR>
    nnoremap <buffer> <silent> i             :exec g:Lf_py "tabExplManager.input()"<CR>
    nnoremap <buffer> <silent> <F1>          :exec g:Lf_py "tabExplManager.toggleHelp()"<CR>
endfunction
