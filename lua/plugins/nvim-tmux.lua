return {
	"alexghergh/nvim-tmux-navigation",
	config = function()
		local nvim_tmux_nav = require("nvim-tmux-navigation")

		nvim_tmux_nav.setup({
			disable_when_zoomed = true, -- Disable navigation when pane is zoomed
		})

		-- Mappings for normal mode (Ctrl + hjkl, Ctrl + Arrow keys, Ctrl + \, and Ctrl + Space)
		vim.keymap.set("n", "<C-h>", nvim_tmux_nav.NvimTmuxNavigateLeft, { desc = "Navigate Left (Tmux/Neovim)" })
		vim.keymap.set("n", "<C-j>", nvim_tmux_nav.NvimTmuxNavigateDown, { desc = "Navigate Down (Tmux/Neovim)" })
		vim.keymap.set("n", "<C-k>", nvim_tmux_nav.NvimTmuxNavigateUp, { desc = "Navigate Up (Tmux/Neovim)" })
		vim.keymap.set("n", "<C-l>", nvim_tmux_nav.NvimTmuxNavigateRight, { desc = "Navigate Right (Tmux/Neovim)" })
		vim.keymap.set("n", "<C-Left>", nvim_tmux_nav.NvimTmuxNavigateLeft, { desc = "Navigate Left (Tmux/Neovim)" })
		vim.keymap.set("n", "<C-Down>", nvim_tmux_nav.NvimTmuxNavigateDown, { desc = "Navigate Down (Tmux/Neovim)" })
		vim.keymap.set("n", "<C-Up>", nvim_tmux_nav.NvimTmuxNavigateUp, { desc = "Navigate Up (Tmux/Neovim)" })
		vim.keymap.set("n", "<C-Right>", nvim_tmux_nav.NvimTmuxNavigateRight, { desc = "Navigate Right (Tmux/Neovim)" })
		vim.keymap.set(
			"n",
			"<C-\\>",
			nvim_tmux_nav.NvimTmuxNavigateLastActive,
			{ desc = "Navigate to Last Active Pane" }
		)
		vim.keymap.set("n", "<C-Space>", nvim_tmux_nav.NvimTmuxNavigateNext, { desc = "Navigate to Next Pane" })

		-- Mappings for insert mode (Ctrl + hjkl, Ctrl + Arrow keys, Ctrl + \, and Ctrl + Space)
		vim.keymap.set("i", "<C-h>", nvim_tmux_nav.NvimTmuxNavigateLeft, { desc = "Navigate Left (Tmux/Neovim)" })
		vim.keymap.set("i", "<C-j>", nvim_tmux_nav.NvimTmuxNavigateDown, { desc = "Navigate Down (Tmux/Neovim)" })
		vim.keymap.set("i", "<C-k>", nvim_tmux_nav.NvimTmuxNavigateUp, { desc = "Navigate Up (Tmux/Neovim)" })
		vim.keymap.set("i", "<C-l>", nvim_tmux_nav.NvimTmuxNavigateRight, { desc = "Navigate Right (Tmux/Neovim)" })
		vim.keymap.set("i", "<C-Left>", nvim_tmux_nav.NvimTmuxNavigateLeft, { desc = "Navigate Left (Tmux/Neovim)" })
		vim.keymap.set("i", "<C-Down>", nvim_tmux_nav.NvimTmuxNavigateDown, { desc = "Navigate Down (Tmux/Neovim)" })
		vim.keymap.set("i", "<C-Up>", nvim_tmux_nav.NvimTmuxNavigateUp, { desc = "Navigate Up (Tmux/Neovim)" })
		vim.keymap.set("i", "<C-Right>", nvim_tmux_nav.NvimTmuxNavigateRight, { desc = "Navigate Right (Tmux/Neovim)" })
		vim.keymap.set(
			"i",
			"<C-\\>",
			nvim_tmux_nav.NvimTmuxNavigateLastActive,
			{ desc = "Navigate to Last Active Pane" }
		)
		vim.keymap.set("i", "<C-Space>", nvim_tmux_nav.NvimTmuxNavigateNext, { desc = "Navigate to Next Pane" })
	end,
}
