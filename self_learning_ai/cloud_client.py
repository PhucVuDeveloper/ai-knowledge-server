#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Bộ điều hợp kết nối Máy Chủ Đám Mây (AI Cloud Client Adapter)
Sử dụng 100% thư viện chuẩn urllib (không cần cài thêm pip requests trên máy client).
Hỗ trợ chuyển đổi mượt mà giữa chế độ Online Server và Offline Local Fallback.
"""

import json
import urllib.request
import urllib.error
from typing import Optional, List, Dict, Any, Tuple

from chatbot import SelfLearningAI


class AICloudClient:
    def __init__(self, server_url: Optional[str] = None, local_engine: Optional[SelfLearningAI] = None):
        """
        :param server_url: Địa chỉ máy chủ (vd: 'http://localhost:8000' hoặc 'https://my-ai.onrender.com')
        :param local_engine: Đối tượng SelfLearningAI dự phòng khi offline
        """
        self.server_url = server_url.rstrip("/") if server_url else ""
        self.local_engine = local_engine or SelfLearningAI()
        self._online_status = False
        if self.server_url:
            self.check_connection()

    def set_server_url(self, url: str) -> bool:
        """Cập nhật địa chỉ Server URL và kiểm tra kết nối ngay."""
        clean_url = url.strip().rstrip("/")
        self.server_url = clean_url
        if not clean_url:
            self._online_status = False
            return False
        return self.check_connection()

    def is_online(self) -> bool:
        return bool(self.server_url and self._online_status)

    def check_connection(self) -> bool:
        """Kiểm tra máy chủ có đang phản hồi không."""
        if not self.server_url:
            self._online_status = False
            return False
        try:
            req = urllib.request.Request(
                f"{self.server_url}/api/knowledge",
                headers={"User-Agent": "AIFloatingClient/2.0"},
                method="GET"
            )
            with urllib.request.urlopen(req, timeout=2.0) as resp:
                if resp.status == 200:
                    self._online_status = True
                    return True
        except Exception:
            pass
        self._online_status = False
        return False

    def _http_request(self, path: str, method: str = "GET", data: Optional[dict] = None) -> Optional[dict]:
        """Gửi request HTTP JSON tới Server."""
        if not self.is_online():
            return None
        url = f"{self.server_url}{path}"
        try:
            headers = {"User-Agent": "AIFloatingClient/2.0", "Content-Type": "application/json"}
            body = json.dumps(data).encode("utf-8") if data else None
            req = urllib.request.Request(url, data=body, headers=headers, method=method)
            with urllib.request.urlopen(req, timeout=4.0) as resp:
                if 200 <= resp.status < 300:
                    return json.loads(resp.read().decode("utf-8"))
        except urllib.error.URLError:
            self._online_status = False
        except Exception as e:
            print(f"[!] Lỗi kết nối Server ({e})")
        return None

    # -------------------------------------------------------------
    # Các hàm nghiệp vụ tương thích với SelfLearningAI
    # -------------------------------------------------------------

    def analyze_intent(self, text: str) -> Dict[str, Any]:
        """Phân tích ý định sử dụng bộ engine (tính toán nhanh tại client)."""
        return self.local_engine.analyze_intent(text)

    def find_all_matches(self, user_question: str, limit: int = 3, min_threshold: float = 0.48) -> List[Dict[str, Any]]:
        """Tìm câu trả lời gợi ý từ Server Online (hoặc cục bộ nếu offline)."""
        if self.is_online():
            payload = {"question": user_question, "limit": limit, "min_threshold": min_threshold}
            res = self._http_request("/api/query", method="POST", data=payload)
            if res and res.get("status") == "success":
                return res.get("matches", [])
        return self.local_engine.find_all_matches(user_question, limit=limit, min_threshold=min_threshold)

    def get_response(self, user_question: str) -> Tuple[Optional[str], float, str, Dict[str, Any]]:
        """Lấy câu trả lời phù hợp nhất."""
        if self.is_online():
            payload = {"question": user_question, "limit": 1}
            res = self._http_request("/api/query", method="POST", data=payload)
            if res and res.get("status") == "success":
                matches = res.get("matches", [])
                analysis = res.get("analysis", self.analyze_intent(user_question))
                if matches:
                    top = matches[0]
                    return top["answer"], top["confidence"], top["pattern"], analysis
                return None, 0.0, "", analysis

        return self.local_engine.get_response(user_question)

    def learn(self, question: str, answer: str) -> bool:
        """Dạy kiến thức mới và đồng bộ lên Server."""
        success_online = False
        if self.is_online():
            payload = {"question": question, "answer": answer}
            res = self._http_request("/api/learn", method="POST", data=payload)
            if res and res.get("status") == "success":
                success_online = True

        # Luôn lưu một bản sao cục bộ để phòng khi offline
        success_local = self.local_engine.learn(question, answer)
        return success_online or success_local

    def add_pending_question(self, question: str) -> bool:
        """Ghi nhận câu hỏi chưa có lời giải lên Server và cục bộ."""
        if self.is_online():
            payload = {"question": question}
            self._http_request("/api/query", method="POST", data=payload)
        return self.local_engine.add_pending_question(question)

    def list_all(self) -> List[Dict[str, Any]]:
        """Lấy danh sách tất cả các mục tri thức."""
        if self.is_online():
            res = self._http_request("/api/knowledge", method="GET")
            if res and res.get("status") == "success":
                return res.get("questions", [])
        return self.local_engine.list_all()

    def update_knowledge_by_index(self, index: int, patterns: List[str], answer: str) -> bool:
        """Cập nhật một mục tri thức."""
        if self.is_online():
            payload = {"patterns": patterns, "answer": answer}
            res = self._http_request(f"/api/knowledge/{index}", method="PUT", data=payload)
            if res and res.get("status") == "success":
                self.local_engine.update_knowledge_by_index(index, patterns, answer)
                return True
        return self.local_engine.update_knowledge_by_index(index, patterns, answer)

    def delete_knowledge_by_index(self, index: int) -> bool:
        """Xóa một mục tri thức."""
        if self.is_online():
            res = self._http_request(f"/api/knowledge/{index}", method="DELETE")
            if res and res.get("status") == "success":
                self.local_engine.delete_knowledge_by_index(index)
                return True
        return self.local_engine.delete_knowledge_by_index(index)

    def add_knowledge_item(self, patterns: List[str], answer: str) -> bool:
        """Thêm một mục tri thức mới."""
        if self.is_online():
            payload = {"patterns": patterns, "answer": answer}
            res = self._http_request("/api/knowledge", method="POST", data=payload)
            if res and res.get("status") == "success":
                self.local_engine.add_knowledge_item(patterns, answer)
                return True
        return self.local_engine.add_knowledge_item(patterns, answer)

    def get_pending_questions(self) -> List[Dict[str, Any]]:
        """Lấy danh sách câu hỏi chờ."""
        if self.is_online():
            res = self._http_request("/api/pending", method="GET")
            if res and res.get("status") == "success":
                return res.get("pending_questions", [])
        return self.local_engine.get_pending_questions()

    def delete_pending_question_by_index(self, index: int) -> bool:
        """Xóa câu hỏi chờ theo index."""
        if self.is_online():
            res = self._http_request(f"/api/pending/{index}", method="DELETE")
            if res and res.get("status") == "success":
                self.local_engine.delete_pending_question_by_index(index)
                return True
        return self.local_engine.delete_pending_question_by_index(index)

    def clear_all_pending_questions(self) -> bool:
        """Xóa sạch câu hỏi chờ."""
        if self.is_online():
            res = self._http_request("/api/pending/all", method="DELETE")
            if res and res.get("status") == "success":
                self.local_engine.clear_all_pending_questions()
                return True
        return self.local_engine.clear_all_pending_questions()
