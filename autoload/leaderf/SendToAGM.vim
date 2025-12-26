" ============================================================================
" File:        SendToAGM.vim
" Description: Send visual selection to Antigravity window
" Author:      Custom Extension
" License:     Apache License, Version 2.0
" ============================================================================

if leaderf#versionCheck() == 0
  finish
endif

exec g:Lf_py "from leaderf.sendToAGMExpl import *"

function! leaderf#SendToAGM#managerId()
  exec g:Lf_py "from leaderf.sendToAGMExpl import sendToAGMExplManager"
  return g:Lf_PyEval("id(sendToAGMExplManager)")
endfunction

function! leaderf#SendToAGM#Maps()
  nmapclear <buffer>
  nnoremap <buffer> <silent> <CR>          :exec g:Lf_py "sendToAGMExplManager.accept()"<CR>
  nnoremap <buffer> <silent> o             :exec g:Lf_py "sendToAGMExplManager.accept()"<CR>
  nnoremap <buffer> <silent> <2-LeftMouse> :exec g:Lf_py "sendToAGMExplManager.accept()"<CR>
  nnoremap <buffer> <silent> q             :exec g:Lf_py "sendToAGMExplManager.quit()"<CR>
  nnoremap <buffer> <silent> <Esc>         :exec g:Lf_py "sendToAGMExplManager.quit()"<CR>
  nnoremap <buffer> <silent> i             :exec g:Lf_py "sendToAGMExplManager.input()"<CR>
  nnoremap <buffer> <silent> <Tab>         :exec g:Lf_py "sendToAGMExplManager.input()"<CR>
  nnoremap <buffer> <silent> <F1>          :exec g:Lf_py "sendToAGMExplManager.toggleHelp()"<CR>
  if has_key(g:Lf_NormalMap, "SendToAGM")
    for i in g:Lf_NormalMap["SendToAGM"]
      exec 'nnoremap <buffer> <silent> '.i[0].' '.i[1]
    endfor
  endif
endfunction

function! leaderf#SendToAGM#setContent(content)
  exec g:Lf_py "sendToAGMExplManager.setSelectionContent('''".a:content."''')"
endfunction
