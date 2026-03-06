"""
setup_offline.py
Run this ONCE to download all CSS/JS assets for offline use.
After running, the app works with NO internet connection.
"""

import os
import sys
import urllib.request
import shutil

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
CSS_DIR  = os.path.join(BASE_DIR, 'static', 'css')
JS_DIR   = os.path.join(BASE_DIR, 'static', 'js')
FONTS_DIR = os.path.join(BASE_DIR, 'static', 'fonts')

os.makedirs(CSS_DIR, exist_ok=True)
os.makedirs(JS_DIR, exist_ok=True)
os.makedirs(FONTS_DIR, exist_ok=True)

ASSETS = [
    # (url, local_path)
    (
        "https://cdn.jsdelivr.net/npm/bootstrap@5.3.2/dist/css/bootstrap.min.css",
        os.path.join(CSS_DIR, "bootstrap.min.css")
    ),
    (
        "https://cdn.jsdelivr.net/npm/bootstrap@5.3.2/dist/js/bootstrap.bundle.min.js",
        os.path.join(JS_DIR, "bootstrap.bundle.min.js")
    ),
    (
        "https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.5.0/css/all.min.css",
        os.path.join(CSS_DIR, "fontawesome.min.css")
    ),
    (
        "https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.5.0/webfonts/fa-solid-900.woff2",
        os.path.join(FONTS_DIR, "fa-solid-900.woff2")
    ),
    (
        "https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.5.0/webfonts/fa-regular-400.woff2",
        os.path.join(FONTS_DIR, "fa-regular-400.woff2")
    ),
    (
        "https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.5.0/webfonts/fa-brands-400.woff2",
        os.path.join(FONTS_DIR, "fa-brands-400.woff2")
    ),
]

def download(url, path):
    if os.path.exists(path) and os.path.getsize(path) > 1000:
        print(f"  ✓ Already exists: {os.path.basename(path)}")
        return True
    try:
        print(f"  ↓ Downloading: {os.path.basename(path)} ...", end='', flush=True)
        urllib.request.urlretrieve(url, path)
        print(f" done ({os.path.getsize(path)//1024} KB)")
        return True
    except Exception as e:
        print(f" FAILED: {e}")
        return False

def fix_fontawesome_css():
    """Fix font paths in fontawesome CSS to point to local fonts."""
    fa_css = os.path.join(CSS_DIR, "fontawesome.min.css")
    if not os.path.exists(fa_css):
        return
    with open(fa_css, 'r', encoding='utf-8') as f:
        content = f.read()
    # Replace CDN webfont paths with local relative paths
    content = content.replace(
        '../webfonts/',
        '/static/fonts/'
    )
    with open(fa_css, 'w', encoding='utf-8') as f:
        f.write(content)
    print("  ✓ Fixed FontAwesome font paths")

def patch_base_html():
    """Replace CDN links in base.html with local static file links."""
    base_html = os.path.join(BASE_DIR, 'templates', 'base.html')
    with open(base_html, 'r', encoding='utf-8') as f:
        content = f.read()

    replacements = [
        (
            '<link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.2/dist/css/bootstrap.min.css" rel="stylesheet">',
            '<link href="/static/css/bootstrap.min.css" rel="stylesheet">'
        ),
        (
            '<link href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.5.0/css/all.min.css" rel="stylesheet">',
            '<link href="/static/css/fontawesome.min.css" rel="stylesheet">'
        ),
        (
            '<link href="https://fonts.googleapis.com/css2?family=Poppins:wght@300;400;500;600;700&family=Playfair+Display:wght@700&display=swap" rel="stylesheet">',
            '<!-- Google Fonts removed for offline use - using system fonts -->'
        ),
        (
            '<script src="https://cdn.jsdelivr.net/npm/bootstrap@5.3.2/dist/js/bootstrap.bundle.min.js"></script>',
            '<script src="/static/js/bootstrap.bundle.min.js"></script>'
        ),
    ]

    changed = False
    for old, new in replacements:
        if old in content:
            content = content.replace(old, new)
            changed = True

    if changed:
        with open(base_html, 'w', encoding='utf-8') as f:
            f.write(content)
        print("  ✓ Patched base.html to use local assets")
    else:
        print("  ✓ base.html already patched (or CDN links not found)")

def main():
    print("\n" + "="*55)
    print("  New Metro Big Bazaar — Offline Asset Setup")
    print("="*55)
    print("\nDownloading assets for offline use...\n")

    success = all(download(url, path) for url, path in ASSETS)

    if success:
        print("\nFixing asset paths...")
        fix_fontawesome_css()
        patch_base_html()
        print("\n" + "="*55)
        print("  ✅ Setup complete! App will work fully offline.")
        print("  Run START_APP.bat (Windows) or start_app.sh (Mac/Linux)")
        print("="*55 + "\n")
    else:
        print("\n⚠️  Some downloads failed.")
        print("  The app will still work with internet, or retry later.")

if __name__ == '__main__':
    main()
