#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# ----- Import các thư viện cần thiết -----
import sys
import os
import logging

# Thiết lập logging chuẩn: log ra cả file app.log và ra terminal
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("app.log"),
        logging.StreamHandler()
    ]
)

import datetime
import time
import json
import traceback
import random
from PyQt6.QtCore import (
    Qt, QSize, QPoint, QTimer, QDateTime, QUrl, QRegularExpression, 
    pyqtSignal
)
from PyQt6.QtGui import (
    QTextCharFormat, QColor, QSyntaxHighlighter, 
    QTextCursor, QPixmap, QDrag, QIcon, QAction
)
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
    QPushButton, QLabel, QLineEdit, QTextEdit, QListWidget, QListWidgetItem,
    QTabWidget, QSplitter, QFrame, QScrollArea, QMenu, QDialog, QComboBox,
    QDateTimeEdit, QToolBar, QStatusBar, QFileDialog, QMessageBox,
    QScrollArea, QToolButton, QSizePolicy, QFormLayout, QDialogButtonBox
)

# ----- Import các module tự tạo -----
from models import Task, Project, Snapshot
from api_client import WindSurfAPIClient, create_api_client
from ultis import format_time_ago
from ai_helper import (
    analyze_code_quality, find_code_issues,
    generate_docstring, suggest_refactor,
    semantic_analysis
)
from ai_ui_integration import (
    get_code_from_editor, show_ai_result_dialog,
    ai_analyze_code_quality, ai_find_code_issues,
    ai_generate_docstring, ai_suggest_refactor,
    ai_semantic_analysis
)
from ai_ui_integration import (
    add_ai_buttons_to_toolbar,
    add_ai_shortcuts_to_editor
)
from settings import get_settings
from ultis import run_in_thread

# ----- Code Highlighter -----

class CodeHighlighter(QSyntaxHighlighter):
    """Syntax highlighter cho code editor"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        
        # Định nghĩa các định dạng
        self.formats = {}
        
        # Định dạng cho từ khóa
        keyword_format = QTextCharFormat()
        keyword_format.setForeground(QColor("#c678dd"))
        keyword_format.setFontWeight(700)
        
        # Định dạng cho chuỗi
        string_format = QTextCharFormat()
        string_format.setForeground(QColor("#98c379"))
        
        # Định dạng cho comment
        comment_format = QTextCharFormat()
        comment_format.setForeground(QColor("#5c6370"))
        comment_format.setFontItalic(True)
        
        # Định dạng cho hàm
        function_format = QTextCharFormat()
        function_format.setForeground(QColor("#61afef"))
        
        # Định dạng cho số
        number_format = QTextCharFormat()
        number_format.setForeground(QColor("#d19a66"))
        
        # Lưu các định dạng
        self.formats["keyword"] = keyword_format
        self.formats["string"] = string_format
        self.formats["comment"] = comment_format
        self.formats["function"] = function_format
        self.formats["number"] = number_format
        
        # Định nghĩa các từ khóa
        self.keywords = [
            "class", "def", "for", "if", "else", "elif", "while", "return",
            "import", "from", "as", "try", "except", "finally", "with",
            "in", "is", "not", "and", "or", "True", "False", "None",
            "self", "super", "lambda", "async", "await", "yield"
        ]
        
        # Tạo các pattern
        self.patterns = []
        
        # Pattern cho từ khóa
        keyword_pattern = "\\b(" + "|".join(self.keywords) + ")\\b"
        self.patterns.append(("keyword", keyword_pattern))
        
        # Pattern cho chuỗi
        self.patterns.append(("string", "'[^']*'"))
        self.patterns.append(("string", '"[^"]*"'))
        
        # Pattern cho comment
        self.patterns.append(("comment", "#[^\n]*"))
        
        # Pattern cho hàm
        self.patterns.append(("function", "\\b[A-Za-z0-9_]+(?=\\()"))
        
        # Pattern cho số
        self.patterns.append(("number", "\\b\\d+\\b"))
    
    def highlightBlock(self, text):
        """Highlight một block text"""
        for pattern_type, pattern in self.patterns:
            format = self.formats[pattern_type]
            
            # Tìm tất cả các match
            expression = QRegularExpression(pattern)
            matches = expression.globalMatch(text)
            
            # Áp dụng định dạng cho mỗi match
            while matches.hasNext():
                match = matches.next()
                self.setFormat(match.capturedStart(), match.capturedLength(), format)

# ----- Task Dialog -----

class TaskDialog(QDialog):
    """Dialog để tạo hoặc chỉnh sửa task"""
    
    def __init__(self, parent=None, task=None):
        super().__init__(parent)
        
        self.task = task
        self.setup_ui()
        
        if task:
            self.setWindowTitle("Edit Task")
            self.fill_form_data()
        else:
            self.setWindowTitle("Create New Task")
    
    def setup_ui(self):
        """Thiết lập giao diện dialog"""
        self.setMinimumWidth(400)
        
        layout = QVBoxLayout(self)
        
        # Form
        form_layout = QFormLayout()
        
        # Task ID
        self.id_field = QLineEdit()
        if not self.task:
            task_id = f"TASK-{random.randint(100, 999)}"
            self.id_field.setText(task_id)
        form_layout.addRow("Task ID:", self.id_field)
        
        # Title
        self.title_field = QLineEdit()
        form_layout.addRow("Title:", self.title_field)
        
        # Description
        self.description_field = QTextEdit()
        self.description_field.setMinimumHeight(100)
        form_layout.addRow("Description:", self.description_field)
        
        # Status
        self.status_field = QComboBox()
        self.status_field.addItems(["todo", "in_progress", "done"])
        form_layout.addRow("Status:", self.status_field)
        
        # Priority
        self.priority_field = QComboBox()
        self.priority_field.addItems(["Low", "Medium", "High"])
        form_layout.addRow("Priority:", self.priority_field)
        
        # Due date
        self.due_date_field = QDateTimeEdit()
        self.due_date_field.setDateTime(QDateTime.currentDateTime().addDays(7))
        self.due_date_field.setCalendarPopup(True)
        form_layout.addRow("Due Date:", self.due_date_field)
        
        layout.addLayout(form_layout)
        
        # Buttons
        button_box = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)
        
        layout.addWidget(button_box)
    
    def fill_form_data(self):
        """Điền dữ liệu từ task vào form"""
        if not self.task:
            return
        
        self.id_field.setText(self.task.get("id", ""))
        self.title_field.setText(self.task.get("title", ""))
        self.description_field.setText(self.task.get("description", ""))
        
        # Thiết lập status
        status_index = self.status_field.findText(self.task.get("status", "todo"))
        if status_index >= 0:
            self.status_field.setCurrentIndex(status_index)
        
        # Thiết lập priority
        priority_index = self.priority_field.findText(self.task.get("priority", "Medium"))
        if priority_index >= 0:
            self.priority_field.setCurrentIndex(priority_index)
        
        # Thiết lập due date
        due_date = self.task.get("due_date")
        if due_date:
            if isinstance(due_date, str):
                due_date = QDateTime.fromString(due_date, Qt.DateFormat.ISODate)
            self.due_date_field.setDateTime(due_date)
    
    def get_task_data(self):
        """Lấy dữ liệu task từ form"""
        return {
            "id": self.id_field.text(),
            "title": self.title_field.text(),
            "description": self.description_field.toPlainText(),
            "status": self.status_field.currentText(),
            "priority": self.priority_field.currentText(),
            "due_date": self.due_date_field.dateTime().toString(Qt.DateFormat.ISODate)
        }
# ----- Task Card cho bảng Kanban -----

class TaskCard(QFrame):
    """Widget thẻ công việc Kanban"""
    
    taskMoved = pyqtSignal(str, str)  # id, new_status
    taskSelected = pyqtSignal(str)    # id
    taskEditRequested = pyqtSignal(str)  # id
    
    def __init__(self, task_id: str, title: str, status="todo", priority="High", parent=None):
        super().__init__(parent)
        
        self.task_id = task_id
        self.status = status
        self.title = title
        self.priority = priority
        self._drag_start_position = QPoint()
        
        # Thiết lập style
        self.setStyleSheet("""
            QFrame {
                background-color: #15151f;
                padding: 5px;
                margin: 0px;
                border: none;
            }
        """)
        
        # Thiết lập sự kiện
        self.setMinimumHeight(70)
        self.setMouseTracking(True)
        self.setAcceptDrops(True)
        
        # Tạo layout
        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 5, 5, 5)
        
        # Task ID label
        id_label = QLabel(f"[{task_id}]")
        id_label.setStyleSheet("color: #00ff00; font-weight: bold; font-size: 12px;")
        
        # Task title label
        title_label = QLabel(title)
        title_label.setStyleSheet("color: #ffffff; font-size: 12px;")
        title_label.setWordWrap(True)
        
        # Task priority label
        priority_label = QLabel(f"Priority: {priority}")
        priority_label.setStyleSheet("color: #6b6b8d; font-size: 10px;")
        
        # Thêm widget vào layout
        layout.addWidget(id_label)
        layout.addWidget(title_label)
        layout.addWidget(priority_label)
        
        # Thanh trạng thái bên trái
        indicator_color = "#00ff00"  # Màu mặc định
        if status == "in_progress":
            indicator_color = "#FFD700"  # Vàng
        
        indicator = QFrame(self)
        indicator.setFixedWidth(4)
        indicator.setFixedHeight(70)
        indicator.setStyleSheet(f"background-color: {indicator_color}; border: none;")
        indicator.move(0, 0)
    
    def mousePressEvent(self, event):
        """Xử lý sự kiện click chuột"""
        if event.button() == Qt.MouseButton.LeftButton:
            # Lưu vị trí bắt đầu kéo thả
            self._drag_start_position = event.pos()
            # Chỉ phát tín hiệu taskSelected khi click đơn, không phải khi bắt đầu kéo
            # self.taskSelected.emit(self.task_id)
        elif event.button() == Qt.MouseButton.RightButton:
            self.showContextMenu(event.pos())
        
        super().mousePressEvent(event)
    
    def mouseDoubleClickEvent(self, event):
        """Xử lý sự kiện double click"""
        if event.button() == Qt.MouseButton.LeftButton:
            self.taskEditRequested.emit(self.task_id)
        
        super().mouseDoubleClickEvent(event)
    
    def mouseReleaseEvent(self, event):
        """Xử lý sự kiện thả chuột"""
        if event.button() == Qt.MouseButton.LeftButton:
            # Nếu không phải đang kéo thả, thì coi đây là click đơn
            start_drag_distance = QApplication.startDragDistance()
            manhattan_length = (event.pos() - self._drag_start_position).manhattanLength()
            if manhattan_length < start_drag_distance:
                # Phát tín hiệu taskSelected khi click đơn
                self.taskSelected.emit(self.task_id)
        
        super().mouseReleaseEvent(event)
    
    def mouseMoveEvent(self, event):
        """Xử lý sự kiện di chuột (để kéo thả)"""
        if not hasattr(self, '_drag_start_position'):
            return
            
        if event.buttons() & Qt.MouseButton.LeftButton:
            # Kiểm tra xem đã di chuyển đủ xa để bắt đầu kéo thả chưa
            start_drag_distance = QApplication.startDragDistance()
            manhattan_length = (event.pos() - self._drag_start_position).manhattanLength()
            logging.debug(f"Manhattan length: {manhattan_length}, start drag distance: {start_drag_distance}")
            
            if manhattan_length < start_drag_distance:
                return
            
            logging.debug(f"Bắt đầu kéo thả task {self.task_id}")
                
            # Tạo mime data để kéo thả
            mime_data = QMimeData()
            mime_data.setText(self.task_id)
            mime_data.setData("application/x-task", self.task_id.encode())
            
            logging.debug(f"Đã tạo mime data cho task {self.task_id}")
            logging.debug(f"MIME formats: {mime_data.formats()}")
            
            # Tạo pixmap để hiển thị khi kéo
            pixmap = QPixmap(self.size())
            self.render(pixmap)
            
            # Tạo drag object
            drag = QDrag(self)
            drag.setMimeData(mime_data)
            drag.setPixmap(pixmap)
            drag.setHotSpot(event.pos())
            
            logging.debug(f"Đã tạo drag object cho task {self.task_id}")
            
            # Thực hiện kéo thả
            logging.debug(f"Thực hiện kéo task {self.task_id}")
            result = drag.exec(Qt.DropAction.MoveAction)
            logging.debug(f"Kết quả kéo thả: {result}")
            
            # Log kết quả kéo thả
            if result == Qt.DropAction.MoveAction:
                logging.info(f"Kéo thả thành công task {self.task_id}")
            else:
                logging.info(f"Kéo thả không thành công task {self.task_id}, kết quả: {result}")
        
        super().mouseMoveEvent(event)
    
    def showContextMenu(self, pos):
        """Hiển thị menu ngữ cảnh khi click chuột phải"""
        context_menu = QMenu(self)
        
        edit_action = context_menu.addAction("Edit Task")
        
        if self.status == "todo":
            move_action = context_menu.addAction("Move to In Progress")
        elif self.status == "in_progress":
            move_action = context_menu.addAction("Move to Done")
        else:
            move_action = context_menu.addAction("Move to To Do")
        
        delete_action = context_menu.addAction("Delete Task")
        
        # Hiển thị menu và xử lý hành động
        action = context_menu.exec(self.mapToGlobal(pos))
        
        if action == edit_action:
            self.taskEditRequested.emit(self.task_id)
        elif action == move_action:
            new_status = ""
            if self.status == "todo":
                new_status = "in_progress"
            elif self.status == "in_progress":
                new_status = "done"
            else:
                new_status = "todo"
            
            self.taskMoved.emit(self.task_id, new_status)
        elif action == delete_action:
            self.parent().parent().parent().remove_task(self.task_id)

class KanbanColumn(QWidget):
    """Widget cho một cột Kanban"""
    
    taskMoved = pyqtSignal(str, str)  # task_id, new_status
    
    def __init__(self, title: str, status: str, parent=None):
        super().__init__(parent)
        
        self.title = title
        self.status = status
        
        # Thiết lập kích thước
        self.setMinimumWidth(255)
        self.setAcceptDrops(True)
        
        # Tạo layout
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        
        # Tạo tiêu đề
        header = QFrame()
        header.setStyleSheet("""
            QFrame {
                background-color: #0a0a12;
                border: none;
            }
        """)
        header.setFixedHeight(30)
        
        # Thêm tiêu đề vào header
        header_layout = QHBoxLayout(header)
        header_layout.setContentsMargins(0, 0, 0, 0)
        title_label = QLabel(title)
        title_label.setStyleSheet("color: #ffffff; font-weight: bold; font-size: 12px;")
        
        # Thêm nút "+" để tạo task mới
        add_button = QPushButton("+")
        add_button.setStyleSheet("""
            QPushButton {
                background-color: transparent;
                color: #00ff00;
                font-weight: bold;
                font-size: 16px;
                border: none;
                max-width: 20px;
            }
            QPushButton:hover {
                color: #ffffff;
            }
        """)
        add_button.clicked.connect(self.add_new_task)
        
        header_layout.addWidget(title_label)
        header_layout.addWidget(add_button, 0, Qt.AlignmentFlag.AlignRight)
        
        # Tạo vùng nội dung
        content = QWidget()
        content.setStyleSheet("""
            QWidget {
                background-color: #121218;
                border: none;
            }
        """)
        
        # Tạo vùng cuộn
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet("""
            QScrollArea {
                border: none;
                background-color: transparent;
            }
            QScrollBar:vertical {
                border: none;
                background: #121218;
                width: 10px;
                margin: 0px;
            }
            QScrollBar::handle:vertical {
                background: #2a2a3a;
                min-height: 20px;
                border-radius: 5px;
            }
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
                border: none;
                background: none;
            }
            QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical {
                background: none;
            }
        """)
        
        # Tạo container cho task
        task_container = QWidget()
        self.task_layout = QVBoxLayout(task_container)
        self.task_layout.setSpacing(10)
        self.task_layout.setContentsMargins(10, 10, 10, 10)
        self.task_layout.addStretch()
        
        # Thêm task container vào scroll area
        scroll.setWidget(task_container)
        
        # Tạo layout nội dung
        content_layout = QVBoxLayout(content)
        content_layout.setContentsMargins(0, 0, 0, 0)
        content_layout.addWidget(scroll)
        
        # Thêm header và content vào layout
        layout.addWidget(header)
        layout.addWidget(content, 1)
    
    def add_task(self, task_id: str, title: str, priority: str = "Medium") -> TaskCard:
        """Thêm task vào cột"""
        task_card = TaskCard(task_id, title, self.status, priority)
        task_card.taskSelected.connect(self.on_task_selected)
        task_card.taskMoved.connect(self.on_task_moved)
        task_card.taskEditRequested.connect(self.on_task_edit_requested)
        
        self.task_layout.insertWidget(self.task_layout.count() - 1, task_card)
        return task_card
    
    def remove_task(self, task_id: str) -> bool:
        """Xóa task khỏi cột"""
        logging.debug(f"Xóa task {task_id} khỏi cột {self.status}")
        for i in range(self.task_layout.count()):
            widget = self.task_layout.itemAt(i).widget()
            if isinstance(widget, TaskCard) and widget.task_id == task_id:
                self.task_layout.removeWidget(widget)
                widget.hide()
                widget.deleteLater()
                return True
        return False
    
    def get_task_count(self) -> int:
        """Lấy số lượng task trong cột"""
        return self.task_layout.count() - 1  # Trừ 1 cho stretch item
    
    def add_new_task(self):
        """Mở dialog để tạo task mới"""
        dialog = TaskDialog(self)
        
        if dialog.exec() == QDialog.DialogCode.Accepted:
            task_data = dialog.get_task_data()
            
            # Thêm task mới
            task_card = self.add_task(task_data["id"], task_data["title"], task_data["priority"])
            
            # Lưu vào bộ nhớ của MainWindow
            parent = self.parent()
            while parent:
                if hasattr(parent, "tasks"):
                    # Lưu task vào bộ nhớ của MainWindow
                    task_data["status"] = self.status  # Gán trạng thái cho task mới
                    parent.tasks[task_data["id"]] = task_data
                    break
                parent = parent.parent()
            
            # Thông báo task mới được tạo
            logging.info(f"Tạo task mới {task_data['id']} trong cột {self.title} ({self.status})")
            print(f"Đã tạo task mới: {task_data}")
    
    def on_task_selected(self, task_id: str):
        """Xử lý khi task được chọn"""
        # Truyền sự kiện lên parent widget
        parent = self.parent()
        while parent:
            if hasattr(parent, "on_task_selected"):
                parent.on_task_selected(task_id)
                break
            parent = parent.parent()
    
    def on_task_moved(self, task_id: str, new_status: str):
        """Xử lý khi task được di chuyển"""
        # Truyền sự kiện lên parent widget
        logging.debug(f"KanbanColumn: Phát tín hiệu di chuyển task {task_id} sang {new_status}")
        self.taskMoved.emit(task_id, new_status)
    
    def on_task_edit_requested(self, task_id: str):
        """Xử lý khi yêu cầu chỉnh sửa task"""
        # Truyền sự kiện lên parent widget
        parent = self.parent()
        while parent:
            if hasattr(parent, "on_task_edit_requested"):
                parent.on_task_edit_requested(task_id)
                break
            parent = parent.parent()
    
    def dragEnterEvent(self, event):
        """Xử lý sự kiện khi kéo vào vùng"""
        logging.debug(f"dragEnterEvent cho cột {self.title}")
        logging.debug(f"MIME formats: {event.mimeData().formats()}")
        
        if event.mimeData().hasText():
            logging.debug(f"MIME text: {event.mimeData().text()}")
            
        if event.mimeData().hasFormat("application/x-task"):
            task_id = event.mimeData().data("application/x-task").data().decode()
            logging.debug(f"Chấp nhận kéo task {task_id} vào cột {self.title}")
            event.setDropAction(Qt.DropAction.MoveAction)
            event.accept()
        else:
            logging.debug(f"Từ chối kéo vào cột {self.title} (không phải task)")
            # Thử kiểm tra nếu có text
            if event.mimeData().hasText():
                task_id = event.mimeData().text()
                logging.debug(f"Nhưng có text: {task_id}, thử chấp nhận")
                event.setDropAction(Qt.DropAction.MoveAction)
                event.accept()
            else:
                event.ignore()
    
    def dragMoveEvent(self, event):
        """Xử lý sự kiện khi kéo trong vùng"""
        if event.mimeData().hasFormat("application/x-task") or event.mimeData().hasText():
            event.setDropAction(Qt.DropAction.MoveAction)
            event.accept()
        else:
            logging.debug(f"Từ chối kéo trong cột {self.title} (không phải task)")
            event.ignore()
    
    def dropEvent(self, event):
        """Xử lý sự kiện khi thả vào vùng"""
        logging.debug(f"dropEvent cho cột {self.title}")
        logging.debug(f"MIME formats: {event.mimeData().formats()}")
        
        # Kiểm tra xem sự kiện có phải từ nút + hay không
        source_widget = event.source()
        if source_widget and isinstance(source_widget, QPushButton):
            logging.debug("Sự kiện từ nút +, bỏ qua")
            event.ignore()
            return
        
        task_id = None
        
        if event.mimeData().hasFormat("application/x-task"):
            task_id = event.mimeData().data("application/x-task").data().decode()
            logging.debug(f"Nhận được task {task_id} thả vào cột {self.title} từ MIME data")
        elif event.mimeData().hasText():
            task_id = event.mimeData().text()
            logging.debug(f"Nhận được task {task_id} thả vào cột {self.title} từ text")
        
        if task_id:
            # Tìm task card nguồn
            source_card = None
            source_column = None
            for column in self.parent().findChildren(KanbanColumn):
                for i in range(column.task_layout.count()):
                    widget = column.task_layout.itemAt(i).widget()
                    if isinstance(widget, TaskCard) and widget.task_id == task_id:
                        source_card = widget
                        source_column = column
                        break
                if source_card:
                    break
            
            if source_card:
                logging.debug(f"Tìm thấy source card cho task {task_id} ở cột {source_column.title} ({source_column.status})")
                
                if source_column.status != self.status:
                    # Di chuyển task sang cột mới
                    logging.info(f"Kéo thả task {task_id} từ cột {source_column.title} ({source_column.status}) sang cột {self.title} ({self.status})")
                    self.taskMoved.emit(task_id, self.status)
                    event.setDropAction(Qt.DropAction.MoveAction)
                    event.accept()
                    return
                else:
                    logging.info(f"Task {task_id} đã ở trong cột {self.title} ({self.status}), không cần di chuyển")
                    event.accept()
                    return
            else:
                logging.warning(f"Không tìm thấy source card cho task {task_id}")
        
        logging.warning("Từ chối thả (không đủ thông tin hoặc không phải task)")
        event.ignore()

# ----- Widget Snapshot -----

class SnapshotList(QWidget):
    """Widget hiển thị danh sách snapshot"""
    
    snapshotSelected = pyqtSignal(dict)  # snapshot_data
    
    def __init__(self, parent=None):
        super().__init__(parent)
        
        # Thiết lập layout
        layout = QVBoxLayout(self)
        
        # Tiêu đề
        title = QLabel("Snapshots")
        title.setStyleSheet("color: #00ff00; font-weight: bold; font-size: 14px;")
        
        # Danh sách snapshot
        self.list_widget = QListWidget()
        self.list_widget.setStyleSheet("""
            QListWidget {
                background-color: #15151f;
                border: none;
                color: #ffffff;
            }
            QListWidget::item {
                padding: 5px;
                border-bottom: 1px solid #2a2a3a;
            }
            QListWidget::item:selected {
                background-color: #2a2a3a;
                color: #00ff00;
            }
        """)
        self.list_widget.currentItemChanged.connect(self.on_item_selected)
        
        # Thêm widget vào layout
        layout.addWidget(title)
        layout.addWidget(self.list_widget)
    
    def add_snapshot(self, snapshot_data: dict):
        """Thêm snapshot vào danh sách"""
        timestamp = snapshot_data.get("timestamp", datetime.datetime.now())
        formatted_time = timestamp.strftime("%H:%M:%S")
        
        item = QListWidgetItem(f"{formatted_time} - Snapshot #{snapshot_data.get('id', 0)}")
        item.setData(Qt.ItemDataRole.UserRole, snapshot_data)
        
        self.list_widget.addItem(item)
    
    def clear_snapshots(self):
        """Xóa tất cả snapshot"""
        self.list_widget.clear()
    
    def on_item_selected(self, current, previous):
        """Xử lý khi chọn snapshot"""
        if current:
            snapshot_data = current.data(Qt.ItemDataRole.UserRole)
            self.snapshotSelected.emit(snapshot_data)

# ----- Tạo cửa sổ chính -----

class MainWindow(QMainWindow):
    """Cửa sổ chính của ứng dụng"""
    
    # --- Gắn các hàm AI helper vào MainWindow để dùng self.<func> ---
    get_code_from_editor = get_code_from_editor
    ai_analyze_code_quality = ai_analyze_code_quality
    ai_find_code_issues = ai_find_code_issues
    ai_generate_docstring = ai_generate_docstring
    ai_suggest_refactor = ai_suggest_refactor
    ai_semantic_analysis = ai_semantic_analysis
    
    def __init__(self):
        super().__init__()
        
        # Thiết lập thuộc tính chính
        self.api_client = None
        self.current_project = None
        self.current_file = None
        self.current_task = None
        self.snapshots = {}  # {file_path: [snapshot1, snapshot2, ...]}
        self.tasks = {}  # {task_id: task_data}
        self.settings = get_settings()
        
        # Thiết lập cửa sổ
        self.setWindowTitle("WindSurf Memory Tracker")
        self.resize(1200, 800)
        
        # Thiết lập style
        self.apply_theme()
        
        # Tạo widget chính
        self.central_widget = QWidget()
        self.main_layout = QVBoxLayout(self.central_widget)
        self.main_layout.setContentsMargins(0, 0, 0, 0)
        self.main_layout.setSpacing(0)
        self.setCentralWidget(self.central_widget)
        
        # Tạo thanh công cụ
        self.create_toolbar()
        
        # Tạo widgets và layout chính
        self.create_main_layout()
        
        # Tạo thanh trạng thái
        self.create_status_bar()
        
        # Khởi tạo API client (giả lập)
        self.init_api_client()
        
        # Khởi tạo cơ sở dữ liệu
        self.init_database()
        
        # Tạo dữ liệu demo
        self.load_sample_data()
        
        # Thiết lập timer cập nhật
        self.update_timer = QTimer(self)
        self.update_timer.timeout.connect(self.update_ui)
        self.update_timer.start(60000)  # Cập nhật mỗi phút

    def apply_theme(self):
        """Áp dụng theme cho ứng dụng"""
        self.setStyleSheet("""
            QMainWindow {
                background-color: #000000;
            }
            QWidget {
                color: #ffffff;
                font-family: Arial, sans-serif;
            }
            QPushButton {
                background-color: #121218;
                border: none;
                border-radius: 5px;
                padding: 5px 10px;
                color: #ffffff;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #1f1f2e;
            }
            QPushButton:pressed {
                background-color: #00ff00;
                color: #000000;
            }
            QLineEdit {
                background-color: #1c1c27;
                border: 1px solid #2d2d3d;
                border-radius: 15px;
                padding: 5px 10px;
                color: #ffffff;
            }
            QTextEdit {
                background-color: #000000;
                border: none;
                color: #abb2bf;
                font-family: Consolas, monospace;
                selection-background-color: #2c3e50;
                selection-color: #ffffff;
            }
            QSplitter::handle {
                background-color: #000000;
            }
            QTabBar::tab {
                background-color: #121218;
                color: #6b6b8d;
                padding: 5px 10px;
                margin-right: 2px;
                border: none;
            }
            QTabBar::tab:selected {
                background-color: #00ff00;
                color: #000000;
                font-weight: bold;
            }
            QTabWidget::pane {
                border: none;
            }
            QDialog {
                background-color: #0f0f17;
            }
            QLabel {
                color: #ffffff;
            }
            QComboBox {
                background-color: #1c1c27;
                border: 1px solid #2d2d3d;
                border-radius: 5px;
                padding: 5px;
                color: #ffffff;
            }
            QComboBox::drop-down {
                border: none;
            }
            QComboBox::down-arrow {
                image: none;
                border-left: 5px solid transparent;
                border-right: 5px solid transparent;
                border-top: 5px solid #ffffff;
                width: 0;
                height: 0;
                margin-right: 5px;
            }
            QComboBox QAbstractItemView {
                background-color: #1c1c27;
                border: 1px solid #2d2d3d;
                selection-background-color: #2a2a3a;
                selection-color: #ffffff;
            }
            QDateTimeEdit {
                background-color: #1c1c27;
                border: 1px solid #2d2d3d;
                border-radius: 5px;
                padding: 5px;
                color: #ffffff;
            }
        """)
    
    def create_toolbar(self):
        """Tạo thanh công cụ chính"""
        toolbar = QToolBar()
        toolbar.setStyleSheet("""
            QToolBar {
                background-color: #000000;
                border: none;
                spacing: 10px;
            }
            QToolButton {
                background-color: transparent;
                border: none;
                color: #ffffff;
                font-weight: bold;
                font-size: 16px;
                padding: 5px 10px;
            }
            QToolButton:hover {
                background-color: #1c1c27;
                border-radius: 5px;
            }
        """)
        toolbar.setMovable(False)
        toolbar.setIconSize(QSize(16, 16))
        toolbar.setFixedHeight(60)
        
        # Logo
        logo_label = QLabel()
        logo_label.setFixedSize(36, 36)
        logo_label.setStyleSheet("""
            QLabel {
                background-color: #00ff00;
                border-radius: 4px;
                color: #000000;
                font-weight: bold;
                font-size: 18px;
                text-align: center;
            }
        """)
        logo_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        logo_label.setText("</>");
        
        # Tên ứng dụng
        app_name = QLabel("WindSurf_Memory")
        app_name.setStyleSheet("color: #00ff00; font-weight: bold; font-size: 20px;")
        
        # Các nút menu
        projects_btn = QPushButton("Projects")
        projects_btn.setStyleSheet("""
            QPushButton {
                background-color: transparent;
                border: none;
                color: #ffffff;
                font-weight: bold;
                font-size: 16px;
            }
            QPushButton:hover {
                color: #00ff00;
            }
        """)
        projects_btn.clicked.connect(self.show_projects)
        
        tasks_btn = QPushButton("Tasks")
        tasks_btn.setStyleSheet("""
            QPushButton {
                background-color: transparent;
                border: none;
                color: #ffffff;
                font-weight: bold;
                font-size: 16px;
            }
            QPushButton:hover {
                color: #00ff00;
            }
        """)
        tasks_btn.clicked.connect(self.show_tasks)
        
        analytics_btn = QPushButton("Analytics")
        analytics_btn.setStyleSheet("""
            QPushButton {
                background-color: transparent;
                border: none;
                color: #ffffff;
                font-weight: bold;
                font-size: 16px;
            }
            QPushButton:hover {
                color: #00ff00;
            }
        """)
        analytics_btn.clicked.connect(self.show_analytics)
        
        terminal_btn = QPushButton("Terminal")
        terminal_btn.setStyleSheet("""
            QPushButton {
                background-color: transparent;
                border: none;
                color: #ffffff;
                font-weight: bold;
                font-size: 16px;
            }
            QPushButton:hover {
                color: #00ff00;
            }
        """)
        terminal_btn.clicked.connect(self.show_terminal)
        
        # --- Thêm các nút AI vào toolbar ---
        add_ai_buttons_to_toolbar(self, toolbar)
        
        # --- Thêm nút giả lập sự kiện vào toolbar ---
        simulate_btn = QAction(" Simulate", self)
        simulate_btn.triggered.connect(self.simulate_editor_events)
        simulate_btn.setToolTip("Simulate editor events (Dev Mode)")
        toolbar.addAction(simulate_btn)
        
        # Spacer
        spacer1 = QWidget()
        spacer1.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Expanding)
        spacer1.setFixedWidth(50)
        
        spacer2 = QWidget()
        spacer2.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        
        # Thanh tìm kiếm
        search_box = QLineEdit()
        search_box.setPlaceholderText("Search...")
        search_box.setFixedWidth(200)
        search_box.setFixedHeight(30)
        search_box.returnPressed.connect(self.search)
        
        # Biểu tượng người dùng
        user_icon = QLabel()
        user_icon.setFixedSize(40, 40)
        user_icon.setStyleSheet("""
            QLabel {
                background-color: #00ff00;
                border-radius: 20px;
            }
        """)
        
        # Thêm widgets vào toolbar
        toolbar.addWidget(logo_label)
        toolbar.addWidget(app_name)
        toolbar.addWidget(spacer1)
        toolbar.addWidget(projects_btn)
        toolbar.addWidget(tasks_btn)
        toolbar.addWidget(analytics_btn)
        toolbar.addWidget(terminal_btn)
        toolbar.addWidget(spacer2)
        toolbar.addWidget(search_box)
        toolbar.addWidget(user_icon)
        
        self.addToolBar(toolbar)

    def create_main_layout(self):
        """Tạo layout chính cho ứng dụng"""
        content_widget = QWidget()
        content_layout = QHBoxLayout(content_widget)
        content_layout.setContentsMargins(10, 10, 10, 10)
        
        # Tạo splitter chính giữa nội dung và sidebar
        main_splitter = QSplitter(Qt.Orientation.Horizontal)
        
        # Tạo vùng nội dung chính bên trái
        left_widget = QWidget()
        left_layout = QVBoxLayout(left_widget)
        left_layout.setContentsMargins(0, 0, 0, 0)
        left_layout.setSpacing(20)
        
        # Tạo editor area
        editor_area = QWidget()
        editor_area_layout = QVBoxLayout(editor_area)
        editor_area_layout.setContentsMargins(0, 0, 0, 0)
        editor_area_layout.setSpacing(0)
        
        # Tab widget cho editor
        self.editor_tab = QTabWidget()
        self.editor_tab.setStyleSheet("""
            QTabWidget::pane {
                background-color: #000000;
                border: none;
            }
            QTabBar::tab {
                background-color: #121218;
                color: #6b6b8d;
                padding: 5px 10px;
                margin-right: 2px;
                border: none;
            }
            QTabBar::tab:selected {
                background-color: #00ff00;
                color: #000000;
                font-weight: bold;
            }
        """)
        
        # Tạo code editor
        self.code_editor = QTextEdit()
        self.code_editor.setPlainText("""class MemoryTracker:
    def __init__(self, editor, options):
        self.editor = editor
        self.options = options
        self.history = []
    
    def track_changes(self):
        snapshot = self.editor.get_content()
        self.analyze_changes(snapshot)
        self.history.push({
            "timestamp": Date.now(),
            "content": snapshot
        })
""")
        self.code_editor.setStyleSheet("""
            QTextEdit {
                background-color: #000000;
                color: #ffffff;
                border: none;
                font-family: Consolas, monospace;
                font-size: 12px;
                padding: 10px;
            }
        """)
        
        # Đăng ký phím tắt AI cho code editor
        add_ai_shortcuts_to_editor(self)
        
        # Áp dụng syntax highlighting
        self.highlighter = CodeHighlighter(self.code_editor.document())
        
        # Tạo các editor tab
        self.editor_tab.addTab(self.code_editor, "MemoryTracker.js")
        
        # Tạo tab trống cho các file khác
        empty_widget1 = QWidget()
        empty_widget2 = QWidget()
        self.editor_tab.addTab(empty_widget1, "KanbanBoard.js")
        self.editor_tab.addTab(empty_widget2, "AIAnalyzer.js")
        
        # Thêm tab vào editor area
        editor_area_layout.addWidget(self.editor_tab)
        
        # Tạo tiêu đề cho bảng Kanban
        kanban_label = QLabel("TASK KANBAN")
        kanban_label.setStyleSheet("""
            QLabel {
                background-color: #000000;
                color: #00ff00;
                font-weight: bold;
                font-size: 14px;
                padding: 10px 0;
            }
        """)
        
        # Tạo bảng Kanban
        kanban_widget = QWidget()
        kanban_layout = QHBoxLayout(kanban_widget)
        kanban_layout.setSpacing(15)
        kanban_layout.setContentsMargins(0, 0, 0, 0)
        
        # Tạo các cột Kanban
        self.todo_column = KanbanColumn("TO DO", "todo")
        self.in_progress_column = KanbanColumn("IN PROGRESS", "in_progress")
        self.done_column = KanbanColumn("DONE", "done")
        
        # Kết nối tín hiệu
        self.todo_column.taskMoved.connect(self.move_task)
        self.in_progress_column.taskMoved.connect(self.move_task)
        self.done_column.taskMoved.connect(self.move_task)
        
        # Thêm cột vào layout Kanban
        kanban_layout.addWidget(self.todo_column)
        kanban_layout.addWidget(self.in_progress_column)
        kanban_layout.addWidget(self.done_column)
        
        # Thêm editor và Kanban vào layout trái
        left_layout.addWidget(editor_area, 1)
        left_layout.addWidget(kanban_label)
        left_layout.addWidget(kanban_widget, 1)
        
        # Tạo sidebar phải
        right_widget = QWidget()
        right_widget.setMaximumWidth(310)
        right_widget.setStyleSheet("background-color: #000000;")
        right_layout = QVBoxLayout(right_widget)
        right_layout.setContentsMargins(10, 10, 10, 10)
        right_layout.setSpacing(20)
        
        # Ngày
        self.date_label = QLabel(datetime.datetime.now().strftime("%A, %B %d, %Y"))
        self.date_label.setStyleSheet("color: #6b6b8d; font-size: 14px; text-align: right;")
        self.date_label.setAlignment(Qt.AlignmentFlag.AlignRight)
        
        # Tiêu đề Memory Stats
        stats_header = QLabel("MEMORY STATS")
        stats_header.setStyleSheet("color: #00ff00; font-weight: bold; font-size: 18px;")
        
        # Widget tổng số thay đổi
        total_changes = QFrame()
        total_changes.setStyleSheet("""
            QFrame {
                background-color: #15151f;
                border-radius: 5px;
            }
        """)
        total_changes_layout = QVBoxLayout(total_changes)
        
        changes_title = QLabel("Total Changes Tracked")
        changes_title.setStyleSheet("color: #ffffff; font-size: 14px;")
        
        self.changes_value = QLabel("5,421")
        self.changes_value.setStyleSheet("color: #00ff00; font-weight: bold; font-size: 30px;")
        
        total_changes_layout.addWidget(changes_title)
        total_changes_layout.addWidget(self.changes_value)
        
        # Biểu đồ hoạt động
        activity_title = QLabel("Activity Last 7 Days")
        activity_title.setStyleSheet("color: #ffffff; font-size: 14px;")
        
        activity_graph = QFrame()
        activity_graph.setStyleSheet("""
            QFrame {
                background-color: #15151f;
                border-radius: 5px;
                padding: 10px;
            }
        """)
        activity_graph.setMinimumHeight(100)
        
        graph_placeholder = QLabel("[ Activity Graph Placeholder ]")
        graph_placeholder.setStyleSheet("color: #00ff00; font-size: 14px;")
        graph_placeholder.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        activity_layout = QVBoxLayout(activity_graph)
        activity_layout.addWidget(graph_placeholder)
        
        # Tiêu đề AI Insights
        ai_header = QLabel("AI INSIGHTS")
        ai_header.setStyleSheet("color: #00ff00; font-weight: bold; font-size: 18px;")
        
        # Tiêu đề sức khỏe code
        code_health_title = QLabel("Code Health")
        code_health_title.setStyleSheet("color: #00ff00; font-weight: bold; font-size: 14px;")
        
        # Widget sức khỏe code
        code_health_widget = QFrame()
        code_health_widget.setStyleSheet("""
            QFrame {
                background-color: #15151f;
                border-radius: 5px;
                padding: 10px;
            }
        """)
        
        # Thanh sức khỏe
        health_bar = QFrame()
        health_bar.setFixedHeight(5)
        health_bar.setFixedWidth(184)  # 80% of 230
        health_bar.setStyleSheet("background-color: #00ff00; border-radius: 2px;")
        
        health_value = QLabel("80% - Good")
        health_value.setStyleSheet("color: #ffffff; font-size: 12px;")
        
        health_details = QLabel("Identified 2 potential refactorings")
        health_details.setStyleSheet("color: #6b6b8d; font-size: 10px;")
        
        code_health_layout = QVBoxLayout(code_health_widget)
        code_health_layout.addWidget(health_bar)
        code_health_layout.addWidget(health_value)
        code_health_layout.addWidget(health_details)
        
        # Tiêu đề hoạt động gần đây
        recent_activity_title = QLabel("Recent Activity")
        recent_activity_title.setStyleSheet("color: #00ff00; font-weight: bold; font-size: 14px;")
        
        # Widget hoạt động gần đây
        recent_activity_widget = QFrame()
        recent_activity_widget.setObjectName("recent_activity_widget")
        recent_activity_widget.setStyleSheet("""
            QFrame {
                background-color: #15151f;
                border-radius: 5px;
                padding: 10px;
            }
        """)
        
        # Tạo layout cho hoạt động gần đây
        recent_activity_layout = QVBoxLayout(recent_activity_widget)
        
        # Thêm các mục hoạt động
        self.activity_items = []
        
        activity1 = QLabel("• Modified MemoryTracker.js")
        activity1.setStyleSheet("color: #ffffff; font-size: 12px;")
        
        time1 = QLabel("5 minutes ago")
        time1.setStyleSheet("color: #6b6b8d; font-size: 10px;")
        
        activity2 = QLabel("• Created KanbanBoard.js")
        activity2.setStyleSheet("color: #ffffff; font-size: 12px;")
        
        time2 = QLabel("47 minutes ago")
        time2.setStyleSheet("color: #6b6b8d; font-size: 10px;")
        
        activity3 = QLabel("• Completed Task-101")
        activity3.setStyleSheet("color: #ffffff; font-size: 12px;")
        
        time3 = QLabel("2 hours ago")
        time3.setStyleSheet("color: #6b6b8d; font-size: 10px;")
        
        # Thêm hoạt động vào layout
        recent_activity_layout.addWidget(activity1)
        recent_activity_layout.addWidget(time1)
        recent_activity_layout.addSpacing(10)
        recent_activity_layout.addWidget(activity2)
        recent_activity_layout.addWidget(time2)
        recent_activity_layout.addSpacing(10)
        recent_activity_layout.addWidget(activity3)
        recent_activity_layout.addWidget(time3)
        
        # Lưu các mục hoạt động để cập nhật sau
        self.activity_items = [
            (activity1, time1),
            (activity2, time2),
            (activity3, time3)
        ]
        
        # Thêm widgets vào sidebar
        right_layout.addWidget(self.date_label)
        right_layout.addWidget(stats_header)
        right_layout.addWidget(total_changes)
        right_layout.addWidget(activity_title)
        right_layout.addWidget(activity_graph)
        right_layout.addWidget(ai_header)
        right_layout.addWidget(code_health_title)
        right_layout.addWidget(code_health_widget)
        right_layout.addWidget(recent_activity_title)
        right_layout.addWidget(recent_activity_widget)
        right_layout.addStretch()
        
        # Thêm widgets vào splitter
        main_splitter.addWidget(left_widget)
        main_splitter.addWidget(right_widget)
        
        # Thiết lập tỷ lệ kéo
        main_splitter.setStretchFactor(0, 7)
        main_splitter.setStretchFactor(1, 3)
        
        # Thêm splitter vào content
        content_layout.addWidget(main_splitter)
        
        # Thêm content vào layout chính
        self.main_layout.addWidget(content_widget)
    
    def create_status_bar(self):
        """Tạo thanh trạng thái"""
        status_bar = QStatusBar()
        status_bar.setStyleSheet("""
            QStatusBar {
                background-color: #000000;
                color: #6b6b8d;
            }
        """)
        
        # Thêm thông tin vào status bar
        status_bar.addPermanentWidget(QLabel("WindSurf Memory Tracker v1.0.0"))
        
        self.setStatusBar(status_bar)
    
    def init_api_client(self):
        """Khởi tạo API client"""
        # Khởi tạo API client trong luồng riêng
        def init_api():
            return create_api_client(use_mock=True)
            
        def on_api_ready(api_client):
            self.api_client = api_client
            logging.info("API client đã được khởi tạo")
            self.statusBar().showMessage("API client đã sẵn sàng", 3000)
            
            # Đăng ký callback xử lý sự kiện từ WindSurf Editor
            self.api_client.on_editor_event(self.handle_editor_event)
            
        def on_api_error(error_info):
            logging.error(f"Lỗi khởi tạo API client: {error_info[1]}")
            self.statusBar().showMessage("Không thể kết nối đến API", 5000)
            # Sử dụng API giả lập trong trường hợp lỗi
            self.api_client = create_api_client(use_mock=True)
            
        # Hiển thị thông báo đang kết nối
        self.statusBar().showMessage("Đang kết nối đến API...")
        
        # Chạy trong luồng riêng
        run_in_thread(
            self, 
            init_api, 
            progress_text="Đang kết nối đến API...",
            on_result=on_api_ready,
            on_error=on_api_error
        )
    
    def handle_editor_event(self, event_data):
        """Xử lý sự kiện từ WindSurf Editor"""
        event_type = event_data.get('type')
        logging.info(f"[DEBUG] Đã gọi handle_editor_event với event_type: {event_type}")
        logging.info(f"[DEBUG] event_data đầy đủ: {event_data}")
        
        if event_type == 'task_created':
            logging.info(f"[DEBUG] Gọi handle_task_created với event_data: {event_data}")
            self.handle_task_created(event_data)
        elif event_type == 'task_updated':
            logging.info(f"[DEBUG] Gọi handle_task_updated với event_data: {event_data}")
            self.handle_task_updated(event_data)
        elif event_type == 'file_linked_to_task':
            logging.info(f"[DEBUG] Gọi handle_file_linked_to_task với event_data: {event_data}")
            self.handle_file_linked_to_task(event_data)
    
    def simulate_editor_events(self):
        """Giả lập các sự kiện từ editor để kiểm thử"""
        if not self.api_client:
            logging.error("API client chưa được khởi tạo")
            return

        try:
            logging.info("\n=== Bắt đầu giả lập sự kiện từ editor ===")
            
            # Tạo task mới
            task_id = "WIND-DEMO-" + datetime.datetime.now().strftime('%H%M%S')
            self._simulate_task_created(
                task_id=task_id,
                title="[DEMO] Task giả lập",
                description="Task được tạo tự động để kiểm thử",
                priority="Medium"
            )
            
            # Cập nhật trạng thái task
            self._simulate_task_updated(
                task_id=task_id,
                new_status="in_progress"
            )
            
            logging.info("=== Hoàn thành giả lập ===")
        except Exception as e:
            logging.error(f"Lỗi khi giả lập: {str(e)}")

    def _simulate_task_created(self, task_id: str, title: str, description: str, priority: str):
        event_data = {
            'type': 'task_created',
            'task_id': task_id,
            'title': title,
            'description': description,
            'priority': priority,
            'status': 'todo',
            'timestamp': datetime.datetime.now().isoformat(),
            'source': 'windsurf_editor'
        }
        self.api_client._notify_editor_event(event_data)
        logging.debug(f"Đã giả lập tạo task: {task_id}")

    def _simulate_task_updated(self, task_id: str, new_status: str):
        event_data = {
            'type': 'task_updated',
            'task_id': task_id,
            'changes': {'status': new_status},
            'timestamp': datetime.datetime.now().isoformat(),
            'source': 'windsurf_editor'
        }
        self.api_client._notify_editor_event(event_data)
        logging.debug(f"Đã giả lập cập nhật task: {task_id} -> {new_status}")

    def handle_task_created(self, event_data):
        """Xử lý sự kiện tạo task mới"""
        task_id = event_data.get('task_id')
        title = event_data.get('title')
        status = event_data.get('status', 'todo')
        priority = event_data.get('priority', 'Medium')
        description = event_data.get('description', '')
        
        # Thêm task vào cột Kanban tương ứng
        if status == 'todo':
            self.todo_column.add_task(task_id, title, priority)
        elif status == 'in_progress':
            self.in_progress_column.add_task(task_id, title, priority)
        elif status == 'done':
            self.done_column.add_task(task_id, title, priority)
        
        # Lưu thông tin task
        self.tasks[task_id] = {
            "id": task_id,
            "title": title,
            "description": description,
            "status": status,
            "priority": priority,
            "created_at": datetime.datetime.now().isoformat()
        }
        
        # Thêm vào hoạt động gần đây
        self.add_recent_activity(f"Task mới: {task_id} - {title}")
        
        # Hiển thị thông báo
        self.statusBar().showMessage(f"Đã nhận task mới từ WindSurf Editor: {task_id}", 3000)
    
    def handle_task_updated(self, event_data):
        """Xử lý sự kiện cập nhật task"""
        task_id = event_data.get('task_id')
        changes = event_data.get('changes', {})
        
        # Kiểm tra xem task có tồn tại không
        if task_id not in self.tasks:
            logging.warning(f"Không tìm thấy task {task_id} để cập nhật")
            return
        
        # Cập nhật trạng thái task nếu có
        new_status = changes.get('status')
        if new_status:
            old_status = self.tasks[task_id]['status']
            self.move_task(task_id, new_status)
            self.add_recent_activity(f"Task {task_id} chuyển từ {old_status} sang {new_status}")
        
        # Cập nhật các thông tin khác
        for key, value in changes.items():
            if key != 'status':
                self.tasks[task_id][key] = value
        
        # Hiển thị thông báo
        self.statusBar().showMessage(f"Đã cập nhật task {task_id} từ WindSurf Editor", 3000)
    
    def handle_file_linked_to_task(self, event_data):
        """Xử lý sự kiện liên kết file với task"""
        task_id = event_data.get('task_id')
        file_path = event_data.get('file_path')
        
        # Kiểm tra xem task có tồn tại không
        if task_id not in self.tasks:
            logging.warning(f"Không tìm thấy task {task_id} để liên kết file")
            return
        
        # Thêm file vào danh sách file của task
        if 'files' not in self.tasks[task_id]:
            self.tasks[task_id]['files'] = []
        
        self.tasks[task_id]['files'].append(file_path)
        
        # Thêm vào hoạt động gần đây
        file_name = os.path.basename(file_path)
        self.add_recent_activity(f"File {file_name} được liên kết với task {task_id}")
        
        # Hiển thị thông báo
        self.statusBar().showMessage(f"Đã liên kết file {file_name} với task {task_id}", 3000)
    
    def init_database(self):
        """Khởi tạo cơ sở dữ liệu"""
        # Trong phiên bản này, chúng ta sẽ giả lập bằng cách sử dụng dictionary
        pass
    
    def load_sample_data(self):
        """Tải dữ liệu mẫu"""
        # Tạo dữ liệu mẫu trong luồng riêng để tránh đóng băng UI
        def create_sample_data():
            # Tạo các task mẫu
            tasks = {
                "TASK-101": {
                    "id": "TASK-101",
                    "title": "Implement memory tracking",
                    "description": "Create core functionality for tracking code changes",
                    "status": "done",
                    "priority": "High",
                    "due_date": QDateTime.currentDateTime().toString(Qt.DateFormat.ISODate)
                },
                "TASK-102": {
                    "id": "TASK-102",
                    "title": "Design Kanban board",
                    "description": "Create UI for task management using Kanban approach",
                    "status": "in_progress",
                    "priority": "Medium",
                    "due_date": QDateTime.currentDateTime().toString(Qt.DateFormat.ISODate)
                },
                "TASK-103": {
                    "id": "TASK-103",
                    "title": "Integrate AI analysis",
                    "description": "Add AI-powered code analysis features",
                    "status": "todo",
                    "priority": "High",
                    "due_date": QDateTime.currentDateTime().toString(Qt.DateFormat.ISODate)
                },
                "TASK-104": {
                    "id": "TASK-104",
                    "title": "Create snapshot system",
                    "description": "Implement code snapshot and version comparison",
                    "status": "todo",
                    "priority": "Medium",
                    "due_date": QDateTime.currentDateTime().toString(Qt.DateFormat.ISODate)
                }
            }
            
            # Tạo một số snapshot mẫu
            snapshots = {
                "/path/to/sample/file.py": [
                    {
                        "id": "snap-001",
                        "timestamp": datetime.datetime.now().isoformat(),
                        "content": "def sample_function():\n    return 'Hello World!'",
                        "related_task": "TASK-101"
                    }
                ]
            }
            
            return {"tasks": tasks, "snapshots": snapshots}
        
        def on_data_loaded(data):
            # Cập nhật dữ liệu
            self.tasks = data["tasks"]
            self.snapshots = data["snapshots"]
            
            # Thêm task vào bảng Kanban
            for task_id, task_data in self.tasks.items():
                if task_data["status"] == "todo":
                    self.todo_column.add_task(task_id, task_data["title"], task_data["priority"])
                elif task_data["status"] == "in_progress":
                    self.in_progress_column.add_task(task_id, task_data["title"], task_data["priority"])
                elif task_data["status"] == "done":
                    self.done_column.add_task(task_id, task_data["title"], task_data["priority"])
            
            # Thông báo đã tải xong dữ liệu
            logging.info("Đã tải dữ liệu mẫu")
            self.statusBar().showMessage("Đã tải dữ liệu mẫu", 3000)
        
        # Chạy trong luồng riêng
        run_in_thread(
            self, 
            create_sample_data, 
            progress_text="Đang tải dữ liệu mẫu...",
            on_result=on_data_loaded
        )
    
    def update_ui(self):
        """Cập nhật giao diện người dùng"""
        # Cập nhật ngày
        self.date_label.setText(datetime.datetime.now().strftime("%A, %B %d, %Y"))
    
    def show_projects(self):
        """Hiển thị màn hình quản lý dự án"""
        QMessageBox.information(self, "Projects", "Projects screen not implemented yet")
    
    def show_tasks(self):
        """Hiển thị màn hình quản lý công việc"""
        QMessageBox.information(self, "Tasks", "Tasks screen not implemented yet")
    
    def show_analytics(self):
        """Hiển thị màn hình phân tích"""
        QMessageBox.information(self, "Analytics", "Analytics screen not implemented yet")
    
    def show_terminal(self):
        """Hiển thị terminal"""
        QMessageBox.information(self, "Terminal", "Terminal screen not implemented yet")
    
    def search(self):
        """Xử lý tìm kiếm"""
        search_text = self.sender().text()
        if search_text:
            QMessageBox.information(self, "Search", f"Searching for: {search_text}")
            self.sender().clear()
    
    def add_recent_activity(self, activity_text, time_text=None):
        """Thêm hoạt động gần đây vào sidebar"""
        try:
            # Nếu không cung cấp thời gian, sử dụng "just now"
            if time_text is None:
                time_text = "just now"
            
            # Tạo widget mới
            activity = QLabel(f"• {activity_text}")
            activity.setStyleSheet("color: #ffffff; font-size: 12px;")
            
            time = QLabel(time_text)
            time.setStyleSheet("color: #6b6b8d; font-size: 10px;")
            
            # Thêm vào đầu danh sách
            self.activity_items.insert(0, (activity, time))
            
            # Giới hạn số lượng hoạt động hiển thị
            if len(self.activity_items) > 5:
                # Xóa mục cuối cùng
                old_activity, old_time = self.activity_items.pop()
                old_activity.setParent(None)
                old_time.setParent(None)
            
            # Cập nhật giao diện
            recent_activity_widget = self.findChild(QFrame, "recent_activity_widget")
            if recent_activity_widget:
                # Xóa tất cả widget hiện tại
                layout = recent_activity_widget.layout()
                while layout.count():
                    item = layout.takeAt(0)
                    if item.widget():
                        item.widget().setParent(None)
                
                # Thêm lại các mục hoạt động
                for i, (act, tim) in enumerate(self.activity_items):
                    layout.addWidget(act)
                    layout.addWidget(tim)
                    if i < len(self.activity_items) - 1:
                        layout.addSpacing(10)
            
            logging.info(f"Đã thêm hoạt động mới: {activity_text}")
        except Exception as e:
            logging.error(f"Lỗi khi thêm hoạt động: {str(e)}")
    
    def move_task(self, task_id, new_status):
        """Di chuyển task sang trạng thái mới"""
        # Kiểm tra xem task có tồn tại trong bộ nhớ không
        if task_id not in self.tasks:
            # Nếu task chưa có trong bộ nhớ, tạo mới
            logging.warning(f"Task {task_id} chưa có trong bộ nhớ, tạo mới với trạng thái {new_status}")
            self.tasks[task_id] = {
                "id": task_id,
                "title": f"Task {task_id}",
                "description": "",
                "status": new_status,
                "priority": "Medium",
                "due_date": (datetime.datetime.now() + datetime.timedelta(days=7)).strftime("%Y-%m-%dT%H:%M:%S")
            }
            return
        
        # Cập nhật trạng thái task trong bộ nhớ
        old_status = self.tasks[task_id]["status"]
        
        # Kiểm tra nếu trạng thái mới giống trạng thái cũ
        if old_status == new_status:
            logging.info(f"Task {task_id} đã ở trạng thái {new_status}, không cần di chuyển")
            return
            
        # Cập nhật trạng thái mới
        self.tasks[task_id]["status"] = new_status
        logging.info(f"Di chuyển task {task_id} từ {old_status} sang {new_status}")
        
        # Cập nhật giao diện
        # Xóa task khỏi cột cũ
        if old_status == "todo":
            self.todo_column.remove_task(task_id)
        elif old_status == "in_progress":
            self.in_progress_column.remove_task(task_id)
        elif old_status == "done":
            self.done_column.remove_task(task_id)
        
        # Thêm task vào cột mới
        task_data = self.tasks[task_id]
        if new_status == "todo":
            self.todo_column.add_task(task_id, task_data["title"], task_data["priority"])
        elif new_status == "in_progress":
            self.in_progress_column.add_task(task_id, task_data["title"], task_data["priority"])
        elif new_status == "done":
            self.done_column.add_task(task_id, task_data["title"], task_data["priority"])
        
        # Cập nhật trạng thái task trên server
        run_in_thread(
            parent=self,
            fn=self.process_task_move,
            on_result=self.on_move_completed,
            on_error=self.on_move_error,
            task_id=task_id,
            old_status=old_status,
            new_status=new_status
        )
    
    def process_task_move(self, task_id, old_status, new_status):
        """Xử lý di chuyển task trên server"""
        # Giả lập gọi API để cập nhật task
        if self.api_client:
            # Giả lập gọi API để cập nhật task
            time.sleep(0.5)  # Giả lập độ trễ mạng
        return {"task_id": task_id, "old_status": old_status, "new_status": new_status}
    
    def on_move_completed(self, result):
        """Xử lý khi di chuyển task thành công"""
        # Cập nhật trạng thái cục bộ
        task_id = result["task_id"]
        old_status = result["old_status"]
        new_status = result["new_status"]
        
        # Cập nhật hoạt động gần đây
        self.add_recent_activity(f"Task {task_id} moved to {new_status}")
        
        # Hiển thị thông báo
        self.statusBar().showMessage(f"Đã di chuyển task {task_id} sang {new_status}", 3000)
    
    def on_move_error(self, error_info):
        """Xử lý khi di chuyển task gặp lỗi"""
        error_type, error_value, traceback_info = error_info
        logging.error(f"Lỗi khi di chuyển task: {error_value}")
        self.statusBar().showMessage(f"Không thể di chuyển task", 5000)
        QMessageBox.warning(self, "Lỗi", f"Không thể di chuyển task: {error_value}")
    
    def on_task_selected(self, task_id):
        """Xử lý khi task được chọn"""
        if task_id in self.tasks:
            self.current_task = self.tasks[task_id]
            QMessageBox.information(self, "Task Selected", f"Selected task: {task_id}")
    
    def on_task_edit_requested(self, task_id):
        """Xử lý khi yêu cầu chỉnh sửa task"""
        if task_id in self.tasks:
            # Mở dialog chỉnh sửa task
            dialog = TaskDialog(self, self.tasks[task_id])
            if dialog.exec():
                # Lấy dữ liệu đã cập nhật
                updated_data = dialog.get_task_data()
                old_status = self.tasks[task_id]["status"]
                new_status = updated_data["status"]
                
                # Định nghĩa hàm cập nhật task trong luồng riêng
                def update_task_data():
                    # Giả lập gọi API để cập nhật task
                    if self.api_client:
                        time.sleep(0.5)  # Giả lập độ trễ mạng
                    return {
                        "task_id": task_id, 
                        "updated_data": updated_data, 
                        "old_status": old_status, 
                        "new_status": new_status
                    }
                
                def on_update_completed(result):
                    # Cập nhật dữ liệu task
                    self.tasks[task_id].update(updated_data)
                    
                    # Ghi log
                    logging.info(f"Đã cập nhật task {task_id}")
                    
                    if old_status != new_status:
                        # Di chuyển task sang cột mới nếu trạng thái thay đổi
                        self.move_task(task_id, new_status)
                    else:
                        # Cập nhật thông tin hiển thị của task
                        if old_status == "todo":
                            self.todo_column.remove_task(task_id)
                            self.todo_column.add_task(task_id, updated_data["title"], updated_data["priority"])
                        elif old_status == "in_progress":
                            self.in_progress_column.remove_task(task_id)
                            self.in_progress_column.add_task(task_id, updated_data["title"], updated_data["priority"])
                        elif old_status == "done":
                            self.done_column.remove_task(task_id)
                            self.done_column.add_task(task_id, updated_data["title"], updated_data["priority"])
                    
                    # Cập nhật thông tin chi tiết nếu task đang được chọn
                    if self.current_task == task_id:
                        self.on_task_selected(task_id)
                    
                    # Cập nhật hoạt động gần đây
                    self.add_recent_activity(f"Task {task_id} updated")
                    
                    # Hiển thị thông báo
                    self.statusBar().showMessage(f"Đã cập nhật task {task_id}", 3000)
                
                def on_update_error(error_info):
                    logging.error(f"Lỗi khi cập nhật task: {error_info[1]}")
                    self.statusBar().showMessage(f"Không thể cập nhật task {task_id}", 5000)
                    QMessageBox.warning(self, "Lỗi", f"Không thể cập nhật task {task_id}")
                
                # Chạy trong luồng riêng
                run_in_thread(
                    self, 
                    update_task_data, 
                    progress_text=f"Đang cập nhật task {task_id}...",
                    on_result=on_update_completed,
                    on_error=on_update_error
                )

# ----- Hàm main -----

def main():
    """Hàm chính để khởi động ứng dụng"""
    app = QApplication(sys.argv)
    
    # Thiết lập logging
    logging.basicConfig(
        level=logging.DEBUG,  # Thay đổi từ INFO sang DEBUG để xem thông tin chi tiết hơn
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    
    # Khởi tạo cửa sổ chính
    main_window = MainWindow()
    main_window.show()
    
    # Chạy ứng dụng
    sys.exit(app.exec())

if __name__ == "__main__":
    main()
