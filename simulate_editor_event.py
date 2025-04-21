#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Script giả lập sự kiện từ WindSurf Editor
Sử dụng để kiểm thử việc tự động nhận task từ editor
"""

import os
import sys
import datetime
import logging
import time
import json
from typing import Dict, Any

# Import API client từ ứng dụng chính
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from api_client import create_api_client, WindSurfAPIClient

# Thiết lập logging
logging.basicConfig(level=logging.INFO, 
                   format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger("windsurf_simulator")

def simulate_task_created(api_client: WindSurfAPIClient, task_id: str, title: str, 
                         description: str = "", priority: str = "Medium", status: str = "todo"):
    """
    Giả lập sự kiện tạo task mới từ WindSurf Editor
    
    Args:
        api_client: API client đã được khởi tạo
        task_id: ID của task (ví dụ: WIND-123)
        title: Tiêu đề task
        description: Mô tả chi tiết
        priority: Độ ưu tiên (High, Medium, Low)
        status: Trạng thái (todo, in_progress, done)
    """
    # Tạo dữ liệu sự kiện
    event_data = {
        'type': 'task_created',
        'task_id': task_id,
        'title': title,
        'description': description,
        'priority': priority,
        'status': status,
        'timestamp': datetime.datetime.now().isoformat(),
        'source': 'windsurf_editor'
    }
    
    # Gửi sự kiện
    logger.info(f"Gửi sự kiện tạo task: {task_id} - {title}")
    api_client._notify_editor_event(event_data)
    logger.info("Đã gửi sự kiện")

def simulate_task_updated(api_client: WindSurfAPIClient, task_id: str, 
                         new_status: str = None, new_title: str = None, 
                         new_description: str = None, new_priority: str = None):
    """
    Giả lập sự kiện cập nhật task từ WindSurf Editor
    
    Args:
        api_client: API client đã được khởi tạo
        task_id: ID của task cần cập nhật
        new_status: Trạng thái mới (nếu có)
        new_title: Tiêu đề mới (nếu có)
        new_description: Mô tả mới (nếu có)
        new_priority: Độ ưu tiên mới (nếu có)
    """
    # Tạo dữ liệu sự kiện
    event_data = {
        'type': 'task_updated',
        'task_id': task_id,
        'timestamp': datetime.datetime.now().isoformat(),
        'source': 'windsurf_editor',
        'changes': {}
    }
    
    # Thêm các thay đổi (nếu có)
    if new_status is not None:
        event_data['changes']['status'] = new_status
    
    if new_title is not None:
        event_data['changes']['title'] = new_title
    
    if new_description is not None:
        event_data['changes']['description'] = new_description
    
    if new_priority is not None:
        event_data['changes']['priority'] = new_priority
    
    # Gửi sự kiện
    logger.info(f"Gửi sự kiện cập nhật task: {task_id}")
    api_client._notify_editor_event(event_data)
    logger.info("Đã gửi sự kiện")

def simulate_file_linked_to_task(api_client: WindSurfAPIClient, task_id: str, file_path: str):
    """
    Giả lập sự kiện liên kết file với task từ WindSurf Editor
    
    Args:
        api_client: API client đã được khởi tạo
        task_id: ID của task
        file_path: Đường dẫn đến file
    """
    # Tạo dữ liệu sự kiện
    event_data = {
        'type': 'file_linked_to_task',
        'task_id': task_id,
        'file_path': file_path,
        'timestamp': datetime.datetime.now().isoformat(),
        'source': 'windsurf_editor'
    }
    
    # Gửi sự kiện
    logger.info(f"Gửi sự kiện liên kết file {file_path} với task {task_id}")
    api_client._notify_editor_event(event_data)
    logger.info("Đã gửi sự kiện")

def main():
    """Hàm chính để chạy giả lập"""
    # Tạo API client
    project_dir = os.path.dirname(os.path.abspath(__file__))
    api_client = create_api_client(use_mock=True, project_dir=project_dir)
    
    # Chờ một chút để đảm bảo ứng dụng chính đã khởi động
    logger.info("Chờ 3 giây để đảm bảo ứng dụng chính đã khởi động...")
    time.sleep(3)
    
    # Giả lập tạo task mới
    simulate_task_created(
        api_client=api_client,
        task_id="WIND-456",
        title="Tính năng mới: Tích hợp với GitHub",
        description="Thêm tính năng đồng bộ task với GitHub Issues",
        priority="High",
        status="todo"
    )
    
    # Chờ một chút để xem kết quả
    logger.info("Chờ 2 giây...")
    time.sleep(2)
    
    # Giả lập cập nhật task
    simulate_task_updated(
        api_client=api_client,
        task_id="WIND-456",
        new_status="in_progress"
    )
    
    # Giả lập liên kết file với task
    simulate_file_linked_to_task(
        api_client=api_client,
        task_id="WIND-456",
        file_path=os.path.join(project_dir, "main.py")
    )
    
    logger.info("Hoàn thành giả lập sự kiện")

if __name__ == "__main__":
    main()
