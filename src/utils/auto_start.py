"""
Auto-Start Manager - Quản lý tự động khởi chạy cùng Windows
(Auto-Start Manager - Manage automatic startup with Windows)
"""

import logging
import os
import sys
import winreg
import subprocess
from pathlib import Path
from typing import Optional


class AutoStartManager:
    """
    Quản lý việc thêm/xóa ứng dụng khỏi Windows Startup.
    (Manage adding/removing application from Windows Startup)
    """
    
    # Tham số cấu hình
    # (Configuration parameters)
    APP_NAME = "BrightTray"
    REGISTRY_KEY_PATH = r"Software\Microsoft\Windows\CurrentVersion\Run"
    TASK_SCHEDULER_NAME = "BrightTray_AutoStart"
    
    def __init__(self):
        """
        Khởi tạo AutoStartManager.
        (Initialize AutoStartManager)
        """
        self.logger = logging.getLogger("BrightTray.AutoStartManager")
        
        # Lấy đường dẫn executable hiện tại
        # (Get current executable path)
        if getattr(sys, 'frozen', False):
            # Đang chạy từ .exe (PyInstaller)
            # (Running from .exe - PyInstaller)
            self.exe_path = sys.executable
        else:
            # Đang chạy từ Python script
            # (Running from Python script)
            self.exe_path = os.path.abspath(sys.argv[0])
        
        self.logger.info(f"AutoStartManager initialized. Executable: {self.exe_path}")
    
    def is_enabled(self) -> bool:
        """
        Kiểm tra auto-start có được bật không.
        (Check if auto-start is enabled)
        
        Returns:
            True nếu đã enabled, False nếu chưa
            (True if enabled, False otherwise)
        """
        # Kiểm tra Registry trước
        # (Check Registry first)
        if self._check_registry():
            return True
        
        # Nếu không có trong Registry, kiểm tra Task Scheduler
        # (If not in Registry, check Task Scheduler)
        if self._check_task_scheduler():
            return True
        
        return False
    
    def enable(self) -> bool:
        """
        Bật auto-start (thử Registry trước, fallback sang Task Scheduler).
        (Enable auto-start - try Registry first, fallback to Task Scheduler)
        
        Returns:
            True nếu thành công, False nếu thất bại
            (True if successful, False if failed)
        """
        self.logger.info("Enabling auto-start...")
        
        # Thử Registry method trước
        # (Try Registry method first)
        if self._enable_registry():
            self.logger.info("Auto-start enabled via Registry")
            return True
        
        # Fallback: Task Scheduler
        # (Fallback: Task Scheduler)
        self.logger.warning("Registry method failed. Trying Task Scheduler...")
        if self._enable_task_scheduler():
            self.logger.info("Auto-start enabled via Task Scheduler")
            return True
        
        self.logger.error("Failed to enable auto-start using all methods")
        return False
    
    def disable(self) -> bool:
        """
        Tắt auto-start (xóa khỏi cả Registry và Task Scheduler).
        (Disable auto-start - remove from both Registry and Task Scheduler)
        
        Returns:
            True nếu thành công, False nếu thất bại
            (True if successful, False if failed)
        """
        self.logger.info("Disabling auto-start...")
        
        success = True
        
        # Xóa khỏi Registry
        # (Remove from Registry)
        if not self._disable_registry():
            success = False
        
        # Xóa khỏi Task Scheduler
        # (Remove from Task Scheduler)
        if not self._disable_task_scheduler():
            success = False
        
        if success:
            self.logger.info("Auto-start disabled successfully")
        else:
            self.logger.warning("Auto-start disabled with some errors")
        
        return success
    
    # ===== REGISTRY METHODS =====
    
    def _check_registry(self) -> bool:
        """
        Kiểm tra app có trong Registry không.
        (Check if app is in Registry)
        """
        try:
            with winreg.OpenKey(
                winreg.HKEY_CURRENT_USER,
                self.REGISTRY_KEY_PATH,
                0,
                winreg.KEY_READ
            ) as key:
                value, _ = winreg.QueryValueEx(key, self.APP_NAME)
                return value == f'"{self.exe_path}"'
        except FileNotFoundError:
            return False
        except Exception as e:
            self.logger.debug(f"Error checking Registry: {e}")
            return False
    
    def _enable_registry(self) -> bool:
        """
        Thêm vào Registry HKCU\Software\Microsoft\Windows\CurrentVersion\Run.
        (Add to Registry HKCU\Software\Microsoft\Windows\CurrentVersion\Run)
        """
        try:
            with winreg.OpenKey(
                winreg.HKEY_CURRENT_USER,
                self.REGISTRY_KEY_PATH,
                0,
                winreg.KEY_WRITE
            ) as key:
                # Thêm path với quotes để handle spaces
                # (Add path with quotes to handle spaces)
                winreg.SetValueEx(
                    key,
                    self.APP_NAME,
                    0,
                    winreg.REG_SZ,
                    f'"{self.exe_path}"'
                )
            return True
        except Exception as e:
            self.logger.error(f"Failed to add to Registry: {e}")
            return False
    
    def _disable_registry(self) -> bool:
        """
        Xóa khỏi Registry.
        (Remove from Registry)
        """
        try:
            with winreg.OpenKey(
                winreg.HKEY_CURRENT_USER,
                self.REGISTRY_KEY_PATH,
                0,
                winreg.KEY_WRITE
            ) as key:
                winreg.DeleteValue(key, self.APP_NAME)
            return True
        except FileNotFoundError:
            # Không tồn tại → coi như đã xóa thành công
            # (Doesn't exist → consider as successfully removed)
            return True
        except Exception as e:
            self.logger.error(f"Failed to remove from Registry: {e}")
            return False
    
    # ===== TASK SCHEDULER METHODS =====
    
    def _check_task_scheduler(self) -> bool:
        """
        Kiểm tra task có tồn tại trong Task Scheduler không.
        (Check if task exists in Task Scheduler)
        """
        try:
            result = subprocess.run(
                ['schtasks', '/Query', '/TN', self.TASK_SCHEDULER_NAME],
                capture_output=True,
                text=True,
                timeout=5
            )
            return result.returncode == 0
        except Exception as e:
            self.logger.debug(f"Error checking Task Scheduler: {e}")
            return False
    
    def _enable_task_scheduler(self) -> bool:
        """
        Tạo scheduled task để chạy khi login.
        (Create scheduled task to run on login)
        """
        try:
            # Xóa task cũ nếu có
            # (Delete old task if exists)
            subprocess.run(
                ['schtasks', '/Delete', '/TN', self.TASK_SCHEDULER_NAME, '/F'],
                capture_output=True,
                timeout=5
            )
            
            # Tạo task mới với delay 10 giây sau khi login
            # (Create new task with 10 second delay after login)
            result = subprocess.run([
                'schtasks', '/Create',
                '/TN', self.TASK_SCHEDULER_NAME,
                '/TR', f'"{self.exe_path}"',
                '/SC', 'ONLOGON',
                '/DELAY', '0000:10',  # Delay 10 giây
                '/RL', 'LIMITED',     # Không cần quyền admin
                '/F'                   # Force overwrite nếu tồn tại
            ], capture_output=True, text=True, timeout=10)
            
            if result.returncode == 0:
                return True
            else:
                self.logger.error(f"schtasks failed: {result.stderr}")
                return False
                
        except Exception as e:
            self.logger.error(f"Failed to create scheduled task: {e}")
            return False
    
    def _disable_task_scheduler(self) -> bool:
        """
        Xóa scheduled task.
        (Remove scheduled task)
        """
        try:
            result = subprocess.run(
                ['schtasks', '/Delete', '/TN', self.TASK_SCHEDULER_NAME, '/F'],
                capture_output=True,
                text=True,
                timeout=5
            )
            # Return code 0 = success, hoặc task không tồn tại
            # (Return code 0 = success, or task doesn't exist)
            return True
        except Exception as e:
            self.logger.error(f"Failed to delete scheduled task: {e}")
            return False
