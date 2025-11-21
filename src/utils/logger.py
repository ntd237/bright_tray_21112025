"""
Logger Setup - Cấu hình logging cho ứng dụng
(Logger Setup - Configure logging for the application)
"""

import logging
import os
from pathlib import Path
from appdirs import user_log_dir


def setup_logger(name: str = "BrightTray", level: int = logging.INFO) -> logging.Logger:
    """
    Thiết lập logger cho ứng dụng.
    (Set up logger for the application)
    
    Args:
        name: Tên logger (Logger name)
        level: Mức độ logging (Logging level)
        
    Returns:
        Logger instance đã được cấu hình
        (Configured logger instance)
    """
    # Tạo logger
    # (Create logger)
    logger = logging.getLogger(name)
    logger.setLevel(level)
    
    # Tránh duplicate handlers nếu gọi nhiều lần
    # (Avoid duplicate handlers if called multiple times)
    if logger.handlers:
        return logger
    
    # Tạo thư mục log nếu chưa tồn tại
    # (Create log directory if it doesn't exist)
    log_dir = Path(user_log_dir("BrightTray", "ntd237"))
    log_dir.mkdir(parents=True, exist_ok=True)
    
    log_file = log_dir / "bright_tray.log"
    
    # Console handler - hiển thị INFO trở lên
    # (Console handler - show INFO and above)
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)
    console_format = logging.Formatter(
        '%(asctime)s - %(levelname)s - %(message)s',
        datefmt='%H:%M:%S'
    )
    console_handler.setFormatter(console_format)
    
    # File handler - ghi tất cả vào file
    # (File handler - write everything to file)
    file_handler = logging.FileHandler(log_file, encoding='utf-8')
    file_handler.setLevel(logging.DEBUG)
    file_format = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(funcName)s:%(lineno)d - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    file_handler.setFormatter(file_format)
    
    # Thêm handlers vào logger
    # (Add handlers to logger)
    logger.addHandler(console_handler)
    logger.addHandler(file_handler)
    
    logger.info(f"Logger initialized. Log file: {log_file}")
    
    return logger
