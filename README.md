# BrightTray

**Monitor Brightness Control via System Tray** - Công cụ điều khiển độ sáng màn hình qua System Tray trên Windows

![BrightTray Icon](resources/icon.png)

---

## 📋 Tính Năng (Features)

- ✅ **Điều khiển độ sáng qua DDC/CI** - Hỗ trợ màn hình rời qua giao thức DDC/CI
- ✅ **Đa màn hình** - Phát hiện tự động và hỗ trợ nhiều màn hình
- ✅ **Sync Mode** - Điều chỉnh đồng bộ tất cả màn hình cùng lúc
- ✅ **Individual Mode** - Điều chỉnh riêng lẻ từng màn hình
- ✅ **Auto-Start** - Tự động khởi chạy cùng Windows
- ✅ **Hot-Plug Support** - Tự động cập nhật khi cắm/tháo màn hình
- ✅ **Chạy nền** - Chỉ hiện system tray icon, không cửa sổ chính

---

## 🚀 Cài Đặt (Installation)

### Cách 1: Sử dụng .exe (Recommended)

1. Download file `BrightTray.exe` từ [Releases](https://github.com/ntd237/bright_tray_21112025/releases)
2. Chạy `BrightTray.exe`
3. Icon sẽ xuất hiện trong system tray
4. Right-click icon để mở menu

### Cách 2: Chạy từ source code

**Yêu cầu (Requirements):**
- Python 3.8+
- Windows 10/11

**Các bước:**

```bash
# Clone repository
git clone https://github.com/ntd237/bright_tray_21112025.git
cd bright_tray_21112025

# Tạo virtual environment (optional nhưng recommended)
python -m venv venv
venv\Scripts\activate

# Cài dependencies
pip install -r requirements.txt

# Chạy ứng dụng
python main.py
```

---

## 📖 Hướng Dẫn Sử Dụng (Usage)

### Menu System Tray

Right-click vào icon trong system tray để mở menu:

```
BrightTray
├── ☑ Sync all monitors      [Toggle sync mode]
├── Global Brightness →       [Nếu sync mode bật]
│   ├── 0%
│   ├── 25%
│   ├── ● 50%                 [Mức hiện tại]
│   ├── 75%
│   └── 100%
├── Primary Monitor →         [Nếu sync mode tắt]
│   ├── 0%
│   ├── ● 60%
│   └── ...
├── Monitor 2 →
│   └── [Tương tự...]
├── ─────────────────
├── ☑ Start with Windows     [Tự động khởi chạy]
├── About
└── Exit
```

### Sync Mode vs Individual Mode

- **Sync Mode** (mặc định): Tất cả màn hình cùng độ sáng
  - Click vào preset (0%, 25%, 50%, 75%, 100%)
  - Tất cả màn hình sẽ đổi cùng lúc

- **Individual Mode**: Mỗi màn hình có độ sáng riêng
  - Uncheck "Sync all monitors"
  - Chọn màn hình muốn điều chỉnh
  - Click preset tương ứng

### Auto-Start

- Check "Start with Windows" để tự khởi chạy khi login
- Ứng dụng sẽ được thêm vào Registry hoặc Task Scheduler (có delay 10s)

---

## 🔧 Build từ Source (Build from Source)

```bash
# Cài dependencies
pip install -r requirements.txt

# Build .exe
python build.py

# Output sẽ ở trong dist/BrightTray.exe
```

---

## ❗ Troubleshooting

### Màn hình không điều chỉnh được độ sáng

**Nguyên nhân:** Màn hình không hỗ trợ DDC/CI hoặc DDC/CI bị tắt trong OSD.

**Giải pháp:**
1. Vào OSD (On-Screen Display) menu của màn hình
2. Tìm setting "DDC/CI" hoặc "External Control"
3. Bật DDC/CI
4. Restart BrightTray

### Menu hiển thị "[No DDC/CI]"

Màn hình này không hỗ trợ DDC/CI. Một số màn hình laptop integrated không hỗ trợ.

### Windows Defender cảnh báo

File .exe chưa được code signing nên Windows Defender có thể cảnh báo.

**Giải pháp:**
1. Click "More info" → "Run anyway"
2. Hoặc thêm vào exclusion list trong Windows Security

### Tray icon không hiện

Kiểm tra Windows taskbar settings:
1. Right-click taskbar → Taskbar settings
2. Tìm "BrightTray" trong "Hidden icons"
3. Enable hiển thị icon

---

## 🛠️ Tech Stack

| Thư viện | Mục đích |
|----------|----------|
| [monitorcontrol](https://github.com/newAM/monitorcontrol) | DDC/CI communication |
| [pystray](https://github.com/moses-palmer/pystray) | System tray icon |
| [Pillow](https://python-pillow.org/) | Image processing |
| [pywin32](https://github.com/mhammond/pywin32) | Windows API |
| [appdirs](https://github.com/ActiveState/appdirs) | Config directory |

---

## 📁 Cấu Trúc Dự Án (Project Structure)

```
bright_tray_21112025/
├── main.py                      # Entry point
├── build.py                     # Build script
├── requirements.txt
├── README.md
│
├── src/
│   ├── core/
│   │   ├── monitor_manager.py   # Phát hiện & quản lý màn hình
│   │   ├── brightness_backend.py # DDC/CI wrapper
│   │   └── brightness_controller.py # Logic điều khiển
│   │
│   ├── ui/
│   │   └── tray_icon.py         # System tray UI
│   │
│   ├── config/
│   │   └── config_manager.py    # Config management
│   │
│   └── utils/
│       ├── auto_start.py        # Auto-start management
│       └── logger.py            # Logging setup
│
└── resources/
    ├── icon.png                 # Tray icon
    └── config_template.json     # Default config
```

---

## 🔒 Quyền Riêng Tư (Privacy)

- ✅ **Không thu thập dữ liệu** - Chạy hoàn toàn local
- ✅ **Không kết nối internet** - Không có network requests
- ✅ **Config được lưu local** tại `%APPDATA%\BrightTray\config.json`
- ✅ **Logs được lưu local** tại `%LOCALAPPDATA%\ntd237\BrightTray\Logs\`

---

## 📝 License

MIT License - see [LICENSE](LICENSE) file for details.

---

## 👤 Author

**ntd237**
- Email: ntd237.work@gmail.com
- GitHub: [@ntd237](https://github.com/ntd237)

---

## 🙏 Acknowledgments

- [monitorcontrol](https://github.com/newAM/monitorcontrol) - DDC/CI library
- [pystray](https://github.com/moses-palmer/pystray) - System tray library
- Inspiration from [Twinkle Tray](https://twinkletray.com/) và [Monitorian](https://github.com/emoacht/Monitorian)

---

## 📮 Support & Feedback

Nếu có vấn đề hoặc đề xuất tính năng, vui lòng [tạo issue](https://github.com/ntd237/bright_tray_21112025/issues) trên GitHub.

**Enjoy! 🌟**
