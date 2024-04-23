return {
  'jay-babu/mason-null-ls.nvim',
  event = { 'BufReadPre', 'BufNewFile' },
  dependencies = {
    'williamboman/mason.nvim',
    'nvimtools/none-ls.nvim',
  },
  config = function()
    require('mason').setup()

    local ensure_installed = { 'jq' }

    -- Ensure that stylua is installed on non-termux systems
    if not vim.g.is_termux then
      vim.list_extend(ensure_installed, { 'stylua', 'black', 'debugpy' })
    end

    require('mason-null-ls').setup {
      ensure_installed = ensure_installed,
    }
  end,
}
