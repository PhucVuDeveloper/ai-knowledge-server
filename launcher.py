#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Bộ Khởi Động Động Trợ Lý AI (Dynamic Hot-Reload Launcher)
Tự động kiểm tra và tải giao diện / tính năng mới nhất từ máy chủ đám mây
mà KHÔNG cần người dùng phải tải hay đóng gói lại file .exe!
"""

import sys
import os
import time
import json
import hashlib
import shutil
import runpy
import threading
import urllib.request
import urllib.error
import tkinter as tk
from tkinter import ttk, messagebox

# Đảm bảo PyInstaller đóng gói đầy đủ các mô-đun phụ thuộc
try:
    import chatbot
    import cloud_client
    import ctypes
    from ctypes import wintypes
    import queue
except ImportError:
    pass

# Xác định đường dẫn môi trường
IS_FROZEN = getattr(sys, 'frozen', False)
if IS_FROZEN:
    EXE_DIR = os.path.dirname(sys.executable)
    BUNDLE_DIR = getattr(sys, '_MEIPASS', EXE_DIR)
else:
    EXE_DIR = os.path.dirname(os.path.abspath(__file__))
    BUNDLE_DIR = EXE_DIR

# Thư mục bộ nhớ đệm an toàn cho Hot-Reload trong %LOCALAPPDATA%
APP_DATA_DIR = os.path.join(os.environ.get("LOCALAPPDATA", os.path.expanduser("~")), "TroLyAI")
os.makedirs(APP_DATA_DIR, exist_ok=True)

CACHED_CLIENT_SCRIPT = os.path.join(APP_DATA_DIR, "app_floating_ai.py")
FALLBACK_CLIENT_SCRIPT = os.path.join(BUNDLE_DIR, "app_floating_ai.py")


def get_server_url() -> str:
    """Lấy địa chỉ máy chủ từ cấu hình cục bộ hoặc mặc định."""
    config_paths = [
        os.path.join(EXE_DIR, "server_config.json"),
        os.path.join(APP_DATA_DIR, "server_config.json"),
        os.path.join(BUNDLE_DIR, "server_config.json")
    ]
    for p in config_paths:
        if os.path.exists(p):
            try:
                with open(p, "r", encoding="utf-8") as f:
                    cfg = json.load(f)
                    url = cfg.get("server_url", "").strip()
                    if url:
                        return url.rstrip("/")
            except Exception:
                pass
    return "https://ai-knowledge-server-cdx5.onrender.com"


class SplashLoader:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("Trợ Lý AI")
        self.root.overrideredirect(True)
        self.root.attributes("-topmost", True)
        
        # Kích thước và căn giữa màn hình
        w, h = 380, 130
        sw = self.root.winfo_screenwidth()
        sh = self.root.winfo_screenheight()
        x = (sw - w) // 2
        y = (sh - h) // 2
        self.root.geometry(f"{w}x{h}+{x}+{y}")
        self.root.configure(bg="#0f172a")

        # Viền trang trí
        border = tk.Frame(self.root, bg="#38bdf8", bd=1)
        border.place(x=0, y=0, relwidth=1, relheight=1)
        
        main_frame = tk.Frame(border, bg="#0f172a")
        main_frame.place(x=1, y=1, relwidth=0.995, relheight=0.985)

        title_lbl = tk.Label(
            main_frame,
            text="🚀 TRỢ LÝ AI - TỰ ĐỘNG CẬP NHẬT",
            font=("Segoe UI", 11, "bold"),
            fg="#38bdf8",
            bg="#0f172a"
        )
        title_lbl.pack(pady=(15, 6))

        self.status_lbl = tk.Label(
            main_frame,
            text="Đang kết nối máy chủ kiểm tra phiên bản mới...",
            font=("Segoe UI", 9),
            fg="#94a3b8",
            bg="#0f172a"
        )
        self.status_lbl.pack(pady=4)

        # Thanh tiến trình
        self.progress = ttk.Progressbar(main_frame, mode="indeterminate", length=300)
        self.progress.pack(pady=(6, 10))
        self.progress.start(10)

        self.target_to_run = None
        self.finished = False

    def update_status(self, text: str, color="#94a3b8"):
        """Cập nhật văn bản thông báo trạng thái."""
        try:
            self.status_lbl.config(text=text, fg=color)
            self.root.update_idletasks()
        except Exception:
            pass

    def run_check(self):
        """Kiểm tra và tải cập nhật trong luồng nền."""
        server_url = get_server_url()
        api_url = f"{server_url}/api/client-code"

        updated = False
        try:
            req = urllib.request.Request(
                api_url,
                headers={"User-Agent": "TroLyAI-Launcher/1.0"}
            )
            # Timeout ngắn 3.5 giây để nếu máy chủ offline/chậm thì vào app ngay
            with urllib.request.urlopen(req, timeout=3.5) as response:
                if response.status == 200:
                    raw_data = response.read().decode("utf-8")
                    data = json.loads(raw_data)
                    remote_code = data.get("code", "")
                    remote_hash = data.get("hash", "")

                    if remote_code:
                        # So sánh mã băm với file hiện tại
                        local_hash = ""
                        if os.path.exists(CACHED_CLIENT_SCRIPT):
                            with open(CACHED_CLIENT_SCRIPT, "rb") as lf:
                                local_hash = hashlib.sha256(lf.read()).hexdigest()

                        if local_hash != remote_hash:
                            self.update_status("⚡ Đang cập nhật giao diện & tính năng mới...", "#38bdf8")
                            temp_file = CACHED_CLIENT_SCRIPT + ".tmp"
                            with open(temp_file, "w", encoding="utf-8") as f:
                                f.write(remote_code)
                            # Hoán đổi nguyên tử an toàn
                            if os.path.exists(CACHED_CLIENT_SCRIPT):
                                os.remove(CACHED_CLIENT_SCRIPT)
                            os.rename(temp_file, CACHED_CLIENT_SCRIPT)
                            updated = True
                            self.update_status("✅ Đã cập nhật thành công bản mới nhất!", "#10b981")
                        else:
                            self.update_status("✨ Ứng dụng đã ở phiên bản mới nhất!", "#10b981")
        except Exception as e:
            # Máy chủ offline, timeout hoặc chưa deploy endpoint
            self.update_status("⚠️ Khởi động với phiên bản đã lưu (Offline)...", "#fbbf24")

        # Xác định file script sẽ chạy
        if os.path.exists(CACHED_CLIENT_SCRIPT):
            self.target_to_run = CACHED_CLIENT_SCRIPT
        elif os.path.exists(FALLBACK_CLIENT_SCRIPT):
            self.target_to_run = FALLBACK_CLIENT_SCRIPT
        else:
            self.target_to_run = None

        time.sleep(0.5 if updated else 0.3)
        self.finished = True
        self.root.after(100, self.root.destroy)

    def start(self) -> str:
        """Hiển thị Splash và chạy kiểm tra cập nhật."""
        thread = threading.Thread(target=self.run_check, daemon=True)
        thread.start()
        self.root.mainloop()
        return self.target_to_run


def launch():
    """Hàm khởi động chính."""
    # Thêm các thư mục cần thiết vào sys.path
    for p in [BUNDLE_DIR, EXE_DIR, APP_DATA_DIR]:
        if p not in sys.path:
            sys.path.insert(0, p)

    # Hiển thị Splash Screen kiểm tra cập nhật
    loader = SplashLoader()
    script_path = loader.start()

    if not script_path or not os.path.exists(script_path):
        messagebox.showerror(
            "Lỗi Khởi Động",
            "Không tìm thấy mã nguồn giao diện Trợ Lý AI (app_floating_ai.py).\nVui lòng kiểm tra lại bộ cài đặt."
        )
        sys.exit(1)

    # Thực thi mã nguồn client với cơ chế tự phục hồi (Self-Healing Fallback)
    try:
        sys.argv[0] = script_path
        runpy.run_path(script_path, run_name="__main__")
    except Exception as e:
        # Nếu phiên bản tải về bị lỗi cú pháp, tự động phục hồi về phiên bản gốc
        if script_path == CACHED_CLIENT_SCRIPT and os.path.exists(FALLBACK_CLIENT_SCRIPT):
            try:
                os.remove(CACHED_CLIENT_SCRIPT)
            except Exception:
                pass
            messagebox.showwarning(
                "Phục Hồi An Toàn",
                f"Phiên bản cập nhật gặp sự cố: {e}\nTrợ lý AI sẽ tự động chạy phiên bản gốc ổn định."
            )
            sys.argv[0] = FALLBACK_CLIENT_SCRIPT
            runpy.run_path(FALLBACK_CLIENT_SCRIPT, run_name="__main__")
        else:
            raise e


if __name__ == "__main__":
    launch()
