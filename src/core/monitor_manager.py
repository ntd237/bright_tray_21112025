"""
Monitor Manager - Quản lý phát hiện và theo dõi màn hình
(Monitor Manager - Manage monitor detection and tracking)
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
    (Manage monitor detection and change event listening)
    """
    
    def __init__(self, brightness_backend):
        """
        Khởi tạo MonitorManager.
        (Initialize MonitorManager)
        
        Args:
            brightness_backend: Instance của BrightnessBackend
                               (Instance of BrightnessBackend)
        """
        self.logger = logging.getLogger("BrightTray.MonitorManager")
        self.backend = brightness_backend
        
        # Callback khi có thay đổi màn hình
        # (Callback when monitor changes)
        self.change_callback: Optional[Callable] = None
        
        # Message pump thread
        self._message_thread: Optional[threading.Thread] = None
        self._hwnd: Optional[int] = None
        self._running = False
        
        self.logger.info("MonitorManager initialized")
    
    def get_monitors(self) -> List:
        """
        Lấy danh sách tất cả màn hình.
        (Get list of all monitors)
        
        Returns:
            List of MonitorInfo objects
        """
        return self.backend.get_all_monitors_info()
    
    def get_monitor_count(self) -> int:
        """
        Lấy số lượng màn hình.
        (Get number of monitors)
        """
        return self.backend.get_monitor_count()
    
    def refresh_monitors(self):
        """
        Làm mới danh sách màn hình.
        (Refresh monitors list)
        """
        self.backend.refresh_monitors()
        self.logger.info(f"Monitors refreshed. Count: {self.get_monitor_count()}")
    
    def listen_display_change(self, callback: Callable):
        """
        Bắt đầu lắng nghe sự kiện WM_DISPLAYCHANGE.
        (Start listening for WM_DISPLAYCHANGE events)
        
        Args:
            callback: Hàm gọi khi có thay đổi màn hình
                     (Function to call when monitors change)
        """
        self.change_callback = callback
        
        # Start message pump trong thread riêng
        # (Start message pump in separate thread)
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
        (Stop listening for events)
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
        (Windows message pump to receive WM_DISPLAYCHANGE)
        
        Chạy trong thread riêng.
        (Runs in separate thread)
        """
        try:
            # Tạo hidden window để nhận messages
            # (Create hidden window to receive messages)
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
                    # (PeekMessage doesn't block, allows checking _running)
                    msg = win32gui.PeekMessage(self._hwnd, 0, 0, win32con.PM_REMOVE)
                    if msg:
                        if msg[1][1] == win32con.WM_QUIT:
                            break
                        win32gui.TranslateMessage(msg[1])
                        win32gui.DispatchMessage(msg[1])
                    else:
                        # Không có message, sleep một chút
                        # (No message, sleep a bit)
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
        (Window procedure to handle Windows messages)
        """
        if msg == win32con.WM_DISPLAYCHANGE:
            self.logger.info("Display configuration changed!")
            
            # Làm mới danh sách monitors
            # (Refresh monitors list)
            self.refresh_monitors()
            
            # Gọi callback nếu có
            # (Call callback if exists)
            if self.change_callback:
                try:
                    self.change_callback()
                except Exception as e:
                    self.logger.error(f"Error in change callback: {e}")
            
            return 0
        
        # Default window procedure
        return win32gui.DefWindowProc(hwnd, msg, wparam, lparam)
