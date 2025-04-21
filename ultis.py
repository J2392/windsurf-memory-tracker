"""
WindSurf Memory Tracker - Tiện ích
---------------------------------
Cung cấp các hàm tiện ích để xử lý snapshot, diff, và các chức năng khác.
"""

import os
import re
import sys
import hashlib
import difflib
import datetime
import zlib
import time
from typing import Dict, List, Tuple, Optional, Any, Union, Callable
import json
import logging
from PyQt6.QtCore import QObject, QThread, pyqtSignal
from PyQt6.QtWidgets import QDialog, QVBoxLayout, QLabel, QProgressBar, QPushButton

# Thiết lập logging
logging.basicConfig(level=logging.INFO, 
                   format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger("windsurf_utils")


# ----- Xử lý snapshot và diff -----

# ----- Tiện ích chung -----
def format_time(dt: datetime.datetime) -> str:
    return dt.strftime('%Y-%m-%d %H:%M:%S')

def slugify(text: str) -> str:
    text = text.lower()
    text = re.sub(r'[^a-z0-9]+', '-', text)
    return text.strip('-')

def validate_email(email: str) -> bool:
    return re.match(r"[^@]+@[^@]+\.[^@]+", email) is not None


def compute_file_hash(content: str) -> str:
    """
    Tính toán hash MD5 của nội dung file.
    
    Args:
        content: Nội dung file
        
    Returns:
        str: Chuỗi hash MD5
    """
    return hashlib.md5(content.encode('utf-8')).hexdigest()


def compress_content(content: str) -> bytes:
    """
    Nén nội dung để lưu trữ hiệu quả.
    
    Args:
        content: Nội dung cần nén
        
    Returns:
        bytes: Dữ liệu đã nén
    """
    return zlib.compress(content.encode('utf-8'))


def decompress_content(compressed_data: bytes) -> str:
    """
    Giải nén nội dung đã lưu trữ.
    
    Args:
        compressed_data: Dữ liệu đã nén
        
    Returns:
        str: Nội dung gốc
    """
    return zlib.decompress(compressed_data).decode('utf-8')


def generate_diff(old_content: str, new_content: str) -> str:
    """
    Tạo diff giữa nội dung cũ và mới theo định dạng unified diff.
    
    Args:
        old_content: Nội dung cũ
        new_content: Nội dung mới
        
    Returns:
        str: Chuỗi diff
    """
    old_lines = old_content.splitlines()
    new_lines = new_content.splitlines()
    
    diff = difflib.unified_diff(
        old_lines, 
        new_lines, 
        fromfile='previous',
        tofile='current',
        lineterm=''
    )
    
    return '\n'.join(diff)


def apply_diff(original_content: str, diff_content: str) -> str:
    """
    Áp dụng diff vào nội dung gốc để tạo nội dung mới.
    
    Args:
        original_content: Nội dung gốc
        diff_content: Nội dung diff
        
    Returns:
        str: Nội dung sau khi áp dụng diff
    """
    # Tách nội dung diff thành các dòng
    diff_lines = diff_content.splitlines()
    
    # Tìm và bỏ qua header của diff
    start_idx = 0
    for i, line in enumerate(diff_lines):
        if line.startswith('+++') or line.startswith('---'):
            start_idx = i + 1
            if i < len(diff_lines) - 1 and (diff_lines[i+1].startswith('+++') or diff_lines[i+1].startswith('---')):
                start_idx = i + 2
                break
    
    # Áp dụng các thay đổi trong diff
    original_lines = original_content.splitlines()
    result_lines = original_lines.copy()
    
    line_idx = 0
    for diff_line in diff_lines[start_idx:]:
        if diff_line.startswith('@@'):
            # Phân tích hunk header để lấy vị trí bắt đầu
            match = re.match(r'@@ -(\d+),(\d+) \+(\d+),(\d+) @@', diff_line)
            if match:
                line_idx = int(match.group(3)) - 1
        elif diff_line.startswith('+'):
            # Thêm dòng mới
            result_lines.insert(line_idx, diff_line[1:])
            line_idx += 1
        elif diff_line.startswith('-'):
            # Xóa dòng
            if line_idx < len(result_lines) and result_lines[line_idx] == diff_line[1:]:
                result_lines.pop(line_idx)
        elif not diff_line.startswith('\\'):  # Bỏ qua các dòng "\ No newline at end of file"
            # Giữ nguyên dòng không đổi
            line_idx += 1
    
    return '\n'.join(result_lines)


def is_significant_change(old_content: str, new_content: str, threshold: float = 0.05) -> bool:
    """
    Kiểm tra xem sự thay đổi giữa nội dung cũ và mới có đáng kể không.
    
    Args:
        old_content: Nội dung cũ
        new_content: Nội dung mới
        threshold: Ngưỡng tỷ lệ thay đổi (0.05 = 5%)
        
    Returns:
        bool: True nếu thay đổi đáng kể
    """
    if not old_content or not new_content:
        return True
    
    # Tính toán sự khác biệt
    matcher = difflib.SequenceMatcher(None, old_content, new_content)
    ratio = matcher.ratio()
    change_ratio = 1.0 - ratio
    
    # So sánh với ngưỡng
    return change_ratio > threshold


# ----- Quản lý task và liên kết -----

def generate_task_id(prefix: str = "TASK") -> str:
    """
    Tạo ID mới cho task.
    
    Args:
        prefix: Tiền tố cho task ID
        
    Returns:
        str: Task ID mới theo định dạng PREFIX-XXX
    """
    # Sử dụng timestamp để tạo ID ngẫu nhiên
    timestamp = int(time.time() * 1000)
    task_number = timestamp % 1000
    
    return f"{prefix}-{task_number:03d}"


def extract_task_references(content: str) -> List[str]:
    """
    Trích xuất các tham chiếu đến task từ nội dung.
    Tìm kiếm các mẫu như TASK-XXX trong nội dung.
    
    Args:
        content: Nội dung cần phân tích
        
    Returns:
        List[str]: Danh sách các task ID được tham chiếu
    """
    # Tìm kiếm các mẫu như TASK-XXX
    pattern = r'(TASK-\d{3})'
    matches = re.findall(pattern, content)
    
    # Loại bỏ các mục trùng lặp
    return list(set(matches))


def guess_related_tasks(content: str, task_list: List[Dict[str, Any]]) -> List[str]:
    """
    Đoán các task có thể liên quan đến nội dung dựa trên tiêu đề và mô tả.
    
    Args:
        content: Nội dung cần phân tích
        task_list: Danh sách các task hiện có
        
    Returns:
        List[str]: Danh sách các task ID có thể liên quan
    """
    related_tasks = []
    
    # Đầu tiên, tìm các tham chiếu trực tiếp
    direct_refs = extract_task_references(content)
    related_tasks.extend(direct_refs)
    
    # Sau đó, tìm kiếm các từ khóa từ tiêu đề task
    for task in task_list:
        # Bỏ qua các task đã tìm thấy trực tiếp
        if task['id'] in related_tasks:
            continue
        
        # Tìm kiếm tiêu đề task trong nội dung
        title_words = task['title'].lower().split()
        significant_words = [w for w in title_words if len(w) > 3]  # Chỉ xét các từ có ý nghĩa
        
        if significant_words:
            # Kiểm tra xem có ít nhất 2 từ quan trọng xuất hiện trong nội dung không
            matches = sum(1 for word in significant_words if word.lower() in content.lower())
            if matches >= 2 or (len(significant_words) == 1 and matches == 1):
                related_tasks.append(task['id'])
    
    return related_tasks


# ----- Tiện ích phân tích mã nguồn -----

def calculate_code_complexity(content: str) -> Dict[str, Any]:
    """
    Tính toán độ phức tạp của mã nguồn.
    
    Args:
        content: Nội dung mã nguồn
        
    Returns:
        Dict[str, Any]: Các chỉ số độ phức tạp
    """
    if not content:
        return {
            'cyclomatic_complexity': 0,
            'nesting_depth': 0,
            'complexity_score': 0
        }
    
    lines = content.splitlines()
    
    # Đếm số câu lệnh rẽ nhánh (if, elif, for, while, except, case)
    branch_keywords = ['if', 'elif', 'for', 'while', 'except', 'case']
    branch_count = 0
    
    # Đo độ sâu lồng nhau tối đa
    current_indent = 0
    max_indent = 0
    indent_stack = [0]
    
    for line in lines:
        stripped = line.strip()
        
        # Bỏ qua các dòng trống và comment
        if not stripped or stripped.startswith('#'):
            continue
        
        # Tính toán indent hiện tại
        indent = len(line) - len(line.lstrip())
        
        # Cập nhật indent stack
        if indent > indent_stack[-1]:
            indent_stack.append(indent)
        elif indent < indent_stack[-1]:
            while indent_stack and indent < indent_stack[-1]:
                indent_stack.pop()
            if not indent_stack or indent != indent_stack[-1]:
                indent_stack.append(indent)
        
        # Cập nhật độ sâu lồng nhau tối đa
        max_indent = max(max_indent, len(indent_stack) - 1)
        
        # Đếm các từ khóa rẽ nhánh
        for keyword in branch_keywords:
            pattern = r'\b' + keyword + r'\b'
            if re.search(pattern, stripped) and not stripped.startswith('def ') and not stripped.startswith('class '):
                branch_count += 1
    
    # Tính toán độ phức tạp cyclomatic (số đường đi + 1)
    cyclomatic_complexity = branch_count + 1
    
    # Tính điểm phức tạp tổng hợp
    complexity_score = (cyclomatic_complexity * 0.7) + (max_indent * 0.3)
    
    return {
        'cyclomatic_complexity': cyclomatic_complexity,
        'nesting_depth': max_indent,
        'branch_count': branch_count,
        'complexity_score': round(complexity_score, 2)
    }


def detect_code_smells(content: str) -> List[Dict[str, Any]]:
    """
    Phát hiện các code smells phổ biến.
    
    Args:
        content: Nội dung mã nguồn
        
    Returns:
        List[Dict[str, Any]]: Danh sách các code smells được phát hiện
    """
    if not content:
        return []
    
    smells = []
    lines = content.splitlines()
    
    # Phát hiện hàm quá dài
    current_function = None
    function_start_line = 0
    function_lines = 0
    in_function = False
    
    for i, line in enumerate(lines):
        stripped = line.strip()
        
        # Bỏ qua các dòng trống và comment
        if not stripped or stripped.startswith('#'):
            continue
        
        # Phát hiện dòng quá dài (>100 ký tự)
        if len(line) > 100:
            smells.append({
                'type': 'long_line',
                'line': i + 1,
                'message': f'Dòng quá dài ({len(line)} ký tự)',
                'severity': 'low'
            })
        
        # Phát hiện biến toàn cục
        if re.search(r'\bglobal\b', line):
            smells.append({
                'type': 'global_variable',
                'line': i + 1,
                'message': 'Sử dụng biến toàn cục',
                'severity': 'medium'
            })
        
        # Phát hiện hàm quá dài
        func_match = re.match(r'^\s*def\s+(\w+)\s*\(', line)
        if func_match:
            # Kết thúc hàm trước đó nếu có
            if in_function and function_lines > 50:
                smells.append({
                    'type': 'long_function',
                    'line': function_start_line + 1,
                    'message': f'Hàm {current_function} quá dài ({function_lines} dòng)',
                    'severity': 'medium'
                })
            
            # Bắt đầu hàm mới
            current_function = func_match.group(1)
            function_start_line = i
            function_lines = 0
            in_function = True
        elif in_function:
            function_lines += 1
        
        # Phát hiện độ sâu lồng nhau quá lớn
        indent = len(line) - len(line.lstrip())
        if indent >= 16:  # 4 cấp lồng nhau (mỗi cấp 4 dấu cách)
            smells.append({
                'type': 'deep_nesting',
                'line': i + 1,
                'message': f'Độ sâu lồng nhau quá lớn ({indent // 4} cấp)',
                'severity': 'medium'
            })
        
        # Phát hiện các magic number
        if re.search(r'[^\w]\d{3,}[^\w]', line) and not stripped.startswith('#'):
            smells.append({
                'type': 'magic_number',
                'line': i + 1,
                'message': 'Sử dụng magic number',
                'severity': 'low'
            })
    
    # Kiểm tra hàm cuối cùng
    if in_function and function_lines > 50:
        smells.append({
            'type': 'long_function',
            'line': function_start_line + 1,
            'message': f'Hàm {current_function} quá dài ({function_lines} dòng)',
            'severity': 'medium'
        })
    
    # Phát hiện các hàm/lớp có tên quá ngắn
    for i, line in enumerate(lines):
        # Tìm các hàm có tên ngắn
        func_match = re.match(r'^\s*def\s+(\w{1,2})\s*\(', line)
        if func_match:
            smells.append({
                'type': 'short_name',
                'line': i + 1,
                'message': f'Tên hàm quá ngắn: {func_match.group(1)}',
                'severity': 'low'
            })
        
        # Tìm các lớp có tên ngắn
        class_match = re.match(r'^\s*class\s+(\w{1,2})\s*[:\(]', line)
        if class_match:
            smells.append({
                'type': 'short_name',
                'line': i + 1,
                'message': f'Tên lớp quá ngắn: {class_match.group(1)}',
                'severity': 'low'
            })
    
    return smells


def truncate_text(text: str, max_length: int = 100, suffix: str = '...') -> str:
    """
    Cắt ngắn văn bản với dấu "...".
    
    Args:
        text: Văn bản cần cắt ngắn
        max_length: Độ dài tối đa
        suffix: Hậu tố khi cắt ngắn
        
    Returns:
        str: Văn bản đã cắt ngắn
    """
    if not text:
        return ""
    
    if len(text) <= max_length:
        return text
    
    return text[:max_length - len(suffix)] + suffix


def highlight_diff(diff_text: str) -> str:
    """
    Tô màu diff để hiển thị trong terminal.
    
    Args:
        diff_text: Văn bản diff
        
    Returns:
        str: Văn bản diff đã được tô màu
    """
    if not diff_text:
        return ""
    
    result = []
    for line in diff_text.splitlines():
        if line.startswith('+'):
            result.append(f"\033[92m{line}\033[0m")  # Màu xanh lá
        elif line.startswith('-'):
            result.append(f"\033[91m{line}\033[0m")  # Màu đỏ
        elif line.startswith('^'):
            result.append(f"\033[94m{line}\033[0m")  # Màu xanh dương
        elif line.startswith('@@'):
            result.append(f"\033[96m{line}\033[0m")  # Màu xanh ngọc
        else:
            result.append(line)
    
    return '\n'.join(result)

def count_code_metrics(content: str) -> Dict[str, int]:
    """
    Tính toán các chỉ số về mã nguồn.
    
    Args:
        content: Nội dung mã nguồn
        
    Returns:
        Dict[str, int]: Các chỉ số (số dòng, comment, v.v.)
    """
    if not content:
        return {
            'total_lines': 0,
            'code_lines': 0,
            'comment_lines': 0,
            'blank_lines': 0,
            'docstring_lines': 0,
            'function_count': 0,
            'class_count': 0,
            'import_count': 0,
            'todo_count': 0,
            'max_line_length': 0,
            'avg_line_length': 0,
            'comment_ratio': 0
        }
    
    lines = content.splitlines()
    total_lines = len(lines)
    blank_lines = 0
    comment_lines = 0
    docstring_lines = 0
    function_count = 0
    class_count = 0
    import_count = 0
    todo_count = 0
    line_lengths = []
    
    in_docstring = False
    docstring_delimiter = None
    
    for line in lines:
        stripped = line.strip()
        line_lengths.append(len(line))
        
        # Kiểm tra dòng trống
        if not stripped:
            blank_lines += 1
            continue
        
        # Kiểm tra docstring
        if in_docstring:
            docstring_lines += 1
            if stripped.endswith(docstring_delimiter):
                in_docstring = False
            continue
        
        # Kiểm tra bắt đầu docstring
        if stripped.startswith('"""') or stripped.startswith("'''"):
            in_docstring = True
            docstring_delimiter = stripped[:3]
            docstring_lines += 1
            # Kiểm tra docstring một dòng
            if len(stripped) > 3 and stripped.endswith(docstring_delimiter):
                in_docstring = False
            continue
        
        # Kiểm tra comment
        if stripped.startswith('#'):
            comment_lines += 1
            # Kiểm tra TODO
            if 'TODO' in stripped.upper():
                todo_count += 1
            continue
        
        # Đếm số hàm
        if re.match(r'^\s*def\s+\w+\s*\(', line):
            function_count += 1
            continue
        
        # Đếm số lớp
        if re.match(r'^\s*class\s+\w+', line):
            class_count += 1
            continue
        
        # Đếm số import
        if re.match(r'^\s*import\s+|^\s*from\s+\w+\s+import', line):
            import_count += 1
            continue
    
    # Tính toán số dòng code
    code_lines = total_lines - blank_lines - comment_lines - docstring_lines
    
    # Tính toán độ dài dòng
    max_line_length = max(line_lengths) if line_lengths else 0
    avg_line_length = sum(line_lengths) / len(line_lengths) if line_lengths else 0
    
    return {
        'total_lines': total_lines,
        'code_lines': code_lines,
        'comment_lines': comment_lines,
        'blank_lines': blank_lines,
        'docstring_lines': docstring_lines,
        'function_count': function_count,
        'class_count': class_count,
        'import_count': import_count,
        'todo_count': todo_count,
        'max_line_length': max_line_length,
        'avg_line_length': round(avg_line_length, 2),
        'comment_ratio': round((comment_lines + docstring_lines) / total_lines * 100, 2) if total_lines > 0 else 0
    }


def identify_code_language(filename: str, content: str = None) -> str:
    """
    Xác định ngôn ngữ lập trình dựa trên tên file và nội dung.
    
    Args:
        filename: Tên file
        content: Nội dung file (tùy chọn)
        
    Returns:
        str: Tên ngôn ngữ lập trình
    """
    ext = os.path.splitext(filename)[1].lower()
    
    language_map = {
        '.py': 'Python',
        '.js': 'JavaScript',
        '.html': 'HTML',
        '.css': 'CSS',
        '.java': 'Java',
        '.c': 'C',
        '.cpp': 'C++',
        '.h': 'C/C++ Header',
        '.cs': 'C#',
        '.go': 'Go',
        '.rb': 'Ruby',
        '.php': 'PHP',
        '.ts': 'TypeScript',
        '.jsx': 'React JSX',
        '.tsx': 'React TSX',
        '.md': 'Markdown',
        '.json': 'JSON',
        '.xml': 'XML',
        '.sql': 'SQL',
        '.sh': 'Shell',
        '.bat': 'Batch',
        '.ps1': 'PowerShell'
    }
    
    return language_map.get(ext, 'Unknown')


# ----- Tiện ích đa luồng -----

class WorkerSignals(QObject):
    """Định nghĩa các tín hiệu cho worker thread"""
    finished = pyqtSignal()
    error = pyqtSignal(tuple)
    result = pyqtSignal(object)
    progress = pyqtSignal(int)


class Worker(QObject):
    """Worker thread để thực hiện các tác vụ nặng"""
    
    def __init__(self, fn: Callable, *args, **kwargs):
        super(Worker, self).__init__()
        self.fn = fn
        self.args = args
        self.kwargs = kwargs
        self.signals = WorkerSignals()
        self._is_running = False
        
    def run(self) -> None:
        """Thực thi hàm trong luồng riêng"""
        self._is_running = True
        try:
            # Kiểm tra xem thread có bị yêu cầu dừng không
            current_thread = QThread.currentThread()
            if hasattr(current_thread, 'isInterruptionRequested') and current_thread.isInterruptionRequested():
                logger.info("Thread bị hủy bỏ trước khi thực thi")
                self.signals.error.emit((InterruptedError, "Thread bị hủy bỏ", None))
                return
            
            # Kiểm tra xem hàm có hỗ trợ tín hiệu progress không
            # Chỉ thêm progress_callback nếu hàm có tham số này trong signature
            import inspect
            try:
                sig = inspect.signature(self.fn)
                if 'progress_callback' in sig.parameters and 'progress_callback' not in self.kwargs:
                    self.kwargs['progress_callback'] = self.signals.progress.emit
            except (ValueError, TypeError):
                # Nếu không lấy được signature (ví dụ với lambda), bỏ qua
                pass
                
            # Thực thi hàm
            result = self.fn(*self.args, **self.kwargs)
            self.signals.result.emit(result)
        except Exception as e:
            import traceback
            trace = traceback.format_exc()
            logger.error(f"Lỗi trong worker thread: {str(e)}\n{trace}")
            self.signals.error.emit((type(e), str(e), trace))
        finally:
            self._is_running = False
            self.signals.finished.emit()
            
    def is_running(self) -> bool:
        """Kiểm tra xem worker có đang chạy không"""
        return self._is_running


def run_in_thread(parent, fn: Callable, progress_text: str = "Đang xử lý...", 
                 on_result: Optional[Callable] = None, on_error: Optional[Callable] = None, 
                 show_dialog: bool = True, *args, **kwargs) -> QThread:
    """
    Chạy một hàm trong luồng riêng và hiển thị dialog tiến trình.
    
    Args:
        parent: Widget cha để hiển thị dialog, hoặc None nếu không cần dialog
        fn: Hàm cần thực thi trong luồng riêng
        progress_text: Văn bản hiển thị trong dialog tiến trình
        on_result: Callback khi có kết quả
        on_error: Callback khi có lỗi
        show_dialog: Nếu True, hiển thị dialog tiến trình; nếu False, chạy ngầm
        *args, **kwargs: Tham số cho hàm fn
        
    Returns:
        QThread: Đối tượng thread được tạo
    """
    # Hàm xử lý kết quả
    def handle_result(result, dialog=None):
        if dialog and dialog.isVisible():
            dialog.accept()
        if on_result:
            on_result(result)
    
    # Hàm xử lý lỗi
    def handle_error(error, dialog=None):
        if dialog and dialog.isVisible():
            dialog.accept()
        logger.error(f"Lỗi trong thread: {error}")
        if on_error:
            on_error(error)
    
    # Tạo thread và worker
    thread = QThread()
    worker = Worker(fn, *args, **kwargs)
    worker.moveToThread(thread)
    
    # Tạo dialog tiến trình nếu cần
    progress_dialog = None
    if show_dialog and parent is not None:
        try:
            progress_dialog = QDialog(parent)
            progress_dialog.setWindowTitle("Đang xử lý")
            progress_dialog.setMinimumWidth(300)
            layout = QVBoxLayout(progress_dialog)
            
            # Thêm label
            label = QLabel(progress_text)
            layout.addWidget(label)
            
            # Thêm thanh tiến trình
            progress_bar = QProgressBar()
            progress_bar.setRange(0, 0)  # Chế độ không xác định
            layout.addWidget(progress_bar)
            
            # Thêm nút hủy (tùy chọn)
            cancel_button = QPushButton("Hủy")
            cancel_button.clicked.connect(lambda: thread.requestInterruption())
            layout.addWidget(cancel_button)
        except Exception as e:
            logger.error(f"Lỗi khi tạo dialog: {e}")
            progress_dialog = None
    
    # Kết nối các tín hiệu
    thread.started.connect(worker.run)
    worker.signals.result.connect(lambda result: handle_result(result, progress_dialog))
    worker.signals.error.connect(lambda error: handle_error(error, progress_dialog))
    worker.signals.progress.connect(lambda value: update_progress(progress_dialog, value) if progress_dialog else None)
    worker.signals.finished.connect(thread.quit)
    worker.signals.finished.connect(worker.deleteLater)
    thread.finished.connect(thread.deleteLater)
    
    # Bắt đầu thread
    thread.start()
    
    # Hiển thị dialog nếu cần
    if progress_dialog:
        try:
            progress_dialog.exec()
        except Exception as e:
            logger.error(f"Lỗi khi hiển thị dialog: {e}")
    
    return thread


def update_progress(dialog, value: int):
    """Cập nhật giá trị của thanh tiến trình"""
    if dialog and hasattr(dialog, 'findChild'):
        progress_bar = dialog.findChild(QProgressBar)
        if progress_bar:
            if value < 0 or value > 100:
                # Chế độ không xác định
                progress_bar.setRange(0, 0)
            else:
                # Chế độ xác định
                progress_bar.setRange(0, 100)
                progress_bar.setValue(value)


# ----- Tiện ích bổ sung -----

def format_time_ago(timestamp: datetime.datetime) -> str:
    """
    Định dạng thời gian theo kiểu "thời gian trước".
    
    Args:
        timestamp: Thời điểm cần định dạng
        
    Returns:
        str: Chuỗi định dạng (ví dụ: "5 phút trước")
    """
    if not timestamp:
        return "không xác định"
        
    try:
        now = datetime.datetime.now()
        # Đảm bảo cùng timezone
        if timestamp.tzinfo is not None:
            now = now.replace(tzinfo=timestamp.tzinfo)
            
        diff = now - timestamp
        
        seconds = diff.total_seconds()
        if seconds < 0:  # Trường hợp thời gian trong tương lai
            return "trong tương lai"
            
        if seconds < 60:
            return "vừa xong"
        
        minutes = seconds // 60
        if minutes < 60:
            return f"{int(minutes)} phút trước"
        
        hours = minutes // 60
        if hours < 24:
            return f"{int(hours)} giờ trước"
        
        days = hours // 24
        if days < 30:
            return f"{int(days)} ngày trước"
        
        months = days // 30
        if months < 12:
            return f"{int(months)} tháng trước"
        
        years = months // 12
        return f"{int(years)} năm trước"
    except Exception as e:
        logger.error(f"Lỗi khi định dạng thời gian: {e}")
        return "không xác định"


def create_directory_if_not_exists(directory: str) -> None:
    """
    Tạo thư mục nếu chưa tồn tại.
    
    Args:
        directory: Đường dẫn đến thư mục
    """
    if not os.path.exists(directory):
        os.makedirs(directory)
        logger.info(f"Đã tạo thư mục: {directory}")


def get_relative_path(file_path: str, base_path: str) -> str:
    """
    Lấy đường dẫn tương đối của file_path so với base_path.
    
    Args:
        file_path: Đường dẫn đầy đủ đến file
        base_path: Đường dẫn cơ sở
        
    Returns:
        str: Đường dẫn tương đối
    """
    return os.path.relpath(file_path, base_path)


# ----- Tiện ích xử lý file và snapshot -----

def safe_read_file(file_path: str, encoding: str = 'utf-8') -> Optional[str]:
    """
    Đọc file với xử lý lỗi an toàn.
    
    Args:
        file_path: Đường dẫn đến file cần đọc
        encoding: Mã hóa ký tự (mặc định: utf-8)
        
    Returns:
        Nội dung file hoặc None nếu có lỗi
    """
    try:
        with open(file_path, 'r', encoding=encoding) as f:
            return f.read()
    except FileNotFoundError:
        logger.error(f"Không tìm thấy file: {file_path}")
        return None
    except PermissionError:
        logger.error(f"Không có quyền truy cập file: {file_path}")
        return None
    except UnicodeDecodeError:
        # Thử lại với mã hóa khác
        try:
            with open(file_path, 'r', encoding='latin-1') as f:
                return f.read()
        except Exception as e:
            logger.error(f"Lỗi khi đọc file {file_path} với mã hóa thay thế: {str(e)}")
            return None
    except Exception as e:
        logger.error(f"Lỗi khi đọc file {file_path}: {str(e)}")
        return None


def safe_write_file(file_path: str, content: str, encoding: str = 'utf-8') -> bool:
    """
    Ghi nội dung vào file với xử lý lỗi an toàn.
    
    Args:
        file_path: Đường dẫn đến file cần ghi
        content: Nội dung cần ghi
        encoding: Mã hóa ký tự (mặc định: utf-8)
        
    Returns:
        bool: True nếu ghi thành công, False nếu có lỗi
    """
    try:
        # Đảm bảo thư mục tồn tại
        os.makedirs(os.path.dirname(os.path.abspath(file_path)), exist_ok=True)
        
        with open(file_path, 'w', encoding=encoding) as f:
            f.write(content)
        return True
    except PermissionError:
        logger.error(f"Không có quyền ghi file: {file_path}")
        return False
    except Exception as e:
        logger.error(f"Lỗi khi ghi file {file_path}: {str(e)}")
        return False


def find_files_by_extension(directory: str, extensions: List[str], recursive: bool = True) -> List[str]:
    """
    Tìm các file theo phần mở rộng trong thư mục.
    
    Args:
        directory: Thư mục cần tìm
        extensions: Danh sách các phần mở rộng (ví dụ: ['py', 'txt'])
        recursive: Nếu True, tìm kiếm đệ quy trong các thư mục con
        
    Returns:
        List[str]: Danh sách đường dẫn đến các file tìm thấy
    """
    result = []
    
    # Chuẩn hóa phần mở rộng (loại bỏ dấu chấm nếu có)
    normalized_extensions = [ext.lstrip('.').lower() for ext in extensions]
    
    try:
        if recursive:
            for root, _, files in os.walk(directory):
                for file in files:
                    if any(file.lower().endswith('.' + ext) for ext in normalized_extensions):
                        result.append(os.path.join(root, file))
        else:
            for item in os.listdir(directory):
                if os.path.isfile(os.path.join(directory, item)) and \
                   any(item.lower().endswith('.' + ext) for ext in normalized_extensions):
                    result.append(os.path.join(directory, item))
    except Exception as e:
        logger.error(f"Lỗi khi tìm file trong {directory}: {str(e)}")
    
    return result


def get_file_age(file_path: str) -> Optional[datetime.datetime]:
    """
    Lấy thời gian sửa đổi gần nhất của file.
    
    Args:
        file_path: Đường dẫn đến file
        
    Returns:
        datetime.datetime: Thời gian sửa đổi gần nhất hoặc None nếu có lỗi
    """
    try:
        mtime = os.path.getmtime(file_path)
        return datetime.datetime.fromtimestamp(mtime)
    except Exception as e:
        logger.error(f"Lỗi khi lấy thời gian sửa đổi của file {file_path}: {str(e)}")
        return None


def create_snapshot(file_path: str, content: Optional[str] = None) -> Dict[str, Any]:
    """
    Tạo snapshot của một file với metadata.
    
    Args:
        file_path: Đường dẫn đến file
        content: Nội dung file (nếu None, sẽ đọc từ file)
        
    Returns:
        Dict[str, Any]: Snapshot bao gồm nội dung và metadata
    """
    try:
        # Đọc nội dung nếu không được cung cấp
        if content is None:
            content = safe_read_file(file_path)
            if content is None:
                return {}
        
        # Tính toán hash
        content_hash = compute_file_hash(content)
        
        # Lấy thời gian sửa đổi
        file_time = get_file_age(file_path) if os.path.exists(file_path) else datetime.datetime.now()
        
        # Xác định ngôn ngữ
        language = identify_code_language(file_path, content)
        
        # Tính toán các chỉ số code
        metrics = count_code_metrics(content) if language else {}
        
        # Tạo snapshot
        snapshot = {
            'file_path': file_path,
            'file_name': os.path.basename(file_path),
            'timestamp': datetime.datetime.now().isoformat(),
            'file_modified': file_time.isoformat() if file_time else None,
            'hash': content_hash,
            'language': language,
            'size': len(content),
            'metrics': metrics,
            'content': content,
            'compressed_content': compress_content(content).hex() if content else None
        }
        
        return snapshot
    except Exception as e:
        logger.error(f"Lỗi khi tạo snapshot cho file {file_path}: {str(e)}")
        return {}


def compare_snapshots(old_snapshot: Dict[str, Any], new_snapshot: Dict[str, Any]) -> Dict[str, Any]:
    """
    So sánh hai snapshot và tạo báo cáo thay đổi.
    
    Args:
        old_snapshot: Snapshot cũ
        new_snapshot: Snapshot mới
        
    Returns:
        Dict[str, Any]: Báo cáo thay đổi
    """
    if not old_snapshot or not new_snapshot:
        return {}
    
    try:
        old_content = old_snapshot.get('content', '')
        new_content = new_snapshot.get('content', '')
        
        # Tạo diff
        diff = generate_diff(old_content, new_content)
        
        # Tính toán sự thay đổi trong metrics
        old_metrics = old_snapshot.get('metrics', {})
        new_metrics = new_snapshot.get('metrics', {})
        metrics_changes = {}
        
        for key in set(old_metrics.keys()) | set(new_metrics.keys()):
            old_value = old_metrics.get(key, 0)
            new_value = new_metrics.get(key, 0)
            if old_value != new_value:
                metrics_changes[key] = {
                    'old': old_value,
                    'new': new_value,
                    'change': new_value - old_value
                }
        
        # Kiểm tra thay đổi đáng kể
        is_significant = is_significant_change(old_content, new_content)
        
        # Tạo báo cáo
        report = {
            'file_path': new_snapshot.get('file_path'),
            'file_name': new_snapshot.get('file_name'),
            'old_timestamp': old_snapshot.get('timestamp'),
            'new_timestamp': new_snapshot.get('timestamp'),
            'old_hash': old_snapshot.get('hash'),
            'new_hash': new_snapshot.get('hash'),
            'is_significant': is_significant,
            'diff': diff,
            'metrics_changes': metrics_changes,
            'size_change': new_snapshot.get('size', 0) - old_snapshot.get('size', 0)
        }
        
        return report
    except Exception as e:
        logger.error(f"Lỗi khi so sánh snapshot: {str(e)}")
        return {}


def sanitize_filename(filename: str) -> str:
    """
    Tạo tên file an toàn, loại bỏ các ký tự không hợp lệ.
    
    Args:
        filename: Tên file cần chuẩn hóa
        
    Returns:
        str: Tên file an toàn
    """
    # Loại bỏ các ký tự không hợp lệ trong tên file
    invalid_chars = '<>:"/\\|?*'
    for char in invalid_chars:
        filename = filename.replace(char, '_')
    
    # Giới hạn độ dài
    if len(filename) > 255:
        name, ext = os.path.splitext(filename)
        filename = name[:255-len(ext)] + ext
    
    # Loại bỏ khoảng trắng ở đầu và cuối
    filename = filename.strip()
    
    # Thay thế tên file rỗng bằng tên mặc định
    if not filename:
        filename = "untitled"
    
    return filename


# ----- Hàm demo và kiểm tra -----

def demo():
    """Demo các hàm tiện ích"""
    print("WindSurf Memory Tracker Utils Demo")
    print("-" * 40)
    
    # Demo diff và apply diff
    original = "Line 1\nLine 2\nLine 3\nLine 4\n"
    modified = "Line 1\nLine 2 modified\nLine 3\nNew line\nLine 4\n"
    
    diff = generate_diff(original, modified)
    print("Diff:")
    print(diff)
    
    # Áp dụng lại diff
    reconstructed = apply_diff(original, diff)
    print("\nReconstruct sau khi áp dụng diff:")
    print(reconstructed)
    print(f"Reconstruct giống nội dung đích: {reconstructed == modified}")
    
    # Demo tìm task ID
    code_with_tasks = """
    /* 
     * This function implements feature for TASK-123
     * It also fixes the bug mentioned in TASK-456
     */
    function processData() {
        // TODO: Complete this for TASK-789
        console.log("Processing data");
    }
    """
    
    task_refs = extract_task_references(code_with_tasks)
    print("\nTask references found:")
    for ref in task_refs:
        print(f"- {ref}")
    
    # Demo phân tích mã nguồn
    metrics = count_code_metrics(code_with_tasks)
    print("\nCode metrics:")
    for key, value in metrics.items():
        print(f"- {key}: {value}")
    
    # Demo định dạng thời gian
    now = datetime.datetime.now()
    five_mins_ago = now - datetime.timedelta(minutes=5)
    two_hours_ago = now - datetime.timedelta(hours=2)
    yesterday = now - datetime.timedelta(days=1)
    
    print("\nTime formatting:")
    print(f"5 minutes ago: {format_time_ago(five_mins_ago)}")
    print(f"2 hours ago: {format_time_ago(two_hours_ago)}")
    print(f"Yesterday: {format_time_ago(yesterday)}")


if __name__ == "__main__":
    demo()