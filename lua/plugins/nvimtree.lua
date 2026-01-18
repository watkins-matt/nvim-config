return {
  'nvim-tree/nvim-tree.lua',
  version = '*',
  lazy = false,
  dependencies = {
    'nvim-tree/nvim-web-devicons',
  },
  config = function()
    require('nvim-tree').setup {}

    -- Barbar integration
    local nvim_tree_events = require('nvim-tree.events')
    local barbar_api = require('barbar.api')

    local function get_tree_size()
      return require('nvim-tree.view').View.width
    end

    nvim_tree_events.subscribe('TreeOpen', function()
      barbar_api.set_offset(get_tree_size())
    end)

    nvim_tree_events.subscribe('Resize', function()
      barbar_api.set_offset(get_tree_size())
    end)

    nvim_tree_events.subscribe('TreeClose', function()
      barbar_api.set_offset(0)
    end)
  end,
}
