FROM python:3.11-slim

WORKDIR /app

# Cài đặt thư viện cần thiết
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Sao chép mã nguồn và cơ sở tri thức
COPY . .

# Mở cổng 8000
EXPOSE 8000

# Chạy FastAPI Server
CMD ["python", "server.py"]
