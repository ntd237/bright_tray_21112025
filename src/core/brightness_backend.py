"""
Brightness Backend - Hybrid DDC/CI + WMI

Strategy:
- Dùng monitorcontrol (DDC/CI) cho external monitors
- Dùng screen_brightness_control (WMI) cho laptop screens
- Auto-detect và fallback
"""

import logging
from typing import Optional, List
from dataclasses import dataclass

# Windows API for primary monitor detection
try:
    import win32api
    import win32con
    WIN32_AVAILABLE = True
except ImportError:
    WIN32_AVAILABLE = False
    logging.warning("pywin32 not available for primary monitor detection")


# Try import monitorcontrol (DDC/CI)
try:
    from monitorcontrol import get_monitors, Monitor, InputSource
    MONITORCONTROL_AVAILABLE = True
except ImportError:
    MONITORCONTROL_AVAILABLE = False
    logging.warning("monitorcontrol library not available. Install with: pip install monitorcontrol")

# Try import screen_brightness_control (WMI)
try:
    import screen_brightness_control as sbc
    SBC_AVAILABLE = True
except ImportError:
    SBC_AVAILABLE = False
    logging.warning("screen_brightness_control library not available. Install with: pip install screen-brightness-control")


@dataclass
class MonitorInfo:
    """
    Thông tin về một màn hình.
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
    Backend để điều khiển độ sáng màn hình - Hybrid DDC/CI + WMI.
    """
    
    def __init__(self):
        """
        Khởi tạo BrightnessBackend.
        """
        self.logger = logging.getLogger("BrightTray.BrightnessBackend")
        
        # Cache danh sách monitors (DDC/CI)
        self.monitors: List[Monitor] = []
        
        # Cache SBC display names (WMI fallback)
        self.sbc_displays = []
        
        # Primary monitor index (detected via Windows API)
        self.primary_monitor_index = 0  # Default fallback
        
        # SWAP Monitor Order - Fix cho setup 2 monitors
        # Set True nếu monitor 0 (external) cần swap với monitor 1 (laptop)
        self.SWAP_MONITOR_ORDER = True  # User requested swap
        
        self.refresh_monitors()
    
    def _detect_primary_monitor_index(self) -> int:
        """
        Detect primary monitor index using Windows API.
        
        Returns:
            Index của primary monitor (0-based)
        """
        if not WIN32_AVAILABLE:
            self.logger.debug("win32api not available, assuming index 0 is primary")
            return 0
        
        try:
            # Get all monitors info using EnumDisplayMonitors
            monitors_info = win32api.EnumDisplayMonitors()
            
            # Find primary monitor
            for idx, (hMonitor, hdcMonitor, rect) in enumerate(monitors_info):
                info = win32api.GetMonitorInfo(hMonitor)
                # Primary monitor has MONITORINFOF_PRIMARY flag
                if info.get('Flags', 0) & win32con.MONITORINFOF_PRIMARY:
                    self.logger.info(f"Primary monitor detected at index {idx}")
                    return idx
            
            # Fallback to 0
            self.logger.warning("Could not detect primary monitor, using index 0")
            return 0
            
        except Exception as e:
            self.logger.error(f"Error detecting primary monitor: {e}")
            return 0
    
    def refresh_monitors(self):
        """
        Làm mới danh sách monitors (call khi có WM_DISPLAYCHANGE).
        """
        # Refresh DDC/CI monitors
        if MONITORCONTROL_AVAILABLE:
            try:
                self.monitors = list(get_monitors())
                self.logger.info(f"Found {len(self.monitors)} DDC/CI monitor(s)")
            except Exception as e:
                self.logger.error(f"Error refreshing DDC/CI monitors: {e}")
                self.monitors = []
        
        # Refresh SBC displays (WMI)
        if SBC_AVAILABLE:
            try:
                self.sbc_displays = sbc.list_monitors()
                self.logger.info(f"Found {len(self.sbc_displays)} WMI display(s): {self.sbc_displays}")
            except Exception as e:
                self.logger.warning(f"Error refreshing WMI displays: {e}")
                self.sbc_displays = []
        
        # Log từng màn hình để debug
        total_count = max(len(self.monitors), len(self.sbc_displays))
        self.logger.info(f"Total monitors detected: {total_count}")
        
        for i in range(total_count):
            # Try DDC/CI first
            if i < len(self.monitors):
                try:
                    with self.monitors[i]:
                        brightness = self.monitors[i].get_luminance()
                    self.logger.info(f"Monitor {i}: DDC/CI ✅ (brightness: {brightness}%)")
                    continue  # Skip WMI if DDC/CI works
                except Exception as e:
                    self.logger.debug(f"Monitor {i}: DDC/CI failed - {e}")
            
            # Fallback to WMI
            if i < len(self.sbc_displays):
                try:
                    display_name = self.sbc_displays[i]
                    brightness = sbc.get_brightness(display=display_name)[0]
                    self.logger.info(f"Monitor {i}: WMI ✅ via {display_name} (brightness: {brightness}%)")
                except Exception as e:
                    self.logger.warning(f"Monitor {i}: WMI also failed - {e}")
        
        # Detect primary monitor index
        self.primary_monitor_index = self._detect_primary_monitor_index()
    
    def _apply_monitor_swap(self, logical_index: int) -> int:
        """
        Convert logical index (UI) to physical index (hardware).

        Args:
            logical_index: Index hiển thị trong UI (0, 1, 2, ...)
            
        Returns:
            Physical index thực tế của hardware
            
        Examples:
            Nếu SWAP_MONITOR_ORDER = True (swap 0 ↔ 1):
            - logical 0 → physical 1
            - logical 1 → physical 0
            - logical 2+ → physical 2+
        """
        if not self.SWAP_MONITOR_ORDER:
            return logical_index
        
        # Chỉ swap 2 monitors đầu tiên
        if logical_index == 0:
            return 1
        elif logical_index == 1:
            return 0
        else:
            return logical_index
    
    def get_monitor_count(self) -> int:
        """
        Lấy số lượng màn hình (hybrid: max of DDC/CI and WMI).
        """
        return max(len(self.monitors), len(self.sbc_displays))
    
    def get_monitor_info(self, index: int) -> Optional[MonitorInfo]:
        """
        Lấy thông tin về màn hình theo index.
        
        Args:
            index: Index của màn hình (Monitor index - LOGICAL)
            
        Returns:
            MonitorInfo object hoặc None nếu không tìm thấy
        """
        # Apply monitor swap: logical → physical
        physical_index = self._apply_monitor_swap(index)
        
        if physical_index < 0 or physical_index >= len(self.monitors):
            return None
        
        monitor = self.monitors[physical_index]
        
        # Kiểm tra DDC/CI support (dùng logical index)
        supports_brightness = self._check_brightness_support(index)
        
        # Tạo unique ID từ LOGICAL index (UI index)
        monitor_id = f"MONITOR_{index}"
        
        # Tạo display name
        name = f"Monitor {index + 1}"
        
        # Check if this is the primary monitor (dùng physical index)
        is_primary = (physical_index == self.primary_monitor_index)
        
        self.logger.debug(f"get_monitor_info: logical={index}, physical={physical_index}, is_primary={is_primary}")
        
        return MonitorInfo(
            id=monitor_id,
            name=name,
            index=index,  # Lưu logical index
            is_primary=is_primary,
            supports_brightness=supports_brightness
        )
    
    def get_all_monitors_info(self) -> List[MonitorInfo]:
        """
        Lấy thông tin tất cả màn hình.
        """
        return [
            self.get_monitor_info(i)
            for i in range(len(self.monitors))
        ]
    
    def _check_brightness_support(self, logical_index: int) -> bool:
        """
        Kiểm tra màn hình có hỗ trợ brightness control không (DDC/CI hoặc WMI).
        
        Args:
            logical_index: Logical index (UI index)
        """
        # Apply swap
        physical_index = self._apply_monitor_swap(logical_index)
        
        total_count = self.get_monitor_count()
        if physical_index < 0 or physical_index >= total_count:
            return False
        
        # Try DDC/CI first (dùng physical index)
        if physical_index < len(self.monitors):
            try:
                monitor = self.monitors[physical_index]
                with monitor:
                    monitor.get_luminance()
                return True  # DDC/CI works!
            except Exception as e:
                self.logger.debug(f"Monitor logical={logical_index} physical={physical_index}: DDC/CI not supported - {e}")
        
        # Fallback to WMI
        if physical_index < len(self.sbc_displays):
            try:
                display_name = self.sbc_displays[physical_index]
                brightness = sbc.get_brightness(display=display_name)
                return len(brightness) > 0  # WMI works!
            except Exception as e:
                self.logger.debug(f"Monitor logical={logical_index} physical={physical_index}: WMI also not supported - {e}")
        
        return False
    
    def get_brightness(self, monitor_id: str) -> Optional[int]:
        """
        Lấy độ sáng hiện tại của màn hình (Hybrid: DDC/CI hoặc WMI).
        
        Args:
            monitor_id: ID của màn hình (Monitor ID - logical)
            
        Returns:
            Độ sáng (0-100) hoặc None nếu error
        """
        logical_index = self._id_to_index(monitor_id)
        if logical_index is None:
            return None
        
        # Apply swap
        physical_index = self._apply_monitor_swap(logical_index)
        
        total_count = self.get_monitor_count()
        if physical_index < 0 or physical_index >= total_count:
            return None
        
        # Try DDC/CI first (dùng physical index)
        if physical_index < len(self.monitors):
            try:
                monitor = self.monitors[physical_index]
                with monitor:
                    brightness = monitor.get_luminance()
                self.logger.debug(f"Monitor {monitor_id} (L{logical_index}→P{physical_index}): DDC/CI brightness = {brightness}%")
                return brightness
            except Exception as e:
                self.logger.debug(f"Monitor {monitor_id}: DDC/CI failed - {e}")
        
        # Fallback to WMI (dùng physical index)
        if physical_index < len(self.sbc_displays):
            try:
                display_name = self.sbc_displays[physical_index]
                brightness_list = sbc.get_brightness(display=display_name)
                brightness = brightness_list[0] if brightness_list else None
                if brightness is not None:
                    self.logger.debug(f"Monitor {monitor_id} (L{logical_index}→P{physical_index}): WMI brightness = {brightness}%")
                    return brightness
            except Exception as e:
                self.logger.error(f"Monitor {monitor_id}: WMI also failed - {e}")
        
        return None
    
    def set_brightness(self, monitor_id: str, value: int) -> bool:
        """
        Đặt độ sáng cho màn hình (Hybrid: DDC/CI hoặc WMI)
        
        Args:
            monitor_id: ID của màn hình (Monitor ID - logical)
            value: Độ sáng mới (0-100)
            
        Returns:
            True nếu thành công, False nếu thất bại
        """
        # Validate range
        value = max(0, min(100, value))
        
        logical_index = self._id_to_index(monitor_id)
        if logical_index is None:
            return False
        
        # Apply swap
        physical_index = self._apply_monitor_swap(logical_index)
        
        total_count = self.get_monitor_count()
        if physical_index < 0 or physical_index >= total_count:
            return False
        
        # Try DDC/CI first
        if physical_index < len(self.monitors):
            try:
                monitor = self.monitors[physical_index]
                with monitor:
                    monitor.set_luminance(value)
                self.logger.info(f"DDC/CI: Set brightness for {monitor_id} (L{logical_index}→P{physical_index}) to {value}%")
                return True
            except Exception as e:
                self.logger.debug(f"Monitor {monitor_id}: DDC/CI set failed - {e}")
        
        # Fallback to WMI
        if physical_index < len(self.sbc_displays):
            try:
                display_name = self.sbc_displays[physical_index]
                sbc.set_brightness(value, display=display_name)
                self.logger.info(f"WMI: Set brightness for {monitor_id} ({display_name}, L{logical_index}→P{physical_index}) to {value}%")
                return True
            except Exception as e:
                self.logger.error(f"Monitor {monitor_id}: WMI set also failed - {e}")
        
        return False
    
    def _id_to_index(self, monitor_id: str) -> Optional[int]:
        """
        Chuyển đổi monitor ID sang index.
        """
        # Format: "MONITOR_0", "MONITOR_1", etc.
        try:
            if monitor_id.startswith("MONITOR_"):
                return int(monitor_id.split("_")[1])
        except Exception:
            pass
        return None
