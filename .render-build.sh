echo "🔧 Installing Rust toolchain..."
curl https://sh.rustup.rs -sSf | sh -s -- -y
source $HOME/.cargo/env

echo "📦 Installing Python dependencies..."
pip install --upgrade pip
pip install -r requirements.txt

echo "✅ Build completed successfully."
