-- Set <space> as the leader key (Must happen before plugins are loaded)
vim.g.mapleader = ' '
vim.g.maplocalleader = ' '

-- Load options
require 'options'

-- Load plugin manager
require 'lazy-config'

-- Load keymaps after plugins
vim.api.nvim_create_autocmd('User', {
  pattern = 'VeryLazy',
  callback = function()
    require 'keymaps'
  end,
})

-- vim: ts=2 sts=2 sw=2 et
