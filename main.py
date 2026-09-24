#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
File khởi chạy chính (Main Entry Point) tối ưu cho Visual Studio Code (VS Code).
Bạn có thể mở tệp này trong VS Code và bấm nút Run (▶️) hoặc phím F5 để chạy!
"""

import sys
import os

# Thiết lập encoding UTF-8 cho Terminal VS Code trên Windows
if sys.platform.startswith("win"):
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        pass


def show_menu():
    banner = """
=====================================================================
🤖  AI TRỢ LÝ TỰ ĐỘNG GỢI Ý & TỰ HỌC KIẾN THỨC (VS CODE EDITION)  🤖
=====================================================================
Chọn chế độ bạn muốn chạy:

 [1] ⚡ Giao diện Nổi Desktop (Quét chuột + Giữ Ctrl / Popup gợi ý)
 [2] 💬 Trò chuyện & Tự học trực tiếp trong Terminal VS Code
 [3] 🧪 Chạy Kiểm thử tự động toàn diện (Test Suite)
 [0] 🚪 Thoát
=====================================================================
"""
    print(banner)


def run_gui():
    print("[*] Đang khởi động Giao diện Nổi Desktop (Floating Assistant)...")
    print("[*] Khi ứng dụng mở lên, bạn có thể bôi đen câu hỏi và nhấn giữ phím Ctrl!")
    from app_floating_ai import main as start_gui
    start_gui()


def run_terminal_chat():
    from chatbot import run_cli
    run_cli()


def run_tests():
    from test_chatbot import test_ai_full_features
    test_ai_full_features()


def main():
    # Nếu có tham số dòng lệnh
    if len(sys.argv) > 1:
        arg = sys.argv[1].lower()
        if arg in ["--gui", "-g", "1"]:
            run_gui()
            return
        elif arg in ["--cli", "-c", "2"]:
            run_terminal_chat()
            return
        elif arg in ["--test", "-t", "3"]:
            run_tests()
            return

    # Nếu chạy trực tiếp từ nút Run (▶️) trong VS Code
    while True:
        show_menu()
        try:
            choice = input("👉 Nhập lựa chọn của bạn (1, 2, 3 hoặc 0): ").strip()
        except (KeyboardInterrupt, EOFError):
            print("\n👋 Tạm biệt bạn!")
            break

        if choice == "1":
            try:
                run_gui()
            except Exception as e:
                print(f"[!] Lỗi khi mở giao diện: {e}")
                print("[*] Chuyển sang chế độ Terminal chat...")
                run_terminal_chat()
            break
        elif choice == "2":
            run_terminal_chat()
            break
        elif choice == "3":
            run_tests()
            input("\nNhấn Enter để quay lại menu...")
        elif choice in ["0", "exit", "quit"]:
            print("👋 Đã thoát chương trình. Hẹn gặp lại!")
            break
        else:
            print("⚠️ Lựa chọn không hợp lệ, vui lòng nhập lại.")


if __name__ == "__main__":
    main()
