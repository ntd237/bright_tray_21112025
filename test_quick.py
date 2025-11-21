"""
Quick Test Script - Kiểm tra nhanh các components
(Quick Test Script - Quick check of components)

Chạy script này để test imports và basic functionality:
(Run this script to test imports and basic functionality:)

    python test_quick.py
"""

import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

print("=" * 60)
print("BrightTray - Quick Test")
print("=" * 60)
print()

# Test imports
print("Testing imports...")

try:
    from src.utils.logger import setup_logger
    print("✅ logger")
except Exception as e:
    print(f"❌ logger: {e}")

try:
    from src.config.config_manager import ConfigManager
    print("✅ config_manager")
except Exception as e:
    print(f"❌ config_manager: {e}")

try:
    from src.core.brightness_backend import BrightnessBackend
    print("✅ brightness_backend")
except Exception as e:
    print(f"❌ brightness_backend: {e}")

try:
    from src.core.monitor_manager import MonitorManager
    print("✅ monitor_manager")
except Exception as e:
    print(f"❌ monitor_manager: {e}")

try:
    from src.core.brightness_controller import BrightnessController
    print("✅ brightness_controller")
except Exception as e:
    print(f"❌ brightness_controller: {e}")

try:
    from src.ui.tray_icon import TrayIcon
    print("✅ tray_icon")
except Exception as e:
    print(f"❌ tray_icon: {e}")

try:
    from src.utils.auto_start import AutoStartManager
    print("✅ auto_start")
except Exception as e:
    print(f"❌ auto_start: {e}")

print()
print("=" * 60)
print("Testing component initialization...")
print("=" * 60)
print()

try:
    logger = setup_logger("Test", level=20)  # INFO level
    print("✅ Logger initialized")
    
    config = ConfigManager()
    print(f"✅ ConfigManager initialized (config_file: {config.config_file})")
    print(f"   - Sync mode: {config.sync_mode}")
    print(f"   - Global brightness: {config.global_brightness}")
    
    backend = BrightnessBackend()
    print(f"✅ BrightnessBackend initialized")
    print(f"   - Monitor count: {backend.get_monitor_count()}")
    
    if backend.get_monitor_count() > 0:
        monitors = backend.get_all_monitors_info()
        for i, monitor in enumerate(monitors):
            print(f"   - {monitor}")
    
    print()
    print("=" * 60)
    print("✅ All tests passed!")
    print("=" * 60)
    print()
    print("Ứng dụng sẵn sàng để chạy với: python main.py")
    print("(Application ready to run with: python main.py)")
    
except Exception as e:
    print(f"❌ Error during initialization: {e}")
    import traceback
    traceback.print_exc()
