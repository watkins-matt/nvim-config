return {
  'nvim-lualine/lualine.nvim',
  dependencies = { 'nvim-tree/nvim-web-devicons', lazy = false },
  config = function()
    require('lualine').setup {
      options = {
        icons_enabled = true,
        theme = 'palenight',
        section_separators = { '', '' },
        component_separators = { '', '' },
        ignore_focus = {
          'dapui_breakpoints',
          'dapui_scopes',
          'dapui_stacks',
          'dapui_watches',
          'dapui_console',
          'dap-repl',
          'neotest-summary',
          'Outline',
        },
      },
      sections = {
        lualine_a = { 'mode' },
        lualine_b = { 'branch', 'diff', 'diagnostics' },
        lualine_c = { 'hostname', 'filename' },
        lualine_x = { 'encoding', 'fileformat', 'filetype' },
        lualine_y = { 'progress' },
        lualine_z = { 'location' },
      },
      inactive_sections = {
        lualine_a = {},
        lualine_b = {},
        lualine_c = { 'filename' },
        lualine_x = { 'location' },
        lualine_y = {},
        lualine_z = {},
      },
      tabline = {},
      extensions = {},
    }
  end,
}
