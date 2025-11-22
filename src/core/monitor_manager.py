"""
Monitor Manager - Quản lý phát hiện và theo dõi màn hình
"""

import logging
import threading
from typing import List, Callable, Optional
import win32api
import win32con
import win32gui


class MonitorManager:
    """
    Quản lý việc phát hiện màn hình và lắng nghe sự kiện thay đổi.
    """
    
    def __init__(self, brightness_backend):
        """
        Khởi tạo MonitorManager.
        
        Args:
            brightness_backend: Instance của BrightnessBackend
        """
        self.logger = logging.getLogger("BrightTray.MonitorManager")
        self.backend = brightness_backend
        
        # Callback khi có thay đổi màn hình
        self.change_callback: Optional[Callable] = None
        
        # Message pump thread
        self._message_thread: Optional[threading.Thread] = None
        self._hwnd: Optional[int] = None
        self._running = False
        
        self.logger.info("MonitorManager initialized")
    
    def get_monitors(self) -> List:
        """
        Lấy danh sách tất cả màn hình.
        
        Returns:
            List of MonitorInfo objects
        """
        return self.backend.get_all_monitors_info()
    
    def get_monitor_count(self) -> int:
        """
        Lấy số lượng màn hình.
        """
        return self.backend.get_monitor_count()
    
    def refresh_monitors(self):
        """
        Làm mới danh sách màn hình.
        """
        self.backend.refresh_monitors()
        self.logger.info(f"Monitors refreshed. Count: {self.get_monitor_count()}")
    
    def listen_display_change(self, callback: Callable):
        """
        Bắt đầu lắng nghe sự kiện WM_DISPLAYCHANGE.
        
        Args:
            callback: Hàm gọi khi có thay đổi màn hình
        """
        self.change_callback = callback
        
        # Start message pump trong thread riêng
        self._running = True
        self._message_thread = threading.Thread(
            target=self._message_pump,
            daemon=True,
            name="DisplayChangeListener"
        )
        self._message_thread.start()
        
        self.logger.info("Started listening for display changes")
    
    def stop_listening(self):
        """
        Dừng lắng nghe sự kiện.
        """
        self._running = False
        
        # Post quit message to message loop
        if self._hwnd:
            try:
                win32gui.PostMessage(self._hwnd, win32con.WM_QUIT, 0, 0)
            except Exception as e:
                self.logger.debug(f"Error posting quit message: {e}")
        
        self.logger.info("Stopped listening for display changes")
    
    def _message_pump(self):
        """
        Windows message pump để nhận WM_DISPLAYCHANGE.
        
        Chạy trong thread riêng
        """
        try:
            # Tạo hidden window để nhận messages
            wc = win32gui.WNDCLASS()
            wc.lpfnWndProc = self._wnd_proc
            wc.lpszClassName = "BrightTrayMonitorListener"
            wc.hInstance = win32api.GetModuleHandle(None)
            
            # Register window class
            try:
                class_atom = win32gui.RegisterClass(wc)
            except Exception as e:
                self.logger.error(f"Failed to register window class: {e}")
                return
            
            # Create window
            self._hwnd = win32gui.CreateWindow(
                class_atom,
                "BrightTray Monitor Listener",
                0,  # No style (invisible)
                0, 0, 0, 0,
                0,  # No parent
                0,  # No menu
                wc.hInstance,
                None
            )
            
            self.logger.debug(f"Created hidden window with HWND: {self._hwnd}")
            
            # Message loop
            while self._running:
                try:
                    # PeekMessage không block, cho phép check _running
                    msg = win32gui.PeekMessage(self._hwnd, 0, 0, win32con.PM_REMOVE)
                    if msg:
                        if msg[1][1] == win32con.WM_QUIT:
                            break
                        win32gui.TranslateMessage(msg[1])
                        win32gui.DispatchMessage(msg[1])
                    else:
                        # Không có message, sleep một chút
                        import time
                        time.sleep(0.1)
                except Exception as e:
                    self.logger.debug(f"Message loop error: {e}")
                    break
            
            # Cleanup
            if self._hwnd:
                try:
                    win32gui.DestroyWindow(self._hwnd)
                except Exception:
                    pass
                self._hwnd = None
            
            try:
                win32gui.UnregisterClass(class_atom, wc.hInstance)
            except Exception:
                pass
            
            self.logger.debug("Message pump stopped")
            
        except Exception as e:
            self.logger.error(f"Message pump error: {e}")
    
    def _wnd_proc(self, hwnd, msg, wparam, lparam):
        """
        Window procedure để xử lý Windows messages.
        """
        if msg == win32con.WM_DISPLAYCHANGE:
            self.logger.info("Display configuration changed!")
            
            # Làm mới danh sách monitors
            self.refresh_monitors()
            
            # Gọi callback nếu có
            if self.change_callback:
                try:
                    self.change_callback()
                except Exception as e:
                    self.logger.error(f"Error in change callback: {e}")
            
            return 0
        
        # Default window procedure
        return win32gui.DefWindowProc(hwnd, msg, wparam, lparam)
