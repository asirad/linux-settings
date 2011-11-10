"SET NOCOMPATIBLE      " we're running Vim, not Vi!
set nocompatible
syntax on             " Enable syntax highlighting
filetype on           " Enable filetype detection
filetype plugin on    " Enable filetype-specific plugins
filetype indent on    " Enable filetype-specific indenting
imap <S-CR>    <CR><CR>end<Esc>-cc
set expandtab
set tabstop=2 shiftwidth=2 softtabstop=2
set autoindent
set autowrite
set ai "Auto indent
set si "Smart indet

nnoremap <F2> :set invpaste!<CR>
"nnoremap <F2> :set invpaste paste?<CR>
"set pastetoggle=<F2>
set showmode

"automate documentation
":Helptags to generate docs for all plugins
call pathogen#infect()
filetype plugin indent on

"macros
"to record macro press q and letter to assign to this macro
"nmap <F2> @q

"ruby
autocmd FileType ruby,eruby set omnifunc=rubycomplete#Complete
autocmd FileType ruby,eruby let g:rubycomplete_buffer_loading = 1
autocmd FileType ruby,eruby let g:rubycomplete_rails = 1
autocmd FileType ruby,eruby let g:rubycomplete_classes_in_global = 1

"improve autocomplete menu color
highlight Pmenu ctermbg=238 gui=bold

"spell
" F6 - enable en
" F7 - enable pl
" F8 - diable
map <F6> <Esc>:setlocal spell! spelllang=en<CR>
map <F7> <Esc>:setlocal spell! spelllang=pl<CR>
hi SpellBad term=reverse ctermfg=white ctermbg=darkred guifg=#ffffff guibg=#7f0000 gui=underline
hi SpellCap guifg=#ffffff guibg=#7f007f
hi SpellRare guifg=#ffffff guibg=#00007f gui=underline
hi SpellLocal term=reverse ctermfg=black ctermbg=darkgreen guifg=#ffffff guibg=#7f0000 gui=underline

"save view
"zf - group
"za - ungroup
"au BufWinLeave *.rb mkview
"au BufWinEnter *.rb silent loadview
au BufWritePost,BufLeave,WinLeave ?* mkview
au BufReadPre ?* silent loadview

""""""""""""""""""""""""""""""
" => Statusline
""""""""""""""""""""""""""""""
" Always hide the statusline
set laststatus=2
" Format the statusline
set statusline=\ %{HasPaste()}%F%m%r%h\ %w\ \ CWD:\ %r%{CurDir()}%h\ \ \Line:\ %l/%L:%c

function! CurDir()
    let curdir = substitute(getcwd(), '/Users/amir/', "~/", "g")
    return curdir
endfunction

function! HasPaste()
    if &paste
        return 'PASTE MODE  '
    else
        return ''
    endif
endfunction

"if $COLORTERM == 'gnome-terminal' 
"  set term=gnome-256color 
"    colorscheme railscasts 
"  else 
"    colorscheme default 
"endif 

set term=xterm-256color
colorscheme railscasts

function! SwitchTags()
  let curdir = CurDir()
  let path1 = curdir . "/tags"
  let path2 = curdir . "/ruby_tags"
  if &tags == path1
    let &tags = path2
    echo &tags
  else
    let &tags = path1
    echo &tags
  endif
endfunction

"my maps
inoremap <F3> <ESC>:tabnew 
inoremap <F4> <ESC>:w<CR>:!ruby -c %<CR>
nnoremap <F3> <ESC>:tabnew 
nnoremap <F4> <ESC>:w<CR>:!ruby -c %<CR>
nnoremap <F5> <ESC>:call SwitchTags()<CR>
inoremap <F5> <ESC>:call SwitchTags()<CR>
vnoremap <F5> <ESC>:call SwitchTags()<CR>
"map <C-n> <ESC>gt
"map <C-p> <ESC>gT

nnoremap <C-o> <ESC>:tabnew<CR>:FufFile<CR>
inoremap <C-o> <ESC>:tabnew<CR>:FufFile<CR>
vnoremap <C-o> <ESC>:tabnew<CR>:FufFile<CR>

nnoremap <C-Down> :m+<CR>==
nnoremap <C-Up> :m-2<CR>==
inoremap <C-Down> <Esc>:m+<CR>==gi
inoremap <C-Up> <Esc>:m-2<CR>==gi
vnoremap <C-Down> :m'>+<CR>gv=gv
vnoremap <C-Up> :m-2<CR>gv=gv

set tags=tags
"noremap .. :tn<CR>
"noremap ,, :tp<CR>
noremap <C-Right> :tn<CR>
noremap <C-Left> :tp<CR>
