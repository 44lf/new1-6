import fitz  # PyMuPDF
import io

class PdfParser:
    @staticmethod
    def parse_pdf(file_bytes: bytes):
        """
        解析 PDF 文件
        :param file_bytes: PDF 文件的二进制内容
        :return: (text_content, avatar_data)
                 - text_content: 提取出的全部文本
                 - avatar_data: 提取出的头像数据 {'bytes': b'...', 'ext': 'png'} 或 None
        """
        # 1. 打开 PDF 流
        doc = fitz.open(stream=file_bytes, filetype="pdf")
        text_content = []
        avatar_data = None
        
        # 2. 遍历页面提取文本
        for page in doc:
            text_content.append(page.get_text())
        
        full_text = "\n".join(text_content)

        # 3. 提取图片（简单的头像启发式策略：取第一页的第一张图片）
        # 简历头像通常在第一页
        if len(doc) > 0:
            page = doc[0]
            image_list = page.get_images(full=True)
            
            if image_list:
                # image_list[0] 是第一张图片的信息
                # 结构: (xref, smask, width, height, bpc, colorspace, ...)
                xref = image_list[0][0]
                
                # 提取图片原始数据
                base_image = doc.extract_image(xref)
                image_bytes = base_image["image"]
                image_ext = base_image["ext"]  # png, jpeg 等
                
                # 这里可以加一些简单的过滤逻辑，比如图片太小可能是图标而不是头像
                # if len(image_bytes) > 1024 * 5: # 大于 5KB
                avatar_data = {
                    "bytes": image_bytes,
                    "ext": image_ext
                }

        doc.close()
        return full_text, avatar_data