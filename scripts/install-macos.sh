#!/bin/bash
set -e

echo "================================"
echo "  Snip2Path v1.3.0 - macOS Installer"
echo "================================"
echo ""

# Check Python
if ! command -v python3 &> /dev/null; then
    echo "[ERROR] Python 3 not found. Please install Python 3.8+ first."
    echo "        https://www.python.org/downloads/"
    exit 1
fi
echo "[OK] Python found"

# Install dependencies
echo "[*] Installing dependencies..."
pip3 install Pillow "pyobjc-framework-Cocoa>=10.0" -q
if [ $? -ne 0 ]; then
    echo "[ERROR] Failed to install dependencies."
    exit 1
fi
echo "[OK] Dependencies installed"

# Install snip2path
echo "[*] Installing snip2path..."
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$SCRIPT_DIR/.."
pip3 install . -q
if [ $? -ne 0 ]; then
    echo "[ERROR] Failed to install snip2path."
    exit 1
fi
echo "[OK] snip2path installed"

# Create application scripts
echo "[*] Creating app scripts..."
APP_DIR="$HOME/Applications/Snip2Path"
mkdir -p "$APP_DIR"

cat > "$APP_DIR/start.sh" << 'EOF'
#!/bin/bash
cd "$(dirname "$0")"
nohup snip2path --watch --silent > /dev/null 2>&1 &
echo "Snip2Path started in background"
EOF
chmod +x "$APP_DIR/start.sh"

cat > "$APP_DIR/stop.sh" << 'EOF'
#!/bin/bash
pkill -f "snip2path --watch"
echo "Snip2Path stopped"
EOF
chmod +x "$APP_DIR/stop.sh"

echo "[OK] App scripts created in $APP_DIR"

echo ""
echo "================================"
echo "  Installation complete!"
echo ""
echo "  Usage:"
echo "    snip2path --watch        Start daemon"
echo "    snip2path                Process once"
echo ""
echo "  App scripts:"
echo "    $APP_DIR/start.sh        Start background daemon"
echo "    $APP_DIR/stop.sh         Stop daemon"
echo ""
echo "  Workflow:"
echo "    1. Cmd+Ctrl+Shift+4 to screenshot to clipboard"
echo "    2. Cmd+V in terminal -> file path"
echo "    3. Cmd+V in WeChat -> image"
echo "================================"
