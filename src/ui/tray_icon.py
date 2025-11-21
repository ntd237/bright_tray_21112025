"""
System Tray Icon - Giao diện system tray
(System Tray Icon - System tray interface)
"""

import logging
from pathlib import Path
from typing import Optional
from PIL import Image, ImageDraw, ImageFont
import pystray
from pystray import MenuItem as Item, Menu


class TrayIcon:
    """
    Quản lý system tray icon và menu.
    (Manage system tray icon and menu)
    """
    
    # Preset brightness levels - Các mức độ sáng preset
    BRIGHTNESS_PRESETS = [0, 25, 50, 75, 100]
    
    def __init__(self, controller, monitor_manager, config_manager, auto_start_manager):
        """
        Khởi tạo TrayIcon.
        (Initialize TrayIcon)
        
        Args:
            controller: Instance của BrightnessController
            monitor_manager: Instance của MonitorManager
            config_manager: Instance của ConfigManager
            auto_start_manager: Instance của AutoStartManager
        """
        self.logger = logging.getLogger("BrightTray.TrayIcon")
        
        self.controller = controller
        self.monitor_manager = monitor_manager
        self.config = config_manager
        self.auto_start_manager = auto_start_manager
        
        # Tray icon instance
        self.icon: Optional[pystray.Icon] = None
        
        # Đường dẫn icon
        # (Icon path)
        self.icon_path = Path(__file__).parent.parent.parent / "resources" / "icon.png"
        
        self.logger.info("TrayIcon initialized")
    
    def create_icon_image(self) -> Image.Image:
        """
        Tạo icon cho system tray.
        (Create icon for system tray)
        
        Returns:
            PIL Image object
        """
        try:
            if self.icon_path.exists():
                image = Image.open(self.icon_path)
                # Resize về 64x64 cho tray icon
                # (Resize to 64x64 for tray icon)
                image = image.resize((64, 64), Image.Resampling.LANCZOS)
                return image
            else:
                self.logger.warning(f"Icon not found at {self.icon_path}. Using default.")
        except Exception as e:
            self.logger.error(f"Error loading icon: {e}. Using default.")
        
        # Fallback: tạo icon đơn giản
        # (Fallback: create simple icon)
        image = Image.new('RGB', (64, 64), color='white')
        draw = ImageDraw.Draw(image)
        draw.ellipse([16, 16, 48, 48], fill='orange', outline='black')
        return image
    
    def build_menu(self) -> Menu:
        """
        Tạo menu cho tray icon.
        (Create menu for tray icon)
        
        Returns:
            pystray Menu object
        """
        monitors = self.monitor_manager.get_monitors()
        sync_mode = self.controller.sync_mode
        
        menu_items = []
        
        # ===== SYNC MODE TOGGLE =====
        menu_items.append(Item(
            "Sync all monitors",
            self.on_toggle_sync,
            checked=lambda item: self.controller.sync_mode
        ))
        
        menu_items.append(Menu.SEPARATOR)
        
        # ===== BRIGHTNESS CONTROLS =====
        if sync_mode:
            # Sync mode: Chỉ hiện global brightness presets
            # (Sync mode: Only show global brightness presets)
            global_brightness = self.config.global_brightness
            
            brightness_items = []
            for preset in self.BRIGHTNESS_PRESETS:
                brightness_items.append(Item(
                    f"{preset}%",
                    lambda _, p=preset: self.on_set_global_brightness(p),
                    checked=lambda item, p=preset: abs(self.config.global_brightness - p) < 5
                ))
            
            menu_items.append(Menu("Global Brightness", Menu(*brightness_items)))
        else:
            # Individual mode: Hiện submenu cho từng màn hình
            # (Individual mode: Show submenu for each monitor)
            for monitor in monitors:
                if monitor.supports_brightness:
                    monitor_items = []
                    
                    # Lấy brightness hiện tại
                    # (Get current brightness)
                    current_brightness = self.config.get_monitor_brightness(monitor.id) or 50
                    
                    for preset in self.BRIGHTNESS_PRESETS:
                        monitor_items.append(Item(
                            f"{preset}%",
                            lambda _, mid=monitor.id, p=preset: self.on_set_monitor_brightness(mid, p),
                            checked=lambda item, mid=monitor.id, p=preset: abs(
                                (self.config.get_monitor_brightness(mid) or 50) - p
                            ) < 5
                        ))
                    
                    menu_items.append(Menu(str(monitor), Menu(*monitor_items)))
                else:
                    # Màn hình không hỗ trợ brightness control
                    # (Monitor doesn't support brightness control)
                    menu_items.append(Item(
                        f"{monitor.name} [No DDC/CI]",
                        lambda _: None,
                        enabled=False
                    ))
        
        menu_items.append(Menu.SEPARATOR)
        
        # ===== AUTO-START TOGGLE =====
        menu_items.append(Item(
            "Start with Windows",
            self.on_toggle_autostart,
            checked=lambda item: self.auto_start_manager.is_enabled()
        ))
        
        menu_items.append(Menu.SEPARATOR)
        
        # ===== ABOUT =====
        menu_items.append(Item("About", self.on_about))
        
        # ===== EXIT =====
        menu_items.append(Item("Exit", self.on_exit))
        
        return Menu(*menu_items)
    
    def rebuild_menu(self):
        """
        Rebuild menu (gọi khi có thay đổi màn hình).
        (Rebuild menu - called when monitors change)
        """
        if self.icon:
            self.logger.info("Rebuilding tray menu...")
            self.icon.menu = self.build_menu()
            self.icon.update_menu()
    
    # ===== EVENT HANDLERS =====
    
    def on_toggle_sync(self, icon, item):
        """
        Xử lý khi toggle sync mode.
        (Handle sync mode toggle)
        """
        new_state = not self.controller.sync_mode
        self.controller.toggle_sync_mode(new_state)
        self.logger.info(f"Sync mode toggled to: {new_state}")
        
        # Rebuild menu để update UI
        # (Rebuild menu to update UI)
        self.rebuild_menu()
    
    def on_set_global_brightness(self, value: int):
        """
        Xử lý khi set global brightness.
        (Handle set global brightness)
        """
        self.logger.info(f"User set global brightness to {value}%")
        self.controller.set_global_brightness(value)
        
        # Update menu để hiển thị checkmark mới
        # (Update menu to show new checkmark)
        self.rebuild_menu()
    
    def on_set_monitor_brightness(self, monitor_id: str, value: int):
        """
        Xử lý khi set brightness cho màn hình cụ thể.
        (Handle set brightness for specific monitor)
        """
        self.logger.info(f"User set brightness for {monitor_id} to {value}%")
        self.controller.set_monitor_brightness(monitor_id, value)
        
        # Update menu
        self.rebuild_menu()
    
    def on_toggle_autostart(self, icon, item):
        """
        Xử lý khi toggle auto-start.
        (Handle auto-start toggle)
        """
        current_state = self.auto_start_manager.is_enabled()
        new_state = not current_state
        
        if new_state:
            success = self.auto_start_manager.enable()
            if success:
                self.config.auto_start = True
                self.logger.info("Auto-start enabled")
            else:
                self.logger.error("Failed to enable auto-start")
        else:
            success = self.auto_start_manager.disable()
            if success:
                self.config.auto_start = False
                self.logger.info("Auto-start disabled")
            else:
                self.logger.error("Failed to disable auto-start")
        
        # Rebuild menu
        self.rebuild_menu()
    
    def on_about(self, icon, item):
        """
        Hiển thị About dialog.
        (Show About dialog)
        """
        import pystray
        from pystray import MenuItem as Item
        
        # Sử dụng notification thay vì dialog (vì pystray không có native dialog)
        # (Use notification instead of dialog - pystray doesn't have native dialog)
        if hasattr(icon, 'notify'):
            icon.notify(
                "BrightTray v1.0.0\n\n"
                "Monitor brightness control tool\n"
                "Author: ntd237\n\n"
                "Using DDC/CI protocol",
                "About BrightTray"
            )
        else:
            self.logger.info("About: BrightTray v1.0.0 by ntd237")
    
    def on_exit(self, icon, item):
        """
        Xử lý khi exit.
        (Handle exit)
        """
        self.logger.info("User requested exit")
        
        # Lưu config cuối cùng
        # (Save final config)
        self.config.save_config(debounce=False)
        
        # Stop monitor listener
        self.monitor_manager.stop_listening()
        
        # Stop icon
        icon.stop()
    
    def run(self):
        """
        Chạy tray icon (blocking).
        (Run tray icon - blocking)
        """
        # Tạo icon
        # (Create icon)
        image = self.create_icon_image()
        menu = self.build_menu()
        
        self.icon = pystray.Icon(
            "BrightTray",
            image,
            "BrightTray - Monitor Brightness Control",
            menu
        )
        
        self.logger.info("Starting tray icon...")
        
        # Run (blocking call)
        self.icon.run()
        
        self.logger.info("Tray icon stopped")
