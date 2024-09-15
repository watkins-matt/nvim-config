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
    require('neotest').setup {
      adapters = {
        require 'neotest-python' {
          -- Extra arguments for nvim-dap configuration
          dap = { justMyCode = false },
          -- Command line arguments for runner
          args = { '--log-level', 'DEBUG' },
          -- Runner to use. Will use pytest if available by default.
          runner = 'pytest',
          -- Custom python path for the runner.
          python = '.venv/bin/python',
          -- Returns if a given file path is a test file.
          is_test_file = function(file_path)
            return file_path:match 'test_.*%.py$' or file_path:match '.*_test%.py$'
          end,
          -- Enable shelling out to `pytest` to discover test instances
          pytest_discover_instances = true,
        },
      },
    }

    -- Keybindings
    vim.keymap.set('n', '<leader>tr', function()
      require('neotest').run.run()
    end, { desc = 'Run nearest test' })
    vim.keymap.set('n', '<leader>tf', function()
      require('neotest').run.run(vim.fn.expand '%')
    end, { desc = 'Run current file' })
    vim.keymap.set('n', '<leader>ts', function()
      require('neotest').summary.toggle()
    end, { desc = 'Toggle test summary' })
    vim.keymap.set('n', '<leader>to', function()
      require('neotest').output.open()
    end, { desc = 'Open test output' })
  end,
}
