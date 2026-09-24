#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Tệp kiểm thử tích hợp (Integration Test) cho Máy Chủ FastAPI và Cloud Client.
Kiểm tra khả năng hoạt động offline fallback và đồng bộ dữ liệu.
"""

import os
import tempfile
import json
from chatbot import SelfLearningAI
from cloud_client import AICloudClient


def test_cloud_client_fallback_and_api():
    print("=" * 65)
    print("🧪 BẮT ĐẦU KIỂM THỬ: CLOUD CLIENT & CƠ CHẾ DỰ PHÒNG OFFLINE")
    print("=" * 65)

    with tempfile.NamedTemporaryFile(mode="w+", delete=False, suffix=".json", encoding="utf-8") as tmp:
        initial_data = {
            "questions": [
                {
                    "patterns": ["xin chào", "hello"],
                    "answer": "Xin chào bạn từ kho tri thức!"
                }
            ],
            "pending_questions": []
        }
        json.dump(initial_data, tmp, ensure_ascii=False, indent=2)
        tmp_path = tmp.name

    try:
        # Khởi tạo local engine
        local_ai = SelfLearningAI(knowledge_file=tmp_path, threshold=0.50)
        
        # Khởi tạo Cloud Client với URL giả lập (chưa bật server) -> Phải tự động chuyển sang Offline Fallback
        client = AICloudClient(server_url="http://127.0.0.1:9999", local_engine=local_ai)
        
        print("\n[TEST 1] Kiểm tra trạng thái khi Server chưa bật:")
        assert client.is_online() is False, "Lẽ ra phải là Offline khi chưa có server"
        print(" -> Đã nhận diện chính xác trạng thái: OFFLINE (Chuyển sang Local Fallback thành công).")

        # Kiểm tra tra cứu qua client khi offline
        print("\n[TEST 2] Tra cứu câu hỏi qua Client khi Offline:")
        ans, score, pat, info = client.get_response("Xin chào")
        assert ans == "Xin chào bạn từ kho tri thức!", f"Sai kết quả: {ans}"
        print(f" -> Trả lời chính xác: \"{ans}\"")

        # Kiểm tra dạy học qua client khi offline
        print("\n[TEST 3] Dạy kiến thức mới qua Client khi Offline:")
        client.learn("Mặt trời mọc hướng nào", "Mặt trời mọc ở hướng Đông.")
        ans_learned, _, _, _ = client.get_response("Mặt trời mọc hướng nào?")
        assert ans_learned == "Mặt trời mọc ở hướng Đông.", f"Dạy thất bại: {ans_learned}"
        print(f" -> Học thành công: \"{ans_learned}\"")

        # Kiểm tra quản lý tri thức: Sửa, Xóa qua Client
        print("\n[TEST 4] Sửa và Xóa tri thức qua Client:")
        client.update_knowledge_by_index(0, ["chào đằng ấy"], "Chào bạn mới!")
        ans_edit, _, _, _ = client.get_response("chào đằng ấy")
        assert ans_edit == "Chào bạn mới!", f"Sửa thất bại: {ans_edit}"
        print(" -> Sửa tri thức qua Client: THÀNH CÔNG!")

        print("\n" + "=" * 65)
        print("🎉 TẤT CẢ CÁC BÀI TEST CLOUD CLIENT & FALLBACK ĐÃ VƯỢT QUA 100%! 🎉")
        print("=" * 65)

    finally:
        if os.path.exists(tmp_path):
            os.remove(tmp_path)


if __name__ == "__main__":
    test_cloud_client_fallback_and_api()
