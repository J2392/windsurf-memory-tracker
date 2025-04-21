"""
WindSurf Memory Tracker - Cấu hình
---------------------------------
Quản lý các thiết lập và cấu hình cho ứng dụng.
"""

import os
import json
import logging
from typing import Dict, Any, List, Optional, Union

# Thiết lập logging
logging.basicConfig(level=logging.INFO, 
                   format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger("windsurf_settings")

# Đường dẫn mặc định
DEFAULT_DATA_DIR = os.path.join(os.path.expanduser("~"), ".windsurf_memory")
DEFAULT_CONFIG_FILE = os.path.join(DEFAULT_DATA_DIR, "config.json")
DEFAULT_DB_FILE = os.path.join(DEFAULT_DATA_DIR, "data.db")
DEFAULT_BACKUP_DIR = os.path.join(DEFAULT_DATA_DIR, "backups")
DEFAULT_LOG_DIR = os.path.join(DEFAULT_DATA_DIR, "logs")

# Tạo thư mục nếu chưa tồn tại
os.makedirs(DEFAULT_DATA_DIR, exist_ok=True)
os.makedirs(DEFAULT_BACKUP_DIR, exist_ok=True)
os.makedirs(DEFAULT_LOG_DIR, exist_ok=True)

# Cấu hình mặc định
DEFAULT_CONFIG = {
    "general": {
        "theme": "dark",
        "language": "en",
        "auto_backup": True,
        "backup_interval_minutes": 30,
        "max_backups": 10,
    },
    "editor": {
        "font_family": "Consolas",
        "font_size": 12,
        "tab_size": 4,
        "use_spaces": True,
        "line_numbers": True,
        "highlight_current_line": True,
        "auto_indent": True,
    },
    "snapshot": {
        "auto_snapshot": True,
        "snapshot_interval_seconds": 60,
        "min_change_threshold": 0.01,
        "max_snapshots_per_file": 100,
        "compresssion_level": 6,
    },
    "kanban": {
        "columns": ["todo", "in_progress", "done"],
        "column_names": {
            "todo": "TO DO",
            "in_progress": "IN PROGRESS",
            "done": "DONE"
        },
        "priorities": ["Low", "Medium", "High"],
        "priority_colors": {
            "Low": "#808080",
            "Medium": "#FFD700",
            "High": "#FF4500"
        }
    },
    "api": {
        "use_mock": True,
        "polling_interval_seconds": 5,
        "watched_extensions": [".py", ".js", ".html", ".css", ".txt"],
    },
    "ui": {
        "colors": {
            "background": "#000000",
            "foreground": "#FFFFFF",
            "accent": "#00FF00",
            "secondary": "#6B6B8D",
            "code_background": "#121218",
            "card_background": "#15151F"
        },
        "layout": {
            "main_split_ratio": 0.7,
            "editor_kanban_ratio": 0.6
        }
    },
    "paths": {
        "data_dir": DEFAULT_DATA_DIR,
        "db_file": DEFAULT_DB_FILE,
        "backup_dir": DEFAULT_BACKUP_DIR,
        "log_dir": DEFAULT_LOG_DIR
    }
}


class Settings:
    """Quản lý cấu hình cho ứng dụng"""
    
    def __init__(self, config_file: str = DEFAULT_CONFIG_FILE):
        self.config_file = config_file
        self.config = self._load_config()
    
    def _load_config(self) -> Dict[str, Any]:
        """Tải cấu hình từ file hoặc tạo mới nếu chưa tồn tại"""
        if os.path.exists(self.config_file):
            try:
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    config = json.load(f)
                
                # Cập nhật cấu hình với các thiết lập mặc định nếu thiếu
                merged_config = DEFAULT_CONFIG.copy()
                self._update_nested_dict(merged_config, config)
                
                logger.info(f"Đã tải cấu hình từ {self.config_file}")
                return merged_config
            except Exception as e:
                logger.error(f"Lỗi khi tải cấu hình: {e}")
                logger.info("Sử dụng cấu hình mặc định")
                return DEFAULT_CONFIG.copy()
        else:
            # Tạo file cấu hình mới với thiết lập mặc định
            self.save_config(DEFAULT_CONFIG.copy())
            return DEFAULT_CONFIG.copy()
    
    def _update_nested_dict(self, d: Dict[str, Any], u: Dict[str, Any]) -> Dict[str, Any]:
        """Cập nhật từ điển đệ quy, chỉ thay đổi các giá trị tồn tại"""
        for k, v in u.items():
            if isinstance(v, dict) and k in d and isinstance(d[k], dict):
                self._update_nested_dict(d[k], v)
            else:
                d[k] = v
        return d
    
    def save_config(self, config: Dict[str, Any] = None) -> bool:
        """Lưu cấu hình hiện tại hoặc cấu hình được chỉ định vào file"""
        if config is None:
            config = self.config
        
        try:
            os.makedirs(os.path.dirname(self.config_file), exist_ok=True)
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(config, f, indent=4)
            
            logger.info(f"Đã lưu cấu hình vào {self.config_file}")
            return True
        except Exception as e:
            logger.error(f"Lỗi khi lưu cấu hình: {e}")
            return False
    
    def get(self, section: str, key: str, default: Any = None) -> Any:
        """Lấy giá trị cấu hình từ section và key"""
        try:
            return self.config[section][key]
        except KeyError:
            logger.warning(f"Không tìm thấy cấu hình {section}.{key}, sử dụng giá trị mặc định: {default}")
            return default
    
    def set(self, section: str, key: str, value: Any) -> bool:
        """Thiết lập giá trị cấu hình cho section và key"""
        try:
            if section not in self.config:
                self.config[section] = {}
            
            self.config[section][key] = value
            logger.info(f"Đã thiết lập {section}.{key} = {value}")
            return True
        except Exception as e:
            logger.error(f"Lỗi khi thiết lập {section}.{key}: {e}")
            return False
    
    def get_section(self, section: str) -> Dict[str, Any]:
        """Lấy toàn bộ section cấu hình"""
        return self.config.get(section, {})
    
    def get_color(self, name: str) -> str:
        """Lấy màu từ cấu hình UI"""
        return self.get("ui", "colors", {}).get(name, "#FFFFFF")
    
    def get_db_path(self) -> str:
        """Lấy đường dẫn đến file cơ sở dữ liệu"""
        return self.get("paths", "db_file", DEFAULT_DB_FILE)
    
    def get_backup_dir(self) -> str:
        """Lấy đường dẫn đến thư mục backup"""
        return self.get("paths", "backup_dir", DEFAULT_BACKUP_DIR)
    
    def get_log_dir(self) -> str:
        """Lấy đường dẫn đến thư mục log"""
        return self.get("paths", "log_dir", DEFAULT_LOG_DIR)
    
    def get_theme(self) -> str:
        """Lấy theme hiện tại"""
        return self.get("general", "theme", "dark")
    
    def get_watched_extensions(self) -> List[str]:
        """Lấy danh sách các phần mở rộng file được theo dõi"""
        return self.get("api", "watched_extensions", [".py", ".js", ".html", ".css", ".txt"])
    
    def reset_to_defaults(self) -> bool:
        """Đặt lại tất cả cấu hình về giá trị mặc định"""
        self.config = DEFAULT_CONFIG.copy()
        return self.save_config()


# Tạo instance mặc định để sử dụng
settings = Settings()


def get_settings() -> Settings:
    """Trả về instance settings toàn cục"""
    return settings

# Hàm trợ giúp để lấy cấu hình từ bất kỳ đâu trong ứng dụng
def get_settings() -> Settings:
    """Trả về instance settings toàn cục"""
    return settings


if __name__ == "__main__":
    # Kiểm tra và hiển thị cấu hình hiện tại
    settings = Settings()
    print(f"Cấu hình hiện tại tại: {settings.config_file}")
    print(json.dumps(settings.config, indent=2))