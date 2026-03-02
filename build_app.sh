#!/bin/bash
# ──────────────────────────────────────────────
# Copysight — macOS .app bundle builder
# Creates dist/Copysight.app (launcher → venv)
# ──────────────────────────────────────────────
set -e

APP_NAME="Copysight"
PROJECT_DIR="$(cd "$(dirname "$0")" && pwd)"
DIST_DIR="$PROJECT_DIR/dist"
APP_DIR="$DIST_DIR/$APP_NAME.app"
CONTENTS="$APP_DIR/Contents"
MACOS="$CONTENTS/MacOS"
RESOURCES="$CONTENTS/Resources"
VENV="$PROJECT_DIR/venv"
PYTHON="$VENV/bin/python"

echo "Building $APP_NAME.app..."
echo "  Project: $PROJECT_DIR"

# ── Verify environment ──
if [ ! -f "$PYTHON" ]; then
    echo "Error: Python venv not found at $VENV"
    echo "Run: python -m venv venv && source venv/bin/activate && pip install -r requirements.txt"
    exit 1
fi

# ── Clean previous build ──
rm -rf "$APP_DIR"
mkdir -p "$MACOS" "$RESOURCES"

# ── 1. Generate app icon ──
echo "  Generating icon..."
"$PYTHON" "$PROJECT_DIR/build_icon.py" "$RESOURCES/AppIcon.iconset"

# Convert iconset → icns
if [ -d "$RESOURCES/AppIcon.iconset" ]; then
    iconutil -c icns "$RESOURCES/AppIcon.iconset" -o "$RESOURCES/AppIcon.icns"
    rm -rf "$RESOURCES/AppIcon.iconset"
    echo "  ✓ Icon created"
else
    echo "  ⚠ Icon generation skipped"
fi

# ── 2. Create launcher script ──
cat > "$MACOS/$APP_NAME" << LAUNCHER
#!/bin/bash
# Copysight launcher — runs from project venv
PROJECT="$PROJECT_DIR"
cd "\$PROJECT"
exec "\$PROJECT/venv/bin/python" "\$PROJECT/app.py"
LAUNCHER
chmod +x "$MACOS/$APP_NAME"
echo "  ✓ Launcher created"

# ── 3. Create Info.plist ──
cat > "$CONTENTS/Info.plist" << 'PLIST'
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>CFBundleName</key>
    <string>Copysight</string>
    <key>CFBundleDisplayName</key>
    <string>Copysight</string>
    <key>CFBundleIdentifier</key>
    <string>com.marcinmajsawicki.copysight</string>
    <key>CFBundleVersion</key>
    <string>2.0</string>
    <key>CFBundleShortVersionString</key>
    <string>2.0</string>
    <key>CFBundleExecutable</key>
    <string>Copysight</string>
    <key>CFBundleIconFile</key>
    <string>AppIcon</string>
    <key>CFBundlePackageType</key>
    <string>APPL</string>
    <key>CFBundleInfoDictionaryVersion</key>
    <string>6.0</string>
    <key>LSMinimumSystemVersion</key>
    <string>12.0</string>
    <key>NSHighResolutionCapable</key>
    <true/>
    <key>LSUIElement</key>
    <false/>
    <key>NSHumanReadableCopyright</key>
    <string>Marcin Majsawicki 2026</string>
</dict>
</plist>
PLIST
echo "  ✓ Info.plist created"

# ── Done ──
echo ""
echo "✓ Built: $APP_DIR"
echo ""
echo "To install:"
echo "  cp -r \"$APP_DIR\" /Applications/"
echo ""
echo "Or double-click dist/Copysight.app in Finder."
