return {
	"rcarriga/nvim-notify",
	config = function()
		local notify = require("notify")

		-- Configure nvim-notify
		notify.setup({
			stages = "fade_in_slide_out",
			timeout = 2000,
			background_colour = "#000000",
			fps = 60,
			render = "default",
			max_width = 50,
		})

		-- Set up file logging wrapper around nvim-notify
		local log_file = vim.fn.stdpath('state') .. '/nvim-errors.log'
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
			return notify(msg, level, opts)
		end
	end,
	priority = 1000,
}
