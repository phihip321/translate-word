# Translate Word

Công cụ dịch file Word từ tiếng Anh sang tiếng Việt bằng Google Gemini.

## Chức năng

- Chọn file Word (.docx)
- Đọc các đoạn văn trong file
- Chia đoạn văn thành từng nhóm 10 đoạn
- Gửi từng nhóm cho Gemini để dịch
- Giữ nguyên thứ tự các đoạn
- Giữ nguyên thuật ngữ y khoa
- Tạo file Word tiếng Việt mới với hậu tố `_VI`

## Yêu cầu

- Python 3.x
- Google Gemini API key

## Cài đặt

Clone project:

```bash
git clone https://github.com/phihip321/translate-word.git