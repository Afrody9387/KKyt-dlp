import os

# DMG Volume name
volume_name = 'Install KKyt-dlp v1.6'

# Application format setting: 'UDBZ' for bzip2 compressed (default), 'ULFO' for lzfse
format = 'UDBZ'

# Window dimensions: ((x, y), (width, height))
window_rect = ((200, 120), (800, 500))

# Background options
# Use string for a background image, or dict for colors
background = 'dmg_background.png'

# Default icon size
icon_size = 120

# We don't want any text below the icons so that the background arrow is the focus
text_size = 14

# Hide extensions
hide_extensions = ['KKyt-dlp.app']

# Files to copy into the DMG
files = ['dist/KKyt-dlp.app']

# Symlinks to create
symlinks = {
    'Applications': '/Applications'
}

# Coordinates for icons relative to the window
icon_locations = {
    'KKyt-dlp.app': (200, 250),
    'Applications': (600, 250)
}
