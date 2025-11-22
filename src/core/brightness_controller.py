"""
Brightness Controller - Logic điều khiển độ sáng
"""

import logging
import threading
from typing import List, Optional


class BrightnessController:
    """
    Controller điều khiển độ sáng với sync mode và individual mode.
    """
    
    def __init__(self, monitor_manager, brightness_backend, config_manager):
        """
        Khởi tạo BrightnessController.
        
        Args:
            monitor_manager: Instance của MonitorManager
            brightness_backend: Instance của BrightnessBackend
            config_manager: Instance của ConfigManager
        """
        self.logger = logging.getLogger("BrightTray.BrightnessController")
        
        self.monitor_manager = monitor_manager
        self.backend = brightness_backend
        self.config = config_manager
        
        # Thread lock để đảm bảo thread safety
        self._lock = threading.Lock()
        
        self.logger.info("BrightnessController initialized")
    
    @property
    def sync_mode(self) -> bool:
        """Sync mode có được bật không"""
        return self.config.sync_mode
    
    def toggle_sync_mode(self, enabled: bool):
        """
        Bật/tắt sync mode.
        
        Args:
            enabled: True để bật, False để tắt
        """
        with self._lock:
            self.config.sync_mode = enabled
            self.logger.info(f"Sync mode {'enabled' if enabled else 'disabled'}")
            
            # Nếu bật sync mode, đồng bộ tất cả màn hình về global brightness
            if enabled:
                global_brightness = self.config.global_brightness
                self._set_all_brightness_internal(global_brightness, save_global=False)
    
    def set_global_brightness(self, value: int):
        """
        Đặt độ sáng cho TẤT CẢ màn hình (sync mode).
        
        Args:
            value: Độ sáng mới (0-100)
        """
        # Validate range
        value = max(0, min(100, value))
        
        with self._lock:
            self.logger.info(f"Setting global brightness to {value}%")
            
            # Lưu vào config
            self.config.global_brightness = value
            
            # Set brightness cho tất cả màn hình
            self._set_all_brightness_internal(value, save_global=False)
    
    def _set_all_brightness_internal(self, value: int, save_global: bool = True):
        """
        Internal method để set brightness cho tất cả màn hình.
        
        Args:
            value: Độ sáng
            save_global: Có lưu vào global_brightness không
        """
        monitors = self.monitor_manager.get_monitors()
        
        for monitor in monitors:
            if monitor.supports_brightness:
                success = self.backend.set_brightness(monitor.id, value)
                if success:
                    # Lưu vào per-monitor config
                    # (Save to per-monitor config)
                    self.config.set_monitor_brightness(monitor.id, value)
                else:
                    self.logger.warning(f"Failed to set brightness for {monitor.name}")
        
        if save_global:
            self.config.global_brightness = value
    
    def set_monitor_brightness(self, monitor_id: str, value: int):
        """
        Đặt độ sáng cho màn hình cụ thể (individual mode).
        
        Args:
            monitor_id: ID của màn hình
            value: Độ sáng mới (0-100)
        """
        # Validate range
        value = max(0, min(100, value))
        
        with self._lock:
            self.logger.info(f"Setting brightness for {monitor_id} to {value}%")
            
            # Set brightness
            success = self.backend.set_brightness(monitor_id, value)
            
            if success:
                # Lưu vào config
                self.config.set_monitor_brightness(monitor_id, value)
            else:
                self.logger.warning(f"Failed to set brightness for {monitor_id}")
    
    def get_monitor_brightness(self, monitor_id: str) -> Optional[int]:
        """
        Lấy độ sáng hiện tại của màn hình.
        
        Args:
            monitor_id: ID của màn hình
            
        Returns:
            Độ sáng (0-100) hoặc None nếu error
        """
        with self._lock:
            return self.backend.get_brightness(monitor_id)
    
    def restore_last_brightness(self):
        """
        Khôi phục độ sáng từ config khi khởi động.
        """
        with self._lock:
            monitors = self.monitor_manager.get_monitors()
            
            if self.sync_mode:
                # Sync mode: apply global brightness
                global_brightness = self.config.global_brightness
                self.logger.info(f"Restoring global brightness: {global_brightness}%")
                self._set_all_brightness_internal(global_brightness, save_global=False)
            else:
                # Individual mode: restore per-monitor brightness
                self.logger.info("Restoring per-monitor brightness")
                for monitor in monitors:
                    if monitor.supports_brightness:
                        saved_brightness = self.config.get_monitor_brightness(monitor.id)
                        if saved_brightness is not None:
                            self.backend.set_brightness(monitor.id, saved_brightness)
                            self.logger.info(f"Restored {monitor.name} to {saved_brightness}%")
                        else:
                            # Không có config đã lưu, dùng mặc định
                            self.logger.debug(f"No saved brightness for {monitor.name}, keeping current")
