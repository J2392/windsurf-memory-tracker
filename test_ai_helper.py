#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Test cho module ai_helper trong WindSurf Memory Tracker

Chạy test với lệnh: python -m pytest test_ai_helper.py -v
"""

import unittest
import json
import os
import tempfile
from unittest.mock import patch, MagicMock
import requests

from ai_helper import (
    AIConfig, config, retry_on_error, validate_prompt,
    call_local_model, call_openai, AIHelper
)


class TestAIConfig(unittest.TestCase):
    """Test cho class AIConfig"""
    
    def test_default_config(self):
        """Test cấu hình mặc định"""
        test_config = AIConfig()
        self.assertEqual(test_config.timeout, 60)
        self.assertEqual(test_config.retries, 2)
        self.assertEqual(test_config.backoff_factor, 2)
        self.assertEqual(test_config.local_model, "qwen2.5-coder-3b-instruct")
        self.assertEqual(test_config.temperature, 0.7)
        
    def test_custom_config(self):
        """Test cấu hình tùy chỉnh"""
        test_config = AIConfig(
            timeout=30,
            retries=3,
            local_model="gpt4all",
            temperature=0.5
        )
        self.assertEqual(test_config.timeout, 30)
        self.assertEqual(test_config.retries, 3)
        self.assertEqual(test_config.local_model, "gpt4all")
        self.assertEqual(test_config.temperature, 0.5)


class TestRetryDecorator(unittest.TestCase):
    """Test cho decorator retry_on_error"""
    
    def test_retry_success(self):
        """Test retry với hàm thành công"""
        mock_func = MagicMock(return_value="success")
        decorated_func = retry_on_error()(mock_func)
        
        result = decorated_func()
        self.assertEqual(result, "success")
        self.assertEqual(mock_func.call_count, 1)
        
    def test_retry_with_allowed_exception(self):
        """Test retry với exception cho phép"""
        mock_func = MagicMock(side_effect=[
            requests.exceptions.ConnectionError("Connection error"),
            "success"
        ])
        decorated_func = retry_on_error(max_retries=1)(mock_func)
        
        result = decorated_func()
        self.assertEqual(result, "success")
        self.assertEqual(mock_func.call_count, 2)
        
    def test_retry_with_not_allowed_exception(self):
        """Test retry với exception không cho phép"""
        mock_func = MagicMock(side_effect=ValueError("Value error"))
        decorated_func = retry_on_error()(mock_func)
        
        with self.assertRaises(ValueError):
            decorated_func()
        self.assertEqual(mock_func.call_count, 1)
        
    def test_retry_max_attempts(self):
        """Test retry với số lần thử tối đa"""
        mock_func = MagicMock(side_effect=requests.exceptions.ConnectionError("Connection error"))
        decorated_func = retry_on_error(max_retries=2)(mock_func)
        
        with self.assertRaises(requests.exceptions.ConnectionError):
            decorated_func()
        self.assertEqual(mock_func.call_count, 3)  # 1 lần đầu + 2 lần retry


class TestValidatePrompt(unittest.TestCase):
    """Test cho hàm validate_prompt"""
    
    def test_valid_prompt(self):
        """Test prompt hợp lệ"""
        self.assertTrue(validate_prompt("This is a valid prompt"))
        
    def test_empty_prompt(self):
        """Test prompt rỗng"""
        self.assertFalse(validate_prompt(""))
        
    def test_whitespace_prompt(self):
        """Test prompt chỉ có khoảng trắng"""
        self.assertFalse(validate_prompt("   "))


class TestCallLocalModel(unittest.TestCase):
    """Test cho hàm call_local_model"""
    
    @patch('requests.post')
    def test_successful_call(self, mock_post):
        """Test gọi API thành công"""
        # Tạo mock response
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "choices": [
                {
                    "message": {
                        "content": "This is a test response"
                    }
                }
            ]
        }
        mock_post.return_value = mock_response
        
        result = call_local_model("Test prompt")
        self.assertEqual(result, "This is a test response")
        
    @patch('requests.post')
    def test_connection_error(self, mock_post):
        """Test lỗi kết nối"""
        mock_post.side_effect = requests.exceptions.ConnectionError("Connection error")
        
        result = call_local_model("Test prompt")
        self.assertTrue(result.startswith("[Lỗi]"))
        
    @patch('requests.post')
    def test_invalid_response(self, mock_post):
        """Test response không hợp lệ"""
        # Tạo mock response không có choices
        mock_response = MagicMock()
        mock_response.json.return_value = {}
        mock_post.return_value = mock_response
        
        result = call_local_model("Test prompt")
        self.assertTrue(result.startswith("[Lỗi]"))


class TestAIHelper(unittest.TestCase):
    """Test cho class AIHelper"""
    
    def setUp(self):
        """Thiết lập cho test"""
        self.ai_helper = AIHelper()
        
    @patch('ai_helper.call_local_model')
    def test_analyze_code_quality(self, mock_call_local_model):
        """Test phân tích chất lượng code"""
        mock_call_local_model.return_value = "Code quality analysis"
        
        result = self.ai_helper.analyze_code_quality("def test(): pass")
        self.assertEqual(result, "Code quality analysis")
        
        # Kiểm tra prompt có chứa code
        args, kwargs = mock_call_local_model.call_args
        self.assertIn("def test(): pass", args[0])
        
    @patch('ai_helper.call_local_model')
    def test_find_code_issues(self, mock_call_local_model):
        """Test tìm lỗi trong code"""
        mock_call_local_model.return_value = "Code issues found"
        
        result = self.ai_helper.find_code_issues("def test(): pass")
        self.assertEqual(result, "Code issues found")
        
    @patch('ai_helper.call_local_model')
    def test_generate_docstring(self, mock_call_local_model):
        """Test tạo docstring"""
        mock_call_local_model.return_value = "Generated docstring"
        
        result = self.ai_helper.generate_docstring("def test(): pass")
        self.assertEqual(result, "Generated docstring")
        
    @patch('ai_helper.call_local_model')
    def test_suggest_refactor(self, mock_call_local_model):
        """Test đề xuất refactor"""
        mock_call_local_model.return_value = "Refactor suggestions"
        
        result = self.ai_helper.suggest_refactor("def test(): pass")
        self.assertEqual(result, "Refactor suggestions")
        
    @patch('ai_helper.call_local_model')
    def test_translate_code(self, mock_call_local_model):
        """Test dịch code"""
        mock_call_local_model.return_value = "Translated code"
        
        result = self.ai_helper.translate_code("def test(): pass", "JavaScript")
        self.assertEqual(result, "Translated code")
        
        # Kiểm tra prompt có chứa ngôn ngữ đích
        args, kwargs = mock_call_local_model.call_args
        self.assertIn("JavaScript", args[0])


if __name__ == "__main__":
    unittest.main()
