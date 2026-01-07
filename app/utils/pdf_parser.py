import fitz  # PyMuPDF

class PdfParser:
    @staticmethod
    def parse_pdf(file_bytes: bytes):
        """
        解析 PDF：提取文本 + 智能提取头像 (带位置权重)
        """
        doc = fitz.open(stream=file_bytes, filetype="pdf")

        # 1. 提取文本
        text = "\n".join([page.get_text("text", sort=True) for page in doc])

        # 2. 智能提取头像
        avatar = None
        best_score = 0

        # 通常只在第一页找头像
        if len(doc) > 0:
            page = doc[0]
            page_width = page.rect.width
            page_height = page.rect.height

            # 遍历页面上的所有图片
            for img in page.get_images(full=True):
                xref = img[0]

                # --- A. 基础信息获取 ---
                try:
                    # 获取图片在页面上的坐标位置 (Rect对象)
                    # 注意：一张图可能在页面显示多次，我们只取第一次出现的位置
                    rects = page.get_image_rects(xref)
                    if not rects: continue
                    bbox = rects[0]  # (x0, y0, x1, y1)

                    base_img = doc.extract_image(xref)
                    img_bytes = base_img["image"]
                    ext = base_img["ext"]
                    w, h = base_img["width"], base_img["height"]
                    size = len(img_bytes)
                except Exception:
                    continue

                # --- B. 硬性过滤 (快速排除干扰项) ---
                # 1. 尺寸过小 (图标) 或 过大 (背景图)
                if w < 50 or h < 50 or size < 2048: continue
                if w > 600 or h > 800: continue

                # 2. 比例极端的 (细长条纹、扁长 Logo)
                ratio = w / h
                if ratio > 1.8 or ratio < 0.4: continue

                # --- C. 评分系统 (满分 100) ---
                score = 0

                # 1.【核心】位置权重 (Location Score) - 最高 40 分
                # 这里的 y0 是图片顶部的坐标。
                # 如果图片顶部在页面的前 30% (0.3)，说明是顶部的图
                if bbox.y0 < page_height * 0.3:
                    score += 20
                    # 进一步：如果是左上角或右上角
                    # 左边: x0 < 页面宽度的 40%
                    # 右边: x1 > 页面宽度的 60%
                    if bbox.x0 < page_width * 0.4 or bbox.x1 > page_width * 0.6:
                        score += 20  # 完美的位置
                elif bbox.y0 < page_height * 0.5:
                    # 如果在前 50%，给一点辛苦分
                    score += 10

                # 2.【核心】比例权重 (Ratio Score) - 最高 40 分
                # 距离标准证件照比例 (3:4=0.75) 或 正方形 (1.0) 越近分越高
                dist = min(abs(ratio - 0.75), abs(ratio - 1.0))
                if dist < 0.1: score += 40    # 非常标准的比例
                elif dist < 0.2: score += 20  # 还凑合
                elif dist < 0.3: score += 10

                # 3. 文件大小权重 (Size Score) - 最高 20 分
                # 头像通常清晰度尚可，不会特别小
                if 10 * 1024 < size < 200 * 1024: # 10KB - 200KB
                    score += 20

                # --- D. 结果更新 ---
                # 设置一个及格线，比如 40 分，防止把一些奇怪的图当头像
                if score > 40 and score > best_score:
                    best_score = score
                    avatar = {"bytes": img_bytes, "ext": ext}

        doc.close()
        return text, avatar