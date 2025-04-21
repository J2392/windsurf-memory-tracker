from PyQt6.QtWidgets import QPushButton, QDialog, QVBoxLayout, QTextEdit, QPushButton as QBtn, QProgressBar, QLabel
from PyQt6.QtGui import QKeySequence, QAction
from PyQt6.QtCore import Qt, QThread, pyqtSignal, QObject
import ai_helper
import traceback

class AIWorker(QObject):
    """Worker để chạy các phân tích AI trong luồng riêng"""
    finished = pyqtSignal()
    result_ready = pyqtSignal(str)
    error = pyqtSignal(str)
    
    def __init__(self, func, code):
        super().__init__()
        self.func = func
        self.code = code
    
    def run(self):
        try:
            result = self.func(self.code)
            self.result_ready.emit(result)
        except Exception as e:
            self.error.emit(str(e) + "\n" + traceback.format_exc())
        finally:
            self.finished.emit()

def show_ai_result_dialog(parent, title, content):
    """Hiển thị dialog kết quả phân tích AI"""
    dlg = QDialog(parent)
    dlg.setWindowTitle(title)
    dlg.setMinimumWidth(600)
    layout = QVBoxLayout(dlg)
    text = QTextEdit()
    text.setReadOnly(True)
    text.setPlainText(content)
    layout.addWidget(text)
    btn = QBtn("Close")
    btn.clicked.connect(dlg.accept)
    layout.addWidget(btn)
    dlg.exec()

def show_ai_progress_dialog(parent, title):
    """Hiển thị dialog tiến trình khi đang phân tích"""
    dlg = QDialog(parent)
    dlg.setWindowTitle(title)
    dlg.setMinimumWidth(400)
    layout = QVBoxLayout(dlg)
    
    # Thêm thông báo
    label = QLabel("Đang phân tích mã nguồn...")
    label.setAlignment(Qt.AlignmentFlag.AlignCenter)
    layout.addWidget(label)
    
    # Thêm thanh tiến trình
    progress = QProgressBar()
    progress.setRange(0, 0)  # Chế độ không xác định
    layout.addWidget(progress)
    
    # Không có nút đóng để tránh người dùng đóng khi đang xử lý
    return dlg

# --- Hàm AI tích hợp vào MainWindow ---
def get_code_from_editor(self):
    return self.code_editor.toPlainText()

def ai_analyze_code_quality(self):
    """Phân tích chất lượng mã trong luồng riêng"""
    code = self.get_code_from_editor()
    if not code.strip():
        show_ai_result_dialog(self, "AI Code Quality", "Không có mã để phân tích")
        return
    
    # Tạo dialog tiến trình
    progress_dlg = show_ai_progress_dialog(self, "Đang phân tích...")
    
    # Tạo thread và worker
    self.thread = QThread()
    self.worker = AIWorker(ai_helper.analyze_code_quality, code)
    self.worker.moveToThread(self.thread)
    
    # Kết nối tín hiệu
    self.thread.started.connect(self.worker.run)
    self.worker.finished.connect(self.thread.quit)
    self.worker.finished.connect(self.worker.deleteLater)
    self.thread.finished.connect(self.thread.deleteLater)
    self.thread.finished.connect(progress_dlg.accept)
    
    # Xử lý kết quả
    self.worker.result_ready.connect(lambda result: show_ai_result_dialog(self, "AI Code Quality", result))
    self.worker.error.connect(lambda error: show_ai_result_dialog(self, "Lỗi", f"Đã xảy ra lỗi khi phân tích: {error}"))
    
    # Bắt đầu thread và hiển thị dialog
    self.thread.start()
    progress_dlg.exec()

def ai_find_code_issues(self):
    """Tìm lỗi trong mã trong luồng riêng"""
    code = self.get_code_from_editor()
    if not code.strip():
        show_ai_result_dialog(self, "AI Find Issues", "Không có mã để phân tích")
        return
    
    # Tạo dialog tiến trình
    progress_dlg = show_ai_progress_dialog(self, "Đang tìm lỗi...")
    
    # Tạo thread và worker
    self.thread = QThread()
    self.worker = AIWorker(ai_helper.find_code_issues, code)
    self.worker.moveToThread(self.thread)
    
    # Kết nối tín hiệu
    self.thread.started.connect(self.worker.run)
    self.worker.finished.connect(self.thread.quit)
    self.worker.finished.connect(self.worker.deleteLater)
    self.thread.finished.connect(self.thread.deleteLater)
    self.thread.finished.connect(progress_dlg.accept)
    
    # Xử lý kết quả
    self.worker.result_ready.connect(lambda result: show_ai_result_dialog(self, "AI Find Issues", result))
    self.worker.error.connect(lambda error: show_ai_result_dialog(self, "Lỗi", f"Đã xảy ra lỗi khi tìm lỗi: {error}"))
    
    # Bắt đầu thread và hiển thị dialog
    self.thread.start()
    progress_dlg.exec()

def ai_generate_docstring(self):
    """Tạo docstring trong luồng riêng"""
    code = self.get_code_from_editor()
    if not code.strip():
        show_ai_result_dialog(self, "AI Docstring", "Không có mã để tạo docstring")
        return
    
    # Tạo dialog tiến trình
    progress_dlg = show_ai_progress_dialog(self, "Đang tạo docstring...")
    
    # Tạo thread và worker
    self.thread = QThread()
    self.worker = AIWorker(ai_helper.generate_docstring, code)
    self.worker.moveToThread(self.thread)
    
    # Kết nối tín hiệu
    self.thread.started.connect(self.worker.run)
    self.worker.finished.connect(self.thread.quit)
    self.worker.finished.connect(self.worker.deleteLater)
    self.thread.finished.connect(self.thread.deleteLater)
    self.thread.finished.connect(progress_dlg.accept)
    
    # Xử lý kết quả
    self.worker.result_ready.connect(lambda result: show_ai_result_dialog(self, "AI Docstring", result))
    self.worker.error.connect(lambda error: show_ai_result_dialog(self, "Lỗi", f"Đã xảy ra lỗi khi tạo docstring: {error}"))
    
    # Bắt đầu thread và hiển thị dialog
    self.thread.start()
    progress_dlg.exec()

def ai_suggest_refactor(self):
    """Đề xuất cải tiến mã trong luồng riêng"""
    code = self.get_code_from_editor()
    if not code.strip():
        show_ai_result_dialog(self, "AI Refactor", "Không có mã để đề xuất cải tiến")
        return
    
    # Tạo dialog tiến trình
    progress_dlg = show_ai_progress_dialog(self, "Đang phân tích cải tiến...")
    
    # Tạo thread và worker
    self.thread = QThread()
    self.worker = AIWorker(ai_helper.suggest_refactor, code)
    self.worker.moveToThread(self.thread)
    
    # Kết nối tín hiệu
    self.thread.started.connect(self.worker.run)
    self.worker.finished.connect(self.thread.quit)
    self.worker.finished.connect(self.worker.deleteLater)
    self.thread.finished.connect(self.thread.deleteLater)
    self.thread.finished.connect(progress_dlg.accept)
    
    # Xử lý kết quả
    self.worker.result_ready.connect(lambda result: show_ai_result_dialog(self, "AI Refactor", result))
    self.worker.error.connect(lambda error: show_ai_result_dialog(self, "Lỗi", f"Đã xảy ra lỗi khi đề xuất cải tiến: {error}"))
    
    # Bắt đầu thread và hiển thị dialog
    self.thread.start()
    progress_dlg.exec()

def ai_semantic_analysis(self):
    """Phân tích ngữ nghĩa mã trong luồng riêng"""
    code = self.get_code_from_editor()
    if not code.strip():
        show_ai_result_dialog(self, "AI Semantic Analysis", "Không có mã để phân tích ngữ nghĩa")
        return
    
    # Tạo dialog tiến trình
    progress_dlg = show_ai_progress_dialog(self, "Đang phân tích ngữ nghĩa...")
    
    # Tạo thread và worker
    self.thread = QThread()
    self.worker = AIWorker(ai_helper.semantic_analysis, code)
    self.worker.moveToThread(self.thread)
    
    # Kết nối tín hiệu
    self.thread.started.connect(self.worker.run)
    self.worker.finished.connect(self.thread.quit)
    self.worker.finished.connect(self.worker.deleteLater)
    self.thread.finished.connect(self.thread.deleteLater)
    self.thread.finished.connect(progress_dlg.accept)
    
    # Xử lý kết quả
    self.worker.result_ready.connect(lambda result: show_ai_result_dialog(self, "AI Semantic Analysis", result))
    self.worker.error.connect(lambda error: show_ai_result_dialog(self, "Lỗi", f"Đã xảy ra lỗi khi phân tích ngữ nghĩa: {error}"))
    
    # Bắt đầu thread và hiển thị dialog
    self.thread.start()
    progress_dlg.exec()

def add_ai_buttons_to_toolbar(self, toolbar):
    ai_analyze_btn = QPushButton("AI Analyze")
    ai_analyze_btn.setStyleSheet("color: #00ff00; font-weight: bold; background: #15151f; border-radius: 5px; padding: 5px 12px;")
    ai_analyze_btn.clicked.connect(self.ai_analyze_code_quality)
    toolbar.addWidget(ai_analyze_btn)

    ai_bug_btn = QPushButton("AI Find Issues")
    ai_bug_btn.setStyleSheet("color: #FFD700; font-weight: bold; background: #15151f; border-radius: 5px; padding: 5px 12px;")
    ai_bug_btn.clicked.connect(self.ai_find_code_issues)
    toolbar.addWidget(ai_bug_btn)

    ai_doc_btn = QPushButton("AI Docstring")
    ai_doc_btn.setStyleSheet("color: #61AFEF; font-weight: bold; background: #15151f; border-radius: 5px; padding: 5px 12px;")
    ai_doc_btn.clicked.connect(self.ai_generate_docstring)
    toolbar.addWidget(ai_doc_btn)

    ai_refactor_btn = QPushButton("AI Refactor")
    ai_refactor_btn.setStyleSheet("color: #00FFFF; font-weight: bold; background: #15151f; border-radius: 5px; padding: 5px 12px;")
    ai_refactor_btn.clicked.connect(self.ai_suggest_refactor)
    toolbar.addWidget(ai_refactor_btn)

    ai_semantic_btn = QPushButton("AI Semantic")
    ai_semantic_btn.setStyleSheet("color: #FF69B4; font-weight: bold; background: #15151f; border-radius: 5px; padding: 5px 12px;")
    ai_semantic_btn.clicked.connect(self.ai_semantic_analysis)
    toolbar.addWidget(ai_semantic_btn)

def add_ai_shortcuts_to_editor(self):
    self.ai_shortcut_analyze = QAction("AI Analyze", self)
    self.ai_shortcut_analyze.setShortcut(QKeySequence("Ctrl+Alt+Q"))
    self.ai_shortcut_analyze.triggered.connect(self.ai_analyze_code_quality)
    self.code_editor.addAction(self.ai_shortcut_analyze)

    self.ai_shortcut_bug = QAction("AI Find Issues", self)
    self.ai_shortcut_bug.setShortcut(QKeySequence("Ctrl+Alt+B"))
    self.ai_shortcut_bug.triggered.connect(self.ai_find_code_issues)
    self.code_editor.addAction(self.ai_shortcut_bug)

    self.ai_shortcut_doc = QAction("AI Docstring", self)
    self.ai_shortcut_doc.setShortcut(QKeySequence("Ctrl+Alt+D"))
    self.ai_shortcut_doc.triggered.connect(self.ai_generate_docstring)
    self.code_editor.addAction(self.ai_shortcut_doc)

    self.ai_shortcut_refactor = QAction("AI Refactor", self)
    self.ai_shortcut_refactor.setShortcut(QKeySequence("Ctrl+Alt+R"))
    self.ai_shortcut_refactor.triggered.connect(self.ai_suggest_refactor)
    self.code_editor.addAction(self.ai_shortcut_refactor)

    self.ai_shortcut_semantic = QAction("AI Semantic", self)
    self.ai_shortcut_semantic.setShortcut(QKeySequence("Ctrl+Alt+S"))
    self.ai_shortcut_semantic.triggered.connect(self.ai_semantic_analysis)
    self.code_editor.addAction(self.ai_shortcut_semantic)
