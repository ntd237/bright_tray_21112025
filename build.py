"""
Build Script - Đóng gói ứng dụng thành .exe
(Build Script - Package application as .exe)

Chạy script này để build .exe với PyInstaller:
(Run this script to build .exe with PyInstaller:)

    python build.py

Output: dist/BrightTray.exe (single file, no console)
"""

import PyInstaller.__main__
import sys
from pathlib import Path


def build():
    """
    Build .exe sử dụng PyInstaller.
    (Build .exe using PyInstaller)
    """
    print("=" * 60)
    print("Building BrightTray.exe...")
    print("=" * 60)
    
    # Đường dẫn files
    # (File paths)
    main_script = 'main.py'
    icon_file = 'resources/icon.png'  # PyInstaller sẽ convert PNG → ICO
    
    # PyInstaller arguments
    args = [
        main_script,
        '--onefile',                    # Đóng gói thành 1 file duy nhất
        '--noconsole',                  # Không hiện console window
        '--name=BrightTray',            # Tên file output
        '--clean',                      # Clean cache trước khi build
        '--optimize=2',                 # Optimize Python bytecode
        
        # Add resources
        f'--add-data=resources;resources',
        
        # Icon (nếu có .ico file, uncomment dòng dưới)
        # (Icon - if .ico file exists, uncomment below)
        # f'--icon={icon_file}',
        
        # Ẩn imports để PyInstaller detect
        # (Hidden imports for PyInstaller detection)
        '--hidden-import=win32api',
        '--hidden-import=win32con',
        '--hidden-import=win32gui',
        '--hidden-import=winreg',
        '--hidden-import=pystray',
        '--hidden-import=PIL',
        '--hidden-import=monitorcontrol',
    ]
    
    print("Running PyInstaller with arguments:")
    for arg in args:
        print(f"  {arg}")
    print()
    
    # Run PyInstaller
    PyInstaller.__main__.run(args)
    
    print()
    print("=" * 60)
    print("Build complete!")
    print("Output: dist/BrightTray.exe")
    print("=" * 60)
    print()
    print("Bạn có thể chạy file .exe từ thư mục dist/")
    print("(You can run the .exe file from the dist/ directory)")


if __name__ == '__main__':
    try:
        build()
    except Exception as e:
        print(f"Build failed: {e}", file=sys.stderr)
        sys.exit(1)
