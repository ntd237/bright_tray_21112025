"""
System Tray Icon - Giao diện system tray
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
    """
    
    # Preset brightness levels - Các mức độ sáng preset
    BRIGHTNESS_PRESETS = [0, 25, 50, 75, 100]
    
    def __init__(self, controller, monitor_manager, config_manager, auto_start_manager):
        """
        Khởi tạo TrayIcon.
        
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
        self.icon_path = Path(__file__).parent.parent.parent / "resources" / "icon.png"
        
        self.logger.info("TrayIcon initialized")
    
    def create_icon_image(self) -> Image.Image:
        """
        Tạo icon cho system tray.
        
        Returns:
            PIL Image object
        """
        try:
            if self.icon_path.exists():
                image = Image.open(self.icon_path)
                # Resize về 64x64 cho tray icon
                image = image.resize((64, 64), Image.Resampling.LANCZOS)
                return image
            else:
                self.logger.warning(f"Icon not found at {self.icon_path}. Using default.")
        except Exception as e:
            self.logger.error(f"Error loading icon: {e}. Using default.")
        
        # Fallback: tạo icon đơn giản
        image = Image.new('RGB', (64, 64), color='white')
        draw = ImageDraw.Draw(image)
        draw.ellipse([16, 16, 48, 48], fill='orange', outline='black')
        return image
    
    def build_menu(self) -> Menu:
        """
        Tạo menu cho tray icon.
        
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
            global_brightness = self.config.global_brightness
            
            brightness_items = []
            for preset in self.BRIGHTNESS_PRESETS:
                # Tạo closure function để bind preset value
                def make_callback(value):
                    def callback(icon, item):
                        self.on_set_global_brightness(value)
                    return callback
                
                def make_checked(value):
                    def checked(item):
                        return abs(self.config.global_brightness - value) < 5
                    return checked
                
                brightness_items.append(Item(
                    f"{preset}%",
                    make_callback(preset),
                    checked=make_checked(preset)
                ))
            
            menu_items.append(Item("Global Brightness", Menu(*brightness_items)))
        else:
            # Individual mode: Hiện submenu cho từng màn hình
            for monitor in monitors:
                if monitor.supports_brightness:
                    monitor_items = []
                    
                    # Lấy brightness hiện tại
                    current_brightness = self.config.get_monitor_brightness(monitor.id) or 50
                    
                    for preset in self.BRIGHTNESS_PRESETS:
                        # Tạo closure functions
                        def make_monitor_callback(mon_id, value):
                            def callback(icon, item):
                                self.on_set_monitor_brightness(mon_id, value)
                            return callback
                        
                        def make_monitor_checked(mon_id, value):
                            def checked(item):
                                return abs((self.config.get_monitor_brightness(mon_id) or 50) - value) < 5
                            return checked
                        
                        monitor_items.append(Item(
                            f"{preset}%",
                            make_monitor_callback(monitor.id, preset),
                            checked=make_monitor_checked(monitor.id, preset)
                        ))
                    
                    menu_items.append(Item(str(monitor), Menu(*monitor_items)))
                else:
                    # Màn hình không hỗ trợ brightness control
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
        """
        if self.icon:
            self.logger.info("Rebuilding tray menu...")
            self.icon.menu = self.build_menu()
            self.icon.update_menu()
    
    # ===== EVENT HANDLERS =====
    
    def on_toggle_sync(self, icon, item):
        """
        Xử lý khi toggle sync mode.
        """
        new_state = not self.controller.sync_mode
        self.controller.toggle_sync_mode(new_state)
        self.logger.info(f"Sync mode toggled to: {new_state}")
        
        # Rebuild menu để update UI
        self.rebuild_menu()
    
    def on_set_global_brightness(self, value: int):
        """
        Xử lý khi set global brightness.
        """
        self.logger.info(f"User set global brightness to {value}%")
        self.controller.set_global_brightness(value)
        
        # Update menu để hiển thị checkmark mới
        self.rebuild_menu()
    
    def on_set_monitor_brightness(self, monitor_id: str, value: int):
        """
        Xử lý khi set brightness cho màn hình cụ thể.
        """
        self.logger.info(f"User set brightness for {monitor_id} to {value}%")
        self.controller.set_monitor_brightness(monitor_id, value)
        
        # Update menu
        self.rebuild_menu()
    
    def on_toggle_autostart(self, icon, item):
        """
        Xử lý khi toggle auto-start.
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
        """
        import pystray
        from pystray import MenuItem as Item
        
        # Sử dụng notification thay vì dialog (vì pystray không có native dialog)
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
        self.config.save_config(debounce=False)
        
        # Stop monitor listener
        self.monitor_manager.stop_listening()
        
        # Stop icon
        icon.stop()
    
    def run(self):
        """
        Chạy tray icon (blocking).
        """
        # Tạo icon
        # (Create icon)
        image = self.create_icon_image()
        menu = self.build_menu()
        
        # NOTE: pystray trên Windows:
        # - Right-click: Luôn show menu
        # - Left-click: Trigger default item (nếu có)
        # Để force left-click cũng show menu, cần workaround phức tạp (win32 API hook)
        # Tạm thời: accept right-click để show menu (standard Windows UX)
        
        self.icon = pystray.Icon(
            "BrightTray",
            image,
            "BrightTray - Monitor Brightness Control",
            menu
        )
        
        self.logger.info("Starting tray icon...")
        self.logger.info("USAGE: Right-click icon để mở menu (Left-click sẽ được implement)")
        
        # Run (blocking call)
        self.icon.run()
        
        self.logger.info("Tray icon stopped")
