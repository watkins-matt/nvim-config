return {
  'jay-babu/mason-null-ls.nvim',
  event = { 'BufReadPre', 'BufNewFile' },
  dependencies = {
    'williamboman/mason.nvim',
    'nvimtools/none-ls.nvim',
  },
  config = function()
    local notify = function(msg, level)
      vim.notify(msg, level, { title = 'Mason Null LS' })
    end
    require('mason').setup()

    local ensure_installed = { 'jq', 'python-lsp-server' }

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

    local function is_pylsp_plugin_installed(plugin_name, package_name)
      local pylsp_install_path = vim.fn.stdpath 'data' .. '/mason/packages/python-lsp-server'
      local plugin_path = pylsp_install_path .. '/venv/lib/python*/site-packages/' .. (package_name or plugin_name):gsub('-', '_')
      return vim.fn.glob(plugin_path) ~= ''
    end

    local function install_pylsp_plugin(plugin_name)
      local mason_registry = require 'mason-registry'
      local pylsp_pkg = mason_registry.get_package 'python-lsp-server'
      local install_dir = pylsp_pkg:get_install_path()

      notify(string.format('Installing %s for pylsp', plugin_name), vim.log.levels.INFO)

      local cmd = string.format('%s/venv/bin/pip install --disable-pip-version-check -U %s', install_dir, plugin_name)
      local output = vim.fn.system(cmd)

      if vim.v.shell_error ~= 0 then
        notify(string.format('Failed to install %s: %s', plugin_name, output), vim.log.levels.ERROR)
      else
        notify(string.format('Successfully installed %s', plugin_name), vim.log.levels.INFO)
      end
    end

    local function ensure_pylsp_plugins()
      local needed_plugins = {
        { 'python-lsp-black', 'pylsp_black' },
        { 'pylsp-mypy', 'pylsp_mypy' },
      }
      local installed_count = 0

      for _, plugin_info in ipairs(needed_plugins) do
        if not table.unpack then
          ---@diagnostic disable-next-line: deprecated
          table.unpack = unpack
        end
        local install_name, package_name = table.unpack(plugin_info)
        if not is_pylsp_plugin_installed(install_name, package_name) then
          install_pylsp_plugin(install_name)
          installed_count = installed_count + 1
        end
      end

      if installed_count > 0 then
        notify(string.format('Installed %d pylsp plugin(s)', installed_count), vim.log.levels.INFO)
      end
    end

    vim.api.nvim_create_autocmd('User', {
      pattern = 'MasonToolsUpdateCompleted',
      callback = function()
        vim.defer_fn(function()
          ensure_pylsp_plugins()
        end, 1000) -- 1000ms delay
      end,
    })
  end,
}
