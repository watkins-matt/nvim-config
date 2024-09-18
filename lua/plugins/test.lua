return {
  'nvim-neotest/neotest',
  dependencies = {
    'nvim-lua/plenary.nvim',
    'nvim-treesitter/nvim-treesitter',
    'antoinemadec/FixCursorHold.nvim',
    'nvim-neotest/nvim-nio',
    'nvim-neotest/neotest-python',
  },
  config = function()
    -- Import the Python project root utility
    local python_project_root = require 'utils.python_root'

    require('neotest').setup {
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
    }

    -- Keybindings
    vim.keymap.set('n', '<leader>tr', function()
      require('neotest').run.run()
    end, { desc = 'Run nearest test' })
    vim.keymap.set('n', '<leader>tf', function()
      require('neotest').run.run(vim.fn.expand '%')
    end, { desc = 'Run current file' })
    vim.keymap.set('n', '<leader>T', function()
      require('neotest').summary.toggle()
    end, { desc = 'Toggle test interface' })
    vim.keymap.set('n', '<leader>to', function()
      require('neotest').output.open()
    end, { desc = 'Open test output' })
  end,
}
