local M = {}

-- Hashtable to store directory -> project root mappings
local project_root_cache = {}

-- Check if the current file is a Python file
local function is_python_file()
  local file_extension = vim.fn.expand '%:e'
  return file_extension == 'py'
end

-- Function to find the Python project root based on markers
function M.find_python_project_root()
  -- Check if the file is a Python file
  if not is_python_file() then
    return nil -- If not a Python file, don't calculate the project root
  end

  local cwd = vim.fn.expand '%:p:h'

  -- Check if the current directory is already cached
  if project_root_cache[cwd] then
    return project_root_cache[cwd]
  end

  -- List of root marker files or directories for Python projects
  local root_markers = { '.git', 'pyproject.toml', 'setup.py', 'requirements.txt', '.venv' }
  local root = cwd

  -- Iterate upwards through parent directories to find the project root
  while root do
    for _, marker in ipairs(root_markers) do
      if vim.fn.isdirectory(root .. '/.venv') == 1 or vim.fn.filereadable(root .. '/' .. marker) == 1 then
        project_root_cache[cwd] = root -- Cache the project root for the current directory
        return root
      end
    end
    -- Move one directory up
    local parent = vim.fn.fnamemodify(root, ':h')
    if parent == root then
      break -- If we've reached the top directory, stop
    end
    root = parent
  end

  -- No project root found, cache it as nil
  project_root_cache[cwd] = nil
  return nil
end

-- Function to get the Python interpreter path (from .venv if available)
function M.get_python_path()
  local project_root = M.find_python_project_root()

  if project_root then
    local venv_path = project_root .. '/.venv/bin/python'
    if vim.fn.filereadable(venv_path) == 1 then
      return venv_path
    end
  end

  -- Fallback to system Python if no project root or venv found
  return 'python3'
end

-- Command to clear the project root cache
vim.api.nvim_create_user_command('ClearProjectRootCache', function()
  project_root_cache = {}
end, {})

return M
