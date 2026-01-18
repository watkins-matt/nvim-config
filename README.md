# Nvim-Config

Personal Neovim configuration with LSP, debugging, testing, and git integration.

## Quick Install

```bash
sudo apt update && sudo apt install -y curl fd-find git lua5.3 make python3 python3-crontab python3-pip python3-requests python3-venv python3-virtualenv ripgrep unzip rust-all nodejs
curl -sSL https://raw.githubusercontent.com/watkins-matt/nvim-config/main/update.py -o ~/update_nvim.py && chmod +x ~/update_nvim.py && sudo python3 ~/update_nvim.py && rm ~/update_nvim.py
```

## Plugin Managers

### :Lazy
Plugin manager for Neovim. Use to install, update, or remove plugins.
- Press `I` to install missing plugins
- Press `U` to update plugins  
- Press `X` to clean unused plugins
- Press `S` to sync (clean + install + update)

### :Mason
Installer for LSP servers, linters, and formatters. Browse and install language tools.
- Press `i` on a package to install
- Press `X` to uninstall
- Press `u` to update

### :LspInfo
Shows which LSP servers are active for the current buffer. Useful for debugging why autocomplete or diagnostics are not working.

### :TSUpdate
Updates Treesitter parsers (syntax highlighting). Run after adding new languages or if syntax highlighting breaks.

### :checkhealth
Runs diagnostic checks on your Neovim setup. Shows issues with plugins, providers (Python, Node), and dependencies.

## Keybindings

Leader key is `<Space>`.

### File Navigation
| Key | Description |
|-----|-------------|
| `<leader>e` | Toggle file explorer (nvim-tree) |
| `<leader>sf` | Search files |
| `<leader>sg` | Search by grep (live) |
| `<leader>s.` | Search recent files |
| `<leader><leader>` | Find open buffers |
| `<leader>/` | Fuzzy search in current buffer |

### Git
| Key | Description |
|-----|-------------|
| `<leader>gg` | Open LazyGit (fullscreen) |
| `<leader>hs` | Stage hunk |
| `<leader>hr` | Reset hunk |
| `<leader>hS` | Stage buffer |
| `<leader>hR` | Reset buffer |
| `<leader>hp` | Preview hunk |
| `<leader>hb` | Blame line |
| `<leader>hd` | Diff against index |
| `<leader>tb` | Toggle line blame |
| `]c` / `[c` | Next/prev git change |

### Testing (neotest)
| Key | Description |
|-----|-------------|
| `<leader>t` | Toggle test summary panel |
| `<leader>rt` | Run nearest test |
| `<leader>rf` | Run current file tests |
| `<leader>ro` | Open test output |

### Debugging (DAP)
| Key | Description |
|-----|-------------|
| `<leader>dc` | Start/Continue |
| `<leader>db` | Toggle breakpoint |
| `<leader>dB` | Set conditional breakpoint |
| `<leader>di` | Step into |
| `<leader>do` | Step over |
| `<leader>du` | Step out |
| `<leader>dt` | Toggle DAP UI |
| `<leader>dr` | Toggle REPL |
| `<leader>dx` | Terminate |

### LSP
| Key | Description |
|-----|-------------|
| `gd` | Go to definition |
| `gr` | Go to references |
| `gI` | Go to implementation |
| `gD` | Go to declaration |
| `K` | Hover documentation |
| `<leader>ca` | Code action |
| `<leader>rn` | Rename symbol |
| `<leader>ds` | Document symbols |
| `<leader>ws` | Workspace symbols |
| `<leader>D` | Type definition |
| `<leader>th` | Toggle inlay hints |

### Search (Telescope)
| Key | Description |
|-----|-------------|
| `<leader>sh` | Search help |
| `<leader>sk` | Search keymaps |
| `<leader>ss` | Search Telescope builtins |
| `<leader>sw` | Search current word |
| `<leader>sd` | Search diagnostics |
| `<leader>sr` | Resume last search |
| `<leader>sn` | Search nvim config files |

### Window Navigation
| Key | Description |
|-----|-------------|
| `Ctrl+h/j/k/l` | Navigate splits (also works with tmux) |
| `Ctrl+arrows` | Navigate splits (alternative) |

### Other
| Key | Description |
|-----|-------------|
| `<leader>f` | Format buffer |
| `<leader>x` | Toggle trouble (diagnostics) |
| `<leader>i` | Enable paste mode + insert |
| `s` / `S` | Leap motion (jump to chars) |

## Automatic Updates

The update script runs nightly at 2am and updates:
- Neovim AppImage (to latest release)
- This configuration (via git pull)
- All plugins (via Lazy sync)

## Error Logging

All warnings and errors are automatically logged to:

```
~/.local/state/nvim/nvim-errors.log
```

View recent errors:
```bash
cat ~/.local/state/nvim/nvim-errors.log
tail -f ~/.local/state/nvim/nvim-errors.log  # live follow
```

## Termux Support

A termux-bootstrap.sh script is provided for Termux installations.

```bash
curl -sL https://raw.githubusercontent.com/watkins-matt/nvim-config/main/termux-bootstrap.sh > termux-bootstrap.sh
bash termux-bootstrap.sh
```

## Credit

Configuration is based on [kickstart-modular](https://github.com/dam9000/kickstart-modular.nvim).
