-- Disable netrw (we're using nvim-tree)
vim.g.loaded_netrw = 1
vim.g.loaded_netrwPlugin = 1

-- Environment detection
vim.g.is_termux = vim.fn.executable 'termux-setup-storage' == 1
vim.g.have_nerd_font = true -- Set to true if using a Nerd Font

--------------------------------------------------------------------------------
-- General Settings
--------------------------------------------------------------------------------

-- Enable 24-bit RGB color in the TUI
vim.opt.termguicolors = true

-- Enable mouse support in all modes
vim.opt.mouse = 'a'

-- Use system clipboard for all operations
vim.opt.clipboard = 'unnamedplus'

-- Enable persistent undo
vim.opt.undofile = true

-- Decrease update time (default 4000ms)
vim.opt.updatetime = 250

-- Time in milliseconds to wait for a mapped sequence to complete
vim.opt.timeoutlen = 300

--------------------------------------------------------------------------------
-- UI Settings
--------------------------------------------------------------------------------

-- Show line numbers
vim.opt.number = true

-- Disable line wrapping
vim.opt.wrap = false

-- Hide the mode indicator (shown in statusline)
vim.opt.showmode = false

-- Hide command line when not in use
vim.opt.cmdheight = 0

-- Always show the signcolumn
vim.opt.signcolumn = 'yes'

-- Highlight the current line
vim.opt.cursorline = true

-- Minimal number of screen lines to keep above and below the cursor
vim.opt.scrolloff = 10

-- Remove the '~' character on empty lines
vim.opt.fillchars = { eob = ' ' }

--------------------------------------------------------------------------------
-- Split Behavior
--------------------------------------------------------------------------------

-- Open new vertical splits to the right
vim.opt.splitright = true

-- Open new horizontal splits below
vim.opt.splitbelow = true

--------------------------------------------------------------------------------
-- Search Settings
--------------------------------------------------------------------------------

-- Ignore case in search patterns
vim.opt.ignorecase = true

-- Override ignorecase if search pattern contains uppercase characters
vim.opt.smartcase = true

-- Show search results as you type
vim.opt.inccommand = 'split'

--------------------------------------------------------------------------------
-- Whitespace Display
--------------------------------------------------------------------------------

-- Show invisible characters
vim.opt.list = true

-- Define which whitespace characters to show
vim.opt.listchars = { tab = '» ', trail = '·', nbsp = '␣' }

--------------------------------------------------------------------------------
-- Indentation
--------------------------------------------------------------------------------

-- Enable smart indenting
vim.opt.breakindent = true

--------------------------------------------------------------------------------
-- File Encoding
--------------------------------------------------------------------------------

-- Set internal encoding of vim
vim.opt.encoding = 'utf-8'

-- Set encoding for files
vim.opt.fileencoding = 'utf-8'

--------------------------------------------------------------------------------
-- Performance
--------------------------------------------------------------------------------

-- Improves smoothness of redrawing
vim.opt.ttyfast = true

-- Enable timeout on keycodes
vim.opt.timeout = true

-- Time in milliseconds to wait for a mapped sequence to complete
vim.opt.timeoutlen = 1000

-- Time in milliseconds to wait for a key code sequence to complete
vim.opt.ttimeoutlen = 0

-- vim: ts=2 sts=2 sw=2 et
