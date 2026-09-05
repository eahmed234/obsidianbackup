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
echo "Ensuring root index.html..."
python3 -c '
import os, shutil

found = False
for f in os.listdir("../public"):
    if f.startswith("the-s") and f.endswith("rah.html"):
        shutil.copyfile(os.path.join("../public", f), "../public/index.html")
        print(f"Mapped {f} -> ../public/index.html")
        found = True
        break

if not found:
    print("Warning: could not find the-sirah.html among:", os.listdir("../public"))
'

echo "=== Build Completed Successfully! Output in public/ ==="
