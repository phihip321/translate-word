# Translate Book

## 1. Mục tiêu dự án

Xây dựng công cụ dịch sách tiếng Anh từ PDF sang tiếng Việt.

Người dùng sẽ:

1. Chọn file PDF.
2. Chương trình đọc và hiển thị danh sách các chương trong sách.
3. Người dùng chọn chương muốn dịch.
4. Chương trình lấy nội dung của chương đó.
5. Dịch tiếng Anh → tiếng Việt bằng Gemini.
6. Tạo file Word tiếng Việt.
7. Người dùng chọn bố cục Word mong muốn.

### Quy trình chính

PDF tiếng Anh
↓
Hiển thị danh sách chương
↓
Người dùng chọn chương
↓
Lấy nội dung chương
↓
Dịch sang tiếng Việt
↓
Tạo Word tiếng Việt
↓
Dàn trang theo bố cục người dùng chọn

---

# 2. Chọn chương

Sau khi người dùng chọn file PDF, chương trình phải tìm các chương trong sách và hiển thị cho người dùng.

Ví dụ:

1. Chapter 1 – Introduction
2. Chapter 2 – Anatomy of the Heart
3. Chapter 3 – Echocardiography
4. Chapter 4 – Valvular Heart Disease
5. Chapter 5 – Coronary Artery Disease

Người dùng có thể chọn:

- Một chương.
- Nhiều chương.
- Toàn bộ sách.

Ví dụ:

3

→ Chỉ dịch Chapter 3.

Hoặc:

1,3,5

→ Dịch Chapter 1, 3 và 5.

Có thể có lựa chọn:

all

→ Dịch toàn bộ sách.

Ưu tiên sử dụng PDF bookmark / mục lục nếu PDF có sẵn.

Nếu PDF không có bookmark thì chương trình có thể tìm Chapter từ nội dung PDF.

---

# 3. Lấy nội dung

Sau khi người dùng chọn chương, chương trình chỉ lấy nội dung thuộc chương đó.

Không cần xử lý toàn bộ sách nếu người dùng chỉ chọn một chương.

Nội dung cần giữ đúng thứ tự xuất hiện trong sách.

Ví dụ:

Chapter 3

Heading

Paragraph 1

Paragraph 2

Hình ảnh

Paragraph 3

Bảng

Paragraph 4

→ phải giữ đúng thứ tự khi đưa sang bước dịch và tạo Word.

---

# 4. Dịch bằng Gemini

Gemini chịu trách nhiệm dịch nội dung tiếng Anh sang tiếng Việt.

## Cách chia nội dung

Nội dung được chia theo **đoạn văn (paragraph)**, không chia theo số ký tự.

Ví dụ:

Đoạn 1
Đoạn 2
Đoạn 3
...
Đoạn 10

Các đoạn được gom thành từng nhóm để gửi cho Gemini.

Số paragraph trong mỗi nhóm sẽ được điều chỉnh sau để tối ưu token.

## Nguyên tắc quan trọng

**1 paragraph tiếng Anh → 1 paragraph tiếng Việt.**

Không được:

- Cắt một paragraph theo số ký tự.
- Cắt ngang câu hoặc ngang ý.
- Tự ý gộp nhiều paragraph thành một paragraph.
- Tự ý chia một paragraph thành nhiều paragraph.
- Làm thay đổi thứ tự các paragraph.

Mỗi paragraph có một ID để chương trình đưa bản dịch trở lại đúng vị trí.

Ví dụ:

[001] The heart is located in the mediastinum.

[002] The right ventricle pumps blood to the lungs.

Gemini trả về:

[001] Tim nằm trong trung thất.

[002] Tâm thất phải bơm máu đến phổi.

Chương trình phải kiểm tra ID và số lượng paragraph trước khi sử dụng bản dịch.

## Yêu cầu đối với bản dịch

- Dịch đầy đủ nội dung.
- Giữ đúng thứ tự.
- Không bỏ sót paragraph.
- Không tự ý thêm nội dung.
- Không tự ý giải thích.
- Không tự ý viết lời mở đầu hoặc kết luận.
- Giữ thuật ngữ chuyên ngành.
- Ưu tiên thuật ngữ y khoa chuẩn.
- Giữ nguyên các ký hiệu, số liệu và công thức cần thiết.

---

# 5. Tạo Word

Sau khi dịch xong, chương trình tạo một file Word tiếng Việt mới.

Không cần cố tạo Word giống hệt bố cục PDF gốc.

Mục tiêu là tạo một cuốn sách Word tiếng Việt có bố cục đẹp và do người dùng lựa chọn.

Ví dụ có thể phát triển các kiểu:

- Bố cục sách thông thường.
- Bố cục sách y khoa.
- Bố cục hai cột.
- Bố cục có hình ảnh.
- Các template khác.

Phần dịch và phần dàn trang phải tách riêng.

Một bản dịch có thể được sử dụng để tạo nhiều kiểu Word khác nhau mà không cần dịch lại.

---

# 6. Hình ảnh

Nếu PDF có hình ảnh thì cố gắng giữ lại hình ảnh.

Hình ảnh không cần gửi cho Gemini nếu không cần dịch.

Ví dụ:

[HÌNH ẢNH]

→ giữ hình ảnh trong Word.

Nếu hình ảnh có caption:

Figure 1.1 Anatomy of the heart

→ dịch caption:

Hình 1.1 Giải phẫu tim

Việc dịch chữ nằm bên trong hình ảnh có thể phát triển sau bằng OCR / Vision nếu cần.

---

# 7. Bảng

Nếu PDF có bảng, cố gắng giữ cấu trúc bảng.

Ví dụ:

PDF:

| Parameter | Normal value |
|---|---|
| Heart rate | 60–100 bpm |

Word:

| Thông số | Giá trị bình thường |
|---|---|
| Nhịp tim | 60–100 lần/phút |

Phiên bản đầu tiên ưu tiên làm phần dịch paragraph hoạt động ổn định trước.

---

# 8. Không mất nội dung

Mỗi paragraph được gửi Gemini phải có ID.

Ví dụ:

[001]
[002]
[003]
...
[010]

Gemini phải trả lại đúng các ID.

Chương trình kiểm tra:

- Số paragraph gửi đi.
- Số paragraph nhận về.
- ID có đầy đủ không.
- ID có bị trùng không.
- Thứ tự có đúng không.

Nếu không khớp thì không đưa batch đó vào Word.

---

# 9. Có thể tiếp tục khi bị lỗi

Nếu quá trình dịch bị gián đoạn, chương trình không nên dịch lại những phần đã hoàn thành.

Ví dụ:

Chapter 3

Đoạn 1–100: đã dịch
Đoạn 101–150: đã dịch
Đoạn 151–200: lỗi

Khi chạy lại chỉ cần tiếp tục từ đoạn 151.

Các lỗi cần xử lý:

- Gemini quota exceeded.
- HTTP 429.
- Timeout.
- Connection error.
- Server error.
- Invalid response.

Không retry vô hạn.

---

# 10. Tiết kiệm token

Không gửi cả cuốn sách cho Gemini cùng một lần.

Không gửi lại những paragraph đã dịch thành công.

Không gửi dữ liệu không cần thiết.

Nội dung được chia theo paragraph và gom thành từng batch.

Ví dụ:

Batch 1:
Paragraph 001–010

Batch 2:
Paragraph 011–020

Batch 3:
Paragraph 021–030

Kích thước batch sẽ được điều chỉnh sau khi thử nghiệm thực tế.

---

# 11. Nguyên tắc thiết kế

Dự án phải đơn giản và dễ bảo trì.

Tách thành các phần:

PDF
→ lấy nội dung

Translation
→ dịch nội dung

Word
→ tạo tài liệu

Layout
→ quyết định bố cục

Không gộp tất cả logic vào một file.

Không xây dựng những thành phần phức tạp khi chưa cần thiết.

---

# 12. Trạng thái hiện tại

Ngày 17/08/2026

Repository:

https://github.com/phihip321/translate-word

Commit gần nhất:

`cba76ed`

Commit:

`WIP: PDF to DOCX pipeline`

## Đã làm

- Đọc PDF.
- Đọc PDF bookmark / mục lục.
- Phát hiện Chapter.
- Xác định phạm vi trang của Chapter.
- Có thể chọn một Chapter.
- Trích xuất text từ PDF.
- Có bước tái cấu trúc text.
- Có thể tạo DOCX cơ bản từ text.

Các thành phần hiện có trong `app_v2` đã bắt đầu xây dựng nền tảng cho PDF pipeline.

## Đang chuyển hướng

Không còn lấy mục tiêu:

PDF
→ Word giống PDF gốc.

Mục tiêu mới là:

PDF
→ chọn chương
→ lấy nội dung
→ dịch
→ tạo Word mới
→ bố cục do người dùng chọn.

## Chưa hoàn thành

- Quy trình chọn Chapter hoàn chỉnh cho người dùng.
- Translation Engine bằng Gemini cho PDF.
- Chia paragraph thành batch để dịch.
- Kiểm tra ID paragraph.
- Lưu trạng thái dịch.
- Tiếp tục dịch sau khi lỗi.
- Giữ hình ảnh.
- Xử lý bảng.
- Tạo Word tiếng Việt hoàn chỉnh.
- Hệ thống bố cục Word.
- Các template Word.

---

# 13. Việc cần làm tiếp theo

## Bước 1

Rà soát toàn bộ `app_v2`.

Không viết lại toàn bộ dự án.

Kiểm tra những phần đã có và tận dụng chúng.

Đặc biệt kiểm tra:

- PDF reader.
- Bookmark parser.
- Chapter detection.
- Text extraction.
- Text reconstruction.
- DOCX writer.

## Bước 2

Làm cho chương trình:

1. Mở file PDF.
2. Tìm các Chapter.
3. Hiển thị danh sách Chapter.
4. Cho người dùng chọn Chapter.
5. Chỉ lấy nội dung Chapter đã chọn.

## Bước 3

Chia nội dung Chapter thành các paragraph.

Mỗi paragraph có ID.

Không chia theo số ký tự.

## Bước 4

Xây Translation Engine:

Paragraph
→ batch
→ Gemini
→ paragraph tiếng Việt.

Kiểm tra ID trước khi chấp nhận kết quả.

## Bước 5

Tạo Word tiếng Việt.

## Bước 6

Sau khi pipeline dịch hoạt động ổn định mới làm:

- hình ảnh.
- bảng.
- caption.
- layout.
- template.
- GUI.

---

# 14. Quy tắc làm việc với Cline

Cline phải đọc README này trước khi sửa code.

Không được tự ý:

- Viết lại toàn bộ `app_v2`.
- Xóa module cũ khi chưa kiểm tra.
- Thay đổi kiến trúc lớn mà chưa giải thích.
- Tạo quá nhiều module không cần thiết.
- Làm GUI trước khi pipeline chính hoạt động.
- Tập trung vào việc giữ nguyên bố cục PDF.

Phải làm từng bước:

Đọc code
→ hiểu code hiện tại
→ đề xuất thay đổi
→ sửa một phần
→ chạy test
→ kiểm tra kết quả
→ mới chuyển sang bước tiếp theo.

Nếu phát hiện phần hiện tại không phù hợp, phải nói rõ lý do trước khi thay đổi lớn.

---

# 15. File test

Thư mục test hiện tại:

`D:\python`

Không đưa sách PDF lớn lên GitHub.

Không commit:

- API key.
- `.env`.
- Sách PDF.
- Word đầu ra.
- File dịch lớn.
- File tạm.

---

# 16. Mục tiêu cuối cùng

Người dùng chỉ cần:

Chọn sách
→ chọn chương
→ chọn bố cục
→ chạy.

Kết quả:

**Một chương hoặc nhiều chương sách tiếng Anh được dịch sang tiếng Việt và tạo thành file Word với bố cục do người dùng lựa chọn.**

Mục tiêu của dự án không phải là:

**"Biến PDF thành một file Word giống hệt PDF."**

Mà là:

**"Biến nội dung một cuốn sách tiếng Anh thành một cuốn sách Word tiếng Việt được dàn trang theo cách mình muốn."**

---

# 17. Điểm dừng hiện tại

**17/08/2026**

Đã có nền tảng đọc PDF và nhận diện Chapter.

Đang chuẩn bị chuyển sang bước:

**PDF → chọn Chapter → lấy paragraph → dịch Gemini.**

Đây là điểm tiếp tục của dự án trong lần làm việc tiếp theo.