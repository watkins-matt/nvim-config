local M = {}

-- Function to check if a pylsp plugin is installed
function M.is_pylsp_plugin_installed(plugin_name, package_name)
  local pylsp_install_path = vim.fn.stdpath 'data' .. '/mason/packages/python-lsp-server'
  local plugin_path = pylsp_install_path .. '/venv/lib/python*/site-packages/' .. (package_name or plugin_name):gsub('-', '_')
  return vim.fn.glob(plugin_path) ~= ''
end

-- Function to install a pylsp plugin
function M.install_pylsp_plugin(plugin_name)
  local mason_registry = require 'mason-registry'
  local pylsp_pkg = mason_registry.get_package 'python-lsp-server'
  local install_dir = pylsp_pkg:get_install_path()

  vim.notify(string.format('Installing %s for pylsp', plugin_name), vim.log.levels.INFO)

  local cmd = string.format('%s/venv/bin/pip install --disable-pip-version-check -U %s', install_dir, plugin_name)
  local output = vim.fn.system(cmd)

  if vim.v.shell_error ~= 0 then
    vim.notify(string.format('Failed to install %s: %s', plugin_name, output), vim.log.levels.ERROR)
  else
    vim.notify(string.format('Successfully installed %s', plugin_name), vim.log.levels.INFO)
  end
end

-- Function to ensure all required pylsp plugins are installed
function M.ensure_pylsp_plugins()
  local needed_plugins = {
    { 'python-lsp-black', 'pylsp_black' },
    { 'pylsp-mypy', 'pylsp_mypy' },
  }
  local installed_count = 0

  for _, plugin_info in ipairs(needed_plugins) do
    local install_name, package_name = table.unpack(plugin_info)
    if not M.is_pylsp_plugin_installed(install_name, package_name) then
      M.install_pylsp_plugin(install_name)
      installed_count = installed_count + 1
    end
  end

  if installed_count > 0 then
    vim.notify(string.format('Installed %d pylsp plugin(s)', installed_count), vim.log.levels.INFO)
  end
end

return M
