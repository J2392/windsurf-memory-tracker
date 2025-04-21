# WindSurf Memory Tracker

![Version](https://img.shields.io/badge/version-1.2.0-blue.svg)
![Python](https://img.shields.io/badge/python-3.10%2B-green.svg)
![License](https://img.shields.io/badge/license-MIT-orange.svg)

WindSurf Memory Tracker là một ứng dụng quản lý task, theo dõi lịch sử code, và phân tích AI cho lập trình viên. Dự án sử dụng PyQt6 cho giao diện, Peewee cho ORM, hỗ trợ Kanban board, thống kê thay đổi code và các tính năng AI insights. Ứng dụng tích hợp với WindSurf Editor để đồng bộ task và theo dõi thay đổi file trong thời gian thực.

📅 **Cập nhật mới (04/2025)**: Bổ sung hỗ trợ nhiều mô hình AI (Claude, Gemini), cải thiện phân tích code, và tối ưu hóa hiệu suất.

## 🚀 Tính năng chính

- **Kanban Task Board:** Quản lý task theo các cột TO DO, IN PROGRESS, DONE với khả năng kéo-thả.
- **Code History & Snapshot:** Theo dõi thay đổi file code, lưu snapshot và diff.
- **AI Insights:** Đánh giá sức khỏe code, gợi ý cải tiến, tìm lỗi và vấn đề bảo mật.
- **Thống kê, Analytics:** Thống kê số lần thay đổi, hoạt động gần đây.
- **Tích hợp WindSurf API:** Nhận event thay đổi file và task từ editor.
- **Giả lập Editor Events:** Tính năng giả lập sự kiện từ editor để kiểm thử và phát triển.
- **Hỗ trợ đa mô hình AI:** Tích hợp với OpenAI, Claude, Gemini và các mô hình local.
- **Phân tích code nâng cao:** Phát hiện code smells, đo độ phức tạp, và đề xuất cải tiến.
- **Cache thông minh:** Tối ưu hóa các API call với cơ chế cache.

## 🗂️ Cấu trúc thư mục

```text
windurf-memory-tracker/
├── main.py              # Entry point, giao diện chính
├── models.py            # Định nghĩa ORM, quản lý DB
├── api_client.py        # Client nhận event từ WindSurf Editor
├── settings.py          # Quản lý cấu hình
├── utils.py             # Helper function (hoặc ultis.py)
├── ai_helper.py         # AI logic, phân tích code
├── ai_ui_integration.py # Tích hợp AI vào giao diện
├── simulate_editor_event.py # Công cụ giả lập sự kiện editor
├── requirements.txt     # Danh sách package Python
├── test_helpers.py      # Test cho utils và ai_helper
├── test_models.py       # Test cho models
├── test_drag_drop.py    # Test cho chức năng kéo-thả
├── run_tests.py         # Script chạy tất cả các test
├── README.md            # Tài liệu này
└── ...
```

## ⚡ Hướng dẫn cài đặt & chạy

### 1. Yêu cầu hệ thống

- Python 3.10 hoặc cao hơn
- PyQt6 6.4.0+
- Peewee ORM 3.15.0+
- Các thư viện khác trong requirements.txt (requests, watchdog, colorlog, v.v.)

### 2. Clone repository

```bash
git clone https://github.com/your-username/windsurf-memory-tracker.git
cd windsurf-memory-tracker
```

### 3. Cài đặt dependencies

```bash
pip install -r requirements.txt
```

### 4. Chạy ứng dụng

```bash
python main.py
```

### 5. Chạy kiểm thử

```bash
# Chạy tất cả các bài kiểm tra
python run_tests.py

# Hoặc chạy kiểm tra cụ thể
python test_helpers.py
python test_models.py
```

```bash
pip install -r requirements.txt
```

### 4. Cấu hình AI (tùy chọn)

Có hai cách để sử dụng tính năng AI:

#### a. Sử dụng mô hình AI local

Cài đặt và chạy một trong các mô hình sau:

- [LM Studio](https://lmstudio.ai/) với mô hình Qwen2.5-coder-3b-instruct
- [Ollama](https://ollama.ai/) với lệnh `ollama run qwen2:3b`

Mô hình sẽ chạy trên endpoint mặc định: `http://localhost:1234/v1/chat/completions`

#### b. Sử dụng OpenAI API

Thêm API key của bạn vào file cấu hình `~/.windsurf_memory/config.json`:

```json
{
  "openai_api_key": "your-api-key-here",
  "use_openai": true
}
```

### 5. Chạy ứng dụng

```bash
python main.py
```

### 6. Sử dụng tính năng giả lập sự kiện

Ứng dụng có tích hợp tính năng giả lập sự kiện từ WindSurf Editor để kiểm thử:

1. Khởi động ứng dụng
2. Nhấn nút "🎮 Simulate" trên thanh công cụ
3. Ứng dụng sẽ tự động tạo task mẫu và cập nhật trạng thái

Bạn có thể xem log chi tiết trong terminal để theo dõi các sự kiện được xử lý.

## 🧪 Hướng dẫn phát triển & kiểm thử

### Chạy tất cả các test

```bash
python run_tests.py
```

Script này sẽ chạy tất cả các test và hiển thị kết quả chi tiết.

### Chạy từng loại test riêng biệt

- **Test cho models:**

  ```bash
  python -m pytest test_models.py -v
  ```

- **Test cho AI helper:**

  ```bash
  python -m pytest test_ai_helper.py -v
  ```

- **Test cho chức năng kéo-thả:**

  ```bash
  python -m pytest test_drag_drop.py -v
  ```

### Thay đổi cấu hình

Có hai cách để thay đổi cấu hình:

1. **Sửa file cấu hình trực tiếp:**
   - `~/.windsurf_memory/config.json` (sinh ra sau lần chạy đầu tiên)

2. **Sử dụng API trong code:**

   ```python
   from settings import Settings
   
   # Lấy cấu hình hiện tại
   config = Settings.get_instance()
   
   # Thay đổi cấu hình
   config.set("ai_model", "gpt-3.5-turbo")
   config.save()
   ```

## 📚 Tài liệu API

### Module AI Helper

`ai_helper.py` cung cấp các chức năng phân tích code và tương tác với các mô hình AI:

```python
from ai_helper import ai_helper

# Phân tích chất lượng code
result = ai_helper.analyze_code_quality(code)

# Tìm lỗi và vấn đề bảo mật
issues = ai_helper.find_code_issues(code)

# Tạo docstring
docstring = ai_helper.generate_docstring(code)

# Đề xuất refactor
refactor = ai_helper.suggest_refactor(code)

# Dịch code sang ngôn ngữ khác
translated = ai_helper.translate_code(code, "JavaScript")
```

### Module Ultis

`ultis.py` cung cấp các hàm tiện ích:

```python
from ultis import run_in_thread

# Chạy hàm trong thread riêng
def my_function(progress_callback=None):
    # Xử lý nặng
    if progress_callback:
        progress_callback(50)  # Báo cáo tiến trình 50%
    return "Kết quả"

# Chạy hàm trong thread riêng với dialog tiến trình
run_in_thread(
    parent=my_widget,
    fn=my_function,
    progress_text="Đang xử lý...",
    on_result=lambda result: print(f"Kết quả: {result}"),
    on_error=lambda error: print(f"Lỗi: {error}")
)
```

## 📝 Ghi chú & đóng góp

- Yêu cầu Python >= 3.10
- Đảm bảo các file: `models.py`, `api_client.py`, `ultis.py`, `ai_helper.py`, `settings.py` cùng thư mục với `main.py`.
- Đóng góp, báo lỗi: tạo issue hoặc PR trên Github.

### Các cải tiến gần đây

- Thêm tính năng giả lập sự kiện từ WindSurf Editor (v1.1.0)
- Tối ưu hóa chức năng kéo-thả trong Kanban board
- Cải thiện xử lý lỗi và retry logic trong AI helper
- Tối ưu hóa xử lý thread và tiến trình
- Cập nhật requirements.txt với các thư viện mới
- Thêm test đơn vị cho models và AI helper

---

### Made with ❤️ by WindSurf Team

![WindSurf Memory Tracker Logo](https://via.placeholder.com/300x80/0A0A0A/00FF00?text=WindSurf+Memory+Tracker)

WindSurf Memory Tracker là ứng dụng theo dõi thay đổi code và quản lý task tích hợp dành cho trình soạn thảo WindSurf. Ứng dụng tự động ghi nhớ và lưu lịch sử các thay đổi mã nguồn, liên kết chúng với task tương ứng trong bảng Kanban, và cung cấp phân tích thông minh về dự án của bạn.

## Tính năng chính

- **Theo dõi thay đổi code tự động**: Lưu lịch sử thay đổi từ WindSurf Editor
- **Quản lý Task theo Kanban**: Bảng trực quan To Do, In Progress, Done
- **Liên kết code với task**: Tự động gắn thay đổi code với task tương ứng
- **Phân tích AI**: Đề xuất cải thiện code và tracking tiến độ dự án
- **Giao diện Hackernoon style**: Dark theme với điểm nhấn neon hiện đại
- **Tích hợp hoàn toàn**: Làm việc song song với trình soạn thảo code

## Yêu cầu hệ thống

- Python 3.8 hoặc cao hơn
- PyQt6
- Các thư viện Python: peewee, watchdog

## Cài đặt

1. Clone repository:

```bash
git clone https://github.com/yourusername/windsurf-memory-tracker.git
cd windsurf-memory-tracker
```

2. Cài đặt thư viện cần thiết:

```bash
pip install PyQt6 peewee watchdog
```

3. Chạy ứng dụng:

```bash
python main.py
```

## Cấu trúc dự án

```
windsurf-memory-tracker/
├── main.py           # Ứng dụng chính và giao diện người dùng
├── models.py         # Định nghĩa mô hình dữ liệu và ORM
├── api_client.py     # Kết nối với WindSurf Editor API
├── utils.py          # Các hàm tiện ích (diff, snapshot, etc.)
├── settings.py       # Cấu hình và thiết lập
└── README.md         # Tài liệu hướng dẫn
```

## Cách sử dụng

### Kết nối với WindSurf Editor

Ứng dụng tự động kết nối với WindSurf Editor trong môi trường phát triển. Trong trường hợp không có WindSurf Editor, ứng dụng sẽ sử dụng API giả lập để theo dõi thay đổi file trong thư mục dự án.

### Quản lý Task

1. Tạo task mới: Nhấp vào nút "+" trong cột Kanban tương ứng
2. Cập nhật trạng thái task: Kéo và thả task giữa các cột
3. Xem chi tiết task: Nhấp vào task để xem thông tin chi tiết và lịch sử thay đổi

### Theo dõi thay đổi code

Ứng dụng tự động theo dõi và lưu các thay đổi khi bạn làm việc trong WindSurf Editor:

1. Mỗi lần lưu file sẽ tạo một snapshot mới
2. Các thay đổi nhỏ được ghi nhận tự động theo thời gian thực
3. Xem lịch sử thay đổi bằng cách chọn file và duyệt qua các phiên bản

### Liên kết code với task

Có hai cách liên kết thay đổi code với task:

1. **Tự động**: Ứng dụng sẽ phân tích code và gợi ý liên kết dựa trên ID task trong comment
2. **Thủ công**: Chọn task và thêm thay đổi code vào task đó

## 🔧 Tùy chỉnh

Bạn có thể tùy chỉnh ứng dụng thông qua file `config.json` hoặc từ giao diện Settings. Một số tùy chọn phổ biến:

- **API Keys**: Cấu hình API key cho OpenAI, Claude, Gemini
- **Cache Settings**: Điều chỉnh thời gian sống của cache và kích thước tối đa
- **UI Theme**: Chọn theme sáng/tối hoặc tùy chỉnh màu sắc
- **Snapshot Settings**: Cấu hình tần suất tạo snapshot và thư mục lưu trữ
- **AI Model Preferences**: Chọn mô hình AI mặc định và tham số

## 🧩 Các module chính

### utils.py (hoặc ultis.py)

Module này cung cấp các tiện ích cho ứng dụng:

- **Xử lý file**: Đọc/ghi file an toàn, tìm kiếm file, tạo snapshot
- **Phân tích code**: Tính toán độ phức tạp, phát hiện code smells, đếm metrics
- **So sánh code**: Tạo và hiển thị diff giữa các phiên bản
- **Tiện ích khác**: Định dạng thời gian, xử lý chuỗi, sanitize input

```python
# Ví dụ sử dụng
import ultis

# Đọc file an toàn
content = ultis.safe_read_file('path/to/file.py')

# Tạo snapshot
snapshot = ultis.create_snapshot('path/to/file.py')

# Phân tích code
metrics = ultis.count_code_metrics(content)
smells = ultis.detect_code_smells(content)
complexity = ultis.calculate_code_complexity(content)
```

### ai_helper.py

Module này cung cấp các chức năng tương tác với AI và phân tích code:

- **Tích hợp đa mô hình**: OpenAI, Claude, Gemini và mô hình local
- **Cache thông minh**: Lưu cache kết quả API để tối ưu hiệu suất
- **Phân tích code**: Đánh giá chất lượng, tìm lỗi, gợi ý cải tiến
- **Tạo nội dung**: Tạo docstring, commit message, tóm tắt code

```python
# Ví dụ sử dụng
import ai_helper

# Phân tích code với OpenAI
result = ai_helper.call_openai("Phân tích đoạn code sau: " + code)

# Sử dụng Claude
result = ai_helper.call_claude("Tìm lỗi trong đoạn code: " + code)

# Tạo commit message từ diff
commit_msg = ai_helper.generate_commit_message(diff_content)
```

- **Loại file theo dõi**: Chỉ định loại file cần theo dõi

## FAQ

**Q: Ứng dụng có lưu trữ toàn bộ code của tôi không?**  
A: Có, nhưng mọi dữ liệu đều được lưu cục bộ trên máy của bạn. Không có thông tin nào được gửi đến máy chủ.

**Q: Tôi có thể sử dụng ứng dụng này với các editor khác ngoài WindSurf không?**  
A: Hiện tại ứng dụng chỉ hỗ trợ WindSurf Editor. Tuy nhiên, với API giả lập, bạn vẫn có thể dùng để theo dõi thay đổi file trong thư mục dự án.

**Q: Có giới hạn về kích thước dự án không?**  
A: Ứng dụng được thiết kế để xử lý các dự án có kích thước vừa và nhỏ. Với dự án lớn, bạn nên điều chỉnh cấu hình để giảm tần suất snapshot.

## Đóng góp

Đóng góp luôn được chào đón! Nếu bạn muốn cải thiện WindSurf Memory Tracker:

1. Fork repository
2. Tạo branch mới (`git checkout -b feature/amazing-feature`)
3. Commit thay đổi (`git commit -m 'Add amazing feature'`)
4. Push đến branch (`git push origin feature/amazing-feature`)
5. Tạo Pull Request

## Giấy phép

Dự án này được phân phối dưới giấy phép MIT. Xem file `LICENSE` để biết thêm thông tin.

## Liên hệ

Nếu bạn có câu hỏi hoặc đề xuất, hãy tạo issue trong repository hoặc liên hệ qua email: example@example.com