" ============================================================================
" File:        lfGitRepo.vim
" Description:
" Author:      Yggdroot <archofortune@gmail.com>
" Website:     https://github.com/Yggdroot
" Note:
" License:     Apache License, Version 2.0
" ============================================================================

function! lfGitRepo#record()
    if leaderf#versionCheck() == 0
        return
    endif
    if has('python3')
        python3 import leaderf.gitRepo; leaderf.gitRepo.gitRepo.record(vim.eval("getcwd()"))
    elseif has('python')
        python import leaderf.gitRepo; leaderf.gitRepo.gitRepo.record(vim.eval("getcwd()"))
    endif
endfunction
