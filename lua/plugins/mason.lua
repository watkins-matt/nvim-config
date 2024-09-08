return {
  'jay-babu/mason-null-ls.nvim',
  event = { 'BufReadPre', 'BufNewFile' },
  dependencies = {
    'williamboman/mason.nvim',
    'nvimtools/none-ls.nvim',
  },
  config = function()
    require('mason').setup()

    local ensure_installed = { 'jq', 'jedi_language_server' }

    -- Ensure that stylua is installed on non-termux systems
    if not vim.g.is_termux then
      table.insert(ensure_installed, 'stylua')
      table.insert(ensure_installed, 'black')
      table.insert(ensure_installed, 'debugpy')
      table.insert(ensure_installed, 'ruff')
    end

    require('mason-null-ls').setup {
      ensure_installed = ensure_installed,
    }
  end,
}
