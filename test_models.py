#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Test cho các model trong WindSurf Memory Tracker

Chạy test với lệnh: python -m pytest test_models.py -v
"""

import os
import unittest
import tempfile
import pytest
import json
import zlib
from datetime import datetime

# Import các model cần test
from models import (
    db, create_tables, Project, User, Task, File, Snapshot, 
    TaskSnapshot, Activity, TaskStatus, TaskPriority, SnapshotType,
    ActivityType
)


class TestModelsBase(unittest.TestCase):
    """Lớp cơ sở cho các test model"""
    
    def setUp(self):
        # Tạo database tạm thời cho test
        self.temp_db_fd, self.temp_db_path = tempfile.mkstemp()
        
        # Lưu lại đường dẫn database gốc
        self.original_db_path = db.database
        
        # Chuyển sang database tạm thời
        db.init(self.temp_db_path)
        db.connect(reuse_if_open=True)
        
        # Tạo tất cả các bảng
        db.create_tables([
            Project, User, Task, File, Snapshot, 
            TaskSnapshot, Activity
        ], safe=True)
        
        # Tạo dữ liệu test cơ bản
        self.project = Project.create(
            name="Test Project",
            path="/path/to/test",
            description="Project for testing"
        )
        
        self.user = User.create(
            username="tester",
            email="test@example.com",
            display_name="Test User"
        )

    def tearDown(self):
        # Đóng kết nối database
        db.close()
        
        # Khôi phục database gốc
        db.init(self.original_db_path)
        
        # Xóa file database tạm thời
        os.close(self.temp_db_fd)
        os.unlink(self.temp_db_path)


class TestProject(TestModelsBase):
    """Test cho model Project"""
    
    def test_create_project(self):
        """Test tạo project mới"""
        project = Project.create(
            name="Another Project",
            path="/path/to/another",
            description="Another project for testing"
        )
        
        # Kiểm tra project đã được tạo
        self.assertEqual(Project.select().count(), 2)  # 1 từ setUp + 1 mới
        self.assertEqual(project.name, "Another Project")
        self.assertEqual(project.path, "/path/to/another")
        
        # Kiểm tra các trường tự động
        self.assertIsNotNone(project.created_at)
        self.assertIsNotNone(project.updated_at)
        
    def test_project_string_representation(self):
        """Test __str__ của Project"""
        self.assertEqual(str(self.project), "Test Project")


class TestUser(TestModelsBase):
    """Test cho model User"""
    
    def test_create_user(self):
        """Test tạo user mới"""
        user = User.create(
            username="another_user",
            email="another@example.com",
            display_name="Another User"
        )
        
        # Kiểm tra user đã được tạo
        self.assertEqual(User.select().count(), 2)  # 1 từ setUp + 1 mới
        self.assertEqual(user.username, "another_user")
        self.assertEqual(user.email, "another@example.com")
        
    def test_user_string_representation(self):
        """Test __str__ của User"""
        # User.__str__ trả về display_name nếu có, nếu không thì trả về username
        self.assertEqual(str(self.user), "Test User")
        
        # Tạo user không có display_name
        user_no_display = User.create(
            username="no_display",
            email="no_display@example.com"
        )
        self.assertEqual(str(user_no_display), "no_display")


class TestTask(TestModelsBase):
    """Test cho model Task"""
    
    def test_create_task(self):
        """Test tạo task mới"""
        task = Task.create(
            id="TASK-001",
            title="Test Task",
            description="A task for testing",
            status=TaskStatus.TODO,
            priority=TaskPriority.HIGH,
            project=self.project,
            assignee=self.user
        )
        
        # Kiểm tra task đã được tạo
        self.assertEqual(Task.select().count(), 1)
        self.assertEqual(task.id, "TASK-001")
        self.assertEqual(task.title, "Test Task")
        self.assertEqual(task.status, TaskStatus.TODO)
        self.assertEqual(task.priority, TaskPriority.HIGH)
        
        # Kiểm tra quan hệ với project và user
        self.assertEqual(task.project.name, "Test Project")
        self.assertEqual(task.assignee.username, "tester")
        
    def test_task_tag_list(self):
        """Test getter/setter cho tag_list"""
        task = Task.create(
            id="TASK-002",
            title="Task with Tags",
            project=self.project,
            tags="[\"python\", \"testing\", \"models\"]"
        )
        
        # Kiểm tra getter
        self.assertEqual(task.tag_list, ["python", "testing", "models"])
        
        # Kiểm tra setter
        task.tag_list = ["updated", "tags"]
        task.save()
        
        # Đọc lại từ database để kiểm tra
        updated_task = Task.get(Task.id == "TASK-002")
        self.assertEqual(updated_task.tag_list, ["updated", "tags"])


class TestFile(TestModelsBase):
    """Test cho model File"""
    
    def test_create_file(self):
        """Test tạo file mới"""
        file = File.create(
            path="/src/main",
            filename="test.py",
            project=self.project
        )
        
        # Kiểm tra file đã được tạo
        self.assertEqual(File.select().count(), 1)
        self.assertEqual(file.path, "/src/main")
        self.assertEqual(file.filename, "test.py")
        
        # Kiểm tra quan hệ với project
        self.assertEqual(file.project.name, "Test Project")
        
    def test_file_full_path(self):
        """Test phương thức full_path"""
        file = File.create(
            path="/src/main",
            filename="test.py",
            project=self.project
        )
        
        self.assertEqual(file.full_path, "/src/main/test.py")


class TestSnapshot(TestModelsBase):
    """Test cho model Snapshot"""
    
    def setUp(self):
        super().setUp()
        self.file = File.create(
            path="/src/main",
            filename="test.py",
            project=self.project
        )
    
    def test_create_snapshot(self):
        """Test tạo snapshot mới"""
        snapshot = Snapshot.create(
            file=self.file,
            user=self.user,
            type=SnapshotType.FULL,
            compressed_content=b"sample content",
            size_bytes=14,
            hash="abc123"
        )
        
        # Kiểm tra snapshot đã được tạo
        self.assertEqual(Snapshot.select().count(), 1)
        self.assertEqual(snapshot.type, SnapshotType.FULL)
        self.assertEqual(snapshot.compressed_content, b"sample content")
        
        # Kiểm tra quan hệ với file và user
        self.assertEqual(snapshot.file.filename, "test.py")
        self.assertEqual(snapshot.user.username, "tester")
    
    def test_snapshot_content(self):
        """Test getter/setter cho content"""
        # Tạo nội dung mẫu và nén
        test_content = "print('Hello, World!')"
        compressed = zlib.compress(test_content.encode('utf-8'))
        
        snapshot = Snapshot.create(
            file=self.file,
            user=self.user,
            type=SnapshotType.FULL,
            compressed_content=compressed,
            size_bytes=len(test_content)
        )
        
        # Test getter
        self.assertEqual(snapshot.content, test_content)
        
        # Test setter
        new_content = "def hello(): print('New content')"
        snapshot.content = new_content
        snapshot.save()
        
        # Đọc lại từ database để kiểm tra
        updated_snapshot = Snapshot.get(Snapshot.id == snapshot.id)
        self.assertEqual(updated_snapshot.content, new_content)
        self.assertEqual(updated_snapshot.size_bytes, len(new_content))


class TestActivity(TestModelsBase):
    """Test cho model Activity"""
    
    def setUp(self):
        super().setUp()
        self.task = Task.create(
            id="TASK-001",
            title="Test Task",
            project=self.project
        )
    
    def test_create_activity(self):
        """Test tạo activity mới"""
        activity = Activity.create(
            user=self.user,
            activity_type=ActivityType.TASK_CREATED,
            details="{\"task_id\": \"TASK-001\"}",
            project=self.project,
            task=self.task
        )
        
        # Kiểm tra activity đã được tạo
        self.assertEqual(Activity.select().count(), 1)
        self.assertEqual(activity.activity_type, ActivityType.TASK_CREATED)
        
        # Kiểm tra quan hệ với user, project và task
        self.assertEqual(activity.user.username, "tester")
        self.assertEqual(activity.project.name, "Test Project")
        self.assertEqual(activity.task.id, "TASK-001")
    
    def test_activity_details_dict(self):
        """Test getter/setter cho details_dict"""
        activity = Activity.create(
            user=self.user,
            activity_type=ActivityType.TASK_CREATED,
            details="{\"task_id\": \"TASK-001\"}",
            project=self.project,
            task=self.task
        )
        
        # Kiểm tra getter
        self.assertEqual(activity.details_dict, {"task_id": "TASK-001"})
        
        # Kiểm tra setter
        activity.details_dict = {"task_id": "TASK-001", "status": "done"}
        activity.save()
        
        # Đọc lại từ database để kiểm tra
        updated_activity = Activity.get(Activity.id == activity.id)
        self.assertEqual(updated_activity.details_dict, {"task_id": "TASK-001", "status": "done"})


if __name__ == "__main__":
    unittest.main()
