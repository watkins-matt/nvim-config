-- Set <space> as the leader key (Must happen before plugins are loaded)
vim.g.mapleader = ' '
vim.g.maplocalleader = ' '

-- Log errors to file
local log_file = vim.fn.stdpath('state') .. '/nvim-errors.log'
local original_notify = vim.notify
vim.notify = function(msg, level, opts)
  -- Log warnings and errors to file
  if level and level >= vim.log.levels.WARN then
    local f = io.open(log_file, 'a')
    if f then
      local timestamp = os.date('%Y-%m-%d %H:%M:%S')
      local level_name = ({ 'TRACE', 'DEBUG', 'INFO', 'WARN', 'ERROR' })[level + 1] or 'UNKNOWN'
      f:write(string.format('[%s] [%s] %s\n', timestamp, level_name, msg))
      f:close()
    end
  end
  return original_notify(msg, level, opts)
end

-- Load options
require 'options'

-- Load keymaps
require 'keymaps'

-- Load plugin manager
require 'lazy-config'

-- vim: ts=2 sts=2 sw=2 et
