#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Tệp kiểm thử tự động toàn diện:
- Phân tích ý định (Intent Classification): Chào, Cảm ơn, Câu hỏi kết hợp
- Bóc tách câu hỏi cốt lõi (Core Question Extraction)
- Trường hợp thực tế: "Xin chào ạ em không đăng nhập được elearning của trường ạ"
- Cơ chế tự học và lưu trữ tri thức
"""

import os
import tempfile
import json
from chatbot import SelfLearningAI


def test_intent_classification_and_learning():
    print("=" * 65)
    print("🧪 BẮT ĐẦU KIỂM THỬ: PHÂN BIỆT Ý ĐỊNH & BÓC TÁCH CÂU HỎI CỐT LÕI")
    print("=" * 65)

    with tempfile.NamedTemporaryFile(mode="w+", delete=False, suffix=".json", encoding="utf-8") as tmp:
        initial_data = {
            "questions": [
                {
                    "patterns": ["xin chào", "chào bạn", "hello"],
                    "answer": "Dạ xin chào bạn! Mình có thể hỗ trợ gì cho bạn hôm nay ạ?"
                },
                {
                    "patterns": ["cảm ơn", "cảm ơn bạn", "thanks"],
                    "answer": "Dạ không có gì ạ! Chúc bạn một ngày tốt lành."
                },
                {
                    "patterns": ["không đăng nhập được elearning của trường", "lỗi đăng nhập elearning"],
                    "answer": "Về lỗi đăng nhập e-learning, bạn hãy kiểm tra mã số sinh viên hoặc bấm 'Quên mật khẩu' để nhận lại qua email trường."
                }
            ],
            "pending_questions": []
        }
        json.dump(initial_data, tmp, ensure_ascii=False, indent=2)
        tmp_path = tmp.name

    try:
        ai = SelfLearningAI(knowledge_file=tmp_path, threshold=0.50)

        # -------------------------------------------------------------
        # TEST 1: Câu chào thuần túy
        # -------------------------------------------------------------
        print("\n[TEST 1] Kiểm tra câu chào thuần túy: 'Xin chào ạ'")
        ans1, conf1, pat1, info1 = ai.get_response("Xin chào ạ")
        print(f" -> Ý định: {info1['intent']} | Cốt lõi: '{info1['core_question']}'")
        assert info1["intent"] == "GREETING", f"Sai ý định: {info1['intent']}"
        assert "xin chào bạn" in ans1.lower(), f"Sai câu trả lời chào: {ans1}"
        print(f" -> Trả lời chuẩn xác: \"{ans1}\"")

        # -------------------------------------------------------------
        # TEST 2: Câu cảm ơn thuần túy (Kiểm tra cả trường hợp ' em cảm ơn ạ!')
        # -------------------------------------------------------------
        print("\n[TEST 2] Kiểm tra câu cảm ơn thuần túy: ' em cảm ơn ạ!'")
        ans2, conf2, pat2, info2 = ai.get_response(" em cảm ơn ạ!")
        print(f" -> Ý định: {info2['intent']} | Cốt lõi: '{info2['core_question']}'")
        assert info2["intent"] == "GRATITUDE", f"Sai ý định: {info2['intent']}"
        assert "không có gì" in ans2.lower(), f"Sai câu trả lời cảm ơn: {ans2}"
        matches_thanks = ai.find_all_matches(" em cảm ơn ạ!")
        assert len(matches_thanks) >= 1, "Không tìm thấy gợi ý cho ' em cảm ơn ạ!'"
        print(f" -> Trả lời chuẩn xác: \"{ans2}\"")
        print(f" -> Gợi ý tìm thấy: {len(matches_thanks)} phương án.")

        # -------------------------------------------------------------
        # TEST 3: Câu kết hợp: Lời chào + Vấn đề thực tế (Trường hợp của người dùng)
        # "Xin chào ạ em không đăng nhập được elearning của trường ạ"
        # -------------------------------------------------------------
        test_case_user = "Xin chào ạ em không đăng nhập được elearning của trường ạ"
        print(f"\n[TEST 3] Kiểm tra câu kết hợp của người dùng:")
        print(f"         \"{test_case_user}\"")
        ans3, conf3, pat3, info3 = ai.get_response(test_case_user)
        print(f" -> Ý định phân loại: {info3['intent']}")
        print(f" -> Vấn đề cốt lõi đã bóc tách: '{info3['core_question']}'")
        print(f" -> Có lời chào: {info3['has_greeting']}")

        # Kiểm tra AI có bóc tách đúng cốt lõi không
        assert info3["intent"] == "COMPOUND_QUESTION", f"Sai phân loại: {info3['intent']}"
        assert "không đăng nhập được elearning của trường" in info3["core_question"], \
            f"Bóc tách cốt lõi sai: '{info3['core_question']}'"

        # Kiểm tra AI KHÔNG ĐƯỢC trả lời nhầm sang câu chào đơn thuần
        assert "e-learning" in ans3 or "elearning" in ans3, f"Trả lời nhầm sang câu chào: {ans3}"
        assert ans3.startswith("Dạ chào bạn!"), f"Không có lời chào mở đầu lịch sự: {ans3}"
        print(f" -> Kết quả phản hồi: \"{ans3}\"")
        print(" -> THÀNH CÔNG: Đã phân biệt rõ ràng câu chào và vấn đề elearning, không bị nhầm lẫn!")

        # -------------------------------------------------------------
        # TEST 4: Câu kết hợp nhưng CHƯA CÓ câu trả lời trong kho tri thức
        # "Chào bạn cho em hỏi học phí kỳ 2 hạn chót khi nào ạ?"
        # -------------------------------------------------------------
        unknown_compound = "Chào bạn cho em hỏi học phí kỳ 2 hạn chót khi nào ạ?"
        print(f"\n[TEST 4] Kiểm tra câu kết hợp chưa có câu trả lời:")
        print(f"         \"{unknown_compound}\"")
        ans4, conf4, pat4, info4 = ai.get_response(unknown_compound)

        # AI phải nhận ra đây là câu hỏi kết hợp và KHÔNG ĐƯỢC trả lời bừa bằng câu chào!
        assert ans4 is None, f"Lẽ ra chưa biết câu này nhưng lại trả về: {ans4}"
        assert info4["intent"] == "COMPOUND_QUESTION"
        assert "học phí kỳ 2 hạn chót khi nào" in info4["core_question"]
        print(f" -> Bóc tách cốt lõi: '{info4['core_question']}'")
        print(" -> Xác nhận: AI không nhầm sang câu chào và báo chưa có câu trả lời.")

        # Tự động lưu vào pending_questions: Phải lưu đúng câu hỏi cốt lõi, không lưu 'chào bạn cho em hỏi'
        ai.add_pending_question(unknown_compound)
        pending_list = ai.get_pending_questions()
        assert len(pending_list) == 1, "Chưa thêm vào danh sách chờ"
        saved_q = pending_list[0]["question"]
        print(f" -> Tự động lưu vào danh sách chờ câu hỏi cốt lõi: '{saved_q}'")
        assert "học phí kỳ 2 hạn chót khi nào" in saved_q, f"Lưu sai câu hỏi chờ: {saved_q}"

        # -------------------------------------------------------------
        # TEST 5: Dạy câu trả lời cho câu hỏi này và hỏi lại
        # -------------------------------------------------------------
        print("\n[TEST 5] Dạy câu trả lời cho vấn đề học phí và hỏi lại:")
        tuition_ans = "Hạn chót đóng học phí kỳ 2 là ngày 15/04/2026 bạn nhé."
        ai.learn(unknown_compound, tuition_ans)

        ans5, conf5, pat5, info5 = ai.get_response("Em chào shop, cho em hỏi học phí kỳ 2 hạn chót khi nào ạ?")
        assert tuition_ans in ans5, f"Câu trả lời chưa khớp: {ans5}"
        print(f" -> Sau khi học, AI đã trả lời chính xác: \"{ans5}\"")

        # -------------------------------------------------------------
        # TEST 6: Kiểm tra tính năng Sửa và Xóa trong kho tri thức
        # -------------------------------------------------------------
        print("\n[TEST 6] Kiểm tra tính năng Sửa và Xóa trong kho tri thức:")
        # 6.1 Sửa mục đầu tiên (xin chào)
        ai.update_knowledge_by_index(0, ["chào đằng ấy", "hi there"], "Chào bạn mới nhé!")
        ans_edit, _, _, _ = ai.get_response("chào đằng ấy")
        assert ans_edit == "Chào bạn mới nhé!", f"Sửa tri thức thất bại: {ans_edit}"
        print(" -> Sửa tri thức (update_knowledge_by_index): THÀNH CÔNG!")

        # 6.2 Thêm tri thức mới
        ai.add_knowledge_item(["thời tiết hôm nay thế nào"], "Thời tiết hôm nay rất đẹp và mát mẻ.")
        ans_new, _, _, _ = ai.get_response("thời tiết hôm nay thế nào")
        assert "mát mẻ" in ans_new, f"Thêm tri thức mới thất bại: {ans_new}"
        print(" -> Thêm tri thức mới (add_knowledge_item): THÀNH CÔNG!")

        # 6.3 Xóa tri thức vừa thêm (mục cuối cùng)
        last_idx = len(ai.list_all()) - 1
        deleted = ai.delete_knowledge_by_index(last_idx)
        assert deleted is True, "Xóa tri thức thất bại"
        ans_deleted, _, _, _ = ai.get_response("thời tiết hôm nay thế nào")
        assert ans_deleted is None, "Mục tri thức vẫn tồn tại sau khi xóa!"
        print(" -> Xóa tri thức (delete_knowledge_by_index): THÀNH CÔNG!")

        # -------------------------------------------------------------
        # TEST 7: Kiểm tra tính năng Xóa trong danh sách câu hỏi chờ (Pending)
        # -------------------------------------------------------------
        print("\n[TEST 7] Kiểm tra tính năng Xóa trong câu hỏi chờ giải đáp:")
        ai.add_pending_question("Câu hỏi chờ mẫu số 1")
        ai.add_pending_question("Câu hỏi chờ mẫu số 2")
        assert len(ai.get_pending_questions()) == 2, "Thêm câu hỏi chờ thất bại"
        
        # 7.1 Xóa một câu hỏi chờ
        deleted_p = ai.delete_pending_question_by_index(0)
        assert deleted_p is True, "Xóa câu hỏi chờ theo index thất bại"
        assert len(ai.get_pending_questions()) == 1, "Số lượng câu hỏi chờ còn lại sai"
        print(" -> Xóa câu hỏi chờ đơn lẻ (delete_pending_question_by_index): THÀNH CÔNG!")

        # 7.2 Xóa tất cả câu hỏi chờ
        ai.clear_all_pending_questions()
        assert len(ai.get_pending_questions()) == 0, "Xóa tất cả câu hỏi chờ thất bại"
        print(" -> Xóa toàn bộ câu hỏi chờ (clear_all_pending_questions): THÀNH CÔNG!")

        print("\n" + "=" * 65)
        print("🎉 TẤT CẢ 7 BÀI TEST TOÀN DIỆN ĐÃ VƯỢT QUA 100%! 🎉")
        print("=" * 65)

    finally:
        if os.path.exists(tmp_path):
            os.remove(tmp_path)


if __name__ == "__main__":
    test_intent_classification_and_learning()
