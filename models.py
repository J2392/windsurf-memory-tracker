"""
WindSurf Memory Tracker - Mô hình dữ liệu
-----------------------------------------
Định nghĩa các mô hình ORM cho việc lưu trữ dữ liệu.
Sử dụng peewee ORM để tương tác với SQLite.
"""

import os
import datetime
import json
import zlib
from enum import Enum
from typing import List, Dict, Optional, Any, Union

from peewee import (
    SqliteDatabase, Model, CharField, TextField, DateTimeField,
    ForeignKeyField, IntegerField, BooleanField, BlobField,
    CompositeKey, FloatField
)

# Thiết lập cơ sở dữ liệu
DB_PATH = os.path.join(os.path.expanduser("~"), ".windsurf_memory", "data.db")
os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
db = SqliteDatabase(DB_PATH)


class BaseModel(Model):
    """Model cơ sở để các model khác kế thừa"""
    
    class Meta:
        database = db


class Project(BaseModel):
    """Đại diện cho một dự án được theo dõi"""
    
    name = CharField(max_length=100, unique=True)
    path = CharField(max_length=500)
    description = TextField(null=True)
    created_at = DateTimeField(default=datetime.datetime.now)
    updated_at = DateTimeField(default=datetime.datetime.now)
    
    def __str__(self):
        return self.name


class User(BaseModel):
    """Đại diện cho người dùng trong hệ thống"""
    
    username = CharField(max_length=100, unique=True)
    email = CharField(max_length=100, null=True)
    display_name = CharField(max_length=100, null=True)
    created_at = DateTimeField(default=datetime.datetime.now)
    
    def __str__(self):
        return self.display_name or self.username


class TaskStatus(Enum):
    """Trạng thái của task"""
    TODO = "todo"
    IN_PROGRESS = "in_progress"
    DONE = "done"


class TaskPriority(Enum):
    """Độ ưu tiên của task"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


class Task(BaseModel):
    """Đại diện cho một task trong bảng Kanban"""
    
    id = CharField(primary_key=True)  # Định dạng: TASK-XXX
    title = CharField(max_length=200)
    description = TextField(null=True)
    status = CharField(default=TaskStatus.TODO.value)
    priority = CharField(default=TaskPriority.MEDIUM.value)
    created_at = DateTimeField(default=datetime.datetime.now)
    updated_at = DateTimeField(default=datetime.datetime.now)
    due_date = DateTimeField(null=True)
    estimated_hours = FloatField(null=True)
    actual_hours = FloatField(null=True)
    tags = TextField(null=True)  # JSON list
    
    project = ForeignKeyField(Project, backref='tasks')
    assignee = ForeignKeyField(User, backref='tasks', null=True)
    parent_task = ForeignKeyField('self', backref='subtasks', null=True)
    
    @property
    def tag_list(self) -> List[str]:
        """Trả về danh sách tags từ chuỗi JSON"""
        if not self.tags:
            return []
        return json.loads(self.tags)
    
    @tag_list.setter
    def tag_list(self, tags: List[str]):
        """Lưu danh sách tags dưới dạng chuỗi JSON"""
        self.tags = json.dumps(tags)
    
    def __str__(self):
        return f"{self.id}: {self.title}"


class File(BaseModel):
    """Đại diện cho một file được theo dõi trong dự án"""
    
    path = CharField(max_length=500)
    filename = CharField(max_length=100)
    project = ForeignKeyField(Project, backref='files')
    created_at = DateTimeField(default=datetime.datetime.now)
    updated_at = DateTimeField(default=datetime.datetime.now)
    
    class Meta:
        indexes = (
            (('project', 'path', 'filename'), True),  # Composite unique index
        )
    
    @property
    def full_path(self) -> str:
        """Trả về đường dẫn đầy đủ đến file"""
        return os.path.join(self.path, self.filename)
    
    def __str__(self):
        return self.full_path


class SnapshotType(Enum):
    """Loại snapshot"""
    FULL = "full"      # Toàn bộ nội dung file
    DELTA = "delta"    # Chỉ chứa sự thay đổi so với snapshot trước đó


class Snapshot(BaseModel):
    """Đại diện cho một snapshot của file tại một thời điểm"""
    
    file = ForeignKeyField(File, backref='snapshots')
    timestamp = DateTimeField(default=datetime.datetime.now)
    user = ForeignKeyField(User, backref='snapshots', null=True)
    type = CharField(default=SnapshotType.FULL.value)
    compressed_content = BlobField()  # Nội dung file đã nén
    parent_snapshot = ForeignKeyField('self', backref='children', null=True)
    comment = TextField(null=True)
    metadata = TextField(null=True)  # JSON object
    size_bytes = IntegerField(default=0)
    hash = CharField(max_length=64, null=True)  # Hash của nội dung
    
    @property
    def content(self) -> str:
        """Giải nén và trả về nội dung của snapshot"""
        return zlib.decompress(self.compressed_content).decode('utf-8')
    
    @content.setter
    def content(self, value: str):
        """Nén và lưu nội dung của snapshot"""
        compressed = zlib.compress(value.encode('utf-8'))
        self.compressed_content = compressed
        self.size_bytes = len(value)
    
    @property
    def metadata_dict(self) -> Dict[str, Any]:
        """Trả về metadata dưới dạng dictionary"""
        if not self.metadata:
            return {}
        return json.loads(self.metadata)
    
    @metadata_dict.setter
    def metadata_dict(self, data: Dict[str, Any]):
        """Lưu metadata dưới dạng JSON"""
        self.metadata = json.dumps(data)
    
    def __str__(self):
        return f"Snapshot {self.id} of {self.file.filename} at {self.timestamp}"


class TaskSnapshot(BaseModel):
    """Liên kết giữa task và snapshot"""
    
    task = ForeignKeyField(Task, backref='snapshots')
    snapshot = ForeignKeyField(Snapshot, backref='tasks')
    linked_at = DateTimeField(default=datetime.datetime.now)
    comment = TextField(null=True)
    
    class Meta:
        primary_key = CompositeKey('task', 'snapshot')


class ActivityType(Enum):
    """Loại hoạt động"""
    FILE_CREATED = "file_created"
    FILE_MODIFIED = "file_modified"
    TASK_CREATED = "task_created"
    TASK_UPDATED = "task_updated"
    TASK_STATUS_CHANGED = "task_status_changed"
    SNAPSHOT_CREATED = "snapshot_created"


class Activity(BaseModel):
    """Lưu trữ hoạt động của người dùng"""
    
    user = ForeignKeyField(User, backref='activities')
    timestamp = DateTimeField(default=datetime.datetime.now)
    activity_type = CharField()
    details = TextField(null=True)  # JSON object
    
    project = ForeignKeyField(Project, backref='activities', null=True)
    task = ForeignKeyField(Task, backref='activities', null=True)
    file = ForeignKeyField(File, backref='activities', null=True)
    snapshot = ForeignKeyField(Snapshot, backref='activities', null=True)
    
    @property
    def details_dict(self) -> Dict[str, Any]:
        """Trả về details dưới dạng dictionary"""
        if not self.details:
            return {}
        return json.loads(self.details)
    
    @details_dict.setter
    def details_dict(self, data: Dict[str, Any]):
        """Lưu details dưới dạng JSON"""
        self.details = json.dumps(data)


# Tạo bảng nếu chưa tồn tại
def create_tables():
    """Tạo tất cả các bảng trong cơ sở dữ liệu"""
    with db:
        db.create_tables([
            Project, User, Task, File, Snapshot, 
            TaskSnapshot, Activity
        ], safe=True)

if __name__ == "__main__":
    create_tables()
    print(f"Đã tạo cơ sở dữ liệu tại: {DB_PATH}")
