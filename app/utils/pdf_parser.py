import fitz  # PyMuPDF
from typing import Optional, Dict, Tuple, Any


class PdfParser:
    @staticmethod
    def parse_pdf(file_bytes: bytes) -> Tuple[str, Optional[Dict[str, Any]]]:
        """解析 PDF：提取文本 + 头像"""
        doc = fitz.open(stream=file_bytes, filetype="pdf")
        try:
            text = "\n".join([p.get_text("text", sort=True) for p in doc])
            avatar = PdfParser._extract_avatar(doc)
            return text, avatar
        finally:
            doc.close()

    @staticmethod
    def _extract_avatar(doc: fitz.Document) -> Optional[Dict[str, Any]]:
        """智能提取头像"""
        if not doc:
            return None

        page = doc[0]
        pw, ph = page.rect.width, page.rect.height
        best, best_score = None, 0

        for img in page.get_images(full=True):
            try:
                # 获取图片信息
                rects = page.get_image_rects(img[0])
                if not rects:
                    continue
                bbox = rects[0]

                base = doc.extract_image(img[0])
                w, h, size = base["width"], base["height"], len(base["image"])
                ratio = w / h if h else 0

                # 快速排除
                if w < 30 or h < 30 or size < 1024:
                    continue
                if ratio > 3 or ratio < 0.25 or w > 1200 or h > 1500:
                    continue

                # 评分：位置 + 尺寸 + 比例
                score = 0

                # 位置 (0-35): 上方且左/右/中
                cy = (bbox.y0 + bbox.y1) / 2 / ph
                cx = (bbox.x0 + bbox.x1) / 2 / pw
                if cy < 0.15:
                    score += 20
                elif cy < 0.35:
                    score += 15
                elif cy < 0.5:
                    score += 10

                if cx < 0.35 or cx > 0.65:
                    score += 15
                else:
                    score += 10

                # 尺寸 (0-25): 合适的像素和文件大小
                if 100 <= min(w, h) <= 400:
                    score += 15
                elif 50 <= min(w, h) <= 500:
                    score += 10

                if 5 <= size / 1024 <= 500:
                    score += 10
                elif 2 <= size / 1024 <= 800:
                    score += 5

                # 比例 (0-25): 接近正方形或证件照
                for ideal in [1.0, 0.75, 0.8, 1.2]:
                    if abs(ratio - ideal) < 0.1:
                        score += 25
                        break
                    elif abs(ratio - ideal) < 0.25:
                        score = max(score, 15)

                if 0.5 <= ratio <= 1.6:
                    score = max(score, 10)

                # 更新最佳
                if score > best_score:
                    best_score = score
                    best = {"bytes": base["image"], "ext": base["ext"]}

            except Exception:
                continue

        return best