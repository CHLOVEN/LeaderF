" ============================================================================
" File:        lfMru.vim
" Description:
" Author:      Yggdroot <archofortune@gmail.com>
" Website:     https://github.com/Yggdroot
" Note:
" License:     Apache License, Version 2.0
" ============================================================================

let g:Lf_CacheDirectory = substitute(g:Lf_CacheDirectory, '[\/]$', '', '')

if !isdirectory(g:Lf_CacheDirectory)
    call mkdir(g:Lf_CacheDirectory, "p")
endif

if !isdirectory(g:Lf_CacheDirectory . '/LeaderF')
    call mkdir(g:Lf_CacheDirectory . '/LeaderF', "p")
endif

let g:Lf_MruCacheFileName = g:Lf_CacheDirectory . '/LeaderF/frecency'

if !filereadable(g:Lf_MruCacheFileName)
    call writefile([], g:Lf_MruCacheFileName)
endif

function! lfMru#CacheFileName()
    return g:Lf_MruCacheFileName
endfunction

function! lfMru#record(name)
    if a:name == '' || !filereadable(a:name) || strpart(a:name, 0, 2) == '\\'
        return
    endif

    let file_list = readfile(g:Lf_MruCacheFileName)
    let found = 0
    let i = 0
    for item in file_list
        let t = split(item, ' ')
        if (len(t) > 2) && (t[2] ==# a:name)
            let found = 1
            let t[1] += 1
            let file_list[i] = printf("%s %s %s", localtime(), t[1], t[2])
            break
        endif
        let i += 1
    endfor

    if found == 0
        call add(file_list, printf("%s 1 %s", localtime(), a:name))
    endif

    call writefile(file_list, g:Lf_MruCacheFileName)
endfunction

function! lfMru#recordBuffer(bufNum)
  call add(g:Lf_MruBufnrs, a:bufNum)
endfunction

function! lfMru#updatePriority(name)
  if a:name == '' || !filereadable(a:name) || strpart(a:name, 0, 2) == '\\'
    return
  endif

  let l:priority_cache = g:Lf_CacheDirectory . '/LeaderF/python' . (has('python3') ? '3' : '2') . '/mru/priority'
  let l:priority_dir = fnamemodify(l:priority_cache, ':h')

  if !isdirectory(l:priority_dir)
    call mkdir(l:priority_dir, 'p')
  endif

  let l:file_path = a:name
  if has('win32') || has('win64')
    let l:file_path = substitute(l:file_path, '\\', '/', 'g')
  endif

  let l:priority_map = {}
  if filereadable(l:priority_cache)
    for line in readfile(l:priority_cache)
      let parts = split(line, ' ')
      if len(parts) >= 2
        let l:priority_map[parts[0]] = parts[1]
      endif
    endfor
  endif

  let l:priority_map[l:file_path] = localtime()

  let l:lines = []
  for [path, timestamp] in items(l:priority_map)
    call add(l:lines, path . ' ' . timestamp)
  endfor

  call writefile(l:lines, l:priority_cache)
endfunction
