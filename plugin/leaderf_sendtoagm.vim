" ============================================================================
" File:        leaderf_sendtoagm.vim
" Description: Send visual selection to Antigravity window
" Author:      Custom Extension
" License:     Apache License, Version 2.0
" ============================================================================

command! -bar -nargs=* -range LeaderfSendToAGM call s:SendToAGM(<line1>, <line2>, <q-args>)

function! s:SendToAGM(line1, line2, args)
  let l:lines = getline(a:line1, a:line2)
  let l:content = join(l:lines, "\n")
  let l:escaped = substitute(l:content, "'", "''", "g")
  let l:escaped = substitute(l:escaped, "\\", "\\\\\\\\", "g")

  exec g:Lf_py "from leaderf.sendToAGMExpl import sendToAGMExplManager"
  exec g:Lf_py "sendToAGMExplManager.setSelectionContent('''".l:escaped."''')"

  execute "Leaderf sendToAGM " . a:args
endfunction

call g:LfRegisterSelf("LeaderfSendToAGM", "send selection to AGM window")

let s:extension = {
      \   "name": "sendToAGM",
      \   "help": "send selection to AGM window",
      \   "manager_id": "leaderf#SendToAGM#managerId",
      \   "arguments": [
      \       {"name": ["--class"], "nargs": 1, "help": "filter by window class"},
      \       {"name": ["--exe"], "nargs": 1, "help": "filter by executable name"},
      \   ]
      \ }
call g:LfRegisterPythonExtension("sendToAGM", s:extension)
