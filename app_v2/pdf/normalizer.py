"""Chuẩn hóa tối thiểu, không thay đổi từ ngữ, cho text sẵn sàng chia chunk."""


class TextNormalizer:
    """Chỉ thay newline vật lý trong paragraph thành một space.

    Bản gốc luôn được giữ ở ``TextSegment.raw_text``; lớp này không sửa chữ,
    dấu câu, hoặc cố xử lý từ bị ngắt bằng hyphen.
    """

    def normalize(self, raw_text: str, kind: str) -> str:
        if kind == "paragraph":
            return raw_text.replace("\r\n", "\n").replace("\r", "\n").replace("\n", " ")
        return raw_text
