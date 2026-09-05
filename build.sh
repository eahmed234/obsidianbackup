#!/usr/bin/env bash
set -e

echo "=== Starting Quartz Build Pipeline for nabiwiki ==="

# 1. Ensure Quartz engine exists
if [ ! -d ".quartz" ]; then
  echo "Cloning Quartz engine..."
  git clone --depth 1 https://github.com/jackyzha0/quartz.git .quartz
fi

cd .quartz

# 2. Install dependencies if needed
if [ ! -d "node_modules" ]; then
  echo "Installing Quartz dependencies..."
  npm install
fi

# 3. Copy custom configuration
if [ -f "../quartz.config.yaml" ]; then
  echo "Applying custom quartz.config.yaml..."
  cp ../quartz.config.yaml quartz.config.yaml
fi

# 4. Build static site
echo "Building static site..."
npm run quartz -- build -d .. -o ../public

# 5. Ensure root index.html is populated from the canonical hub (The Sīrah)
if [ -f "../public/the-sīrah.html" ]; then
  echo "Linking the-sīrah.html as root index.html..."
  cp -f "../public/the-sīrah.html" "../public/index.html"
fi

echo "=== Build Completed Successfully! Output in public/ ==="
