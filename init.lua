-- Based on https://github.com/dam9000/kickstart-modular.nvim

-- disable netrw since we are using nvim-tree
vim.g.loaded_netrw = 1
vim.g.loaded_netrwPlugin = 1
vim.opt.termguicolors = true

-- Check if we are running on Termux, by doing command -v termux-setup-storage &> /dev/null
-- and set a global variable.
vim.g.is_termux = vim.fn.executable 'termux-setup-storage' == 1

-- Set <space> as the leader key
-- See `:help mapleader`
--  NOTE: Must happen before plugins are loaded (otherwise wrong leader will be used)
vim.g.mapleader = ' '
vim.g.maplocalleader = ' '

-- Set to true if you have a Nerd Font installed and selected in the terminal
vim.g.have_nerd_font = true

require 'options'
require 'keymaps'
require 'lazy-config'

-- vim: ts=2 sts=2 sw=2 et
