"""
Configuration Manager - Quản lý cấu hình người dùng
"""

import json
import logging
import threading
from pathlib import Path
from typing import Dict, Any, Optional
from appdirs import user_config_dir


class ConfigManager:
    """
    Quản lý việc lưu/đọc cấu hình người dùng.
    """
    
    # Tham số cấu hình cố định ở đầu file
    CONFIG_VERSION = "1.0"
    DEFAULT_SYNC_MODE = True
    DEFAULT_GLOBAL_BRIGHTNESS = 50
    DEBOUNCE_SECONDS = 1.0  # Chờ 1 giây trước khi lưu config
    
    def __init__(self):
        """
        Khởi tạo ConfigManager
        """
        self.logger = logging.getLogger("BrightTray.ConfigManager")
        
        # Xác định đường dẫn config file
        self.config_dir = Path(user_config_dir("BrightTray", "ntd237"))
        self.config_file = self.config_dir / "config.json"
        
        # Template mặc định
        self.template_path = Path(__file__).parent.parent.parent / "resources" / "config_template.json"
        
        # Timer cho debouncing
        self._save_timer: Optional[threading.Timer] = None
        self._lock = threading.Lock()
        
        # Load config khi khởi tạo
        self.config = self.load_config()
        
        self.logger.info(f"ConfigManager initialized. Config file: {self.config_file}")
    
    def load_config(self) -> Dict[str, Any]:
        """
        Đọc cấu hình từ file. Tạo mới nếu không tồn tại.
        
        Returns:
            Dictionary chứa cấu hình
        """
        try:
            # Nếu file config tồn tại, đọc nó
            if self.config_file.exists():
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    config = json.load(f)
                
                # Validate và migrate nếu cần
                config = self._validate_and_migrate(config)
                
                self.logger.info("Config loaded successfully")
                return config
            else:
                # Tạo config mới từ template
                self.logger.info("Config file not found. Creating new config from template.")
                return self._create_default_config()
                
        except Exception as e:
            self.logger.error(f"Error loading config: {e}. Using default config.")
            return self._create_default_config()
    
    def _create_default_config(self) -> Dict[str, Any]:
        """
        Tạo cấu hình mặc định.
        
        Returns:
            Dictionary cấu hình mặc định
        """
        # Đọc từ template nếu có
        try:
            if self.template_path.exists():
                with open(self.template_path, 'r', encoding='utf-8') as f:
                    return json.load(f)
        except Exception as e:
            self.logger.warning(f"Could not load template: {e}. Using hardcoded defaults.")
        
        # Fallback: hardcoded defaults
        return {
            "version": self.CONFIG_VERSION,
            "sync_mode": self.DEFAULT_SYNC_MODE,
            "global_brightness": self.DEFAULT_GLOBAL_BRIGHTNESS,
            "per_monitor": {},
            "auto_start": False,
            "last_monitors": []
        }
    
    def _validate_and_migrate(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """
        Validate và migrate config cũ sang version mới nếu cần.
        
        Args:
            config: Config hiện tại
            
        Returns:
            Config đã được validated/migrated
        """
        # Kiểm tra version
        config_version = config.get("version", "0.0")
        
        if config_version != self.CONFIG_VERSION:
            self.logger.info(f"Migrating config from version {config_version} to {self.CONFIG_VERSION}")
            # TODO: Thêm migration logic khi có version mới
            config["version"] = self.CONFIG_VERSION
        
        # Đảm bảo các field bắt buộc tồn tại
        default_config = self._create_default_config()
        for key in default_config:
            if key not in config:
                config[key] = default_config[key]
                self.logger.debug(f"Added missing config key: {key}")
        
        return config
    
    def save_config(self, debounce: bool = True):
        """
        Lưu cấu hình vào file. Có thể debounce để tránh ghi quá nhiều.
        
        Args:
            debounce: Có dùng debouncing không
        """
        with self._lock:
            # Hủy timer cũ nếu có
            if self._save_timer is not None:
                self._save_timer.cancel()
            
            if debounce:
                # Tạo timer mới
                self._save_timer = threading.Timer(
                    self.DEBOUNCE_SECONDS,
                    self._write_config_to_file
                )
                self._save_timer.start()
            else:
                # Lưu ngay lập tức
                self._write_config_to_file()
    
    def _write_config_to_file(self):
        """
        Ghi config vào file (internal method).
        """
        try:
            # Tạo thư mục nếu chưa tồn tại
            self.config_dir.mkdir(parents=True, exist_ok=True)
            
            # Ghi file
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(self.config, f, indent=2, ensure_ascii=False)
            
            self.logger.debug("Config saved successfully")
            
        except Exception as e:
            self.logger.error(f"Error saving config: {e}")
    
    # ===== GETTERS & SETTERS =====
    
    def get(self, key: str, default: Any = None) -> Any:
        """
        Lấy giá trị config theo key.
        """
        return self.config.get(key, default)
    
    def set(self, key: str, value: Any, save: bool = True):
        """
        Đặt giá trị config và tự động lưu.
        
        Args:
            key: Key cần set
            value: Giá trị mới
            save: Có lưu ngay không
        """
        self.config[key] = value
        if save:
            self.save_config(debounce=True)
    
    # ===== SPECIFIC GETTERS/SETTERS =====
    
    @property
    def sync_mode(self) -> bool:
        """Sync mode enabled hay không (Whether sync mode is enabled)"""
        return self.config.get("sync_mode", self.DEFAULT_SYNC_MODE)
    
    @sync_mode.setter
    def sync_mode(self, value: bool):
        """Set sync mode"""
        self.set("sync_mode", value)
    
    @property
    def global_brightness(self) -> int:
        """Độ sáng toàn cục"""
        return self.config.get("global_brightness", self.DEFAULT_GLOBAL_BRIGHTNESS)
    
    @global_brightness.setter
    def global_brightness(self, value: int):
        """Set độ sáng toàn cục"""
        # Validate range
        value = max(0, min(100, value))
        self.set("global_brightness", value)
    
    def get_monitor_brightness(self, monitor_id: str) -> Optional[int]:
        """
        Lấy độ sáng của màn hình cụ thể.
        """
        return self.config.get("per_monitor", {}).get(monitor_id)
    
    def set_monitor_brightness(self, monitor_id: str, value: int):
        """
        Lưu độ sáng của màn hình cụ thể.
        """
        # Validate range
        value = max(0, min(100, value))
        
        if "per_monitor" not in self.config:
            self.config["per_monitor"] = {}
        
        self.config["per_monitor"][monitor_id] = value
        self.save_config(debounce=True)
    
    @property
    def auto_start(self) -> bool:
        """Auto-start enabled hay không"""
        return self.config.get("auto_start", False)
    
    @auto_start.setter
    def auto_start(self, value: bool):
        """Set auto-start"""
        self.set("auto_start", value)
