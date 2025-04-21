"""
WindSurf Memory Tracker - API Client
-----------------------------------
Module này chịu trách nhiệm kết nối với WindSurf Editor.
Bao gồm các hàm để lắng nghe sự kiện thay đổi file, lưu file,
và lấy nội dung file từ WindSurf Editor.

Vì chưa có API thực của WindSurf, module này sẽ cung cấp:
1. API giả lập cho phát triển ban đầu
2. Interface để tích hợp API thật sau này
"""

import os
import time
import threading
import logging
import json
import hashlib
import datetime
from typing import Dict, List, Callable, Any, Optional, Tuple
from pathlib import Path
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler, FileSystemEvent

# Thiết lập logging
logging.basicConfig(level=logging.INFO, 
                   format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger("windsurf_api")

# Định nghĩa các kiểu callback
FileChangedCallback = Callable[[str, str], None]  # (file_path, content) -> None
FileSavedCallback = Callable[[str, str], None]    # (file_path, content) -> None
EditorEventCallback = Callable[[Dict[str, Any]], None]  # (event_data) -> None


class WindSurfAPIClient:
    """
    Client để tương tác với WindSurf Editor API.
    
    Cung cấp các phương thức để:
    - Đăng ký callback cho sự kiện thay đổi file
    - Lấy nội dung file hiện tại
    - Kiểm tra trạng thái kết nối
    """
    
    def __init__(self, use_mock: bool = True):
        """
        Khởi tạo API client.
        
        Args:
            use_mock: Sử dụng API giả lập (True) hoặc kết nối API thật (False)
        """
        self.use_mock = use_mock
        self.mock_api = None
        self.connected = False
        self._callbacks = {
            'file_changed': [],
            'file_saved': [],
            'editor_event': [],
        }
        
        if use_mock:
            self.mock_api = MockWindSurfAPI(self)
            self.connected = True
            logger.info("Sử dụng WindSurf API giả lập")
        else:
            # Thiết lập kết nối với API thật ở đây
            # TODO: Implement khi có API thật
            logger.warning("Kết nối API thật chưa được thực hiện")
            
    def connect(self) -> bool:
        """
        Kết nối đến WindSurf API.
        
        Returns:
            bool: True nếu kết nối thành công, False nếu thất bại
        """
        if self.use_mock:
            self.connected = True
            return True
        
        # TODO: Implement kết nối API thật
        logger.warning("Kết nối API thật chưa được thực hiện")
        return False
    
    def disconnect(self) -> None:
        """Ngắt kết nối với WindSurf API."""
        if self.use_mock and self.mock_api:
            self.mock_api.stop()
        
        self.connected = False
        logger.info("Đã ngắt kết nối với WindSurf API")
    
    def is_connected(self) -> bool:
        """
        Kiểm tra trạng thái kết nối.
        
        Returns:
            bool: True nếu đang kết nối, False nếu không
        """
        return self.connected
    
    def on_file_changed(self, callback: FileChangedCallback) -> None:
        """
        Đăng ký callback để nhận thông báo khi file thay đổi.
        
        Args:
            callback: Hàm sẽ được gọi khi file thay đổi
        """
        self._callbacks['file_changed'].append(callback)
    
    def on_file_saved(self, callback: FileSavedCallback) -> None:
        """
        Đăng ký callback để nhận thông báo khi file được lưu.
        
        Args:
            callback: Hàm sẽ được gọi khi file được lưu
        """
        self._callbacks['file_saved'].append(callback)
    
    def on_editor_event(self, callback: EditorEventCallback) -> None:
        """
        Đăng ký callback để nhận thông báo về các sự kiện khác từ editor.
        
        Args:
            callback: Hàm sẽ được gọi khi có sự kiện
        """
        self._callbacks['editor_event'].append(callback)
    
    def get_file_content(self, file_path: str) -> Optional[str]:
        """
        Lấy nội dung hiện tại của file từ editor.
        
        Args:
            file_path: Đường dẫn đến file
            
        Returns:
            str: Nội dung file hoặc None nếu không thể lấy
        """
        if not self.connected:
            logger.error("Không thể lấy nội dung file: Chưa kết nối API")
            return None
        
        if self.use_mock and self.mock_api:
            return self.mock_api.get_file_content(file_path)
        
        # TODO: Implement khi có API thật
        logger.warning("Lấy nội dung file từ API thật chưa được thực hiện")
        return None
    
    def get_open_files(self) -> List[str]:
        """
        Lấy danh sách các file đang mở trong editor.
        
        Returns:
            List[str]: Danh sách đường dẫn đến các file đang mở
        """
        if not self.connected:
            logger.error("Không thể lấy danh sách file: Chưa kết nối API")
            return []
        
        if self.use_mock and self.mock_api:
            return self.mock_api.get_open_files()
        
        # TODO: Implement khi có API thật
        logger.warning("Lấy danh sách file từ API thật chưa được thực hiện")
        return []
    
    def get_active_project(self) -> Optional[Dict[str, Any]]:
        """
        Lấy thông tin về dự án đang hoạt động.
        
        Returns:
            Dict: Thông tin dự án hoặc None nếu không có dự án nào
        """
        if not self.connected:
            logger.error("Không thể lấy thông tin dự án: Chưa kết nối API")
            return None
        
        if self.use_mock and self.mock_api:
            return self.mock_api.get_active_project()
        
        # TODO: Implement khi có API thật
        logger.warning("Lấy thông tin dự án từ API thật chưa được thực hiện")
        return None
    
    # Phương thức nội bộ để gọi callbacks
    def _notify_file_changed(self, file_path: str, content: str) -> None:
        """Thông báo cho các callbacks khi file thay đổi"""
        for callback in self._callbacks['file_changed']:
            try:
                callback(file_path, content)
            except Exception as e:
                logger.error(f"Lỗi trong callback file_changed: {e}")
    
    def _notify_file_saved(self, file_path: str, content: str) -> None:
        """Thông báo cho các callbacks khi file được lưu"""
        for callback in self._callbacks['file_saved']:
            try:
                callback(file_path, content)
            except Exception as e:
                logger.error(f"Lỗi trong callback file_saved: {e}")
    
    def _notify_editor_event(self, event_data: Dict[str, Any]) -> None:
        """Thông báo cho các callbacks khi có sự kiện khác từ editor"""
        for callback in self._callbacks['editor_event']:
            try:
                callback(event_data)
            except Exception as e:
                logger.error(f"Lỗi trong callback editor_event: {e}")


class FileWatcher(FileSystemEventHandler):
    """
    Theo dõi thay đổi file trong thư mục dự án.
    Sử dụng watchdog để nhận thông báo khi file thay đổi.
    """
    
    def __init__(self, api_client: WindSurfAPIClient, watched_path: str, 
                 file_patterns: List[str] = None):
        super().__init__()
        self.api_client = api_client
        self.watched_path = os.path.abspath(watched_path)
        self.file_patterns = file_patterns or ['*.py', '*.js', '*.html', '*.css', '*.txt']
        self.last_modified = {}  # {file_path: last_modified_time}
        
    def on_modified(self, event: FileSystemEvent) -> None:
        """Xử lý sự kiện khi file bị sửa đổi"""
        if not event.is_directory and self._is_watched_file(event.src_path):
            # Kiểm tra để tránh các sự kiện trùng lặp
            current_mtime = os.path.getmtime(event.src_path)
            last_mtime = self.last_modified.get(event.src_path, 0)
            
            # Chỉ xử lý nếu thời gian sửa đổi khác với lần cuối
            if current_mtime > last_mtime:
                self.last_modified[event.src_path] = current_mtime
                
                # Đọc nội dung file
                try:
                    with open(event.src_path, 'r', encoding='utf-8') as f:
                        content = f.read()
                    
                    # Thông báo cho API client
                    self.api_client._notify_file_changed(event.src_path, content)
                    logger.debug(f"File thay đổi: {event.src_path}")
                except Exception as e:
                    logger.error(f"Lỗi khi đọc file {event.src_path}: {e}")
    
    def on_created(self, event: FileSystemEvent) -> None:
        """Xử lý sự kiện khi file mới được tạo"""
        if not event.is_directory and self._is_watched_file(event.src_path):
            # Đọc nội dung file
            try:
                with open(event.src_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                # Cập nhật thời gian sửa đổi
                self.last_modified[event.src_path] = os.path.getmtime(event.src_path)
                
                # Thông báo cho API client
                self.api_client._notify_editor_event({
                    'type': 'file_created',
                    'file_path': event.src_path,
                    'timestamp': datetime.datetime.now().isoformat()
                })
                logger.debug(f"File mới: {event.src_path}")
            except Exception as e:
                logger.error(f"Lỗi khi đọc file mới {event.src_path}: {e}")
    
    def _is_watched_file(self, file_path: str) -> bool:
        """Kiểm tra xem file có nằm trong danh sách theo dõi không"""
        if not os.path.isfile(file_path):
            return False
        
        for pattern in self.file_patterns:
            if Path(file_path).match(pattern.replace('*', '**/*')):
                return True
        
        return False


class MockWindSurfAPI:
    """
    API giả lập để thử nghiệm tích hợp với WindSurf Editor.
    
    Mô phỏng:
    - Theo dõi thay đổi file trong thư mục
    - Thông báo khi file được lưu
    - Cung cấp dữ liệu giả về dự án và file đang mở
    """
    
    def __init__(self, api_client: WindSurfAPIClient):
        self.api_client = api_client
        self.watched_paths = []
        self.observers = []
        self.watchers = []
        self.mock_project_dir = None
        self.mock_open_files = []
        
    def start_watching(self, project_dir: str) -> None:
        """Bắt đầu theo dõi thư mục dự án"""
        self.mock_project_dir = os.path.abspath(project_dir)
        
        if not os.path.isdir(self.mock_project_dir):
            logger.error(f"Thư mục dự án không tồn tại: {self.mock_project_dir}")
            return
        
        # Thiết lập file watcher
        watcher = FileWatcher(self.api_client, self.mock_project_dir)
        observer = Observer()
        observer.schedule(watcher, self.mock_project_dir, recursive=True)
        observer.start()
        
        self.watched_paths.append(self.mock_project_dir)
        self.observers.append(observer)
        self.watchers.append(watcher)
        
        logger.info(f"Bắt đầu theo dõi thư mục: {self.mock_project_dir}")
        
        # Thêm một số file vào danh sách "đang mở" để giả lập
        self._update_mock_open_files()
        
        # Thông báo sự kiện project_opened
        self.api_client._notify_editor_event({
            'type': 'project_opened',
            'project_path': self.mock_project_dir,
            'timestamp': datetime.datetime.now().isoformat()
        })
    
    def stop(self) -> None:
        """Dừng theo dõi tất cả thư mục"""
        for observer in self.observers:
            observer.stop()
        
        for observer in self.observers:
            observer.join()
        
        self.watched_paths = []
        self.observers = []
        self.watchers = []
        self.mock_project_dir = None
        self.mock_open_files = []
        
        logger.info("Đã dừng theo dõi tất cả thư mục")
    
    def simulate_file_save(self, file_path: str) -> None:
        """Giả lập việc lưu file"""
        if not os.path.isfile(file_path):
            logger.error(f"Không thể giả lập lưu file: File không tồn tại {file_path}")
            return
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            self.api_client._notify_file_saved(file_path, content)
            logger.info(f"Đã giả lập lưu file: {file_path}")
        except Exception as e:
            logger.error(f"Lỗi khi giả lập lưu file {file_path}: {e}")
    
    def get_file_content(self, file_path: str) -> Optional[str]:
        """Lấy nội dung file từ hệ thống file"""
        if not os.path.isfile(file_path):
            logger.error(f"Không thể lấy nội dung file: File không tồn tại {file_path}")
            return None
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                return f.read()
        except Exception as e:
            logger.error(f"Lỗi khi đọc nội dung file {file_path}: {e}")
            return None
    
    def get_open_files(self) -> List[str]:
        """Trả về danh sách file "đang mở" trong giả lập"""
        return self.mock_open_files
    
    def get_active_project(self) -> Optional[Dict[str, Any]]:
        """Trả về thông tin dự án "đang hoạt động" trong giả lập"""
        if not self.mock_project_dir:
            return None
        
        return {
            'name': os.path.basename(self.mock_project_dir),
            'path': self.mock_project_dir,
            'open_files': self.mock_open_files,
            'timestamp': datetime.datetime.now().isoformat()
        }
    
    def _update_mock_open_files(self) -> None:
        """Cập nhật danh sách file "đang mở" dựa vào thư mục dự án"""
        if not self.mock_project_dir:
            return
        
        self.mock_open_files = []
        
        # Tìm tối đa 5 file để giả lập "đang mở"
        file_count = 0
        for root, _, files in os.walk(self.mock_project_dir):
            for file in files:
                if file.endswith(('.py', '.js', '.html', '.css', '.txt')):
                    file_path = os.path.join(root, file)
                    self.mock_open_files.append(file_path)
                    file_count += 1
                
                if file_count >= 5:
                    break
            
            if file_count >= 5:
                break


# Hàm tiện ích để khởi tạo và sử dụng API client
def create_api_client(use_mock: bool = True, project_dir: str = None) -> WindSurfAPIClient:
    """
    Tạo và khởi tạo API client.
    
    Args:
        use_mock: Sử dụng API giả lập
        project_dir: Đường dẫn đến thư mục dự án (chỉ cần cho API giả lập)
        
    Returns:
        WindSurfAPIClient: API client đã được khởi tạo
    """
    client = WindSurfAPIClient(use_mock=use_mock)
    
    if use_mock and project_dir:
        client.mock_api.start_watching(project_dir)
    
    return client


# Hàm demo
def demo():
    """Demo sử dụng API client"""
    # Lấy thư mục hiện tại làm thư mục dự án mẫu
    current_dir = os.path.dirname(os.path.abspath(__file__))
    
    # Khởi tạo API client
    client = create_api_client(use_mock=True, project_dir=current_dir)
    
    # Đăng ký callbacks
    def on_file_changed(file_path, content):
        print(f"File thay đổi: {file_path}")
        print(f"Kích thước nội dung: {len(content)} bytes")
    
    def on_file_saved(file_path, content):
        print(f"File được lưu: {file_path}")
        print(f"Hash nội dung: {hashlib.md5(content.encode()).hexdigest()}")
    
    def on_editor_event(event_data):
        print(f"Sự kiện editor: {json.dumps(event_data, indent=2)}")
    
    client.on_file_changed(on_file_changed)
    client.on_file_saved(on_file_saved)
    client.on_editor_event(on_editor_event)
    
    # Hiển thị thông tin
    print("WindSurf Memory Tracker API Client Demo")
    print("-" * 40)
    print(f"Đang kết nối: {client.is_connected()}")
    
    # Lấy thông tin dự án
    project = client.get_active_project()
    if project:
        print(f"Dự án hiện tại: {project['name']} ({project['path']})")
        print(f"Số file đang mở: {len(project['open_files'])}")
    
    # Lấy danh sách file đang mở
    open_files = client.get_open_files()
    print("\nCác file đang mở:")
    for file in open_files:
        print(f"- {os.path.basename(file)}")
    
    # Giả lập lưu file
    if open_files:
        print("\nGiả lập lưu file đầu tiên...")
        client.mock_api.simulate_file_save(open_files[0])
    
    # Chạy trong 10 giây
    print("\nChờ các sự kiện (10 giây)...")
    try:
        time.sleep(10)
    except KeyboardInterrupt:
        pass
    
    # Ngắt kết nối
    client.disconnect()
    print("\nĐã ngắt kết nối")


if __name__ == "__main__":
    demo()