"""
BrightTray - Monitor Brightness Control via System Tray
Main Entry Point

Công cụ điều khiển độ sáng màn hình qua System Tray

Author: ntd237
Version: 1.0.0
"""

import sys
import logging
from pathlib import Path

# Add src to path để có thể import modules
sys.path.insert(0, str(Path(__file__).parent / "src"))

from src.utils.logger import setup_logger
from src.config.config_manager import ConfigManager
from src.core.brightness_backend import BrightnessBackend
from src.core.monitor_manager import MonitorManager
from src.core.brightness_controller import BrightnessController
from src.ui.tray_icon import TrayIcon
from src.utils.auto_start import AutoStartManager


def main():
    """
    Entry point chính của ứng dụng.
    """
    # Setup logging
    logger = setup_logger("BrightTray", level=logging.INFO)
    logger.info("=" * 60)
    logger.info("BrightTray v1.0.0 - Starting...")
    logger.info("=" * 60)
    
    try:
        # ===== INITIALIZE COMPONENTS =====
        logger.info("Initializing components...")
        
        # Config Manager
        config_manager = ConfigManager()
        
        # Brightness Backend
        brightness_backend = BrightnessBackend()
        
        # Monitor Manager
        monitor_manager = MonitorManager(brightness_backend)
        
        # Brightness Controller
        controller = BrightnessController(
            monitor_manager,
            brightness_backend,
            config_manager
        )
        
        # Auto-Start Manager
        auto_start_manager = AutoStartManager()
        
        logger.info("All components initialized successfully")
        
        # ===== RESTORE SETTINGS =====
        logger.info("Restoring last brightness settings...")
        controller.restore_last_brightness()
        
        # ===== INITIALIZE TRAY ICON =====
        logger.info("Initializing system tray icon...")
        tray = TrayIcon(
            controller,
            monitor_manager,
            config_manager,
            auto_start_manager
        )
        
        # ===== SETUP DISPLAY CHANGE LISTENER =====
        logger.info("Setting up display change listener...")
        monitor_manager.listen_display_change(
            callback=lambda: tray.rebuild_menu()
        )
        
        # ===== RUN TRAY ICON (BLOCKING) =====
        logger.info("Application ready. Running tray icon...")
        logger.info("Monitor count: %d", monitor_manager.get_monitor_count())
        logger.info("Sync mode: %s", "enabled" if controller.sync_mode else "disabled")
        logger.info("=" * 60)
        
        tray.run()
        
        # ===== CLEANUP =====
        logger.info("Application shutting down...")
        
        # Cleanup code đã được handle trong tray.on_exit()
        
        logger.info("Shutdown complete")
        return 0
        
    except KeyboardInterrupt:
        logger.info("Interrupted by user")
        return 0
        
    except Exception as e:
        logger.error(f"Fatal error: {e}", exc_info=True)
        return 1


if __name__ == '__main__':
    sys.exit(main())
