#!/usr/bin/env bash
set -e

echo "=== Starting Quartz Build Pipeline for nabiwiki ==="

# 0. Refuse to build if citations, links or the hub are broken (see audit.py)
echo "Auditing citations, links and hub..."
python3 audit.py --no-content

# 1. Ensure Quartz engine exists — at a pinned commit.
#    patch-quartz.mjs rewrites Quartz's built files (slugs, search), so an unannounced upstream change
#    can break the site. To upgrade: raise QUARTZ_REF, delete .quartz, build locally, and check search.
QUARTZ_REF="${QUARTZ_REF:-beeeed45b82a3cd559d4645fee41f5f699f89188}"   # Quartz v5.1.0, 10 Nov 2026
if [ ! -d ".quartz" ]; then
  echo "Fetching Quartz engine at ${QUARTZ_REF}..."
  git init -q .quartz
  git -C .quartz remote add origin https://github.com/jackyzha0/quartz.git
  git -C .quartz fetch -q --depth 1 origin "${QUARTZ_REF}"
  git -C .quartz checkout -q FETCH_HEAD
elif [ "$(git -C .quartz rev-parse HEAD 2>/dev/null)" != "${QUARTZ_REF}" ]; then
  echo "Warning: .quartz is not at the pinned commit ${QUARTZ_REF}; delete .quartz to refetch it."
fi

cd .quartz

# 2. Install dependencies if needed
if [ ! -d "node_modules" ]; then
  echo "Installing Quartz dependencies..."
  npm install
fi

# 3. Copy custom configuration & styles
if [ -f "../quartz.config.yaml" ]; then
  echo "Applying custom quartz.config.yaml..."
  cp ../quartz.config.yaml quartz.config.yaml
fi
if [ -f "../custom.scss" ]; then
  echo "Applying custom styles (Noto Naskh Arabic & Noto Serif)..."
  cp ../custom.scss quartz/styles/custom.scss
fi

# 4. Patch Quartz for clean ASCII transliteration slugs (prevents infinite redirect loops on CDN)
if [ -f "../patch-quartz.mjs" ]; then
  echo "Applying ASCII slug patch to Quartz..."
  node ../patch-quartz.mjs
fi

# 5. Build static site
echo "Building static site..."
npm run quartz -- build -d .. -o ../public

# 6. Mark every page whose note is still tagged `unverified` (see site_notice.py)
python3 ../site_notice.py ../public

# Contents sidebar, infoboxes and chronological links, built from the hub and frontmatter (see site_nav.py)
python3 ../site_nav.py ../public

# Search: other names and spellings in the index, redirects for them, disambiguation pages for shared
# names; fails the build if a query listed under "expect" in site_search.json no longer matches (see site_search.py)
python3 ../site_search.py ../public

# 7. The homepage is the short start page (Start Here.md); the hub (The Sīrah) stays at /the-sirah.
#    If the start page is missing, fall back to the hub so the site always has a homepage.
echo "Ensuring root index.html..."
python3 -c '
import os, shutil, sys

pub = "../public"
src = "start-here.html"
if not os.path.exists(os.path.join(pub, src)):
    src = next((f for f in os.listdir(pub) if f.startswith("the-s") and f.endswith("rah.html")), None)
    print("Warning: start-here.html not found; using the hub as the homepage.")
if not src:
    sys.exit("No start page and no hub page in public/ - refusing to deploy a site without a homepage.")
shutil.copyfile(os.path.join(pub, src), os.path.join(pub, "index.html"))
print(f"Mapped {src} -> index.html")
'

echo "=== Build Completed Successfully! Output in public/ ==="
