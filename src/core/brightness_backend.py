"""
Brightness Backend - Wrapper cho DDC/CI communication
(Brightness Backend - Wrapper for DDC/CI communication)
"""

import logging
from typing import Optional, List
from dataclasses import dataclass


# Try import monitorcontrol
# (Thử import monitorcontrol)
try:
    from monitorcontrol import get_monitors, Monitor, InputSource
    MONITORCONTROL_AVAILABLE = True
except ImportError:
    MONITORCONTROL_AVAILABLE = False
    logging.warning("monitorcontrol library not available. Install with: pip install monitorcontrol")


@dataclass
class MonitorInfo:
    """
    Thông tin về một màn hình.
    (Information about a monitor)
    """
    id: str  # Unique identifier
    name: str  # Display name
    index: int  # Monitor index
    is_primary: bool  # Primary monitor hay không
    supports_brightness: bool  # Hỗ trợ điều chỉnh độ sáng không
    
    def __str__(self):
        primary_tag = " (Primary)" if self.is_primary else ""
        support_tag = "" if self.supports_brightness else " [No DDC/CI]"
        return f"{self.name}{primary_tag}{support_tag}"


class BrightnessBackend:
    """
    Backend để điều khiển độ sáng màn hình qua DDC/CI.
    (Backend to control monitor brightness via DDC/CI)
    """
    
    def __init__(self):
        """
        Khởi tạo BrightnessBackend.
        (Initialize BrightnessBackend)
        """
        self.logger = logging.getLogger("BrightTray.BrightnessBackend")
        
        if not MONITORCONTROL_AVAILABLE:
            self.logger.error("monitorcontrol library not available!")
            self.monitors: List[Monitor] = []
            return
        
        # Cache danh sách monitors
        # (Cache monitors list)
        self.monitors: List[Monitor] = []
        self.refresh_monitors()
    
    def refresh_monitors(self):
        """
        Làm mới danh sách monitors (call khi có WM_DISPLAYCHANGE).
        (Refresh monitors list - call when WM_DISPLAYCHANGE occurs)
        """
        if not MONITORCONTROL_AVAILABLE:
            return
        
        try:
            self.monitors = list(get_monitors())
            self.logger.info(f"Found {len(self.monitors)} monitor(s)")
            
            # Log thông tin từng màn hình
            # (Log info for each monitor)
            for i, monitor in enumerate(self.monitors):
                try:
                    # Thử lấy brightness để test DDC/CI support
                    # (Try to get brightness to test DDC/CI support)
                    with monitor:
                        brightness = monitor.get_luminance()
                    self.logger.info(f"Monitor {i}: Supports DDC/CI, current brightness: {brightness}%")
                except Exception as e:
                    self.logger.warning(f"Monitor {i}: DDC/CI not supported or error: {e}")
                    
        except Exception as e:
            self.logger.error(f"Error refreshing monitors: {e}")
            self.monitors = []
    
    def get_monitor_count(self) -> int:
        """
        Lấy số lượng màn hình.
        (Get number of monitors)
        """
        return len(self.monitors)
    
    def get_monitor_info(self, index: int) -> Optional[MonitorInfo]:
        """
        Lấy thông tin về màn hình theo index.
        (Get monitor info by index)
        
        Args:
            index: Index của màn hình (Monitor index)
            
        Returns:
            MonitorInfo object hoặc None nếu không tìm thấy
            (MonitorInfo object or None if not found)
        """
        if index < 0 or index >= len(self.monitors):
            return None
        
        monitor = self.monitors[index]
        
        # Kiểm tra DDC/CI support
        # (Check DDC/CI support)
        supports_brightness = self._check_brightness_support(index)
        
        # Tạo unique ID từ index (có thể improve bằng serial number)
        # (Create unique ID from index - can improve with serial number)
        monitor_id = f"MONITOR_{index}"
        
        # Tạo display name
        # (Create display name)
        name = f"Monitor {index + 1}"
        
        # Monitor đầu tiên thường là primary
        # (First monitor is usually primary)
        is_primary = (index == 0)
        
        return MonitorInfo(
            id=monitor_id,
            name=name,
            index=index,
            is_primary=is_primary,
            supports_brightness=supports_brightness
        )
    
    def get_all_monitors_info(self) -> List[MonitorInfo]:
        """
        Lấy thông tin tất cả màn hình.
        (Get info for all monitors)
        """
        return [
            self.get_monitor_info(i)
            for i in range(len(self.monitors))
        ]
    
    def _check_brightness_support(self, index: int) -> bool:
        """
        Kiểm tra màn hình có hỗ trợ DDC/CI brightness control không.
        (Check if monitor supports DDC/CI brightness control)
        """
        if index < 0 or index >= len(self.monitors):
            return False
        
        try:
            monitor = self.monitors[index]
            with monitor:
                # Thử get brightness
                # (Try to get brightness)
                monitor.get_luminance()
            return True
        except Exception as e:
            self.logger.debug(f"Monitor {index} does not support brightness control: {e}")
            return False
    
    def get_brightness(self, monitor_id: str) -> Optional[int]:
        """
        Lấy độ sáng hiện tại của màn hình.
        (Get current brightness of monitor)
        
        Args:
            monitor_id: ID của màn hình (Monitor ID)
            
        Returns:
            Độ sáng (0-100) hoặc None nếu error
            (Brightness 0-100 or None if error)
        """
        index = self._id_to_index(monitor_id)
        if index is None:
            return None
        
        if index < 0 or index >= len(self.monitors):
            return None
        
        try:
            monitor = self.monitors[index]
            with monitor:
                brightness = monitor.get_luminance()
            self.logger.debug(f"Monitor {monitor_id}: brightness = {brightness}%")
            return brightness
        except Exception as e:
            self.logger.error(f"Failed to get brightness for {monitor_id}: {e}")
            return None
    
    def set_brightness(self, monitor_id: str, value: int) -> bool:
        """
        Đặt độ sáng cho màn hình.
        (Set brightness for monitor)
        
        Args:
            monitor_id: ID của màn hình (Monitor ID)
            value: Độ sáng mới (0-100) (New brightness 0-100)
            
        Returns:
            True nếu thành công, False nếu thất bại
            (True if successful, False if failed)
        """
        # Validate range
        value = max(0, min(100, value))
        
        index = self._id_to_index(monitor_id)
        if index is None:
            return False
        
        if index < 0 or index >= len(self.monitors):
            return False
        
        try:
            monitor = self.monitors[index]
            with monitor:
                monitor.set_luminance(value)
            self.logger.info(f"Set brightness for {monitor_id} to {value}%")
            return True
        except Exception as e:
            self.logger.error(f"Failed to set brightness for {monitor_id}: {e}")
            return False
    
    def _id_to_index(self, monitor_id: str) -> Optional[int]:
        """
        Chuyển đổi monitor ID sang index.
        (Convert monitor ID to index)
        """
        # Format: "MONITOR_0", "MONITOR_1", etc.
        try:
            if monitor_id.startswith("MONITOR_"):
                return int(monitor_id.split("_")[1])
        except Exception:
            pass
        return None
