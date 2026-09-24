#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Hệ thống AI Tự Động Trả Lời & Tự Học Kiến Thức
Mô-đun lõi: Xử lý ngôn ngữ, Phân loại ý định (Intent Classification),
So khớp thông minh và Quản lý cơ sở tri thức.
"""

import json
import os
import re
import difflib
from typing import Optional, Tuple, List, Dict, Any


class SelfLearningAI:
    # Danh sách các mẫu lời chào tiếng Việt và tiếng Anh
    GREETING_PATTERNS = [
        r"\bxin chào\b", r"\bchào bạn\b", r"\bchào shop\b", r"\bchào ad\b",
        r"\bchào admin\b", r"\bchào anh\b", r"\bchào chị\b", r"\bchào thầy\b",
        r"\bchào cô\b", r"\bchào\b", r"\bhello\b", r"\bhi\b", r"\balo\b",
        r"\bgood morning\b", r"\bgood afternoon\b"
    ]

    # Danh sách các mẫu lời cảm ơn
    GRATITUDE_PATTERNS = [
        r"\bcảm ơn\b", r"\bcam on\b", r"\bcám ơn\b", r"\bthank you\b",
        r"\bthanks\b", r"\bthank\b", r"\bđã giúp đỡ\b"
    ]

    # Các từ đệm, kính ngữ, đại từ nhân xưng tiếng Việt cần lọc sạch để lấy câu hỏi cốt lõi
    FILLER_PREFIXES = [
        r"^(dạ\s+|vâng\s+)+",
        r"^(cho\s+em\s+hỏi\s+|cho\s+mình\s+hỏi\s+|cho\s+hỏi\s+)+",
        r"^(em\s+muốn\s+hỏi\s+|mình\s+muốn\s+hỏi\s+)+",
        r"^(ad\s+cho\s+hỏi\s+|bạn\s+ơi\s+|ad\s+ơi\s+|thầy\s+ơi\s+|cô\s+ơi\s+)+",
        r"^(em\s+|mình\s+|tôi\s+)"
    ]

    FILLER_SUFFIXES = [
        r"(\s+giúp\s+em\s+với\s+ạ|\s+giúp\s+em\s+với|\s+với\s+ạ|\s+với\s+nha|\s+với|\s+nhé|\s+nha)+$",
        r"(\s+được\s+không\s+ạ|\s+được\s+không|\s+thế\s+ạ|\s+vậy\s+ạ|\s+ạ)+$"
    ]

    def __init__(self, knowledge_file: str = "knowledge_base.json", threshold: float = 0.50):
        """
        Khởi tạo AI tự học.
        :param knowledge_file: Đường dẫn tệp lưu trữ cơ sở tri thức JSON.
        :param threshold: Ngưỡng tin cậy (0.0 đến 1.0) để quyết định chấp nhận câu trả lời.
        """
        self.knowledge_file = knowledge_file
        self.threshold = threshold
        self.knowledge = self.load_knowledge()

    def load_knowledge(self) -> Dict[str, Any]:
        """Nạp tri thức từ tệp JSON."""
        default_data = {"questions": [], "pending_questions": []}
        if not os.path.exists(self.knowledge_file):
            return default_data
        try:
            with open(self.knowledge_file, "r", encoding="utf-8") as f:
                data = json.load(f)
                if not isinstance(data, dict):
                    return default_data
                data.setdefault("questions", [])
                data.setdefault("pending_questions", [])
                return data
        except Exception as e:
            print(f"[!] Lỗi khi đọc tệp tri thức ({e}). Khởi tạo kho mới.")
            return default_data

    def save_knowledge(self) -> bool:
        """Lưu toàn bộ tri thức vào tệp JSON."""
        try:
            with open(self.knowledge_file, "w", encoding="utf-8") as f:
                json.dump(self.knowledge, f, ensure_ascii=False, indent=2)
            return True
        except Exception as e:
            print(f"[!] Lỗi khi lưu tri thức: {e}")
            return False

    @staticmethod
    def preprocess_text(text: str) -> str:
        """
        Chuẩn hóa văn bản cơ bản:
        - Chữ thường, bỏ dấu câu và khoảng trắng dư thừa
        """
        if not text:
            return ""
        text = text.lower().strip()
        text = re.sub(r"[?!.,;:\"'’‘()\[\]{}_+\\-]", " ", text)
        text = re.sub(r"\s+", " ", text).strip()
        return text

    def analyze_intent(self, text: str) -> Dict[str, Any]:
        """
        Phân tích ý định người dùng (Intent Analysis) & Bóc tách câu hỏi cốt lõi:
        - Nhận diện: GREETING (Câu chào thuần), GRATITUDE (Câu cảm ơn thuần),
                     COMPOUND_QUESTION (Lời chào/cảm ơn + Câu hỏi thực tế),
                     QUESTION (Câu hỏi trực tiếp).
        - Trích xuất: core_question (vấn đề cốt lõi đã loại bỏ chào hỏi, kính ngữ).
        """
        raw = text.strip()
        cleaned = self.preprocess_text(raw)

        if not cleaned:
            return {
                "intent": "EMPTY",
                "core_question": "",
                "has_greeting": False,
                "has_gratitude": False,
                "greeting_phrase": ""
            }

        # 1. Kiểm tra sự xuất hiện của lời chào
        has_greeting = False
        greeting_phrase = ""
        for pat in self.GREETING_PATTERNS:
            m = re.search(pat, cleaned)
            if m:
                has_greeting = True
                greeting_phrase = m.group(0)
                break

        # 2. Kiểm tra sự xuất hiện của lời cảm ơn
        has_gratitude = False
        for pat in self.GRATITUDE_PATTERNS:
            if re.search(pat, cleaned):
                has_gratitude = True
                break

        # 3. Bóc tách câu hỏi cốt lõi (Core Question) bằng vòng lặp bóc tách tuần tự
        working_text = cleaned
        changed = True
        while changed:
            before = working_text
            # Lọc bỏ từ đệm / đại từ nhân xưng ở đầu câu (em, mình, cho em hỏi, dạ, vâng, ad ơi...)
            for pat in self.FILLER_PREFIXES:
                working_text = re.sub(pat, "", working_text).strip()
            # Lọc bỏ lời chào ở đầu câu
            for pat in self.GREETING_PATTERNS:
                working_text = re.sub(r"^" + pat + r"\s*", "", working_text).strip()
            # Lọc bỏ lời cảm ơn ở đầu hoặc cuối câu
            for pat in self.GRATITUDE_PATTERNS:
                working_text = re.sub(r"^" + pat + r"\s*", "", working_text).strip()
                working_text = re.sub(r"\s*" + pat + r"$", "", working_text).strip()
            # Lọc bỏ từ đệm / kính ngữ ở cuối câu (ạ, nhé, nha, với ạ, giúp em với...)
            for pat in self.FILLER_SUFFIXES:
                working_text = re.sub(pat, "", working_text).strip()

            changed = (working_text != before)

        core_question = working_text.strip()

        # 4. Xác định phân loại ý định (Intent Classification)
        # Nếu sau khi loại bỏ chào, cảm ơn và từ đệm mà phần còn lại rỗng hoặc quá ngắn (dưới 3 ký tự)
        if len(core_question) < 3:
            if has_gratitude:
                intent = "GRATITUDE"
                core_question = "cảm ơn"
            elif has_greeting:
                intent = "GREETING"
                core_question = "xin chào"
            else:
                intent = "QUESTION"
        else:
            # Còn lại phần nội dung câu hỏi thực sự
            if has_greeting or has_gratitude:
                intent = "COMPOUND_QUESTION"
            else:
                intent = "QUESTION"

        return {
            "intent": intent,
            "core_question": core_question,
            "has_greeting": has_greeting,
            "has_gratitude": has_gratitude,
            "greeting_phrase": greeting_phrase
        }

    def calculate_similarity(self, s1: str, s2: str) -> float:
        """
        Tính toán độ tương đồng giữa 2 câu:
        Kết hợp SequenceMatcher và Jaccard Index tập từ.
        """
        p1 = self.preprocess_text(s1)
        p2 = self.preprocess_text(s2)

        if not p1 or not p2:
            return 0.0

        if p1 == p2:
            return 1.0

        seq_ratio = difflib.SequenceMatcher(None, p1, p2).ratio()

        tokens1 = set(p1.split())
        tokens2 = set(p2.split())
        intersection = tokens1.intersection(tokens2)
        union = tokens1.union(tokens2)
        jaccard_ratio = len(intersection) / len(union) if union else 0.0

        combined = (0.5 * seq_ratio) + (0.5 * jaccard_ratio)

        if tokens1 and tokens2:
            min_len = min(len(tokens1), len(tokens2))
            overlap_ratio = len(intersection) / min_len
            if tokens1.issubset(tokens2) or tokens2.issubset(tokens1):
                combined = max(combined, 0.70 + 0.30 * overlap_ratio)
            elif overlap_ratio >= 0.75:
                combined = max(combined, 0.65 + 0.25 * overlap_ratio)

        return round(min(combined, 1.0), 3)

    def find_all_matches(self, user_question: str, limit: int = 3, min_threshold: Optional[float] = None) -> List[Dict[str, Any]]:
        """
        Tìm tất cả các câu trả lời gợi ý phù hợp dựa trên ý định và câu hỏi cốt lõi.
        """
        if min_threshold is None:
            min_threshold = self.threshold

        analysis = self.analyze_intent(user_question)
        intent = analysis["intent"]
        core_q = analysis["core_question"]
        has_greeting = analysis["has_greeting"]

        # Nếu là câu chào thuần túy: Tra cứu mẫu chào
        if intent == "GREETING":
            core_q = "xin chào"
        # Nếu là câu cảm ơn thuần túy: Tra cứu mẫu cảm ơn
        elif intent == "GRATITUDE":
            core_q = "cảm ơn"

        results = []
        seen_answers = set()

        for item in self.knowledge.get("questions", []):
            ans = item.get("answer", "")
            if not ans or ans in seen_answers:
                continue

            patterns = item.get("patterns", [])

            # Nếu đây là câu hỏi kết hợp (có thắc mắc thực sự), loại bỏ các câu trả lời chỉ là chào/cảm ơn đơn thuần
            if intent in ["COMPOUND_QUESTION", "QUESTION"]:
                is_pure_greeting_item = any(p in ["xin chào", "chào bạn", "hello", "hi"] for p in patterns)
                is_pure_gratitude_item = any(p in ["cảm ơn", "thanks", "thank you", "cảm ơn bạn"] for p in patterns)
                if is_pure_greeting_item or is_pure_gratitude_item:
                    continue

            # Nếu là câu chào thuần túy: Ưu tiên mục tri thức có chứa lời chào
            if intent == "GREETING":
                is_greeting_item = any(re.search(pat, p) for p in patterns for pat in self.GREETING_PATTERNS)
                if not is_greeting_item:
                    continue

            # Nếu là câu cảm ơn thuần túy: Ưu tiên mục tri thức có chứa lời cảm ơn
            if intent == "GRATITUDE":
                is_gratitude_item = any(re.search(pat, p) for p in patterns for pat in self.GRATITUDE_PATTERNS)
                if not is_gratitude_item:
                    continue

            best_item_score = 0.0
            best_item_pattern = ""

            for pat in patterns:
                score = self.calculate_similarity(core_q, pat)
                if score > best_item_score:
                    best_item_score = score
                    best_item_pattern = pat

            if best_item_score >= min_threshold:
                seen_answers.add(ans)
                
                # Nếu người dùng có lời chào trong câu kết hợp, thêm tiền tố chào lịch sự vào câu trả lời
                final_answer = ans
                if intent == "COMPOUND_QUESTION" and has_greeting:
                    if not final_answer.startswith("Dạ") and not final_answer.startswith("Xin chào"):
                        final_answer = f"Dạ chào bạn! {final_answer}"

                results.append({
                    "answer": final_answer,
                    "confidence": best_item_score,
                    "pattern": best_item_pattern,
                    "core_question": core_q,
                    "intent": intent
                })

        results.sort(key=lambda x: x["confidence"], reverse=True)
        return results[:limit]

    def get_response(self, user_question: str) -> Tuple[Optional[str], float, str, Dict[str, Any]]:
        """
        Lấy câu trả lời phù hợp nhất.
        Trả về: (câu trả lời, điểm tin cậy, mẫu câu khớp, thông tin phân tích ý định)
        """
        analysis = self.analyze_intent(user_question)
        matches = self.find_all_matches(user_question, limit=1)

        if matches:
            top = matches[0]
            return top["answer"], top["confidence"], top["pattern"], analysis

        return None, 0.0, "", analysis

    def add_pending_question(self, question: str) -> bool:
        """
        Tự động ghi nhận câu hỏi chưa có câu trả lời vào danh sách 'pending_questions'.
        Lưu ý: Tự động trích xuất câu hỏi cốt lõi để không lưu phần chào rườm rà!
        """
        analysis = self.analyze_intent(question)
        core_q = analysis["core_question"]

        # Không lưu vào danh sách chờ nếu chỉ là chào hoặc cảm ơn
        if analysis["intent"] in ["GREETING", "GRATITUDE"] or not core_q or len(core_q) < 3:
            return False

        pending_list = self.knowledge.setdefault("pending_questions", [])
        for p in pending_list:
            if self.calculate_similarity(core_q, p.get("question", "")) >= 0.80:
                p["hit_count"] = p.get("hit_count", 1) + 1
                self.save_knowledge()
                return False

        pending_list.append({
            "question": core_q,
            "raw_input": question.strip(),
            "hit_count": 1
        })
        self.save_knowledge()
        return True

    def get_pending_questions(self) -> List[Dict[str, Any]]:
        """Lấy danh sách các câu hỏi chưa được trả lời."""
        return self.knowledge.get("pending_questions", [])

    def delete_pending_question_by_index(self, index: int) -> bool:
        """Xóa một câu hỏi khỏi danh sách pending_questions theo chỉ số index."""
        pending_list = self.knowledge.get("pending_questions", [])
        if 0 <= index < len(pending_list):
            pending_list.pop(index)
            return self.save_knowledge()
        return False

    def clear_all_pending_questions(self) -> bool:
        """Xóa toàn bộ danh sách câu hỏi đang chờ giải đáp."""
        self.knowledge["pending_questions"] = []
        return self.save_knowledge()

    def learn(self, question: str, answer: str) -> bool:
        """
        Tiếp thu kiến thức mới:
        - Chuẩn hóa câu hỏi thành câu hỏi cốt lõi để học chính xác.
        """
        analysis = self.analyze_intent(question)
        target_q = analysis["core_question"] if analysis["core_question"] else question.strip()
        ans_clean = answer.strip()

        if not target_q or not ans_clean:
            return False

        match, score, _ = self.find_best_match(target_q)

        if match and score >= 0.85:
            patterns = [self.preprocess_text(p) for p in match.get("patterns", [])]
            if self.preprocess_text(target_q) not in patterns:
                match.setdefault("patterns", []).append(target_q)
            match["answer"] = ans_clean
        else:
            new_item = {
                "patterns": [target_q],
                "answer": ans_clean
            }
            self.knowledge.setdefault("questions", []).append(new_item)

        # Xóa khỏi pending_questions nếu có
        pending_list = self.knowledge.get("pending_questions", [])
        self.knowledge["pending_questions"] = [
            p for p in pending_list if self.calculate_similarity(target_q, p.get("question", "")) < 0.75
        ]

        return self.save_knowledge()

    def find_best_match(self, question: str) -> Tuple[Optional[Dict[str, Any]], float, str]:
        """Tìm item gốc có độ khớp cao nhất."""
        matches = self.find_all_matches(question, limit=1)
        if matches:
            top = matches[0]
            for item in self.knowledge.get("questions", []):
                if item.get("answer") == top["answer"] or top["answer"].endswith(item.get("answer", "")):
                    return item, top["confidence"], top["pattern"]
        return None, 0.0, ""

    def forget(self, keyword: str) -> int:
        """Xóa kiến thức theo từ khóa."""
        k_clean = self.preprocess_text(keyword)
        if not k_clean:
            return 0

        initial_count = len(self.knowledge.get("questions", []))
        filtered = []

        for item in self.knowledge.get("questions", []):
            should_remove = False
            for pat in item.get("patterns", []):
                if k_clean in self.preprocess_text(pat) or self.calculate_similarity(keyword, pat) >= 0.75:
                    should_remove = True
                    break
            if not should_remove:
                filtered.append(item)

        deleted = initial_count - len(filtered)
        if deleted > 0:
            self.knowledge["questions"] = filtered
            self.save_knowledge()
        return deleted

    def update_knowledge_by_index(self, index: int, patterns: List[str], answer: str) -> bool:
        """Cập nhật mục tri thức theo chỉ số index (0-indexed)."""
        questions = self.knowledge.get("questions", [])
        if 0 <= index < len(questions):
            clean_patterns = [p.strip() for p in patterns if p.strip()]
            if not clean_patterns or not answer.strip():
                return False
            questions[index] = {
                "patterns": clean_patterns,
                "answer": answer.strip()
            }
            return self.save_knowledge()
        return False

    def delete_knowledge_by_index(self, index: int) -> bool:
        """Xóa mục tri thức theo chỉ số index (0-indexed)."""
        questions = self.knowledge.get("questions", [])
        if 0 <= index < len(questions):
            questions.pop(index)
            return self.save_knowledge()
        return False

    def add_knowledge_item(self, patterns: List[str], answer: str) -> bool:
        """Thêm mới một mục tri thức gồm danh sách mẫu câu hỏi và câu trả lời."""
        clean_patterns = [p.strip() for p in patterns if p.strip()]
        if not clean_patterns or not answer.strip():
            return False
        self.knowledge.setdefault("questions", []).append({
            "patterns": clean_patterns,
            "answer": answer.strip()
        })
        return self.save_knowledge()

    def list_all(self) -> List[Dict[str, Any]]:
        """Lấy toàn bộ tri thức hiện tại."""
        return self.knowledge.get("questions", [])


def run_cli():
    """Giao diện dòng lệnh tương tác trực tiếp trong Terminal VS Code."""
    base_dir = os.path.dirname(os.path.abspath(__file__))
    kb_path = os.path.join(base_dir, "knowledge_base.json")
    ai = SelfLearningAI(knowledge_file=kb_path, threshold=0.50)

    print("\n" + "=" * 65)
    print("🤖  AI TỰ HỌC KIẾN THỨC & PHÂN BIỆT Ý ĐỊNH THÔNG MINH  🤖")
    print("=" * 65)
    print("• Thử gõ câu chào: 'Xin chào', 'Hello shop'...")
    print("• Thử gõ lời cảm ơn: 'Cảm ơn bạn nhiều nhé', 'Thanks'...")
    print("• Thử gõ câu kết hợp: 'Xin chào ạ em không đăng nhập được elearning của trường ạ'...")
    print("• Gõ '/xem' để xem tri thức, '/thoat' để kết thúc.\n")

    while True:
        try:
            user_input = input("👤 Bạn: ").strip()
        except (KeyboardInterrupt, EOFError):
            print("\n👋 Tạm biệt bạn!")
            break

        if not user_input:
            continue

        cmd = user_input.lower()
        if cmd in ["/thoat", "/exit", "thoat", "exit"]:
            print("🤖 AI: Tạm biệt bạn! Chúc bạn một ngày tuyệt vời.")
            break
        elif cmd == "/xem":
            items = ai.list_all()
            print(f"\n📚 KHO TRI THỨC HIỆN TẠI ({len(items)} mục):")
            for idx, item in enumerate(items, 1):
                pats = ", ".join(item.get("patterns", []))
                print(f" {idx}. [{pats}] -> {item.get('answer')[:80]}...")
            print()
            continue

        answer, conf, pat, analysis = ai.get_response(user_input)
        intent = analysis["intent"]
        core_q = analysis["core_question"]

        intent_labels = {
            "GREETING": "🤝 Lời chào",
            "GRATITUDE": "🙏 Lời cảm ơn",
            "COMPOUND_QUESTION": "💡 Câu hỏi kết hợp (Có chào hỏi + Thắc mắc)",
            "QUESTION": "❓ Câu hỏi trực tiếp"
        }
        label = intent_labels.get(intent, intent)

        print(f"   [Phân loại: {label} | Cốt lõi: '{core_q}']")

        if answer:
            percent = int(conf * 100)
            print(f"🤖 AI ({percent}% tin cậy):\n{answer}\n")
        else:
            print(f"🤖 AI: Tôi đã hiểu bạn đang hỏi về: '{core_q}'.")
            print("      Tuy nhiên hiện tại tôi chưa có câu trả lời cho vấn đề này.")
            print("      Hệ thống đã tự động lưu lại vào danh sách chờ học!")
            ai.add_pending_question(user_input)

            teach = input("      Bạn có thể chỉ cho tôi câu trả lời đúng được không? (hoặc gõ 'boqua'): ").strip()
            if teach and teach.lower() != "boqua":
                ai.learn(core_q, teach)
                print(f"🤖 AI: Cảm ơn bạn! Tôi đã ghi nhớ lời giải cho: '{core_q}'.\n")
            else:
                print("🤖 AI: Đã ghi nhận thắc mắc. Chúng ta nói về chủ đề khác nhé!\n")


if __name__ == "__main__":
    run_cli()
