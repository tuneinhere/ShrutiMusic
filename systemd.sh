#!/bin/bash

SERVICE_NAME=$(basename "$(pwd)")
REPO_DIR="$(pwd)"
VENV_DIR="$REPO_DIR/venv"
ENV_FILE="$REPO_DIR/.env"

# 🔹 Cek & install Node.js + npm kalau belum ada
if ! command -v node &> /dev/null || ! command -v npm &> /dev/null; then
    echo "🚀 Menginstall Node.js & npm..."
    curl -fssL https://deb.nodesource.com/setup_19.x | sudo -E bash -
    sudo apt-get install -y nodejs
    sudo npm i -g npm
else
    echo "ℹ️ Node.js & npm sudah terinstall."
fi

# 🔹 Cek versi
node -v
npm -v

# 🔹 Install node-fetch
if [ ! -d "node_modules/node-fetch" ]; then
    echo "📦 Menginstall node-fetch..."
    npm install node-fetch
else
    echo "ℹ️ node-fetch sudah terinstall."
fi

echo "📦 Menyiapkan virtual environment untuk $SERVICE_NAME..."
if [ ! -d "$VENV_DIR" ]; then
    python3 -m venv "$VENV_DIR"
    echo "✅ Virtual environment dibuat."
else
    echo "ℹ️ Virtual environment sudah ada."
fi

source "$VENV_DIR/bin/activate"
pip install --upgrade pip
pip install -r "$REPO_DIR/requirements.txt"

echo "🔧 Membuat systemd service untuk $SERVICE_NAME..."

if [ -f "$ENV_FILE" ]; then
    ENV_LINE="EnvironmentFile=$ENV_FILE"
    echo "📄 File .env ditemukan, akan dimuat oleh systemd."
else
    ENV_LINE=""
    echo "⚠️ File .env tidak ditemukan, bagian EnvironmentFile dilewati."
fi

sudo tee /etc/systemd/system/$SERVICE_NAME.service > /dev/null <<EOF
[Unit]
Description=Ubot $SERVICE_NAME
After=network.target

[Service]
Type=simple
User=$USER
WorkingDirectory=$REPO_DIR
$ENV_LINE
ExecStart=/bin/bash -c 'source $VENV_DIR/bin/activate && bash start'
Restart=always
RestartSec=5
Environment=PYTHONUNBUFFERED=1

[Install]
WantedBy=multi-user.target
EOF

echo "🔄 Reload systemd dan mengaktifkan service $SERVICE_NAME..."

sudo systemctl daemon-reload
sudo systemctl enable $SERVICE_NAME
sudo systemctl restart $SERVICE_NAME

echo "✅ Service '$SERVICE_NAME' berhasil dibuat dan dijalankan!"
sudo systemctl status $SERVICE_NAME --no-pager
