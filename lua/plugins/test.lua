return {
  'nvim-neotest/neotest',
  dependencies = {
    'nvim-lua/plenary.nvim',
    'nvim-treesitter/nvim-treesitter',
    'antoinemadec/FixCursorHold.nvim',
    'nvim-neotest/nvim-nio',
    'nvim-neotest/neotest-python',
  },
  keys = {
    { '<leader>t', desc = 'Toggle test interface and focus' },
    { '<leader>rt', desc = 'Run nearest test' },
    { '<leader>rf', desc = 'Run current file' },
    { '<leader>ro', desc = 'Open test output' },
  },
  config = function()
    -- Import the Python project root utility
    local python_project_root = require 'utils.python_root'

    -- Function to calculate sidebar width based on terminal width
    local function calculate_sidebar_width()
      local width = vim.o.columns

      if width > 120 then
        return math.floor(width * 0.35) -- 35% for large screens
      elseif width > 80 then
        return math.floor(width * 0.35) -- 35% for medium screens
      else
        return math.floor(width * 0.3) -- 30% for small screens
      end
    end

    local sidebar_width = calculate_sidebar_width()

    -- Setup Neotest with the calculated sidebar width
    require('neotest').setup {
      summary = {
        enabled = true,
        count = true,
        animated = true,
        follow = true,
        expand_errors = true,
        open = 'botright vsplit | vertical resize ' .. sidebar_width,
      },
      icons = {
        passed = '✔', -- Checkmark for passed
        running = '⟳', -- Circular arrow for running
        failed = '✖', -- Cross for failed
        skipped = '➖', -- Minus sign for skipped
        unknown = '?', -- Question mark for unknown
        non_collapsible = '─', -- Horizontal line
        collapsed = '─', -- Collapsed state
        expanded = '╮', -- Expanded state
        child_prefix = '├', -- Prefix for children nodes
        final_child_prefix = '╰', -- Prefix for the final child node
        child_indent = '│', -- Indentation for children nodes
        final_child_indent = ' ', -- Final indentation
      },
      adapters = {
        require 'neotest-python' {
          dap = { justMyCode = false },
          args = { '--log-level', 'DEBUG' },
          runner = 'pytest',
          -- Dynamically use the Python interpreter from the project root
          python = python_project_root.get_python_path(),
          is_test_file = function(file_path)
            return file_path:match 'test_.*%.py$' or file_path:match '.*_test%.py$'
          end,
          pytest_discover_instances = true,
        },
      },
    }

    -- Function to get the summary window ID
    local function get_summary_window()
      for _, win in ipairs(vim.api.nvim_tabpage_list_wins(0)) do
        local buf = vim.api.nvim_win_get_buf(win)
        if vim.api.nvim_buf_get_option(buf, 'filetype') == 'neotest-summary' then
          return win
        end
      end
      return nil
    end

    -- Function to toggle summary and focus the summary window
    local function toggle_summary_and_focus()
      require('neotest').summary.toggle()
      -- Use a short delay to allow the window to open
      vim.defer_fn(function()
        local summary_win = get_summary_window()
        if summary_win then
          vim.api.nvim_set_current_win(summary_win)
          -- Set buffer-local keymaps for 'q' and 't' to close the window
          local buf = vim.api.nvim_win_get_buf(summary_win)
          vim.keymap.set('n', 'q', function()
            vim.api.nvim_win_close(summary_win, true)
          end, { noremap = true, silent = true, buffer = buf, desc = 'Close test summary' })
          vim.keymap.set('n', 't', function()
            vim.api.nvim_win_close(summary_win, true)
          end, { noremap = true, silent = true, buffer = buf, desc = 'Close test summary' })
        end
      end, 50) -- 50ms delay
    end

    -- Keybindings
    vim.keymap.set('n', '<leader>t', toggle_summary_and_focus, { desc = 'Toggle test interface and focus' })

    vim.keymap.set('n', '<leader>rt', function()
      require('neotest').run.run()
    end, { desc = 'Run nearest test' })
    vim.keymap.set('n', '<leader>rf', function()
      require('neotest').run.run(vim.fn.expand '%')
    end, { desc = 'Run current file' })
    vim.keymap.set('n', '<leader>ro', function()
      require('neotest').output.open()
    end, { desc = 'Open test output' })
  end,
}
