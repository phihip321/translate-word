# 📚 Book Translator

## 🚀 Cài đặt
1. Chạy install.bat
2. Mở config/config.yaml và thêm Gemini API key
3. Chạy 	est_config.py để kiểm tra
4. Chạy 
un.bat để sử dụng

## 🔑 Lấy Gemini API Key
https://makersuite.google.com/app/apikey
@'
# 📚 Ứng dụng Dịch Sách Tự Động (Book Translator)

> Dùng Gemini 3.5 Flash để dịch sách tiếng Anh sang tiếng Việt, chọn từng chapter hoặc toàn bộ, xuất ra file Word.

---

## 🎯 **Mục đích**

- Tự động trích xuất văn bản từ PDF.
- Nhận diện các chapter.
- Cho phép chọn chapter cần dịch hoặc dịch toàn bộ.
- Dịch sang tiếng Việt bằng Gemini 3.5 Flash.
- Xuất ra file Word (.docx) có bố cục rõ ràng (tiêu đề + đoạn văn được đánh số).

---

## 📁 **Cấu trúc thư mục**
PDF
  ↓
1. Trích xuất ẢNH (PyMuPDF)
   → Lưu vào temp_images/img_1.jpg, img_2.jpg, ...
   → Ghi nhận vị trí trang
  ↓
2. Trích xuất VĂN BẢN (pdfplumber)
   → Text thô, có chứa Fig. X.X, Table X.X
  ↓
3. Làm sạch + Đánh dấu
   → Xóa số trang, header, footer
   → Đánh dấu ảnh: [IMAGE 1: chú thích]
   → Đánh dấu bảng: [TABLE 1: ...]
  ↓
4. Phát hiện Chapter
   → Tách thành các chapter riêng biệt
  ↓
5. Gửi lên GEMINI (từng chapter)
   → Prompt: "Dịch sang tiếng Việt. Giữ nguyên [IMAGE X], [TABLE X]. Không dịch tài liệu tham khảo."
   → Nhận kết quả: text đã dịch, giữ nguyên placeholder
  ↓
6. Parse kết quả
   → Tách thành các đoạn, tiêu đề, bảng, ảnh
  ↓
7. Xuất WORD
   → [IMAGE X] → Chèn ảnh thật từ temp_images/
   → [TABLE X] → Tạo bảng trong Word
   → Đoạn văn → Thêm vào Word với số thứ tự
   → Heading → Dùng style Heading
  ↓
8. Dọn dẹp
   → Xóa thư mục temp_images/
  ↓
✅ File Word hoàn chỉnh trong thư mục output/
app_v3/
├── config/
│   └── config.yaml
├── input/                         # Đặt file PDF vào đây
├── output/                        # File Word sau khi dịch
├── temp_images/                   # Ảnh trích xuất từ PDF (tự tạo, tự xóa)
├── src/
│   ├── main.py                    # Chạy chính
│   ├── pdf_processor.py           # Đọc PDF + trích xuất ảnh
│   ├── paragraph_detector.py      # Tách đoạn (có thể bỏ qua vì Gemini tự làm)
│   ├── translator.py              # Gọi Gemini
│   ├── docx_generator.py          # Tạo Word + chèn ảnh + bảng
│   └── utils.py
├── .env
├── .env.example
├── .gitignore
├── requirements.txt
└── README.md
pdfplumber>=0.10.0      # Đọc PDF, trích xuất text
pypdf2>=3.0.0           # Fallback
PyMuPDF>=1.23.0         # Trích xuất ảnh từ PDF (quan trọng!)
nltk>=3.8.1             # (Có thể không cần nếu để Gemini tự tách đoạn)
google-generativeai>=0.3.0  # Gemini API
python-docx>=1.0.0      # Tạo file Word
pyyaml>=6.0
tqdm>=4.65.0
python-dotenv>=1.0.0
pdfplumber>=0.10.0      # Đọc PDF, trích xuất text
pypdf2>=3.0.0           # Fallback
PyMuPDF>=1.23.0         # Trích xuất ảnh từ PDF (quan trọng!)
nltk>=3.8.1             # (Có thể không cần nếu để Gemini tự tách đoạn)
google-generativeai>=0.3.0  # Gemini API
python-docx>=1.0.0      # Tạo file Word
pyyaml>=6.0
tqdm>=4.65.0
python-dotenv>=1.0.0