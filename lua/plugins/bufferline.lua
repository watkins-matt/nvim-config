return {
  'akinsho/bufferline.nvim',
  version = '*',
  lazy = false,
  dependencies = { 'nvim-tree/nvim-web-devicons' },
  config = function()
    local function get_gutter_width()
      local win = vim.fn.getwininfo(vim.fn.win_getid())[1]
      return win and win.textoff or 4
    end

    local function is_nvimtree_open()
      for _, win in ipairs(vim.api.nvim_list_wins()) do
        local buf = vim.api.nvim_win_get_buf(win)
        if vim.bo[buf].filetype == 'NvimTree' then
          return true
        end
      end
      return false
    end

    -- Custom highlights
    vim.api.nvim_set_hl(0, 'BufferLineOffsetTitle', { fg = '#7aa2f7', bg = '#1a1b26', bold = true })
    vim.api.nvim_set_hl(0, 'BufferLineOffsetSeparator', { fg = '#0e0e14', bg = '#0e0e14' })

    require('bufferline').setup {
      options = {
        mode = 'buffers',
        numbers = 'none',
        indicator = { style = 'none' },
        buffer_close_icon = '',
        modified_icon = '●',
        close_icon = '',
        left_trunc_marker = '',
        right_trunc_marker = '',
        tab_size = 0,
        max_name_length = 30,
        truncate_names = false,
        padding = 1,
        diagnostics = false,
        show_buffer_icons = true,
        show_buffer_close_icons = false,
        show_close_icon = false,
        separator_style = 'slant',
        always_show_bufferline = true,
        offsets = {
          {
            filetype = 'NvimTree',
            text = ' File Explorer ',
            text_align = 'center',
            highlight = 'BufferLineOffsetTitle',
            separator = string.rep(' ', 7),
          },
        },
        custom_areas = {
          left = function()
            if is_nvimtree_open() then
              return {}
            end
            local width = get_gutter_width()
            return {{ text = string.rep(' ', width), bg = '#0e0e14' }}
          end,
        },
      },
      highlights = {
        offset_separator = {
          fg = '#0e0e14',
          bg = '#0e0e14',
        },
      },
    }

    local map = vim.keymap.set
    map('n', '<A-,>', '<Cmd>BufferLineCyclePrev<CR>')
    map('n', '<A-.>', '<Cmd>BufferLineCycleNext<CR>')
    map('n', '<A-c>', '<Cmd>bdelete<CR>')
    map('n', '<leader>n', '<Cmd>tabnew<CR>', { desc = 'New buffer' })
    map('n', '<leader>bp', '<Cmd>BufferLinePick<CR>')
  end,
}
