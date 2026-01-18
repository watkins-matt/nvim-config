local pylsp = require 'utils.pylsp'

-- Detect if running on Termux
local is_termux = vim.g.is_termux or false

-- Termux-specific skip list for LSP servers not to install via Mason
local termux_skip_servers = {
  lua_ls = true, -- Skip lua_ls on Termux
  -- Add other servers to skip on Termux here
}

-- List of all LSP servers and their configurations
local all_servers = {
  pylsp = {
    settings = {
      pylsp = {
        plugins = {
          autopep8 = { enabled = false },
          black = { enabled = true },
          yapf = { enabled = false },
          ruff = { enabled = false }, -- Enabled in lint.lua
          flake8 = { enabled = false },
          pycodestyle = { enabled = false },
          pyflakes = { enabled = false },
          pylint = { enabled = false },
          pylsp_mypy = { enabled = true, dmypy = true, report_progress = true },
          jedi_completion = { fuzzy = true },
          pyls_isort = { enabled = true },
        },
      },
    },
  },
  lua_ls = {
    settings = {
      Lua = {
        completion = {
          callSnippet = 'Replace',
        },
      },
    },
  },
}

-- Filter servers to install via Mason, excluding those in the Termux skip list
local servers_to_install = {}
for server, config in pairs(all_servers) do
  if not (is_termux and termux_skip_servers[server]) then
    servers_to_install[server] = config
  end
end

-- Enhance LSP capabilities with nvim-cmp
local capabilities = vim.lsp.protocol.make_client_capabilities()
capabilities = vim.tbl_deep_extend('force', capabilities, require('cmp_nvim_lsp').default_capabilities())

return {
  { -- LSP Configuration & Plugins
    'neovim/nvim-lspconfig',
    dependencies = {
      { 'williamboman/mason.nvim', config = true },
      'williamboman/mason-lspconfig.nvim',
      'jay-babu/mason-null-ls.nvim',
      'nvimdev/lspsaga.nvim',
      { 'j-hui/fidget.nvim', opts = { notification = { window = { winblend = 0, avoid = { 'NvimTree' } } } } },
      { 'folke/neodev.nvim', opts = {} },
    },
    config = function()
      require('mason').setup()

      require('mason-lspconfig').setup {
        ensure_installed = vim.tbl_keys(servers_to_install),
        automatic_installation = true,
        handlers = {
          function(server_name)
            local server = servers_to_install[server_name] or {}
            server.capabilities = vim.tbl_deep_extend('force', {}, capabilities, server.capabilities or {})
            require('lspconfig')[server_name].setup(server)

            if server_name == 'pylsp' then
              pylsp.ensure_pylsp_plugins()
            end
          end,
        },
      }

      -- Manually setup LSP servers skipped by Mason (e.g., lua_ls on Termux)
      for server, config in pairs(all_servers) do
        if is_termux and termux_skip_servers[server] then
          require('lspconfig')[server].setup(config)
        end
      end

      -- Setup additional LSP servers not managed by Mason (e.g., Dart)
      if vim.fn.executable 'dart' == 1 then
        require('lspconfig').dartls.setup {}
      end

      -- Autocommands for LSP attachment
      vim.api.nvim_create_autocmd('LspAttach', {
        group = vim.api.nvim_create_augroup('lsp-attach', { clear = true }),
        callback = function(event)
          local buf = event.buf
          local client = vim.lsp.get_client_by_id(event.data.client_id)

          local function map(keys, func, desc)
            vim.keymap.set('n', keys, func, { buffer = buf, desc = 'LSP: ' .. desc })
          end

          map('gd', require('telescope.builtin').lsp_definitions, '[G]oto [D]efinition')
          map('gr', require('telescope.builtin').lsp_references, '[G]oto [R]eferences')
          map('gI', require('telescope.builtin').lsp_implementations, '[G]oto [I]mplementation')
          map('<leader>D', require('telescope.builtin').lsp_type_definitions, 'Type [D]efinition')
          map('<leader>ds', require('telescope.builtin').lsp_document_symbols, '[D]ocument [S]ymbols')
          map('<leader>ws', require('telescope.builtin').lsp_dynamic_workspace_symbols, '[W]orkspace [S]ymbols')
          map('<leader>rn', vim.lsp.buf.rename, '[R]e[n]ame')
          map('<leader>ca', vim.lsp.buf.code_action, '[C]ode [A]ction')
          map('K', vim.lsp.buf.hover, 'Hover Documentation')
          map('gD', vim.lsp.buf.declaration, '[G]oto [D]eclaration')

          if client and client.server_capabilities.documentHighlightProvider then
            vim.api.nvim_create_autocmd({ 'CursorHold', 'CursorHoldI' }, {
              buffer = buf,
              callback = vim.lsp.buf.document_highlight,
            })
            vim.api.nvim_create_autocmd({ 'CursorMoved', 'CursorMovedI' }, {
              buffer = buf,
              callback = vim.lsp.buf.clear_references,
            })
          end

          if client and client.server_capabilities.inlayHintProvider and vim.lsp.inlay_hint then
            map('<leader>th', function()
              vim.lsp.inlay_hint(buf, not vim.lsp.inlay_hint.is_enabled())
            end, '[T]oggle Inlay [H]ints')
          end
        end,
      })
    end,
  },
}
