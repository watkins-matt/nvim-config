return {
  {
    'mfussenegger/nvim-lint',
    dependencies = {
      'williamboman/mason.nvim',
      'jay-babu/mason-null-ls.nvim',
      'nvimtools/none-ls.nvim',
    },
    event = { 'BufReadPre', 'BufNewFile' },
    config = function()
      -- Define ensure_installed list with Termux-specific skip
      local ensure_installed = { 'jq', 'ruff', 'prettier', 'eslint' }

      if not vim.g.is_termux then
        table.insert(ensure_installed, 'stylua')
        table.insert(ensure_installed, 'black')
        table.insert(ensure_installed, 'debugpy')
      end

      -- Setup mason-null-ls
      require('mason-null-ls').setup {
        ensure_installed = ensure_installed,
        automatic_setup = true,
      }

      -- Setup nvim-lint
      local lint = require 'lint'
      lint.linters_by_ft = {
        markdown = { 'markdownlint' },
        python = { 'ruff' },
      }

      -- Autocommand for linting on specific events
      local lint_augroup = vim.api.nvim_create_augroup('lint', { clear = true })
      vim.api.nvim_create_autocmd({ 'BufEnter', 'BufWritePost', 'InsertLeave' }, {
        group = lint_augroup,
        callback = function()
          lint.try_lint()
        end,
      })
    end,
  },
}
