#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sys
import unittest
from unittest.mock import MagicMock, patch
from PyQt6.QtCore import Qt, QMimeData, QPoint, QByteArray
from PyQt6.QtGui import QDrag
from PyQt6.QtWidgets import QApplication, QPushButton, QWidget

# Import các lớp cần test
from main import KanbanColumn, TaskCard, MainWindow

class MockMimeData:
    """Lớp giả lập QMimeData để sử dụng trong test"""
    def __init__(self, task_id):
        self.task_id = task_id
        self._formats = ["text/plain"]
        if task_id:
            self._formats.append("application/x-task")
    
    def hasText(self):
        return True
    
    def text(self):
        return self.task_id
    
    def hasFormat(self, format_type):
        return format_type in self._formats
    
    def formats(self):
        return self._formats
    
    def data(self, format_type):
        if format_type == "application/x-task":
            mock_data = MagicMock()
            mock_data.data.return_value = self.task_id.encode()
            return mock_data
        return None

class MockDropEvent:
    """Lớp giả lập sự kiện thả để sử dụng trong test"""
    def __init__(self, source_widget, mime_data):
        self.source_widget = source_widget
        self.mime_data_obj = mime_data
        self.accepted = False
        self.ignored = False
        self.drop_action = None
    
    def source(self):
        return self.source_widget
    
    def mimeData(self):
        return self.mime_data_obj
    
    def accept(self):
        self.accepted = True
        self.ignored = False
    
    def ignore(self):
        self.ignored = True
        self.accepted = False
    
    def setDropAction(self, action):
        self.drop_action = action

class TestDragDrop(unittest.TestCase):
    """Kiểm thử chức năng kéo thả trong ứng dụng WindSurf Memory Tracker"""
    
    @classmethod
    def setUpClass(cls):
        """Khởi tạo ứng dụng Qt trước khi chạy test"""
        cls.app = QApplication.instance() or QApplication(sys.argv)
    
    def setUp(self):
        """Thiết lập môi trường test cho mỗi test case"""
        # Tạo main window
        self.main_window = MainWindow()
        
        # Lấy các cột Kanban
        self.todo_column = self.main_window.todo_column
        self.in_progress_column = self.main_window.in_progress_column
        self.done_column = self.main_window.done_column
        
        # Tạo một task mẫu
        self.test_task_id = "TEST-123"
        self.test_task_title = "Test Task"
        self.test_task_priority = "Medium"
        
        # Thêm task vào cột TODO
        self.task_card = self.todo_column.add_task(
            self.test_task_id, 
            self.test_task_title, 
            self.test_task_priority
        )
        
        # Thêm task vào bộ nhớ của MainWindow
        self.main_window.tasks[self.test_task_id] = {
            "id": self.test_task_id,
            "title": self.test_task_title,
            "description": "Test description",
            "status": "todo",
            "priority": self.test_task_priority,
            "due_date": "2025-05-01T12:00:00"
        }
        
        # Kết nối tín hiệu taskMoved với phương thức di chuyển task
        self.in_progress_column.taskMoved.connect(self.main_window.move_task)
        self.done_column.taskMoved.connect(self.main_window.move_task)
        
        # Sửa lại thuộc tính task_layout trong các cột để phù hợp với test
        if not hasattr(self.todo_column, 'task_layout'):
            self.todo_column.task_layout = self.todo_column.tasks_layout
        if not hasattr(self.in_progress_column, 'task_layout'):
            self.in_progress_column.task_layout = self.in_progress_column.tasks_layout
        if not hasattr(self.done_column, 'task_layout'):
            self.done_column.task_layout = self.done_column.tasks_layout
            
        # Patch hàm run_in_thread để tránh lỗi trong quá trình test
        def mock_run_in_thread(func, on_result=None, on_error=None, **kwargs):
            try:
                result = func(**kwargs)
                if on_result:
                    on_result(result)
                return result
            except Exception as e:
                if on_error:
                    on_error(sys.exc_info())
                raise e
                
        # Patch hàm run_in_thread trong main_window
        self.main_window.run_in_thread = mock_run_in_thread
    
    def tearDown(self):
        """Dọn dẹp sau mỗi test case"""
        self.main_window.close()
    
    def test_add_task_button_not_confused_with_drag(self):
        """Kiểm tra nút thêm task không bị nhầm lẫn với kéo thả"""
        # Tạo sự kiện giả lập từ nút +
        add_button = QPushButton("+")
        mime_data = MockMimeData(self.test_task_id)
        
        # Giả lập sự kiện dropEvent
        event = MockDropEvent(add_button, mime_data)
        
        # Gọi dropEvent trên cột in_progress
        self.in_progress_column.dropEvent(event)
        
        # Kiểm tra xem sự kiện có bị bỏ qua không
        self.assertTrue(event.ignored)
        
        # Kiểm tra xem task vẫn ở cột cũ
        self.assertEqual(self.main_window.tasks[self.test_task_id]["status"], "todo")
    
    def test_drag_drop_between_columns(self):
        """Kiểm tra kéo thả task giữa các cột"""
        # Tạo mime data với task id
        mime_data = MockMimeData(self.test_task_id)
        
        # Giả lập sự kiện dropEvent
        event = MockDropEvent(self.task_card, mime_data)
        
        # Gọi dropEvent trên cột in_progress
        with patch.object(self.in_progress_column, 'findChildren', return_value=[self.todo_column]):
            self.in_progress_column.dropEvent(event)
        
        # Kiểm tra xem task có được di chuyển sang cột mới không
        self.assertEqual(self.main_window.tasks[self.test_task_id]["status"], "in_progress")
        
        # Kiểm tra xem sự kiện có được chấp nhận không
        self.assertTrue(event.accepted)
    
    def test_drag_drop_same_column(self):
        """Kiểm tra kéo thả task trong cùng một cột"""
        # Tạo mime data với task id
        mime_data = MockMimeData(self.test_task_id)
        
        # Giả lập sự kiện dropEvent
        event = MockDropEvent(self.task_card, mime_data)
        
        # Gọi dropEvent trên cùng cột todo
        with patch.object(self.todo_column, 'findChildren', return_value=[self.todo_column]):
            self.todo_column.dropEvent(event)
        
        # Kiểm tra xem task vẫn ở cột cũ
        self.assertEqual(self.main_window.tasks[self.test_task_id]["status"], "todo")
        
        # Kiểm tra xem sự kiện có được chấp nhận không
        self.assertTrue(event.accepted)

if __name__ == "__main__":
    unittest.main()
