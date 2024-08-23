-- Set <space> as the leader key (Must happen before plugins are loaded)
vim.g.mapleader = ' '
vim.g.maplocalleader = ' '

-- Load options
require 'options'

-- Load keymaps
require 'keymaps'

-- Load plugin manager
require 'lazy-config'

-- vim: ts=2 sts=2 sw=2 et
