return {
  'nvim-tree/nvim-tree.lua',
  version = '*',
  lazy = false,
  dependencies = {
    'nvim-tree/nvim-web-devicons',
  },
  config = function()
    require('nvim-tree').setup {
      view = {
        width = 30,
        side = 'left',
        signcolumn = 'no',
      },
      renderer = {
        group_empty = true,
        highlight_git = true,
        icons = {
          show = {
            git = true,
            folder = true,
            file = true,
            folder_arrow = true,
          },
        },
      },
      filters = {
        dotfiles = false,
      },
      git = {
        enable = true,
        ignore = false,
      },
      actions = {
        open_file = {
          quit_on_open = false,
        },
      },
    }

    -- Match NvimTree separator to background
    vim.api.nvim_set_hl(0, 'NvimTreeWinSeparator', { fg = '#1a1b26', bg = '#1a1b26' })

    -- Clean up stale NvimTree buffers on toggle
    local api = require('nvim-tree.api')
    local original_toggle = api.tree.toggle
    api.tree.toggle = function(...)
      -- Delete any orphaned NvimTree buffers
      for _, buf in ipairs(vim.api.nvim_list_bufs()) do
        local name = vim.api.nvim_buf_get_name(buf)
        if name:match('NvimTree_') and not vim.api.nvim_buf_is_loaded(buf) then
          pcall(vim.api.nvim_buf_delete, buf, { force = true })
        end
      end
      return original_toggle(...)
    end
  end,
  keys = {
    { '<leader>e', '<Cmd>NvimTreeToggle<CR>', desc = 'Toggle file explorer' },
    { '<leader>E', '<Cmd>NvimTreeFindFile<CR>', desc = 'Find file in explorer' },
  },
}
