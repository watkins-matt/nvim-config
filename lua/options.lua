-- File: lua/options.lua

--------------------------------------------------------------------------------
-- Environment Detection
--------------------------------------------------------------------------------

-- Check if running on Termux
vim.g.is_termux = vim.fn.executable("termux-setup-storage") == 1

-- Check if running inside tmux
vim.g.is_tmux = vim.env.TMUX ~= nil

--------------------------------------------------------------------------------
-- Clipboard Settings
--------------------------------------------------------------------------------

-- Set up clipboard provider based on environment
if vim.g.is_termux then
	-- Termux-specific clipboard settings
	vim.g.clipboard = {
		name = "termux",
		copy = {
			["+"] = "termux-clipboard-set",
			["*"] = "termux-clipboard-set",
		},
		paste = {
			["+"] = "termux-clipboard-get",
			["*"] = "termux-clipboard-get",
		},
	}
else
	-- Default clipboard setting for other environments
	vim.opt.clipboard:append("unnamedplus")
end

-- Enable clipboard integration
vim.opt.clipboard:append("unnamedplus")

--------------------------------------------------------------------------------
-- Mouse Settings
--------------------------------------------------------------------------------

-- Enable mouse support in all modes
vim.opt.mouse = "a"

-- Disable right-click menu
vim.opt.mousemodel = "extend"

-- Enable focus follows mouse
vim.opt.mousefocus = true

-- Hide mouse when typing
vim.opt.mousehide = true

--------------------------------------------------------------------------------
-- User Interface Settings
--------------------------------------------------------------------------------

-- Show line numbers
vim.opt.number = true

-- Disable relative line numbers (set to true to enable)
vim.opt.relativenumber = false

-- Hide the mode indicator (shown in statusline)
vim.opt.showmode = false

-- Hide command line when not in use
vim.opt.cmdheight = 0

-- Always show the sign column
vim.opt.signcolumn = "yes"

-- Highlight the current line
vim.opt.cursorline = true

-- Minimal number of screen lines to keep above and below the cursor
vim.opt.scrolloff = 10

-- Remove the '~' character on empty lines
vim.opt.fillchars = { eob = " " }

-- Enable 24-bit RGB color in the TUI
vim.opt.termguicolors = true

-- Disable lazyredraw to fix issues with tmux
vim.opt.lazyredraw = false

--------------------------------------------------------------------------------
-- Indentation and Whitespace
--------------------------------------------------------------------------------

-- Enable smart indenting
vim.opt.breakindent = true

-- Show invisible characters
vim.opt.list = true

-- Define which whitespace characters to show
vim.opt.listchars = { tab = "» ", trail = "·", nbsp = "␣" }

--------------------------------------------------------------------------------
-- Search Settings
--------------------------------------------------------------------------------

-- Ignore case in search patterns
vim.opt.ignorecase = true

-- Override ignorecase if search pattern contains uppercase characters
vim.opt.smartcase = true

-- Show search results as you type
vim.opt.inccommand = "split"

--------------------------------------------------------------------------------
-- Window Behavior
--------------------------------------------------------------------------------

-- Open new vertical splits to the right
vim.opt.splitright = true

-- Open new horizontal splits below
vim.opt.splitbelow = true

--------------------------------------------------------------------------------
-- Performance and Timing
--------------------------------------------------------------------------------

-- Decrease update time (default 4000ms)
vim.opt.updatetime = 250

-- Time in milliseconds to wait for a mapped sequence to complete
vim.opt.timeoutlen = 300

-- Improves smoothness of redrawing
vim.opt.ttyfast = true

-- Enable timeout on keycodes
vim.opt.timeout = true

-- Time in milliseconds to wait for a mapped sequence to complete
vim.opt.timeoutlen = 1000

-- Time in milliseconds to wait for a key code sequence to complete
vim.opt.ttimeoutlen = 0

--------------------------------------------------------------------------------
-- File Handling
--------------------------------------------------------------------------------

-- Enable persistent undo
vim.opt.undofile = true

-- Disable netrw (we're using nvim-tree)
vim.g.loaded_netrw = 1
vim.g.loaded_netrwPlugin = 1

-- Set internal encoding of vim
vim.opt.encoding = "utf-8"

-- Set encoding for files
vim.opt.fileencoding = "utf-8"

--------------------------------------------------------------------------------
-- Key Mappings for Copy/Paste
--------------------------------------------------------------------------------

local function map(mode, lhs, rhs, opts)
	local options = { noremap = true, silent = true }
	if opts then
		options = vim.tbl_extend("force", options, opts)
	end
	vim.keymap.set(mode, lhs, rhs, options)
end

-- Copy in visual mode
map("v", "<C-c>", '"+y')

-- Cut in visual mode
map("v", "<C-x>", '"+d')

-- Paste in normal mode
map("n", "<C-v>", ':set paste<CR>"+p:set nopaste<CR>', { noremap = true, silent = true })

-- Paste in insert mode
map("i", "<C-v>", "<C-o>:set paste<CR><C-R>+<C-o>:set nopaste<CR>", { noremap = true, silent = true })

-- Paste in command mode
map("c", "<C-v>", "<C-R>+", { noremap = true, silent = true })

--------------------------------------------------------------------------------
-- Autocommands
--------------------------------------------------------------------------------

-- Highlight on yank
vim.api.nvim_create_autocmd("TextYankPost", {
	group = vim.api.nvim_create_augroup("highlight_yank", { clear = true }),
	callback = function()
		vim.highlight.on_yank()
	end,
})

-- vim: ts=2 sts=2 sw=2 et
