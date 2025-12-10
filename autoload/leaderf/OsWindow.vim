" ============================================================================
" File:        OsWindow.vim
" Description:
" Author:      Yggdroot <archofortune@gmail.com>
" Website:     https://github.com/Yggdroot
" Note:
" License:     Apache License, Version 2.0
" ============================================================================

if leaderf#versionCheck() == 0  " this check is necessary
    finish
endif

exec g:Lf_py "from leaderf.osWindowExpl import *"

function! leaderf#OsWindow#managerId()
    exec g:Lf_py "from leaderf.osWindowExpl import osWindowExplManager"
    return g:Lf_PyEval("id(osWindowExplManager)")
endfunction

function! leaderf#OsWindow#Maps()
    nmapclear <buffer>
    nnoremap <buffer> <silent> <CR>          :exec g:Lf_py "osWindowExplManager.accept()"<CR>
    nnoremap <buffer> <silent> o             :exec g:Lf_py "osWindowExplManager.accept()"<CR>
    nnoremap <buffer> <silent> <2-LeftMouse> :exec g:Lf_py "osWindowExplManager.accept()"<CR>
    nnoremap <buffer> <silent> q             :exec g:Lf_py "osWindowExplManager.quit()"<CR>
    nnoremap <buffer> <silent> <Esc>         :exec g:Lf_py "osWindowExplManager.quit()"<CR>
    nnoremap <buffer> <silent> i             :exec g:Lf_py "osWindowExplManager.input()"<CR>
    nnoremap <buffer> <silent> <Tab>         :exec g:Lf_py "osWindowExplManager.input()"<CR>
    nnoremap <buffer> <silent> <F1>          :exec g:Lf_py "osWindowExplManager.toggleHelp()"<CR>
    if has_key(g:Lf_NormalMap, "OsWindow")
        for i in g:Lf_NormalMap["OsWindow"]
            exec 'nnoremap <buffer> <silent> '.i[0].' '.i[1]
        endfor
    endif
endfunction
