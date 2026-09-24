#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Máy Chủ AI Tri Thức Tập Trung (FastAPI Central Knowledge Server)
Phục vụ nhiều người dùng đồng thời, chia sẻ và đồng bộ kho tri thức thời gian thực.
"""

import os
import sys
import threading
from typing import List, Optional, Dict, Any
from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

# Nạp mô-đun AI
from chatbot import SelfLearningAI

app = FastAPI(
    title="AI Central Knowledge Base API",
    description="Máy chủ chia sẻ tri thức và trả lời tự động cho nhiều người dùng đồng thời.",
    version="2.0.0"
)

# Cho phép kết nối CORS từ mọi nguồn (Web, Desktop Client, Chrome Extension, Mobile)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Khởi tạo AI Engine với cơ chế khóa đồng bộ luồng (Thread-safe Lock)
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
KB_PATH = os.path.join(BASE_DIR, "knowledge_base.json")
ai_engine = SelfLearningAI(knowledge_file=KB_PATH, threshold=0.50)
db_lock = threading.Lock()


# -------------------------------------------------------------
# Pydantic Schemas
# -------------------------------------------------------------
class QueryRequest(BaseModel):
    question: str
    limit: Optional[int] = 3
    min_threshold: Optional[float] = 0.48


class LearnRequest(BaseModel):
    question: str
    answer: str


class KnowledgeItemSchema(BaseModel):
    patterns: List[str]
    answer: str


class PendingQuestionSchema(BaseModel):
    question: str


# -------------------------------------------------------------
# API Endpoints
# -------------------------------------------------------------

@app.get("/", response_class=HTMLResponse)
def index_dashboard():
    """Trang Web Dashboard giám sát trạng thái máy chủ."""
    with db_lock:
        total_questions = len(ai_engine.list_all())
        total_pending = len(ai_engine.get_pending_questions())

    html_content = f"""
    <!DOCTYPE html>
    <html lang="vi">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>AI Central Knowledge Server</title>
        <link href="https://fonts.googleapis.com/css2?family=Segoe+UI:wght@400;600;700&display=swap" rel="stylesheet">
        <style>
            * {{ box-sizing: border-box; margin: 0; padding: 0; }}
            body {{ font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; background-color: #0f172a; color: #f8fafc; padding: 30px 20px; }}
            .container {{ max-width: 800px; margin: 0 auto; }}
            .header {{ text-align: center; margin-bottom: 30px; }}
            .header h1 {{ font-size: 26px; color: #38bdf8; margin-bottom: 8px; }}
            .badge-online {{ display: inline-block; background-color: #10b981; color: #042f2e; padding: 4px 12px; border-radius: 20px; font-weight: 700; font-size: 13px; }}
            .stats-grid {{ display: grid; grid-template-columns: 1fr 1fr; gap: 20px; margin-bottom: 30px; }}
            .card {{ background-color: #1e293b; border-radius: 12px; padding: 20px; border: 1px solid #334155; }}
            .card h3 {{ font-size: 14px; color: #94a3b8; text-transform: uppercase; margin-bottom: 8px; }}
            .card .number {{ font-size: 36px; font-weight: 700; color: #f1f5f9; }}
            .actions {{ display: flex; gap: 12px; justify-content: center; margin-bottom: 30px; }}
            .btn {{ text-decoration: none; padding: 10px 20px; border-radius: 8px; font-weight: 600; font-size: 14px; transition: 0.2s; }}
            .btn-primary {{ background-color: #38bdf8; color: #0f172a; }}
            .btn-primary:hover {{ background-color: #7dd3fc; }}
            .btn-secondary {{ background-color: #334155; color: #f8fafc; }}
            .btn-secondary:hover {{ background-color: #475569; }}
            .api-info {{ background-color: #1e293b; border-radius: 12px; padding: 20px; border: 1px solid #334155; font-size: 14px; line-height: 1.6; }}
            .api-info code {{ background-color: #0f172a; color: #38bdf8; padding: 2px 6px; border-radius: 4px; }}
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <h1>🤖 AI Central Knowledge Base Server</h1>
                <p style="margin-bottom: 12px; color: #94a3b8;">Máy chủ chia sẻ và đồng bộ tri thức tự động đa người dùng</p>
                <span class="badge-online">● ĐANG HOẠT ĐỘNG (ONLINE)</span>
            </div>

            <div class="stats-grid">
                <div class="card">
                    <h3>📚 Tri thức đã học</h3>
                    <div class="number">{total_questions}</div>
                    <p style="color: #64748b; font-size: 13px; margin-top: 4px;">Chủ đề câu hỏi dùng chung cho toàn bộ người dùng</p>
                </div>
                <div class="card">
                    <h3>⏳ Câu hỏi chờ giải đáp</h3>
                    <div class="number" style="color: #f59e0b;">{total_pending}</div>
                    <p style="color: #64748b; font-size: 13px; margin-top: 4px;">Câu hỏi do người dùng quét qua nhưng chưa có lời giải</p>
                </div>
            </div>

            <div class="actions">
                <a href="/docs" class="btn btn-primary" target="_blank">📖 Xem Tài Liệu API (Swagger UI)</a>
                <a href="/api/knowledge" class="btn btn-secondary" target="_blank">🔍 Xem Dữ Liệu JSON</a>
            </div>

            <div class="api-info">
                <h4 style="color: #38bdf8; margin-bottom: 8px;">🔗 Hướng dẫn kết nối Desktop App:</h4>
                <p>Trong ứng dụng <code>app_floating_ai.py</code>, bạn chỉ cần nhập địa chỉ Server URL này vào ô cài đặt máy chủ trên thanh tiêu đề để chuyển sang chế độ dùng chung Online!</p>
            </div>
        </div>
    </body>
    </html>
    """
    return HTMLResponse(content=html_content)


@app.post("/api/query")
def query_knowledge(req: QueryRequest):
    """
    So khớp câu hỏi với kho tri thức tập trung:
    - Phân tích ý định (Intent Analysis).
    - Bóc tách câu hỏi cốt lõi (Core Question).
    - Trả về danh sách câu trả lời gợi ý kèm % tin cậy.
    - Nếu không tìm thấy, tự động ghi nhận vào pending_questions.
    """
    with db_lock:
        matches = ai_engine.find_all_matches(req.question, limit=req.limit, min_threshold=req.min_threshold)
        analysis = ai_engine.analyze_intent(req.question)

        # Nếu không có câu trả lời và không phải câu chào/cảm ơn đơn thuần
        if not matches and analysis["intent"] not in ["GREETING", "GRATITUDE"]:
            ai_engine.add_pending_question(req.question)

        return {
            "status": "success",
            "matches": matches,
            "analysis": analysis,
            "found": len(matches) > 0
        }


@app.post("/api/learn")
def learn_knowledge(req: LearnRequest):
    """
    Dạy kiến thức mới:
    - Cập nhật tức thì vào kho tri thức chung.
    - Tất cả người dùng khác lập tức có thể tra cứu được câu trả lời này!
    """
    q = req.question.strip()
    a = req.answer.strip()
    if not q or not a:
        raise HTTPException(status_code=400, detail="Câu hỏi và câu trả lời không được để trống")

    with db_lock:
        success = ai_engine.learn(q, a)

    if success:
        return {"status": "success", "message": f"Đã học và đồng bộ tri thức mới: '{q}'"}
    raise HTTPException(status_code=500, detail="Không thể lưu tri thức mới")


@app.get("/api/knowledge")
def get_all_knowledge():
    """Lấy danh sách tất cả các mục tri thức đã học."""
    with db_lock:
        return {
            "status": "success",
            "count": len(ai_engine.list_all()),
            "questions": ai_engine.list_all()
        }


@app.post("/api/knowledge")
def add_knowledge_item_api(req: KnowledgeItemSchema):
    """Thêm một mục tri thức mới trực tiếp."""
    with db_lock:
        success = ai_engine.add_knowledge_item(req.patterns, req.answer)
    if success:
        return {"status": "success", "message": "Đã thêm tri thức mới thành công"}
    raise HTTPException(status_code=400, detail="Dữ liệu mẫu câu hỏi hoặc câu trả lời không hợp lệ")


@app.put("/api/knowledge/{index}")
def update_knowledge_item_api(index: int, req: KnowledgeItemSchema):
    """Cập nhật một mục tri thức theo chỉ số index."""
    with db_lock:
        success = ai_engine.update_knowledge_by_index(index, req.patterns, req.answer)
    if success:
        return {"status": "success", "message": f"Đã cập nhật mục tri thức #{index}"}
    raise HTTPException(status_code=404, detail="Không tìm thấy mục tri thức với chỉ số này")


@app.delete("/api/knowledge/{index}")
def delete_knowledge_item_api(index: int):
    """Xóa một mục tri thức theo chỉ số index."""
    with db_lock:
        success = ai_engine.delete_knowledge_by_index(index)
    if success:
        return {"status": "success", "message": f"Đã xóa mục tri thức #{index}"}
    raise HTTPException(status_code=404, detail="Không tìm thấy mục tri thức với chỉ số này")


@app.get("/api/pending")
def get_all_pending():
    """Lấy danh sách tất cả các câu hỏi đang chờ giải đáp."""
    with db_lock:
        return {
            "status": "success",
            "count": len(ai_engine.get_pending_questions()),
            "pending_questions": ai_engine.get_pending_questions()
        }


@app.delete("/api/pending/all")
def clear_all_pending_api():
    """Xóa sạch toàn bộ danh sách câu hỏi chờ."""
    with db_lock:
        ai_engine.clear_all_pending_questions()
    return {"status": "success", "message": "Đã xóa toàn bộ câu hỏi chờ"}


@app.delete("/api/pending/{index}")
def delete_pending_item_api(index: int):
    """Xóa một câu hỏi chờ theo chỉ số index."""
    with db_lock:
        success = ai_engine.delete_pending_question_by_index(index)
    if success:
        return {"status": "success", "message": f"Đã xóa câu hỏi chờ #{index}"}
    raise HTTPException(status_code=404, detail="Không tìm thấy câu hỏi chờ với chỉ số này")


def start_server(host="0.0.0.0", port=8000):
    """Khởi chạy máy chủ qua Uvicorn."""
    import uvicorn
    print(f"[*] Đang khởi động AI Central Knowledge Server tại: http://{host}:{port}")
    print(f"[*] Tài liệu OpenAPI Swagger UI: http://{host}:{port}/docs")
    uvicorn.run("server:app", host=host, port=port, reload=False)


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8000))
    start_server(host="0.0.0.0", port=port)
