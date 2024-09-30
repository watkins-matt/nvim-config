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
  },
  config = function()
    local dap = require 'dap'
    local dapui = require 'dapui'

    -- Set nvim-notify as the default notification handler
    vim.notify = require 'notify'

    -- Function to calculate dap-ui sidebar width with min and max constraints
    local function calculate_sidebar_width()
      local width = vim.o.columns
      local min_width = 20
      local max_width = 40
      if width > 160 then
        return max_width
      elseif width > 120 then
        return math.floor(min_width + (width - 120) / 40 * (max_width - min_width))
      else
        return min_width
      end
    end

    local sidebar_width = calculate_sidebar_width()

    -- Function to determine dap-ui layouts based on terminal size
    local function get_dapui_layout()
      local width = vim.o.columns
      local height = vim.o.lines
      local sidebar_width = calculate_sidebar_width()

      if width > 120 then
        return {
          {
            elements = { 'scopes', 'breakpoints', 'stacks', 'watches' },
            size = sidebar_width, -- Width for left panel
            position = 'left',
          },
          {
            elements = { 'repl', 'console' },
            size = math.floor(height * 0.3), -- Height for bottom panel
            position = 'bottom',
          },
        }
      elseif width > 80 then
        return {
          {
            elements = { 'scopes', 'breakpoints', 'stacks' },
            size = sidebar_width, -- Width for left panel
            position = 'left',
          },
          -- REPL and console are hidden on medium screens
        }
      else
        return {
          {
            elements = { 'scopes', 'breakpoints' },
            size = sidebar_width, -- Width for left panel
            position = 'left',
          },
          -- REPL and console are hidden on small screens
        }
      end
    end

    -- Setup Mason for automatic debug adapter installation
    require('mason-nvim-dap').setup {
      automatic_installation = true,
      ensure_installed = {
        'python',
        'dart',
      },
    }

    -- Setup dap-ui with dynamic layout
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
      layouts = get_dapui_layout(), -- Apply dynamic layout
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

    -- Function to get the dap-ui window ID by filetype
    local function get_dapui_window(filetype)
      for _, win in ipairs(vim.api.nvim_tabpage_list_wins(0)) do
        local buf = vim.api.nvim_win_get_buf(win)
        if vim.api.nvim_buf_get_option(buf, 'filetype') == filetype then
          return win
        end
      end
      return nil
    end

    -- Function to toggle specific dap-ui elements and focus
    local function toggle_dapui_element_and_focus(element, filetype)
      dapui.toggle { elements = { element } }
      -- Delay to allow window to open
      vim.defer_fn(function()
        local win = get_dapui_window(filetype)
        if win then
          vim.api.nvim_set_current_win(win)
        end
      end, 50)
    end

    -- Keybindings for toggling repl and console individually
    vim.keymap.set('n', '<leader>dq', function()
      toggle_dapui_element_and_focus('repl', 'dap-repl')
    end, { desc = 'Debug: Toggle REPL and focus' })

    vim.keymap.set('n', '<leader>dw', function()
      toggle_dapui_element_and_focus('console', 'dap-console')
    end, { desc = 'Debug: Toggle Console and focus' })

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

    -- Import the Python project root utility
    local python_project_root = require 'utils.python_root'

    -- Check if the Python interpreter exists, otherwise print a warning
    if vim.fn.executable(python_project_root.get_python_path()) == 1 then
      require('dap-python').setup(python_project_root.get_python_path())
    else
      vim.notify('Warning: Python executable not found! Python debugging won’t work.', vim.log.levels.WARN)
    end

    -- Additional configurations for Dart can be added here
  end,
}
