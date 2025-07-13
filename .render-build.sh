#!/usr/bin/env bash

echo "🔧 Installing Rust toolchain to $HOME..."

# install Rust to user-local path (won’t touch /usr/local)
curl https://sh.rustup.rs -sSf | sh -s -- -y --no-modify-path
export PATH="$HOME/.cargo/bin:$PATH"

echo "📦 Installing Python dependencies..."
pip install --upgrade pip
pip install -r requirements.txt
