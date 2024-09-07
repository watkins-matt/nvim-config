return {
  'isobit/vim-caddyfile',
  ft = { 'caddyfile' },
  config = function()
    vim.filetype.add {
      filename = {
        ['Caddyfile'] = 'caddyfile',
      },
    }
  end,
}
