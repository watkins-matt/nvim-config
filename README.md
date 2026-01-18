# Nvim-Config

This is my personal Neovim configuration.

## Quick Install

The repository includes an install and update script, update.py which will download the latest
AppImage and install it, as well as cloning this repository as the NVIM configuration. Finally,
it will add a crontab entry so that NVIM and the configuration from this repository are updated
nightly.

```bash
sudo apt update && sudo apt install -y curl fd-find git lua5.3 make python3 python3-crontab python3-pip python3-requests python3-venv python3-virtualenv ripgrep unzip rust-all nodejs
curl -sSL https://raw.githubusercontent.com/watkins-matt/nvim-config/main/update.py -o ~/update_nvim.py && chmod +x ~/update_nvim.py && sudo python3 ~/update_nvim.py && rm ~/update_nvim.py
```

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

My goal was to make the configuration work on both normal
systems and with Termux. A termux-bootstrap.sh script is
provided which should install all dependencies.

### Installation on Termux

```bash
curl -sL https://raw.githubusercontent.com/watkins-matt/nvim-config/main/termux-bootstrap.sh > termux-bootstrap.sh
bash termux-bootstrap.sh
```

## Credit

Configuration is based on [kickstart-modular](https://github.com/dam9000/kickstart-modular.nvim).
