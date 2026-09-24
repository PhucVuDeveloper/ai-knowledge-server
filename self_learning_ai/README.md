# Ứng Dụng AI Gợi Ý Câu Trả Lời & Tự Học Kiến Thức (VS Code Edition)

Dự án trợ lý AI thông minh chạy trực tiếp trên **Visual Studio Code (VS Code)** và Desktop Windows.

---

## 💻 Cách Chạy Trên Visual Studio Code (VS Code)

### Bước 1: Mở dự án trong VS Code
Thư mục dự án đã được mở sẵn trong VS Code tại đường dẫn:
```
C:\Users\phucvh\.gemini\antigravity\scratch\self_learning_ai
```

### Bước 2: Cài đặt Python (nếu VS Code hiển thị thông báo)
- Nếu góc dưới cùng bên phải VS Code hiện thông báo yêu cầu cài đặt Python, bạn chỉ cần bấm **Install**.
- Hoặc mở Microsoft Store trên máy tính, tìm **Python 3.11** hoặc **Python 3.12** và bấm **Get / Cài đặt**.

### Bước 3: Khởi chạy dự án
Có 2 cách rất đơn giản:
1. **Cách 1 (Nút Play ▶️)**:
   - Mở tệp **`main.py`** trong VS Code.
   - Nhìn lên góc trên cùng bên phải của cửa sổ soạn thảo, bấm vào nút **Play (▶️ Run Python File)**.
2. **Cách 2 (Phím F5)**:
   - Nhấn phím **F5** trên bàn phím.
   - Menu lựa chọn sẽ xuất hiện:
     - Chọn `[1]` để mở **Giao diện Nổi Desktop** (Bôi đen câu hỏi + giữ `Ctrl` hiện popup).
     - Chọn `[2]` để **Chat và tự học trực tiếp** ngay trong Terminal của VS Code.
     - Chọn `[3]` để chạy **Kiểm thử tự động**.

---

## ⚡ Các Tính Năng Đã Tích Hợp

1. **Gợi ý nổi tại chuột**: Bôi đen câu hỏi trên bất kỳ ứng dụng nào và nhấn giữ phím `Ctrl` (hoặc bấm `Ctrl + Q`) -> Popup xuất hiện ngay tại con trỏ chuột.
2. **Nút [Sao chép]**: Bấm 1 phát là nội dung được copy vào clipboard để dán vào tin nhắn chat.
3. **Phân tích ý định & Bóc tách câu hỏi cốt lõi**:
   - Tự động nhận diện câu chào, câu cảm ơn và câu kết hợp (lời chào + câu hỏi thực tế như *"Xin chào ạ em không đăng nhập được elearning của trường ạ"*).
   - Lọc bỏ từ đệm, kính ngữ và trích xuất đúng vấn đề cần giải quyết.
4. **Quản lý Kho Tri Thức (Thêm, Sửa, Xóa)**:
   - Trong Tab **📚 Kho Tri Thức Đã Học**:
     - ✏️ **Sửa Tri Thức**: Chọn câu cần sửa và bấm nút *"Sửa Tri Thức"* (hoặc nhấp đúp chuột vào hàng) để sửa mẫu câu hỏi hoặc câu trả lời.
     - 🗑️ **Xóa Tri Thức**: Chọn câu cần xóa và bấm nút *"Xóa Tri Thức"* (hoặc nhấn phím `Delete`) -> Xác nhận xóa tức thì.
     - ➕ **Thêm Tri Thức Mới**: Nhập mẫu câu hỏi và câu trả lời để dạy thủ công trực tiếp.
5. **Quản lý Câu Hỏi Chờ Giải Đáp (Dạy & Xóa)**:
   - Trong Tab **⏳ Câu Hỏi Chờ Giải Đáp**:
     - 🗑️ **Xóa Câu Đang Chọn**: Chọn câu hỏi chờ không cần thiết và bấm *"Xóa Câu Đang Chọn"* (hoặc phím `Delete`).
     - 🧹 **Xóa Tất Cả**: Xóa sạch toàn bộ danh sách câu hỏi chờ chỉ bằng 1 thao tác.
     - ✍️ **Dạy & Học Ngay**: Chọn câu hỏi chờ, nhập câu trả lời vào ô phía dưới và bấm *"Lưu & Học Ngay"* để chuyển thành tri thức chính thức.
6. **Tự động lưu câu hỏi lạ**: Nếu chưa có câu trả lời, AI tự ghi nhận vào `pending_questions` và mở ô cho bạn dạy ngay tại chỗ.
7. **Cấu hình sẵn cho VS Code**: Tệp `.vscode/launch.json` và `.vscode/settings.json` đã được cài đặt sẵn UTF-8 và chế độ gỡ lỗi (debug).
