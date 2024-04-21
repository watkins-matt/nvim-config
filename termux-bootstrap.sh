#!/bin/bash

# Update and upgrade Termux packages
pkg update && pkg upgrade -y

# Install essential packages
pkg install -y \
    curl \
    binutils \
    dart \
    fd \
    git \
    jq \
    lua-language-server \
    lua53 \
    neovim \
    nodejs \
    openssh \
    openssl \
    python \
    ruff \
    stylua \
    wget \

# Create .config for Neovim
mkdir -p ~/.config/nvim
mkdir -p ~/.local/share/nvim
mkdir -p ~/.termux

# Download and set the Nerd Font for Termux
curl -fLo ~/.termux/font.ttf https://github.com/ryanoasis/nerd-fonts/raw/HEAD/patched-fonts/SourceCodePro/SauceCodeProNerdFontMono-Regular.ttf
termux-reload-settings
