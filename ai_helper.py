#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
AI Helper Module cho WindSurf Memory Tracker
-------------------------------------------
Module này cung cấp các hàm tiện ích để tương tác với các mô hình AI
thông qua các API như OpenAI hoặc các mô hình local như LMStudio, Ollama.

Các chức năng chính:
- Gọi API đến các mô hình AI
- Phân tích chất lượng code
- Tìm lỗi và vấn đề trong code
- Sinh docstring và unit test
- Đề xuất cải tiến code
"""

import os
import time
import json
import logging
import traceback
import requests
from dataclasses import dataclass
from typing import Dict, List, Any, Optional, Union, Tuple, Callable, TypeVar, cast
from functools import wraps

# Thiết lập logging
logger = logging.getLogger("windsurf_ai")

# Type variables cho decorator
T = TypeVar('T')
F = TypeVar('F', bound=Callable[..., Any])


@dataclass
class AIConfig:
    """Cấu hình cho các API AI"""
    # Cấu hình chung
    timeout: int = 60       # Giới hạn thời gian chờ (giây)
    retries: int = 2        # Số lần thử lại
    backoff_factor: int = 2  # Hệ số tăng thời gian chờ giữa các lần thử
    cache_enabled: bool = True  # Bật/tắt cache
    cache_ttl: int = 3600    # Thời gian sống của cache (giây)
    
    # Cấu hình OpenAI
    openai_api_key: str = ""  # API key cho OpenAI
    openai_model: str = "gpt-3.5-turbo"  # Model mặc định cho OpenAI
    openai_api_base: str = "https://api.openai.com/v1"  # Base URL cho OpenAI API
    
    # Cấu hình Anthropic Claude
    claude_api_key: str = ""  # API key cho Anthropic Claude
    claude_model: str = "claude-3-haiku-20240307"  # Model mặc định cho Claude
    
    # Cấu hình Google Gemini
    gemini_api_key: str = ""  # API key cho Google Gemini
    gemini_model: str = "gemini-pro"  # Model mặc định cho Gemini
    
    # Cấu hình local model
    local_endpoint: str = "http://localhost:1234/v1/chat/completions"  # Endpoint cho local model
    local_model: str = "qwen2.5-coder-3b-instruct"  # Model mặc định cho local
    
    # Cấu hình generation
    temperature: float = 0.7  # Độ sáng tạo mặc định
    max_tokens: int = 1000    # Số token tối đa trong kết quả
    streaming: bool = False   # Có sử dụng streaming response hay không

# Cấu hình mặc định
config = AIConfig()

# Cache cho các kết quả API
response_cache = {}


def get_cache_key(prompt: str, model: str, temperature: float) -> str:
    """
    Tạo khóa cache dựa trên prompt, model và temperature.
    
    Args:
        prompt: Nội dung prompt
        model: Tên model sử dụng
        temperature: Độ sáng tạo
        
    Returns:
        str: Khóa cache (hash)
    """
    # Tạo chuỗi đầu vào cho hash
    input_str = f"{prompt}|{model}|{temperature}"
    
    # Tạo hash MD5
    import hashlib
    return hashlib.md5(input_str.encode()).hexdigest()


def cache_response(key: str, response: str) -> None:
    """
    Lưu kết quả vào cache.
    
    Args:
        key: Khóa cache
        response: Kết quả cần lưu
    """
    if not config.cache_enabled:
        return
    
    response_cache[key] = {
        'response': response,
        'timestamp': time.time()
    }


def get_cached_response(key: str) -> Optional[str]:
    """
    Lấy kết quả từ cache nếu có và chưa hết hạn.
    
    Args:
        key: Khóa cache
        
    Returns:
        Optional[str]: Kết quả từ cache hoặc None nếu không có/hết hạn
    """
    if not config.cache_enabled or key not in response_cache:
        return None
    
    cache_entry = response_cache[key]
    cache_age = time.time() - cache_entry['timestamp']
    
    # Kiểm tra thời gian sống của cache
    if cache_age > config.cache_ttl:
        # Xóa cache hết hạn
        del response_cache[key]
        return None
    
    logger.info(f"Sử dụng kết quả từ cache (tuổi: {cache_age:.1f}s)")
    return cache_entry['response']


def clear_cache() -> None:
    """
Xóa tất cả các mục trong cache.
    """
    response_cache.clear()
    logger.info("Cache đã được xóa")


def retry_on_error(max_retries: Optional[int] = None, backoff_factor: Optional[int] = None,
                  allowed_exceptions: Tuple[type, ...] = (requests.RequestException, ConnectionError, TimeoutError)):
    """
    Decorator để thử lại hàm khi gặp lỗi.
    
    Args:
        max_retries: Số lần thử lại tối đa. Nếu None, sẽ dùng giá trị từ config.
        backoff_factor: Hệ số tăng thời gian chờ giữa các lần thử. Nếu None, sẽ dùng giá trị từ config.
        allowed_exceptions: Tuple các loại exception sẽ được thử lại.
        
    Returns:
        Decorator function
    """
    def decorator(func: F) -> F:
        @wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            # Sử dụng giá trị từ config nếu không được chỉ định
            _max_retries = max_retries if max_retries is not None else config.retries
            _backoff_factor = backoff_factor if backoff_factor is not None else config.backoff_factor
            
            retries = 0
            last_exception = None
            
            while retries <= _max_retries:
                try:
                    return func(*args, **kwargs)
                except allowed_exceptions as e:
                    last_exception = e
                    retries += 1
                    if retries > _max_retries:
                        logger.error(f"Hết số lần thử lại ({_max_retries}). Lỗi cuối cùng: {str(e)}")
                        break
                    
                    wait_time = _backoff_factor ** retries
                    logger.warning(f"Gặp lỗi: {str(e)}. Thử lại sau {wait_time} giây (lần {retries}/{_max_retries})")
                    time.sleep(wait_time)
                except Exception as e:
                    # Các exception khác không nằm trong allowed_exceptions sẽ được raise ngay lập tức
                    logger.error(f"Gặp lỗi không xử lý được: {str(e)}")
                    raise
            
            # Nếu đã hết số lần thử và vẫn lỗi
            if last_exception:
                logger.error(f"Không thể thực hiện thao tác sau {_max_retries} lần thử")
                raise last_exception
            
            return None  # Không bao giờ đến đây, nhưng cần để type checker hài lòng
            
        return cast(F, wrapper)
    return decorator


@retry_on_error()
def call_openai(prompt: str, api_key: Optional[str] = None, model: Optional[str] = None, 
              temperature: Optional[float] = None, max_tokens: Optional[int] = None, 
              timeout: Optional[int] = None) -> str:
    """
    Gọi OpenAI API và trả về kết quả.
    
    Args:
        prompt: Nội dung cần gửi đến mô hình
        api_key: API key cho OpenAI. Nếu None, sẽ dùng giá trị từ config
        model: Tên mô hình cần sử dụng. Nếu None, sẽ dùng giá trị từ config
        temperature: Độ sáng tạo (0.0-1.0). Nếu None, sẽ dùng giá trị từ config
        max_tokens: Số token tối đa trong kết quả. Nếu None, sẽ dùng giá trị từ config
        timeout: Thời gian chờ tối đa (giây). Nếu None, sẽ dùng giá trị từ config
        
    Returns:
        Kết quả từ mô hình hoặc thông báo lỗi
    """
    # Sử dụng giá trị từ config nếu không được chỉ định
    _api_key = api_key if api_key is not None else config.openai_api_key
    _model = model if model is not None else config.openai_model
    _temperature = temperature if temperature is not None else config.temperature
    _max_tokens = max_tokens if max_tokens is not None else config.max_tokens
    _timeout = timeout if timeout is not None else config.timeout
    
    if not _api_key:
        error_msg = "Thiếu OpenAI API key"
        logger.error(error_msg)
        return f"[Lỗi] {error_msg}"
    
    if not validate_prompt(prompt):
        error_msg = "Prompt không hợp lệ (rỗng hoặc chỉ có khoảng trắng)"
        logger.error(error_msg)
        return f"[Lỗi] {error_msg}"
        
    headers = {"Authorization": f"Bearer {_api_key}"}
    data = {
        "model": _model, 
        "messages": [{"role": "user", "content": prompt}],
        "temperature": _temperature,
        "max_tokens": _max_tokens
    }
    
    try:
        logger.info(f"Gọi OpenAI API với model {_model}")
        start_time = time.time()
        
        resp = requests.post(
            "https://api.openai.com/v1/chat/completions", 
            headers=headers, 
            json=data,
            timeout=_timeout
        )
        resp.raise_for_status()
        
        result = resp.json()
        duration = time.time() - start_time
        
        if "choices" not in result or len(result["choices"]) == 0:
            error_msg = "Không có kết quả từ OpenAI API"
            logger.error(error_msg)
            return f"[Lỗi] {error_msg}"
            
        content = result["choices"][0]["message"]["content"]
        logger.info(f"Nhận được kết quả từ OpenAI ({len(content)} ký tự) trong {duration:.2f}s")
        return content
        
    except requests.exceptions.ConnectionError:
        error_msg = "Không thể kết nối đến OpenAI API. Kiểm tra kết nối mạng."
        logger.error(error_msg)
        return f"[Lỗi] {error_msg}"
        
    except requests.exceptions.Timeout:
        error_msg = f"Yêu cầu bị timeout sau {_timeout} giây"
        logger.error(error_msg)
        return f"[Lỗi] {error_msg}"
        
    except requests.exceptions.HTTPError as e:
        error_msg = f"Lỗi HTTP: {e}"
        logger.error(error_msg)
        return f"[Lỗi] {error_msg}"
        
    except ValueError as e:
        error_msg = f"Lỗi khi xử lý JSON response: {e}"
        logger.error(error_msg)
        return f"[Lỗi] {error_msg}"
        
    except Exception as e:
        error_msg = f"Lỗi không xác định khi gọi OpenAI API: {e}"
        logger.error(f"{error_msg}\n{traceback.format_exc()}")
        return f"[Lỗi] {error_msg}"

@retry_on_error()
def call_local_model(prompt: str, endpoint: Optional[str] = None, model: Optional[str] = None,
                   temperature: Optional[float] = None, max_tokens: Optional[int] = None, 
                   timeout: Optional[int] = None) -> str:
    """
    Gửi prompt tới LMStudio (hoặc Ollama, LMDeploy...) và trả về kết quả.
    
    Args:
        prompt: Nội dung cần gửi đến mô hình
        endpoint: Địa chỉ API endpoint. Nếu None, sẽ dùng giá trị từ config
        model: Tên mô hình cần sử dụng. Nếu None, sẽ dùng giá trị từ config
        temperature: Độ sáng tạo (0.0-1.0). Nếu None, sẽ dùng giá trị từ config
        max_tokens: Số token tối đa trong kết quả. Nếu None, sẽ dùng giá trị từ config
        timeout: Thời gian chờ tối đa (giây). Nếu None, sẽ dùng giá trị từ config
        
    Returns:
        Kết quả từ mô hình hoặc thông báo lỗi
    """
    # Sử dụng giá trị từ config nếu không được chỉ định
    _endpoint = endpoint if endpoint is not None else config.local_endpoint
    _model = model if model is not None else config.local_model
    _temperature = temperature if temperature is not None else config.temperature
    _max_tokens = max_tokens if max_tokens is not None else config.max_tokens
    _timeout = timeout if timeout is not None else config.timeout
    
    if not validate_prompt(prompt):
        error_msg = "Prompt không hợp lệ (rỗng hoặc chỉ có khoảng trắng)"
        logger.error(error_msg)
        return f"[Lỗi] {error_msg}"
    
    payload = {
        "model": _model,
        "messages": [{"role": "user", "content": prompt}],
        "temperature": _temperature,
        "max_tokens": _max_tokens,
        "stream": False
    }
    
    try:
        logger.info(f"Gọi LLM API ({_model}) tại {_endpoint}")
        start_time = time.time()
        
        resp = requests.post(_endpoint, json=payload, timeout=_timeout)
        resp.raise_for_status()
        
        data = resp.json()
        duration = time.time() - start_time
        
        # Kiểm tra kết quả hợp lệ
        if "choices" not in data or len(data["choices"]) == 0:
            error_msg = "Không có kết quả từ LLM server"
            logger.error(error_msg)
            return f"[Lỗi] {error_msg}"
            
        if "message" not in data["choices"][0] or "content" not in data["choices"][0]["message"]:
            error_msg = "Kết quả từ LLM server không đúng định dạng"
            logger.error(error_msg)
            return f"[Lỗi] {error_msg}"
        
        # Lấy kết quả từ response
        content = data["choices"][0]["message"]["content"]
        logger.info(f"Nhận được kết quả từ LLM ({len(content)} ký tự) trong {duration:.2f}s")
        return content
        
    except requests.exceptions.ConnectionError:
        error_msg = f"Không thể kết nối đến {_endpoint}. Kiểm tra xem LLM server có đang chạy không."
        logger.error(error_msg)
        return f"[Lỗi] {error_msg}"
        
    except requests.exceptions.Timeout:
        error_msg = f"Yêu cầu bị timeout sau {_timeout} giây"
        logger.error(error_msg)
        return f"[Lỗi] {error_msg}"
        
    except requests.exceptions.HTTPError as e:
        status_code = e.response.status_code if hasattr(e, 'response') else 'unknown'
        error_msg = f"Lỗi HTTP {status_code}: {str(e)}"
        logger.error(error_msg)
        return f"[Lỗi] {error_msg}"
        
    except ValueError as e:
        error_msg = f"Lỗi khi xử lý JSON response: {str(e)}"
        logger.error(error_msg)
        return f"[Lỗi] {error_msg}"
        
    except KeyError as e:
        error_msg = f"Thiếu trường dữ liệu trong kết quả: {str(e)}"
        logger.error(error_msg)
        return f"[Lỗi] {error_msg}"
        
    except Exception as e:
        error_msg = f"Lỗi không xác định khi gọi LLM: {str(e)}"
        logger.error(f"{error_msg}\n{traceback.format_exc()}")
        return f"[Lỗi] {error_msg}"


class AIHelper:
    """
    Lớp quản lý các chức năng AI trong ứng dụng.
    Cung cấp các phương thức để phân tích và tối ưu code sử dụng mô hình AI.
    """
    
    def __init__(self, custom_config: Optional[AIConfig] = None):
        """
        Khởi tạo AIHelper với cấu hình tùy chỉnh.
        
        Args:
            custom_config: Cấu hình tùy chỉnh, nếu None sẽ sử dụng cấu hình mặc định
        """
        self.config = custom_config if custom_config else config
    
    def analyze_code_quality(self, code: str, temperature: float = 0.3) -> str:
        """
        Đánh giá chất lượng code bằng LLM.
        
        Args:
            code: Mã nguồn cần phân tích
            temperature: Độ sáng tạo của mô hình (0.0-1.0)
            
        Returns:
            Kết quả phân tích chất lượng code
        """
        prompt = f"""Đánh giá chất lượng đoạn code sau, chỉ ra điểm mạnh/yếu, code smell nếu có.
Hãy phân tích theo các tiêu chí: tính bảo trì, hiệu suất, tính rò rỉ, và các best practice.

```python
{code}
```

Kết quả đánh giá:"""
        return call_local_model(prompt, temperature=temperature)
    
    def find_code_issues(self, code: str, temperature: float = 0.3) -> str:
        """
        Tìm lỗi, bug, vấn đề bảo mật trong code bằng LLM.
        
        Args:
            code: Mã nguồn cần phân tích
            temperature: Độ sáng tạo của mô hình (0.0-1.0)
            
        Returns:
            Danh sách các vấn đề được phát hiện
        """
        prompt = f"""Tìm lỗi, bug, hoặc vấn đề bảo mật trong đoạn code sau.
Hãy phân tích kỹ lưỡng và liệt kê các vấn đề theo mức độ nghiêm trọng (Critical, High, Medium, Low).

```python
{code}
```

Các vấn đề phát hiện:
"""
        return call_local_model(prompt, temperature=temperature)
    
    def generate_docstring(self, code: str, temperature: float = 0.3) -> str:
        """
        Sinh docstring/comment cho code bằng LLM.
        
        Args:
            code: Mã nguồn cần tạo docstring
            temperature: Độ sáng tạo của mô hình (0.0-1.0)
            
        Returns:
            Docstring được tạo ra
        """
        prompt = f"""Viết docstring chi tiết cho đoạn code sau theo chuẩn Google style.
Bao gồm mô tả chức năng, các tham số (với kiểu dữ liệu), giá trị trả về, và các exception nếu có.

```python
{code}
```

Docstring:
"""
        return call_local_model(prompt, temperature=temperature)
    
    def suggest_refactor(self, code: str, temperature: float = 0.3) -> str:
        """
        Đề xuất refactor/tối ưu hóa code bằng LLM.
        
        Args:
            code: Mã nguồn cần refactor
            temperature: Độ sáng tạo của mô hình (0.0-1.0)
            
        Returns:
            Đề xuất refactor và mã nguồn đã được cải tiến
        """
        prompt = f"""Đề xuất cách tối ưu hóa hoặc refactor đoạn code sau.
Hãy giải thích lý do cần refactor và cung cấp mã nguồn đã được cải tiến.

```python
{code}
```

Đề xuất refactor:
"""
        return call_local_model(prompt, temperature=temperature)
    
    def semantic_analysis(self, code: str, temperature: float = 0.3) -> str:
        """
        Phân tích ý nghĩa, mục đích đoạn code bằng LLM.
        
        Args:
            code: Mã nguồn cần phân tích
            temperature: Độ sáng tạo của mô hình (0.0-1.0)
            
        Returns:
            Phân tích ý nghĩa và mục đích của code
        """
        prompt = f"""Phân tích mục đích, ý nghĩa của đoạn code sau (không chỉ mô tả cú pháp).
Hãy giải thích thuật toán, logic, và cách tiếp cận được sử dụng.

```python
{code}
```

Phân tích:
"""
        return call_local_model(prompt, temperature=temperature)
    
    def explain_code(self, code: str, temperature: float = 0.3) -> str:
        """
        Giải thích code dành cho người mới bắt đầu bằng LLM.
        
        Args:
            code: Mã nguồn cần giải thích
            temperature: Độ sáng tạo của mô hình (0.0-1.0)
            
        Returns:
            Giải thích code theo cách dễ hiểu
        """
        prompt = f"""Giải thích đoạn code sau theo cách dễ hiểu cho người mới học lập trình.
Hãy giải thích từng dòng và khái niệm quan trọng.

```python
{code}
```

Giải thích:
"""
        return call_local_model(prompt, temperature=temperature)
    
    def generate_unit_test(self, code: str, temperature: float = 0.3) -> str:
        """
        Tạo unit test cho code bằng LLM.
        
        Args:
            code: Mã nguồn cần tạo unit test
            temperature: Độ sáng tạo của mô hình (0.0-1.0)
            
        Returns:
            Unit test được tạo ra
        """
        prompt = f"""Viết unit test cho đoạn code sau sử dụng pytest.
Bao gồm các test case cho các tình huống biên thử và các trường hợp hợp lệ.

```python
{code}
```

Unit test:
"""
        return call_local_model(prompt, temperature=temperature)
    
    def translate_code(self, code: str, target_language: str, temperature: float = 0.3) -> str:
        """
        Dịch code từ Python sang ngôn ngữ lập trình khác.
        
        Args:
            code: Mã nguồn Python cần dịch
            target_language: Ngôn ngữ đích (ví dụ: "JavaScript", "Java", "C++")
            temperature: Độ sáng tạo của mô hình (0.0-1.0)
            
        Returns:
            Mã nguồn đã được dịch sang ngôn ngữ đích
        """
        prompt = f"""Dịch đoạn code Python sau sang {target_language}.
Giữ nguyên chức năng và logic, đồng thời tận dụng các tính năng đặc trưng của {target_language}.

```python
{code}
```

Mã {target_language}:
"""
        return call_local_model(prompt, temperature=temperature)
    
    def improve_error_handling(self, code: str, temperature: float = 0.3) -> str:
        """
        Cải thiện xử lý lỗi trong code.
        
        Args:
            code: Mã nguồn cần cải thiện xử lý lỗi
            temperature: Độ sáng tạo của mô hình (0.0-1.0)
            
        Returns:
            Mã nguồn với xử lý lỗi được cải thiện
        """
        prompt = f"""Cải thiện xử lý lỗi trong đoạn code sau.
Thêm try-except blocks cho các thao tác có thể gây lỗi, xử lý các trường hợp đặc biệt, và đảm bảo code không bị crash.

```python
{code}
```

Code với xử lý lỗi cải thiện:
"""
        return call_local_model(prompt, temperature=temperature)


# Các hàm tiện ích
def validate_prompt(prompt: str) -> bool:
    """Kiểm tra xem prompt có hợp lệ không (không rỗng và không chỉ có khoảng trắng)"""
    return len(prompt.strip()) > 0


@retry_on_error()
def call_claude(prompt: str, api_key: Optional[str] = None, model: Optional[str] = None,
               temperature: Optional[float] = None, max_tokens: Optional[int] = None,
               timeout: Optional[int] = None) -> str:
    """
    Gọi Anthropic Claude API và trả về kết quả.
    
    Args:
        prompt: Nội dung cần gửi đến mô hình
        api_key: API key cho Claude. Nếu None, sẽ dùng giá trị từ config
        model: Tên mô hình cần sử dụng. Nếu None, sẽ dùng giá trị từ config
        temperature: Độ sáng tạo (0.0-1.0). Nếu None, sẽ dùng giá trị từ config
        max_tokens: Số token tối đa trong kết quả. Nếu None, sẽ dùng giá trị từ config
        timeout: Thời gian chờ tối đa (giây). Nếu None, sẽ dùng giá trị từ config
        
    Returns:
        Kết quả từ mô hình hoặc thông báo lỗi
    """
    # Sử dụng giá trị từ config nếu không được chỉ định
    _api_key = api_key if api_key is not None else config.claude_api_key
    _model = model if model is not None else config.claude_model
    _temperature = temperature if temperature is not None else config.temperature
    _max_tokens = max_tokens if max_tokens is not None else config.max_tokens
    _timeout = timeout if timeout is not None else config.timeout
    
    # Kiểm tra cache
    cache_key = get_cache_key(prompt, _model, _temperature)
    cached_response = get_cached_response(cache_key)
    if cached_response:
        return cached_response
    
    if not _api_key:
        error_msg = "Thiếu Claude API key"
        logger.error(error_msg)
        return f"[Lỗi] {error_msg}"
    
    if not validate_prompt(prompt):
        error_msg = "Prompt không hợp lệ (rỗng hoặc chỉ có khoảng trắng)"
        logger.error(error_msg)
        return f"[Lỗi] {error_msg}"
    
    headers = {
        "x-api-key": _api_key,
        "anthropic-version": "2023-06-01",
        "content-type": "application/json"
    }
    
    data = {
        "model": _model,
        "messages": [{"role": "user", "content": prompt}],
        "temperature": _temperature,
        "max_tokens": _max_tokens
    }
    
    try:
        logger.info(f"Gọi Claude API với model {_model}")
        start_time = time.time()
        
        resp = requests.post(
            "https://api.anthropic.com/v1/messages",
            headers=headers,
            json=data,
            timeout=_timeout
        )
        resp.raise_for_status()
        
        result = resp.json()
        duration = time.time() - start_time
        
        content = result.get("content", [])
        if not content or not isinstance(content, list):
            error_msg = "Không có kết quả từ Claude API"
            logger.error(error_msg)
            return f"[Lỗi] {error_msg}"
            
        # Lấy nội dung văn bản từ kết quả
        text_content = ""
        for block in content:
            if block.get("type") == "text":
                text_content += block.get("text", "")
        
        logger.info(f"Nhận được kết quả từ Claude ({len(text_content)} ký tự) trong {duration:.2f}s")
        
        # Lưu vào cache
        cache_response(cache_key, text_content)
        
        return text_content
        
    except Exception as e:
        error_msg = f"Lỗi khi gọi Claude API: {str(e)}"
        logger.error(f"{error_msg}\n{traceback.format_exc()}")
        return f"[Lỗi] {error_msg}"


@retry_on_error()
def call_gemini(prompt: str, api_key: Optional[str] = None, model: Optional[str] = None,
               temperature: Optional[float] = None, max_tokens: Optional[int] = None,
               timeout: Optional[int] = None) -> str:
    """
    Gọi Google Gemini API và trả về kết quả.
    
    Args:
        prompt: Nội dung cần gửi đến mô hình
        api_key: API key cho Gemini. Nếu None, sẽ dùng giá trị từ config
        model: Tên mô hình cần sử dụng. Nếu None, sẽ dùng giá trị từ config
        temperature: Độ sáng tạo (0.0-1.0). Nếu None, sẽ dùng giá trị từ config
        max_tokens: Số token tối đa trong kết quả. Nếu None, sẽ dùng giá trị từ config
        timeout: Thời gian chờ tối đa (giây). Nếu None, sẽ dùng giá trị từ config
        
    Returns:
        Kết quả từ mô hình hoặc thông báo lỗi
    """
    # Sử dụng giá trị từ config nếu không được chỉ định
    _api_key = api_key if api_key is not None else config.gemini_api_key
    _model = model if model is not None else config.gemini_model
    _temperature = temperature if temperature is not None else config.temperature
    _max_tokens = max_tokens if max_tokens is not None else config.max_tokens
    _timeout = timeout if timeout is not None else config.timeout
    
    # Kiểm tra cache
    cache_key = get_cache_key(prompt, _model, _temperature)
    cached_response = get_cached_response(cache_key)
    if cached_response:
        return cached_response
    
    if not _api_key:
        error_msg = "Thiếu Gemini API key"
        logger.error(error_msg)
        return f"[Lỗi] {error_msg}"
    
    if not validate_prompt(prompt):
        error_msg = "Prompt không hợp lệ (rỗng hoặc chỉ có khoảng trắng)"
        logger.error(error_msg)
        return f"[Lỗi] {error_msg}"
    
    try:
        logger.info(f"Gọi Gemini API với model {_model}")
        start_time = time.time()
        
        url = f"https://generativelanguage.googleapis.com/v1/models/{_model}:generateContent?key={_api_key}"
        
        data = {
            "contents": [{"parts": [{"text": prompt}]}],
            "generationConfig": {
                "temperature": _temperature,
                "maxOutputTokens": _max_tokens,
                "topP": 0.8,
                "topK": 40
            }
        }
        
        resp = requests.post(
            url,
            json=data,
            timeout=_timeout
        )
        resp.raise_for_status()
        
        result = resp.json()
        duration = time.time() - start_time
        
        # Xử lý kết quả
        if not result.get("candidates"):
            error_msg = "Không có kết quả từ Gemini API"
            logger.error(error_msg)
            return f"[Lỗi] {error_msg}"
            
        content = result["candidates"][0]["content"]["parts"][0]["text"]
        logger.info(f"Nhận được kết quả từ Gemini ({len(content)} ký tự) trong {duration:.2f}s")
        
        # Lưu vào cache
        cache_response(cache_key, content)
        
        return content
        
    except Exception as e:
        error_msg = f"Lỗi khi gọi Gemini API: {str(e)}"
        logger.error(f"{error_msg}\n{traceback.format_exc()}")
        return f"[Lỗi] {error_msg}"


def estimate_token_count(text: str) -> int:
    """
    Ước tính số token trong văn bản.
    
    Args:
        text: Văn bản cần ước tính
        
    Returns:
        int: Ước tính số token
    """
    # Phương pháp ước tính đơn giản: 1 token ~ 4 ký tự
    return len(text) // 4


# Tạo instance mặc định của AIHelper
ai_helper = AIHelper()


# Các hàm wrapper để tương thích ngược với code cũ
def analyze_code_quality(code: str, endpoint: Optional[str] = None, 
                        model: Optional[str] = None, temperature: float = 0.3) -> str:
    """Đánh giá chất lượng code bằng LLM local"""
    return ai_helper.analyze_code_quality(code, temperature)


def find_code_issues(code: str, endpoint: Optional[str] = None, 
                    model: Optional[str] = None, temperature: float = 0.3) -> str:
    """Tìm lỗi, bug, vấn đề bảo mật trong code bằng LLM local"""
    return ai_helper.find_code_issues(code, temperature)


def generate_docstring(code: str, endpoint: Optional[str] = None, 
                      model: Optional[str] = None, temperature: float = 0.3) -> str:
    """Sinh docstring/comment cho code bằng LLM local"""
    return ai_helper.generate_docstring(code, temperature)


def suggest_refactor(code: str, endpoint: Optional[str] = None, 
                    model: Optional[str] = None, temperature: float = 0.3) -> str:
    """Đề xuất refactor/tối ưu hóa code bằng LLM local"""
    return ai_helper.suggest_refactor(code, temperature)


def semantic_analysis(code: str, endpoint: Optional[str] = None, 
                     model: Optional[str] = None, temperature: float = 0.3) -> str:
    """Phân tích ý nghĩa, mục đích đoạn code bằng LLM local"""
    return ai_helper.semantic_analysis(code, temperature)


def explain_code(code: str, endpoint: Optional[str] = None,
                model: Optional[str] = None, temperature: float = 0.3) -> str:
    """Giải thích code dành cho người mới bắt đầu bằng LLM local"""
    return ai_helper.explain_code(code, temperature)


def generate_unit_test(code: str, endpoint: Optional[str] = None,
                      model: Optional[str] = None, temperature: float = 0.3) -> str:
    """Tạo unit test cho code bằng LLM local"""
    return ai_helper.generate_unit_test(code, temperature)


def summarize_code(code: str, max_length: int = 500, temperature: float = 0.3) -> str:
    """
    Tóm tắt mã nguồn thành một mô tả ngắn gọn.
    
    Args:
        code: Mã nguồn cần tóm tắt
        max_length: Độ dài tối đa của bản tóm tắt
        temperature: Độ sáng tạo của mô hình (0.0-1.0)
        
    Returns:
        str: Bản tóm tắt mã nguồn
    """
    prompt = f"""Tóm tắt mã nguồn sau thành một mô tả ngắn gọn, không quá {max_length} ký tự. 
    Tập trung vào mục đích, chức năng chính và cấu trúc của code.

    ```
    {code}
    ```
    """
    return ai_helper._call_ai(prompt, temperature)


def review_code_changes(old_code: str, new_code: str, temperature: float = 0.3) -> str:
    """
    Review các thay đổi code giữa phiên bản cũ và mới.
    
    Args:
        old_code: Mã nguồn cũ
        new_code: Mã nguồn mới
        temperature: Độ sáng tạo của mô hình (0.0-1.0)
        
    Returns:
        str: Báo cáo review các thay đổi
    """
    import difflib
    diff = '\n'.join(difflib.unified_diff(
        old_code.splitlines(),
        new_code.splitlines(),
        fromfile='old',
        tofile='new',
        lineterm=''
    ))
    
    prompt = f"""Review các thay đổi code sau đây. Đánh giá chất lượng của các thay đổi, 
    chỉ ra các vấn đề tiềm ẩn và đề xuất cải tiến nếu có.

    ```diff
    {diff}
    ```
    """
    return ai_helper._call_ai(prompt, temperature)


def generate_commit_message(diff: str, temperature: float = 0.3) -> str:
    """
    Tạo commit message từ diff.
    
    Args:
        diff: Nội dung diff
        temperature: Độ sáng tạo của mô hình (0.0-1.0)
        
    Returns:
        str: Commit message được tạo ra
    """
    prompt = f"""Tạo một commit message có ý nghĩa cho các thay đổi code sau đây. 
    Commit message nên ngắn gọn, rõ ràng và mô tả được mục đích của các thay đổi.
    Sử dụng định dạng sau: tiêu đề ngắn gọn trên dòng đầu tiên, sau đó là một dòng trống, 
    tiếp theo là mô tả chi tiết hơn (nếu cần).

    ```diff
    {diff}
    ```
    """
    return ai_helper._call_ai(prompt, temperature)
