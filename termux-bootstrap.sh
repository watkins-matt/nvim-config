#!/bin/bash

# Update and upgrade Termux packages
pkg update && pkg upgrade -y

# Install essential packages
pkg install -y \
    curl \
    binutils \
    dart \
    fd \
    gh \
    git \
    jq \
    lazygit \
    lua-language-server \
    lua53 \
    neovim \
    nodejs \
    openssh \
    openssl \
    python \
    ruff \
    stylua \
    wget

# Create .config for Neovim
mkdir -p ~/.config/nvim
mkdir -p ~/.local/share/nvim
mkdir -p ~/.termux

# Download and set the Nerd Font for Termux
curl -fLo ~/.termux/font.ttf https://github.com/ryanoasis/nerd-fonts/raw/HEAD/patched-fonts/SourceCodePro/SauceCodeProNerdFontMono-Regular.ttf
termux-reload-settings

# Warn the user that existing configurations will be deleted
read -p "Existing configuration at ~/.config/nvim will be deleted. Press Enter to continue..."
rm -rf ~/.config/nvim/*

# Clone the configuration
git clone https://github.com/watkins-matt/nvim-config.git ~/.config/nvim
