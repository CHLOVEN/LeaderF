" ============================================================================
" File:        GitRepo.vim
" Description:
" Author:      Yggdroot <archofortune@gmail.com>
" Website:     https://github.com/Yggdroot
" Note:
" License:     Apache License, Version 2.0
" ============================================================================

if leaderf#versionCheck() == 0  " this check is necessary
    finish
endif

exec g:Lf_py "from leaderf.gitRepoExpl import *"

function! leaderf#GitRepo#Maps()
    nmapclear <buffer>
    nnoremap <buffer> <silent> <CR>          :exec g:Lf_py "gitRepoExplManager.accept()"<CR>
    nnoremap <buffer> <silent> o             :exec g:Lf_py "gitRepoExplManager.accept()"<CR>
    nnoremap <buffer> <silent> <2-LeftMouse> :exec g:Lf_py "gitRepoExplManager.accept()"<CR>
    nnoremap <buffer> <silent> x             :exec g:Lf_py "gitRepoExplManager.accept('h')"<CR>
    nnoremap <buffer> <silent> v             :exec g:Lf_py "gitRepoExplManager.accept('v')"<CR>
    nnoremap <buffer> <silent> t             :exec g:Lf_py "gitRepoExplManager.accept('t')"<CR>
    nnoremap <buffer> <silent> q             :exec g:Lf_py "gitRepoExplManager.quit()"<CR>
    " nnoremap <buffer> <silent> <Esc>         :exec g:Lf_py "gitRepoExplManager.quit()"<CR>
    nnoremap <buffer> <silent> i             :exec g:Lf_py "gitRepoExplManager.input()"<CR>
    nnoremap <buffer> <silent> <Tab>         :exec g:Lf_py "gitRepoExplManager.input()"<CR>
    nnoremap <buffer> <silent> <F1>          :exec g:Lf_py "gitRepoExplManager.toggleHelp()"<CR>
    nnoremap <buffer> <silent> p             :exec g:Lf_py "gitRepoExplManager._previewResult(True)"<CR>
    nnoremap <buffer> <silent> j             :<C-U>exec g:Lf_py "gitRepoExplManager.moveAndPreview('j')"<CR>
    nnoremap <buffer> <silent> k             :<C-U>exec g:Lf_py "gitRepoExplManager.moveAndPreview('k')"<CR>
    nnoremap <buffer> <silent> <Up>          :<C-U>exec g:Lf_py "gitRepoExplManager.moveAndPreview('Up')"<CR>
    nnoremap <buffer> <silent> <Down>        :<C-U>exec g:Lf_py "gitRepoExplManager.moveAndPreview('Down')"<CR>
    nnoremap <buffer> <silent> <PageUp>      :<C-U>exec g:Lf_py "gitRepoExplManager.moveAndPreview('PageUp')"<CR>
    nnoremap <buffer> <silent> <PageDown>    :<C-U>exec g:Lf_py "gitRepoExplManager.moveAndPreview('PageDown')"<CR>
    nnoremap <buffer> <silent> <C-Up>        :exec g:Lf_py "gitRepoExplManager._toUpInPopup()"<CR>
    nnoremap <buffer> <silent> <C-Down>      :exec g:Lf_py "gitRepoExplManager._toDownInPopup()"<CR>
    nnoremap <buffer> <silent> <Esc>         :exec g:Lf_py "gitRepoExplManager.closePreviewPopupOrQuit()"<CR>
    if has_key(g:Lf_NormalMap, "GitRepo")
        for i in g:Lf_NormalMap["GitRepo"]
            exec 'nnoremap <buffer> <silent> '.i[0].' '.i[1]
        endfor
    endif
endfunction

function! leaderf#GitRepo#NormalModeFilter(winid, key) abort
    let key = leaderf#RemapKey(g:Lf_PyEval("id(gitRepoExplManager)"), get(g:Lf_KeyMap, a:key, a:key))
    return leaderf#NormalModeFilter(g:Lf_PyEval("id(gitRepoExplManager)"), a:winid, a:key)
endfunction
