return {
  'mfussenegger/nvim-dap',
  dependencies = {
    -- UI for nvim-dap
    'rcarriga/nvim-dap-ui',
    'rcarriga/nvim-notify',
    -- Required for nvim-dap-ui
    'nvim-neotest/nvim-nio',

    -- Installs the debug adapters for you
    'williamboman/mason.nvim',
    'jay-babu/mason-nvim-dap.nvim',

    -- Python debugging
    'mfussenegger/nvim-dap-python',

    -- Dart debugging
    'mfussenegger/nvim-dap',
  },
  config = function()
    local dap = require 'dap'
    local dapui = require 'dapui'

    -- Set nvim-notify as the default notification handler
    vim.notify = require 'notify'

    -- Mason setup for automatic debug adapter installation
    require('mason-nvim-dap').setup {
      automatic_installation = true,
      ensure_installed = {
        'python',
        'dart',
      },
    }

    -- Custom dap-ui setup, only overriding specific fields
    dapui.setup {
      icons = { expanded = '▾', collapsed = '▸', current_frame = '*' }, -- Custom icons
      controls = { -- Custom control icons
        element = 'repl',
        enabled = true,
        icons = {
          pause = '⏸',
          play = '▶',
          step_into = '⏎',
          step_over = '⏭',
          step_out = '⏮',
          step_back = 'b',
          run_last = '▶▶',
          terminate = '⏹',
          disconnect = '⏏',
        },
      },
      floating = {
        border = 'single',
        mappings = {
          close = { 'q', '<Esc>' },
        },
      },
    }

    -- Automatically open and close dap-ui
    dap.listeners.after.event_initialized['dapui_config'] = function()
      dapui.open()
    end
    dap.listeners.before.event_terminated['dapui_config'] = function()
      dapui.close()
    end
    dap.listeners.before.event_exited['dapui_config'] = function()
      dapui.close()
    end

    -- Keybindings for debugging, all under <leader>d
    vim.keymap.set('n', '<leader>dc', dap.continue, { desc = 'Debug: Start/Continue' })
    vim.keymap.set('n', '<leader>di', dap.step_into, { desc = 'Debug: Step Into' })
    vim.keymap.set('n', '<leader>do', dap.step_over, { desc = 'Debug: Step Over' })
    vim.keymap.set('n', '<leader>du', dap.step_out, { desc = 'Debug: Step Out' })
    vim.keymap.set('n', '<leader>db', dap.toggle_breakpoint, { desc = 'Debug: Toggle Breakpoint' })
    vim.keymap.set('n', '<leader>dB', function()
      dap.set_breakpoint(vim.fn.input 'Breakpoint condition: ')
    end, { desc = 'Debug: Set Conditional Breakpoint' })
    vim.keymap.set('n', '<leader>dr', dap.repl.toggle, { desc = 'Debug: Toggle REPL' })
    vim.keymap.set('n', '<leader>dl', dap.run_last, { desc = 'Debug: Run Last' })
    vim.keymap.set('n', '<leader>dx', dap.terminate, { desc = 'Debug: Terminate' })
    vim.keymap.set('n', '<leader>dt', dapui.toggle, { desc = 'Debug: Toggle DAP UI' })

    -- Custom notification to avoid full-screen notifications
    vim.notify = require 'notify' -- Use nvim-notify instead of default vim.notify

    -- Import the Python project root utility
    local python_project_root = require 'utils.python_root'

    -- Check if the Python interpreter exists, otherwise print a warning
    if vim.fn.executable(python_project_root.get_python_path()) == 1 then
      require('dap-python').setup(python_project_root.get_python_path())
    else
      vim.notify('Warning: Python executable not found! Python debugging won’t work.', vim.log.levels.WARN)
    end

    -- Check if Dart is installed before setting up
    -- if vim.fn.executable 'dart' == 1 then
    --   require('dap-dart').setup()
    -- else
    --   vim.notify('Warning: Dart executable not found! Dart debugging won’t work.', vim.log.levels.WARN)
    -- end
  end,
}
