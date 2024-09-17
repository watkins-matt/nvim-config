return {
  'SuperBo/fugit2.nvim',
  opts = {
    width = 70,
    external_diffview = true,
  },
  dependencies = {
    'MunifTanjim/nui.nvim',
    'nvim-tree/nvim-web-devicons',
    'nvim-lua/plenary.nvim',
    {
      'chrisgrieser/nvim-tinygit',
      dependencies = { 'stevearc/dressing.nvim' },
    },
  },
  cmd = { 'Fugit2', 'Fugit2Blame', 'Fugit2Diff', 'Fugit2Graph' },
  keys = {
    { '<leader>F', mode = 'n', '<cmd>Fugit2<cr>' },
  },
}
