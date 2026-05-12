#!/bin/bash
set -e

echo "================================"
echo "  Snip2Path v1.4.0 - Linux Installer"
echo "================================"
echo ""

# Check Python
if ! command -v python3 &> /dev/null; then
    echo "[ERROR] Python 3 not found. Please install Python 3.8+ first."
    echo "        https://www.python.org/downloads/"
    exit 1
fi
echo "[OK] Python found"

# Check clipboard backend
if [ -n "$WAYLAND_DISPLAY" ]; then
    if ! command -v wl-copy &> /dev/null; then
        echo "[WARN] Wayland detected but wl-clipboard not found."
        echo "       Install it: sudo apt install wl-clipboard"
        echo "       (or equivalent for your distro)"
    else
        echo "[OK] Wayland clipboard backend (wl-clipboard) found"
    fi
else
    if ! command -v xclip &> /dev/null; then
        echo "[WARN] xclip not found. Install it: sudo apt install xclip"
        echo "       (or equivalent for your distro)"
    else
        echo "[OK] X11 clipboard backend (xclip) found"
    fi
fi

# Install dependencies
echo "[*] Installing dependencies..."
pip3 install Pillow -q
echo "[OK] Dependencies installed"

# Install snip2path
echo "[*] Installing snip2path..."
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$SCRIPT_DIR/.."
pip3 install . -q
echo "[OK] snip2path installed"

# Create application scripts
echo "[*] Creating app scripts..."
APP_DIR="$HOME/.local/share/snip2path"
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
echo "    1. Screenshot tool (e.g. gnome-screenshot, flameshot)"
echo "    2. Ctrl+V in terminal -> file path"
echo "    3. Ctrl+V in chat apps -> image"
echo ""
echo "  Note: Linux clipboard cannot hold both image and text."
echo "        Default: image is restored (chat apps work)."
echo "        Use --with-text to paste path in terminal."
echo "================================"
