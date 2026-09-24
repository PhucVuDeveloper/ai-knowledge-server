#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Ứng dụng AI Gợi Ý Câu Trả Lời & Tự Học Kiến Thức
Tính năng:
- Bôi đen câu hỏi và Giữ phím Ctrl (hoặc bấm Ctrl+Q / quét chuột) để kích hoạt popup gợi ý nổi tại chuột.
- Gợi ý câu trả lời có sẵn với tỷ lệ tin cậy (kèm nút Sao chép nhanh).
- Tự động phát hiện và lưu câu hỏi chưa biết vào danh sách chờ.
- Cho phép dạy câu trả lời mới ngay tại popup nổi!
"""

import sys
import os
import time
import queue
import threading
import ctypes
from ctypes import wintypes
import tkinter as tk
from tkinter import ttk, messagebox

# Nạp mô-đun AI và Cloud Client
from chatbot import SelfLearningAI
from cloud_client import AICloudClient

# Định nghĩa các hằng số Win32 API
VK_LBUTTON = 0x01
VK_CONTROL = 0x11
VK_Q = 0x51
KEYEVENTF_KEYUP = 0x0002

user32 = ctypes.windll.user32


class POINT(ctypes.Structure):
    _fields_ = [("x", wintypes.LONG), ("y", wintypes.LONG)]


def get_mouse_position():
    """Lấy tọa độ con trỏ chuột hiện tại trên màn hình."""
    pt = POINT()
    user32.GetCursorPos(ctypes.byref(pt))
    return pt.x, pt.y


def is_key_pressed(vk_code):
    """Kiểm tra xem một phím ảo có đang được nhấn hay không."""
    return bool(user32.GetAsyncKeyState(vk_code) & 0x8000)


def send_ctrl_c():
    """Mô phỏng phím tắt Ctrl+C để sao chép văn bản đang bôi đen vào Clipboard."""
    VK_C = 0x43
    VK_CTRL = 0x11
    # Nhả phím nếu đang giữ
    user32.keybd_event(VK_CTRL, 0, 0, 0)
    user32.keybd_event(VK_C, 0, 0, 0)
    time.sleep(0.05)
    user32.keybd_event(VK_C, 0, KEYEVENTF_KEYUP, 0)
    user32.keybd_event(VK_CTRL, 0, KEYEVENTF_KEYUP, 0)


class FloatingPopup(tk.Toplevel):
    """Cửa sổ gợi ý nổi xuất hiện tại vị trí con trỏ chuột."""
    def __init__(self, master, ai_engine: SelfLearningAI, question: str, x: int, y: int, on_knowledge_updated=None):
        super().__init__(master)
        self.ai = ai_engine
        self.question = question.strip()
        self.on_knowledge_updated = on_knowledge_updated

        # Cấu hình cửa sổ nổi luôn trên cùng, không viền thanh tiêu đề chuẩn Windows
        self.overrideredirect(True)
        self.attributes("-topmost", True)
        self.configure(bg="#1E1E2E")

        # Khung viền ngoài
        self.container = tk.Frame(self, bg="#1E1E2E", bd=2, relief="ridge", highlightbackground="#89B4FA", highlightthickness=1)
        self.container.pack(fill="both", expand=True, padx=2, pady=2)

        self.setup_ui()
        self.adjust_position(x, y)

        # Đóng popup khi nhấn phím Esc
        self.bind("<Escape>", lambda e: self.destroy())
        # Tự động lấy focus để nhận phím Esc
        self.after(50, self.focus_force)

    def setup_ui(self):
        # 1. Header bar
        header_frame = tk.Frame(self.container, bg="#181825")
        header_frame.pack(fill="x", padx=6, pady=(6, 4))

        title_lbl = tk.Label(
            header_frame,
            text="🤖  AI TRỢ LÝ GỢI Ý CÂU TRẢ LỜI",
            font=("Segoe UI", 9, "bold"),
            fg="#89B4FA",
            bg="#181825"
        )
        title_lbl.pack(side="left")

        close_btn = tk.Label(
            header_frame,
            text="✕",
            font=("Segoe UI", 10, "bold"),
            fg="#F38BA8",
            bg="#181825",
            cursor="hand2"
        )
        close_btn.pack(side="right")
        close_btn.bind("<Button-1>", lambda e: self.destroy())

        # 2. Câu hỏi đang tra cứu & Phân loại ý định
        analysis = self.ai.analyze_intent(self.question)
        self.analysis = analysis
        intent = analysis["intent"]
        core_q = analysis["core_question"]

        intent_badges = {
            "GREETING": ("🤝 Lời Chào", "#89B4FA"),
            "GRATITUDE": ("🙏 Lời Cảm Ơn", "#A6E3A1"),
            "COMPOUND_QUESTION": ("💡 Chào Hỏi & Thắc Mắc", "#F9E2AF"),
            "QUESTION": ("❓ Câu Hỏi Trực Tiếp", "#CBA6F7")
        }
        badge_text, badge_color = intent_badges.get(intent, ("❓ Câu Hỏi", "#89B4FA"))

        q_frame = tk.Frame(self.container, bg="#313244", padx=8, pady=6)
        q_frame.pack(fill="x", padx=8, pady=4)

        top_q_row = tk.Frame(q_frame, bg="#313244")
        top_q_row.pack(fill="x")

        # Huy hiệu ý định
        tk.Label(
            top_q_row,
            text=f"[{badge_text}]",
            font=("Segoe UI", 8, "bold"),
            fg=badge_color,
            bg="#313244"
        ).pack(side="left")

        display_q = (self.question[:110] + "...") if len(self.question) > 110 else self.question
        tk.Label(
            q_frame,
            text=f"\"{display_q}\"",
            font=("Segoe UI", 9, "italic"),
            fg="#CDD6F4",
            bg="#313244",
            wraplength=380,
            justify="left"
        ).pack(anchor="w", pady=(2, 0))

        # Nếu là câu kết hợp, hiển thị rõ phần cốt lõi được AI bóc tách
        if intent == "COMPOUND_QUESTION" and core_q:
            tk.Label(
                q_frame,
                text=f"🎯 Vấn đề nhận diện: \"{core_q}\"",
                font=("Segoe UI", 8, "bold"),
                fg="#A6E3A1",
                bg="#313244",
                wraplength=380,
                justify="left"
            ).pack(anchor="w", pady=(3, 0))

        # 3. Tra cứu câu trả lời trong cơ sở tri thức
        matches = self.ai.find_all_matches(self.question, limit=3, min_threshold=0.48)

        if matches:
            self.render_found_answers(matches)
        else:
            self.render_not_found()

    def render_found_answers(self, matches):
        """Hiển thị danh sách câu trả lời gợi ý khi tìm thấy."""
        res_frame = tk.Frame(self.container, bg="#1E1E2E")
        res_frame.pack(fill="both", expand=True, padx=8, pady=4)

        tk.Label(
            res_frame,
            text=f"💡 Tìm thấy {len(matches)} câu trả lời phù hợp (Click để sao chép):",
            font=("Segoe UI", 9, "bold"),
            fg="#A6E3A1",
            bg="#1E1E2E"
        ).pack(anchor="w", pady=(2, 6))

        for idx, item in enumerate(matches, 1):
            ans = item["answer"]
            conf = int(item["confidence"] * 100)

            card = tk.Frame(res_frame, bg="#2A2B3C", bd=1, relief="solid", padx=6, pady=6)
            card.pack(fill="x", pady=3)

            top_row = tk.Frame(card, bg="#2A2B3C")
            top_row.pack(fill="x")

            conf_color = "#A6E3A1" if conf >= 75 else "#F9E2AF"
            tk.Label(
                top_row,
                text=f"Phương án #{idx} ({conf}% tin cậy)",
                font=("Segoe UI", 8, "bold"),
                fg=conf_color,
                bg="#2A2B3C"
            ).pack(side="left")

            copy_btn = tk.Button(
                top_row,
                text="📋 Sao chép",
                font=("Segoe UI", 8),
                bg="#89B4FA",
                fg="#11111B",
                activebackground="#B4BEFE",
                bd=0,
                padx=6,
                pady=1,
                cursor="hand2",
                command=lambda a=ans: self.copy_answer(a)
            )
            copy_btn.pack(side="right")

            ans_lbl = tk.Label(
                card,
                text=ans,
                font=("Segoe UI", 9),
                fg="#F5E0DC",
                bg="#2A2B3C",
                wraplength=370,
                justify="left"
            )
            ans_lbl.pack(anchor="w", pady=(4, 0))
            # Cho phép click cả ô để copy
            card.bind("<Button-1>", lambda e, a=ans: self.copy_answer(a))
            ans_lbl.bind("<Button-1>", lambda e, a=ans: self.copy_answer(a))

    def render_not_found(self):
        """Hiển thị giao diện khi không tìm thấy và ô dạy học tức thì."""
        # Tự động ghi câu hỏi vào danh sách chờ
        self.ai.add_pending_question(self.question)
        if self.on_knowledge_updated:
            self.on_knowledge_updated()

        not_found_frame = tk.Frame(self.container, bg="#1E1E2E")
        not_found_frame.pack(fill="both", expand=True, padx=8, pady=4)

        warn_box = tk.Frame(not_found_frame, bg="#45475A", padx=8, pady=6)
        warn_box.pack(fill="x", pady=2)

        tk.Label(
            warn_box,
            text="⚠️  Không tìm thấy câu trả lời có sẵn!",
            font=("Segoe UI", 9, "bold"),
            fg="#F38BA8",
            bg="#45475A"
        ).pack(anchor="w")

        tk.Label(
            warn_box,
            text="✅ Hệ thống đã tự động ghi nhớ câu hỏi này vào danh sách chờ tìm câu trả lời.",
            font=("Segoe UI", 8),
            fg="#BAC2DE",
            bg="#45475A",
            wraplength=370,
            justify="left"
        ).pack(anchor="w", pady=(2, 0))

        # Khung nhập câu trả lời để dạy ngay
        teach_box = tk.LabelFrame(
            not_found_frame,
            text=" ✍️ Dạy câu trả lời cho AI ngay tại đây: ",
            font=("Segoe UI", 8, "bold"),
            fg="#F9E2AF",
            bg="#1E1E2E",
            padx=6,
            pady=6
        )
        teach_box.pack(fill="x", pady=6)

        self.ans_text = tk.Text(teach_box, height=3, font=("Segoe UI", 9), bg="#313244", fg="#CDD6F4", bd=0, insertbackground="#CDD6F4")
        self.ans_text.pack(fill="x", pady=3)
        self.ans_text.focus_set()

        save_btn = tk.Button(
            teach_box,
            text="💾 Lưu & Dạy AI Ngay",
            font=("Segoe UI", 8, "bold"),
            bg="#A6E3A1",
            fg="#11111B",
            activebackground="#94E2D5",
            bd=0,
            padx=10,
            pady=3,
            cursor="hand2",
            command=self.save_and_learn
        )
        save_btn.pack(side="right", pady=2)

    def save_and_learn(self):
        """Học kiến thức mới ngay từ popup."""
        new_ans = self.ans_text.get("1.0", tk.END).strip()
        if not new_ans:
            messagebox.showwarning("Thông báo", "Vui lòng nhập nội dung câu trả lời!")
            return

        self.ai.learn(self.question, new_ans)
        if self.on_knowledge_updated:
            self.on_knowledge_updated()

        # Cập nhật lại giao diện popup thành đã có câu trả lời
        for child in self.container.winfo_children():
            child.destroy()
        self.setup_ui()
        self.copy_answer(new_ans)

    def copy_answer(self, answer_text: str):
        """Sao chép câu trả lời vào Clipboard và hiển thị thông báo ngắn."""
        self.clipboard_clear()
        self.clipboard_append(answer_text)
        self.update()

        # Hiển thị toast thông báo
        toast = tk.Label(
            self.container,
            text="✓ Đã sao chép vào bộ nhớ tạm (Clipboard)!",
            font=("Segoe UI", 8, "bold"),
            fg="#11111B",
            bg="#A6E3A1",
            padx=6,
            pady=2
        )
        toast.pack(fill="x", padx=8, pady=(2, 6))
        self.after(1200, lambda: self.destroy())

    def adjust_position(self, mouse_x: int, mouse_y: int):
        """Định vị cửa sổ popup thông minh cạnh chuột, tránh tràn màn hình."""
        self.update_idletasks()
        w = max(self.winfo_width(), 410)
        h = max(self.winfo_height(), 180)

        screen_w = self.winfo_screenwidth()
        screen_h = self.winfo_screenheight()

        pos_x = mouse_x + 15
        pos_y = mouse_y + 15

        # Nếu bị tràn cạnh phải
        if pos_x + w > screen_w:
            pos_x = max(0, mouse_x - w - 10)

        # Nếu bị tràn cạnh dưới
        if pos_y + h > screen_h:
            pos_y = max(0, mouse_y - h - 10)

        self.geometry(f"{w}x{h}+{pos_x}+{pos_y}")


class EditKnowledgeDialog(tk.Toplevel):
    """Cửa sổ Modal hỗ trợ Thêm mới và Chỉnh sửa mục tri thức."""
    def __init__(self, master, title: str, initial_patterns: list, initial_answer: str, on_save):
        super().__init__(master)
        self.title(title)
        self.geometry("540x440")
        self.minsize(460, 380)
        self.configure(bg="#1E1E2E")
        self.on_save = on_save

        # Giữ modal luôn ở trên cửa sổ cha
        self.transient(master)
        self.grab_set()

        self.setup_ui(initial_patterns, initial_answer)

        # Nhấn Escape để đóng
        self.bind("<Escape>", lambda e: self.destroy())
        self.center_window()

    def center_window(self):
        self.update_idletasks()
        w = self.winfo_width()
        h = self.winfo_height()
        sw = self.winfo_screenwidth()
        sh = self.winfo_screenheight()
        x = (sw - w) // 2
        y = (sh - h) // 2
        self.geometry(f"{w}x{h}+{x}+{y}")

    def setup_ui(self, initial_patterns, initial_answer):
        f = tk.Frame(self, bg="#1E1E2E", padx=16, pady=14)
        f.pack(fill="both", expand=True)

        # 1. Nhãn & Ô nhập các mẫu câu hỏi
        tk.Label(
            f,
            text="Mẫu các câu hỏi tương đương (mỗi câu một dòng hoặc cách nhau bằng dấu phẩy):",
            font=("Segoe UI", 9, "bold"),
            fg="#89B4FA",
            bg="#1E1E2E"
        ).pack(anchor="w", pady=(0, 4))

        self.patterns_text = tk.Text(
            f, height=4, font=("Segoe UI", 10), bg="#313244", fg="#CDD6F4",
            bd=0, padx=8, pady=6, insertbackground="#CDD6F4"
        )
        self.patterns_text.pack(fill="x", pady=(0, 10))
        if initial_patterns:
            self.patterns_text.insert("1.0", "\n".join(initial_patterns))

        # 2. Nhãn & Ô nhập câu trả lời
        tk.Label(
            f,
            text="Nội dung câu trả lời của AI:",
            font=("Segoe UI", 9, "bold"),
            fg="#A6E3A1",
            bg="#1E1E2E"
        ).pack(anchor="w", pady=(0, 4))

        self.ans_text = tk.Text(
            f, height=8, font=("Segoe UI", 10), bg="#313244", fg="#CDD6F4",
            bd=0, padx=8, pady=6, insertbackground="#CDD6F4"
        )
        self.ans_text.pack(fill="both", expand=True, pady=(0, 12))
        if initial_answer:
            self.ans_text.insert("1.0", initial_answer)

        # 3. Nút bấm thao tác
        btn_row = tk.Frame(f, bg="#1E1E2E")
        btn_row.pack(fill="x")

        tk.Button(
            btn_row,
            text="✕ Hủy Bỏ",
            font=("Segoe UI", 9),
            bg="#45475A",
            fg="#CDD6F4",
            activebackground="#585B70",
            bd=0,
            padx=12,
            pady=5,
            cursor="hand2",
            command=self.destroy
        ).pack(side="right", padx=(6, 0))

        tk.Button(
            btn_row,
            text="💾 Lưu Tri Thức",
            font=("Segoe UI", 9, "bold"),
            bg="#A6E3A1",
            fg="#11111B",
            activebackground="#94E2D5",
            bd=0,
            padx=16,
            pady=5,
            cursor="hand2",
            command=self.save
        ).pack(side="right")

    def save(self):
        raw_patterns = self.patterns_text.get("1.0", tk.END).strip()
        ans = self.ans_text.get("1.0", tk.END).strip()

        if not raw_patterns or not ans:
            messagebox.showwarning("Cảnh báo", "Vui lòng nhập ít nhất một câu hỏi và nội dung câu trả lời!")
            return

        # Tách patterns theo dòng hoặc dấu phẩy
        patterns = []
        for line in raw_patterns.split("\n"):
            for part in line.split(","):
                part = part.strip()
                if part and part not in patterns:
                    patterns.append(part)

        if not patterns:
            messagebox.showwarning("Cảnh báo", "Vui lòng nhập ít nhất một mẫu câu hỏi hợp lệ!")
            return

        self.on_save(patterns, ans)
        self.destroy()


class GlobalMouseKeyMonitor(threading.Thread):
    """
    Tiến trình chạy nền lắng nghe tổ hợp phím và chuột toàn màn hình:
    - Khi người dùng giữ phím Ctrl và bôi đen chuột (nhả chuột trái khi Ctrl đang giữ).
    - Hoặc khi người dùng nhấn tổ hợp Ctrl + Q sau khi bôi đen bất kỳ văn bản nào.
    """
    def __init__(self, trigger_queue: queue.Queue):
        super().__init__(daemon=True)
        self.trigger_queue = trigger_queue
        self.is_running = True
        self.was_mouse_down = False
        self.last_trigger_time = 0

    def run(self):
        while self.is_running:
            time.sleep(0.04)
            now = time.time()
            if now - self.last_trigger_time < 0.8:
                continue

            ctrl_pressed = is_key_pressed(VK_CONTROL)
            lbutton_pressed = is_key_pressed(VK_LBUTTON)
            q_pressed = is_key_pressed(VK_Q)

            # Trường hợp 1: Nhấn phím tắt nhanh Ctrl + Q
            if ctrl_pressed and q_pressed:
                self.trigger_extraction()
                continue

            # Trường hợp 2: Giữ Ctrl và quét chuột (nhấn giữ chuột rồi nhả ra trong khi Ctrl vẫn giữ)
            if ctrl_pressed:
                if lbutton_pressed:
                    self.was_mouse_down = True
                elif self.was_mouse_down:
                    # Chuột trái vừa được nhả ra trong khi Ctrl vẫn đang được nhấn
                    self.was_mouse_down = False
                    self.trigger_extraction()
            else:
                self.was_mouse_down = False

    def trigger_extraction(self):
        """Mô phỏng Ctrl+C để lấy đoạn văn bản đang bôi đen và báo về GUI."""
        self.last_trigger_time = time.time()
        time.sleep(0.08)
        # Gửi tín hiệu copy
        send_ctrl_c()
        time.sleep(0.12)

        x, y = get_mouse_position()
        self.trigger_queue.put(("EXTRACT_SELECTION", x, y))

    def stop(self):
        self.is_running = False


class DashboardWindow(tk.Tk):
    """Cửa sổ ứng dụng chính: Bảng điều khiển, Quản lý tri thức và Khu vực thử nghiệm."""
    def __init__(self):
        super().__init__()
        self.title("AI Gợi Ý Câu Trả Lời & Tự Học Kiến Thức")
        self.geometry("780x560")
        self.minsize(680, 480)
        self.configure(bg="#1E1E2E")

        # Đường dẫn cơ sở dữ liệu tri thức và cấu hình máy chủ
        base_dir = os.path.dirname(os.path.abspath(__file__))
        kb_path = os.path.join(base_dir, "knowledge_base.json")
        self.config_path = os.path.join(base_dir, "server_config.json")

        saved_server_url = self.load_server_config()
        local_ai = SelfLearningAI(knowledge_file=kb_path, threshold=0.50)
        self.ai = AICloudClient(server_url=saved_server_url, local_engine=local_ai)

        # Hàng đợi giao tiếp luồng
        self.event_queue = queue.Queue()
        self.current_popup = None

        self.setup_styles()
        self.setup_ui()

        # Khởi động bộ lắng nghe chuột và phím Ctrl toàn hệ thống
        self.monitor = GlobalMouseKeyMonitor(self.event_queue)
        self.monitor.start()

        # Vòng lặp kiểm tra hàng đợi sự kiện
        self.after(100, self.process_events)
        self.protocol("WM_DELETE_WINDOW", self.on_close)

    def load_server_config(self) -> str:
        """Đọc địa chỉ Server URL đã lưu."""
        if os.path.exists(self.config_path):
            try:
                with open(self.config_path, "r", encoding="utf-8") as f:
                    cfg = json.load(f)
                    return cfg.get("server_url", "http://localhost:8000")
            except Exception:
                pass
        return "http://localhost:8000"

    def save_server_config(self, url: str):
        """Lưu lại địa chỉ Server URL."""
        try:
            with open(self.config_path, "w", encoding="utf-8") as f:
                json.dump({"server_url": url}, f, ensure_ascii=False, indent=2)
        except Exception:
            pass

    def connect_server(self):
        """Kết nối tới Server Online tập trung."""
        url = self.server_url_entry.get().strip()
        self.save_server_config(url)
        is_ok = self.ai.set_server_url(url)
        self.update_server_status_ui()
        self.refresh_learned_list()
        self.refresh_pending_list()
        if is_ok:
            messagebox.showinfo("Kết nối thành công", f"Đã kết nối thành công tới Server Online:\n{url}\n\nToàn bộ tri thức sẽ được đồng bộ dùng chung với mọi người!")
        else:
            messagebox.showwarning("Thông báo", f"Không thể kết nối tới Server: {url}\n\nỨng dụng tự động chuyển sang chế độ Cục bộ (Offline).")

    def update_server_status_ui(self):
        """Cập nhật nhãn trạng thái kết nối máy chủ."""
        if self.ai.is_online():
            self.server_status_lbl.config(
                text="🟢 ONLINE (Dùng chung)",
                fg="#A6E3A1"
            )
        else:
            self.server_status_lbl.config(
                text="🟠 CỤC BỘ (Offline)",
                fg="#FAB387"
            )

    def setup_styles(self):
        style = ttk.Style(self)
        style.theme_use("clam")
        style.configure("TNotebook", background="#181825", borderwidth=0)
        style.configure("TNotebook.Tab", background="#313244", foreground="#CDD6F4", padding=[12, 6], font=("Segoe UI", 9, "bold"))
        style.map("TNotebook.Tab", background=[("selected", "#89B4FA")], foreground=[("selected", "#11111B")])

        style.configure("Treeview", background="#313244", foreground="#CDD6F4", fieldbackground="#313244", font=("Segoe UI", 9))
        style.configure("Treeview.Heading", background="#181825", foreground="#89B4FA", font=("Segoe UI", 9, "bold"))
        style.map("Treeview", background=[("selected", "#45475A")], foreground=[("selected", "#A6E3A1")])

    def setup_ui(self):
        # 1. Header Banner
        header = tk.Frame(self, bg="#181825", pady=10, padx=16)
        header.pack(fill="x")

        title = tk.Label(
            header,
            text="⚡ AI TRỢ LÝ TỰ ĐỘNG GỢI Ý & TỰ HỌC KIẾN THỨC",
            font=("Segoe UI", 13, "bold"),
            fg="#89B4FA",
            bg="#181825"
        )
        title.pack(anchor="w")

        status_text = "🟢 Đang hoạt động | Giữ phím CTRL và bôi đen câu hỏi (hoặc bấm CTRL + Q) ở bất kỳ đâu để hiện gợi ý!"
        self.status_lbl = tk.Label(
            header,
            text=status_text,
            font=("Segoe UI", 9),
            fg="#A6E3A1",
            bg="#181825"
        )
        self.status_lbl.pack(anchor="w", pady=(3, 0))

        # Thanh kết nối Máy Chủ Online dùng chung
        server_bar = tk.Frame(header, bg="#181825", pady=6)
        server_bar.pack(fill="x", pady=(6, 0))

        tk.Label(
            server_bar,
            text="🌐 Server Online:",
            font=("Segoe UI", 9, "bold"),
            fg="#89B4FA",
            bg="#181825"
        ).pack(side="left")

        self.server_url_entry = tk.Entry(
            server_bar,
            font=("Segoe UI", 9),
            bg="#313244",
            fg="#CDD6F4",
            bd=0,
            width=36
        )
        self.server_url_entry.pack(side="left", padx=8)
        self.server_url_entry.insert(0, self.ai.server_url or "http://localhost:8000")
        self.server_url_entry.bind("<Return>", lambda e: self.connect_server())

        tk.Button(
            server_bar,
            text="🔗 Kết Nối",
            font=("Segoe UI", 8, "bold"),
            bg="#89B4FA",
            fg="#11111B",
            activebackground="#B4BEFE",
            bd=0,
            padx=10,
            pady=2,
            cursor="hand2",
            command=self.connect_server
        ).pack(side="left", padx=(0, 10))

        self.server_status_lbl = tk.Label(
            server_bar,
            text="...",
            font=("Segoe UI", 9, "bold"),
            bg="#181825"
        )
        self.server_status_lbl.pack(side="left")
        self.update_server_status_ui()

        # 2. Tabs
        self.notebook = ttk.Notebook(self)
        self.notebook.pack(fill="both", expand=True, padx=12, pady=10)

        # Tab 1: Thử nghiệm nhanh (Playground)
        self.tab_playground = tk.Frame(self.notebook, bg="#1E1E2E")
        self.notebook.add(self.tab_playground, text=" 🧪 Thử Nghiệm Nhanh ")
        self.setup_playground_tab()

        # Tab 2: Câu hỏi đã học
        self.tab_learned = tk.Frame(self.notebook, bg="#1E1E2E")
        self.notebook.add(self.tab_learned, text=" 📚 Kho Tri Thức Đã Học ")
        self.setup_learned_tab()

        # Tab 3: Câu hỏi chưa có câu trả lời (Pending)
        self.tab_pending = tk.Frame(self.notebook, bg="#1E1E2E")
        self.notebook.add(self.tab_pending, text=" ⏳ Câu Hỏi Chờ Giải Đáp ")
        self.setup_pending_tab()

    def setup_playground_tab(self):
        """Tab cho phép người dùng thử nghiệm quét chọn câu hỏi ngay trong ứng dụng."""
        f = tk.Frame(self.tab_playground, bg="#1E1E2E", padx=16, pady=12)
        f.pack(fill="both", expand=True)

        guide = (
            "👉 HƯỚNG DẪN THỬ NGHIỆM:\n"
            "1. Dùng chuột bôi đen một trong các câu hỏi mẫu bên dưới.\n"
            "2. Nhấn giữ phím CTRL (hoặc bấm tổ hợp CTRL + Q).\n"
            "3. Một cửa sổ popup gợi ý sẽ lập tức xuất hiện ngay cạnh con trỏ chuột của bạn!"
        )
        tk.Label(
            f, text=guide, font=("Segoe UI", 9), fg="#BAC2DE", bg="#313244",
            justify="left", padx=12, pady=8, bd=1, relief="solid"
        ).pack(fill="x", pady=(0, 10))

        # Text mẫu để bôi đen
        tk.Label(f, text="📝 Khung văn bản mẫu (Bạn có thể quét chuột bôi đen câu hỏi tại đây):", font=("Segoe UI", 9, "bold"), fg="#CDD6F4", bg="#1E1E2E").pack(anchor="w")

        self.sample_text = tk.Text(f, height=8, font=("Segoe UI", 10), bg="#313244", fg="#CDD6F4", bd=0, padx=8, pady=8)
        self.sample_text.pack(fill="x", pady=6)

        sample_content = (
            "- Xin chào ạ em không đăng nhập được elearning của trường ạ\n"
            "- Cảm ơn shop nhiều nhé ạ!\n"
            "- Xin chào bạn\n"
            "- Giá sản phẩm bao nhiêu tiền vậy ạ?\n"
            "- Thời gian giao hàng bao lâu?\n"
            "- Python là gì?\n"
            "- Thủ đô của Việt Nam là gì?\n"
            "- Học phí kỳ 2 đóng khi nào? (Câu này chưa có trong tri thức, thử bôi đen để AI tự học!)"
        )
        self.sample_text.insert("1.0", sample_content)

        # Ô kiểm tra thủ công bằng gõ phím
        test_frame = tk.Frame(f, bg="#1E1E2E", pady=6)
        test_frame.pack(fill="x")

        tk.Label(test_frame, text="🔍 Hoặc nhập câu hỏi để thử tìm kiếm:", font=("Segoe UI", 9, "bold"), fg="#CDD6F4", bg="#1E1E2E").pack(side="left")
        self.test_input = tk.Entry(test_frame, font=("Segoe UI", 10), bg="#313244", fg="#CDD6F4", bd=0)
        self.test_input.pack(side="left", fill="x", expand=True, padx=8)
        self.test_input.bind("<Return>", lambda e: self.trigger_manual_popup())

        test_btn = tk.Button(
            test_frame,
            text="Gợi Ý Ngay",
            font=("Segoe UI", 9, "bold"),
            bg="#89B4FA",
            fg="#11111B",
            bd=0,
            padx=10,
            pady=3,
            cursor="hand2",
            command=self.trigger_manual_popup
        )
        test_btn.pack(side="right")

    def setup_learned_tab(self):
        """Tab hiển thị danh sách câu hỏi đã học trong knowledge_base.json."""
        f = tk.Frame(self.tab_learned, bg="#1E1E2E", padx=12, pady=10)
        f.pack(fill="both", expand=True)

        columns = ("id", "patterns", "answer")
        self.tree_learned = ttk.Treeview(f, columns=columns, show="headings", height=12)
        self.tree_learned.heading("id", text="STT")
        self.tree_learned.heading("patterns", text="Mẫu câu hỏi tương đương")
        self.tree_learned.heading("answer", text="Câu trả lời")

        self.tree_learned.column("id", width=40, anchor="center")
        self.tree_learned.column("patterns", width=320)
        self.tree_learned.column("answer", width=360)

        scrollbar = ttk.Scrollbar(f, orient="vertical", command=self.tree_learned.yview)
        self.tree_learned.configure(yscrollcommand=scrollbar.set)

        self.tree_learned.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        # Thanh công cụ: Thêm, Sửa, Xóa, Làm mới
        btn_bar = tk.Frame(self.tab_learned, bg="#1E1E2E", pady=8)
        btn_bar.pack(fill="x")

        tk.Button(
            btn_bar, text="➕ Thêm Tri Thức Mới", font=("Segoe UI", 9, "bold"),
            bg="#A6E3A1", fg="#11111B", activebackground="#94E2D5", bd=0, padx=10, pady=4,
            cursor="hand2", command=self.add_new_knowledge
        ).pack(side="left", padx=(0, 6))

        tk.Button(
            btn_bar, text="✏️ Sửa Tri Thức", font=("Segoe UI", 9, "bold"),
            bg="#F9E2AF", fg="#11111B", activebackground="#FAB387", bd=0, padx=10, pady=4,
            cursor="hand2", command=self.edit_selected_knowledge
        ).pack(side="left", padx=6)

        tk.Button(
            btn_bar, text="🗑️ Xóa Tri Thức", font=("Segoe UI", 9, "bold"),
            bg="#F38BA8", fg="#11111B", activebackground="#EBA0AC", bd=0, padx=10, pady=4,
            cursor="hand2", command=self.delete_selected_knowledge
        ).pack(side="left", padx=6)

        tk.Button(
            btn_bar, text="🔄 Làm Mới", font=("Segoe UI", 9),
            bg="#89B4FA", fg="#11111B", activebackground="#B4BEFE", bd=0, padx=10, pady=4,
            cursor="hand2", command=self.refresh_learned_list
        ).pack(side="right")

        # Gán phím tắt: Nhấp đúp chuột để sửa, phím Delete để xóa
        self.tree_learned.bind("<Double-1>", lambda e: self.edit_selected_knowledge())
        self.tree_learned.bind("<Delete>", lambda e: self.delete_selected_knowledge())

        self.refresh_learned_list()

    def edit_selected_knowledge(self):
        """Mở cửa sổ chỉnh sửa mục tri thức đang được chọn."""
        sel = self.tree_learned.selection()
        if not sel:
            messagebox.showinfo("Thông báo", "Vui lòng click chọn 1 mục tri thức trong danh sách để sửa!")
            return

        item_data = self.tree_learned.item(sel[0])
        idx = int(item_data["values"][0]) - 1  # 0-indexed

        all_items = self.ai.list_all()
        if 0 <= idx < len(all_items):
            target = all_items[idx]
            EditKnowledgeDialog(
                self,
                title="✏️ Chỉnh Sửa Tri Thức",
                initial_patterns=target.get("patterns", []),
                initial_answer=target.get("answer", ""),
                on_save=lambda pats, ans: self.save_edited_knowledge(idx, pats, ans)
            )

    def save_edited_knowledge(self, index: int, patterns: list, answer: str):
        """Lưu lại nội dung sau khi chỉnh sửa."""
        if self.ai.update_knowledge_by_index(index, patterns, answer):
            self.refresh_learned_list()
            messagebox.showinfo("Thành công", "Đã cập nhật mục tri thức thành công!")
        else:
            messagebox.showerror("Lỗi", "Không thể cập nhật mục tri thức này.")

    def delete_selected_knowledge(self):
        """Xóa mục tri thức đang được chọn."""
        sel = self.tree_learned.selection()
        if not sel:
            messagebox.showinfo("Thông báo", "Vui lòng click chọn 1 mục tri thức cần xóa!")
            return

        item_data = self.tree_learned.item(sel[0])
        idx = int(item_data["values"][0]) - 1
        patterns_str = item_data["values"][1]

        confirm = messagebox.askyesno(
            "Xác nhận xóa",
            f"Bạn có chắc chắn muốn xóa mục tri thức này không?\n\nCâu hỏi: {patterns_str[:80]}..."
        )
        if confirm:
            if self.ai.delete_knowledge_by_index(idx):
                self.refresh_learned_list()
                messagebox.showinfo("Thành công", "Đã xóa mục tri thức khỏi bộ nhớ!")
            else:
                messagebox.showerror("Lỗi", "Không thể xóa mục tri thức này.")

    def add_new_knowledge(self):
        """Mở hộp thoại thêm mới tri thức."""
        EditKnowledgeDialog(
            self,
            title="➕ Thêm Tri Thức Mới",
            initial_patterns=[],
            initial_answer="",
            on_save=self.save_new_knowledge
        )

    def save_new_knowledge(self, patterns: list, answer: str):
        """Lưu mục tri thức vừa thêm mới."""
        if self.ai.add_knowledge_item(patterns, answer):
            self.refresh_learned_list()
            messagebox.showinfo("Thành công", "Đã thêm mục tri thức mới vào bộ nhớ!")
        else:
            messagebox.showerror("Lỗi", "Vui lòng nhập đầy đủ câu hỏi và câu trả lời.")

    def setup_pending_tab(self):
        """Tab hiển thị các câu hỏi được AI tự động gom lại khi không tìm thấy kết quả."""
        f = tk.Frame(self.tab_pending, bg="#1E1E2E", padx=12, pady=10)
        f.pack(fill="both", expand=True)

        info = "Danh sách câu hỏi bạn hoặc khách hàng đã hỏi nhưng AI chưa biết, được tự động lưu lại:"
        tk.Label(f, text=info, font=("Segoe UI", 9, "italic"), fg="#BAC2DE", bg="#1E1E2E").pack(anchor="w", pady=(0, 6))

        columns = ("id", "question", "hit_count")
        self.tree_pending = ttk.Treeview(f, columns=columns, show="headings", height=10)
        self.tree_pending.heading("id", text="STT")
        self.tree_pending.heading("question", text="Câu hỏi chưa có câu trả lời")
        self.tree_pending.heading("hit_count", text="Số lần hỏi")

        self.tree_pending.column("id", width=40, anchor="center")
        self.tree_pending.column("question", width=550)
        self.tree_pending.column("hit_count", width=80, anchor="center")

        self.tree_pending.pack(fill="both", expand=True)

        # Thanh công cụ quản lý câu hỏi chờ: Xóa, Xóa tất cả, Làm mới
        pending_btn_bar = tk.Frame(self.tab_pending, bg="#1E1E2E", pady=6)
        pending_btn_bar.pack(fill="x")

        tk.Button(
            pending_btn_bar, text="🗑️ Xóa Câu Đang Chọn", font=("Segoe UI", 9, "bold"),
            bg="#F38BA8", fg="#11111B", activebackground="#EBA0AC", bd=0, padx=10, pady=3,
            cursor="hand2", command=self.delete_selected_pending
        ).pack(side="left", padx=(0, 6))

        tk.Button(
            pending_btn_bar, text="🧹 Xóa Tất Cả", font=("Segoe UI", 9),
            bg="#45475A", fg="#CDD6F4", activebackground="#585B70", bd=0, padx=10, pady=3,
            cursor="hand2", command=self.clear_all_pending
        ).pack(side="left", padx=6)

        tk.Button(
            pending_btn_bar, text="🔄 Làm Mới", font=("Segoe UI", 9),
            bg="#89B4FA", fg="#11111B", activebackground="#B4BEFE", bd=0, padx=10, pady=3,
            cursor="hand2", command=self.refresh_pending_list
        ).pack(side="right")

        # Gán phím Delete để xóa nhanh câu hỏi chờ đang chọn
        self.tree_pending.bind("<Delete>", lambda e: self.delete_selected_pending())

        # Thanh thao tác dạy nhanh
        teach_bar = tk.Frame(self.tab_pending, bg="#313244", padx=8, pady=8)
        teach_bar.pack(fill="x", pady=(4, 0))

        tk.Label(teach_bar, text="Dạy câu trả lời cho câu đang chọn:", font=("Segoe UI", 9, "bold"), fg="#F9E2AF", bg="#313244").pack(side="left")
        self.pending_ans_entry = tk.Entry(teach_bar, font=("Segoe UI", 9), bg="#1E1E2E", fg="#CDD6F4", bd=0)
        self.pending_ans_entry.pack(side="left", fill="x", expand=True, padx=8)

        tk.Button(
            teach_bar, text="Lưu & Học Ngay", font=("Segoe UI", 8, "bold"),
            bg="#A6E3A1", fg="#11111B", bd=0, padx=8, pady=3,
            command=self.teach_selected_pending
        ).pack(side="right")

        self.refresh_pending_list()

    def delete_selected_pending(self):
        """Xóa câu hỏi chờ đang được chọn."""
        sel = self.tree_pending.selection()
        if not sel:
            messagebox.showinfo("Thông báo", "Vui lòng click chọn 1 câu hỏi trong danh sách chờ để xóa!")
            return

        item_data = self.tree_pending.item(sel[0])
        idx = int(item_data["values"][0]) - 1
        q_text = item_data["values"][1]

        confirm = messagebox.askyesno(
            "Xác nhận xóa",
            f"Bạn có chắc chắn muốn xóa câu hỏi chờ này không?\n\n\"{q_text}\""
        )
        if confirm:
            if self.ai.delete_pending_question_by_index(idx):
                self.refresh_pending_list()
                messagebox.showinfo("Thành công", "Đã xóa câu hỏi khỏi danh sách chờ!")
            else:
                messagebox.showerror("Lỗi", "Không thể xóa câu hỏi này.")

    def clear_all_pending(self):
        """Xóa toàn bộ câu hỏi trong danh sách chờ."""
        pending = self.ai.get_pending_questions()
        if not pending:
            messagebox.showinfo("Thông báo", "Danh sách câu hỏi chờ hiện đang trống!")
            return

        confirm = messagebox.askyesno(
            "Xác nhận xóa tất cả",
            f"Bạn có chắc chắn muốn xóa toàn bộ {len(pending)} câu hỏi trong danh sách chờ giải đáp không?"
        )
        if confirm:
            self.ai.clear_all_pending_questions()
            self.refresh_pending_list()
            messagebox.showinfo("Thành công", "Đã dọn dẹp sạch danh sách câu hỏi chờ!")

    def refresh_learned_list(self):
        """Cập nhật bảng danh sách câu hỏi đã học."""
        for item in self.tree_learned.get_children():
            self.tree_learned.delete(item)

        questions = self.ai.list_all()
        for idx, item in enumerate(questions, 1):
            patterns = " | ".join(item.get("patterns", []))
            ans = item.get("answer", "")
            self.tree_learned.insert("", "end", values=(idx, patterns, ans))

    def refresh_pending_list(self):
        """Cập nhật bảng câu hỏi đang chờ giải đáp."""
        for item in self.tree_pending.get_children():
            self.tree_pending.delete(item)

        pending = self.ai.get_pending_questions()
        for idx, item in enumerate(pending, 1):
            q = item.get("question", "")
            count = item.get("hit_count", 1)
            self.tree_pending.insert("", "end", values=(idx, q, count))

    def teach_selected_pending(self):
        """Dạy câu trả lời cho câu hỏi đang được chọn trong bảng pending."""
        sel = self.tree_pending.selection()
        if not sel:
            messagebox.showinfo("Thông báo", "Vui lòng click chọn một câu hỏi trong danh sách chờ!")
            return

        item = self.tree_pending.item(sel[0])
        q = item["values"][1]
        ans = self.pending_ans_entry.get().strip()

        if not ans:
            messagebox.showwarning("Thông báo", "Vui lòng nhập câu trả lời!")
            return

        self.ai.learn(q, ans)
        self.pending_ans_entry.delete(0, tk.END)
        self.refresh_learned_list()
        self.refresh_pending_list()
        messagebox.showinfo("Thành công", f"Đã học xong câu trả lời cho: '{q}'")

    def show_floating_popup(self, question: str, x: int, y: int):
        """Hiển thị popup nổi tại tọa độ x, y."""
        if not question or len(question.strip()) < 2:
            return

        # Đóng popup cũ nếu đang mở
        if self.current_popup and self.current_popup.winfo_exists():
            self.current_popup.destroy()

        def on_update():
            self.refresh_learned_list()
            self.refresh_pending_list()

        self.current_popup = FloatingPopup(self, self.ai, question, x, y, on_knowledge_updated=on_update)

    def trigger_manual_popup(self):
        """Kích hoạt popup thủ công từ ô nhập kiểm tra."""
        q = self.test_input.get().strip()
        if q:
            x, y = get_mouse_position()
            self.show_floating_popup(q, x, y)

    def process_events(self):
        """Đọc và xử lý các sự kiện được gửi từ luồng lắng nghe ngầm."""
        try:
            while not self.event_queue.empty():
                event_type, x, y = self.event_queue.get_nowait()
                if event_type == "EXTRACT_SELECTION":
                    # Lấy nội dung từ Clipboard vừa được copy
                    try:
                        clip_text = self.clipboard_get().strip()
                        if clip_text and len(clip_text) >= 2:
                            self.show_floating_popup(clip_text, x, y)
                    except Exception:
                        pass
        except Exception:
            pass

        self.after(100, self.process_events)

    def on_close(self):
        """Đóng ứng dụng an toàn."""
        self.monitor.stop()
        self.destroy()


def main():
    app = DashboardWindow()
    app.mainloop()


if __name__ == "__main__":
    main()
