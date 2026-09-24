# Hướng Dẫn Triển Khai Máy Chủ AI Lên Cloud (Hoàn Toàn Miễn Phí)

Tài liệu này hướng dẫn bạn cách đưa máy chủ **AI Central Knowledge Server** lên mạng Internet để nhiều người ở khắp mọi nơi có thể cùng kết nối, tra cứu và đóng góp tri thức chung.

---

## 🌟 Phương Án 1: Triển khai Miễn Phí lên Render.com (Khuyên dùng)
*Render.com cung cấp gói Free Web Service có hỗ trợ HTTPS bảo mật toàn cầu.*

### Các bước thực hiện:

1. **Bước 1: Đẩy mã nguồn lên GitHub**
   - Đăng nhập vào [GitHub](https://github.com/) và tạo một Repository mới (ví dụ: `ai-knowledge-server`).
   - Tải toàn bộ các tệp trong thư mục `self_learning_ai` lên Repository đó.

2. **Bước 2: Tạo Web Service trên Render**
   - Truy cập trang chủ [Render.com](https://render.com/) và đăng ký/đăng nhập bằng tài khoản GitHub.
   - Nhấn **New +** và chọn **Web Service**.
   - Chọn kho lưu trữ GitHub `ai-knowledge-server` của bạn.

3. **Bước 3: Cấu hình trên Render**
   - **Name**: `ai-knowledge-server` (hoặc tên tùy thích).
   - **Runtime**: `Python 3`.
   - **Build Command**: `pip install -r requirements.txt`.
   - **Start Command**: `python server.py`.
   - **Instance Type**: Chọn **Free**.
   - Nhấn nút **Create Web Service**.

4. **Bước 4: Nhận địa chỉ Server URL**
   - Sau khoảng 2 phút xây dựng, Render sẽ cung cấp cho bạn một đường link HTTPS công khai, ví dụ:
     ```text
     https://ai-knowledge-server-xyz.onrender.com
     ```
   - Bạn mở thử link này trên trình duyệt để thấy trang Dashboard trạng thái máy chủ!

5. **Bước 5: Kết nối Desktop App của mọi người vào Server**
   - Gửi địa chỉ link trên cho bạn bè, đồng nghiệp.
   - Trong ứng dụng Desktop `app_floating_ai.py` trên máy của họ:
     - Nhập link `https://ai-knowledge-server-xyz.onrender.com` vào ô **Server Online**.
     - Bấm nút **[🔗 Kết Nối]**.
     - Đèn trạng thái chuyển sang: `🟢 ONLINE (Dùng chung)`.
   - **Từ giờ, bất kỳ ai dạy AI một câu hỏi mới, tất cả mọi người khác đều có thể hỏi và nhận câu trả lời đó ngay lập tức!**

---

## 🏠 Phương Án 2: Chạy Server trong Mạng Nội Bộ (LAN / Wi-Fi)
*Nếu bạn chỉ muốn chia sẻ giữa các máy tính cùng bắt chung 1 mạng Wi-Fi (trong nhà hoặc văn phòng):*

1. Trên máy tính chủ (máy của bạn), nhấp đúp chạy tệp: **`run_server.bat`**.
2. Tìm địa chỉ IP máy tính của bạn:
   - Mở PowerShell và gõ: `ipconfig`
   - Tìm dòng **IPv4 Address**, ví dụ: `192.168.1.15`.
3. Trên các máy tính khác trong cùng Wi-Fi:
   - Mở ứng dụng Desktop, nhập địa chỉ: `http://192.168.1.15:8000`
   - Bấm **Kết Nối** là xong!
