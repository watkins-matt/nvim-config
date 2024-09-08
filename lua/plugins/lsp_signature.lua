return {
  'ray-x/lsp_signature.nvim',
  event = 'LspAttach',
  opts = {
    bind = true,
    handler_opts = {
      border = 'rounded',
    },
    floating_window_off_y = -8,
    floating_window_off_x = -5,
  },
  config = function(_, opts)
    require('lsp_signature').setup(opts)
  end,
}
