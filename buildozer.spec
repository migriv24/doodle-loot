[app]
title           = Doodle Loot
package.name    = doodleloot
package.domain  = com.doodleloot

source.dir      = .
source.include_exts = py,wav
source.include_patterns = assets/audio/*.wav
source.exclude_dirs = __pycache__,.git,bin,.buildozer,adapters/mobile_adapter

version         = 0.1
requirements    = python3==3.10.12,cython==0.29.37,pygame==2.1.0

# Portrait-only, no title bar
orientation     = portrait
fullscreen      = 1

# Icons & presplash (drop files here when ready)
# icon.filename   = assets/icon.png
# presplash.filename = assets/presplash.png

android.permissions     = VIBRATE
android.api             = 33
android.minapi          = 26
android.ndk             = 25b
android.ndk_api         = 26
android.accept_sdk_license = True
android.archs           = arm64-v8a, armeabi-v7a

# SDL2 bootstrap — required for pygame (not kivy)
p4a.bootstrap           = sdl2

# Keep logcat readable
android.logcat_filters  = *:S python:D

[buildozer]
log_level       = 2
warn_on_root    = 0
