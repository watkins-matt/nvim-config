return {
	"rcarriga/nvim-notify",
	config = function()
		-- Set nvim-notify as the default notification handler
		vim.notify = require("notify")

		-- Configure nvim-notify (example settings)
		require("notify").setup({
			stages = "fade_in_slide_out", -- Animation style
			timeout = 2000, -- Timeout for notifications (in ms)
			background_colour = "#000000", -- Background color of notifications
			fps = 60, -- Frames per second for animations
			render = "default", -- Render style
			max_width = 50, -- Maximum width of notification window
		})
	end,
	-- Optional: Make sure it loads early
	priority = 1000,
}
