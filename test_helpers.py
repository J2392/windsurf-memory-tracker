#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Kiểm thử các chức năng helper trong WindSurf Memory Tracker
----------------------------------------------------------
Script này kiểm tra các chức năng mới đã thêm vào ultis.py và ai_helper.py
"""

import os
import sys
import unittest
import tempfile
import json
import shutil
from typing import Dict, Any, List

# Import các module cần test
import ultis
import ai_helper


class TestUltisFileOperations(unittest.TestCase):
    """Kiểm thử các chức năng xử lý file trong ultis.py"""
    
    def setUp(self):
        """Thiết lập môi trường test"""
        # Tạo thư mục tạm thời cho test
        self.test_dir = tempfile.mkdtemp()
        self.test_file = os.path.join(self.test_dir, "test_file.txt")
        self.test_content = "Đây là nội dung test.\nDòng thứ hai.\n"
        
        # Tạo file test
        with open(self.test_file, "w", encoding="utf-8") as f:
            f.write(self.test_content)
            
        # Tạo một số file khác để test find_files_by_extension
        self.py_file = os.path.join(self.test_dir, "test.py")
        self.json_file = os.path.join(self.test_dir, "test.json")
        
        with open(self.py_file, "w") as f:
            f.write("print('Hello World')")
            
        with open(self.json_file, "w") as f:
            f.write('{"test": "data"}')
    
    def tearDown(self):
        """Dọn dẹp sau khi test"""
        # Xóa thư mục tạm thời
        shutil.rmtree(self.test_dir)
    
    def test_safe_read_file(self):
        """Kiểm tra hàm safe_read_file"""
        # Test đọc file tồn tại
        content = ultis.safe_read_file(self.test_file)
        self.assertEqual(content, self.test_content)
        
        # Test đọc file không tồn tại
        non_existent_file = os.path.join(self.test_dir, "not_exist.txt")
        content = ultis.safe_read_file(non_existent_file)
        self.assertIsNone(content)
    
    def test_safe_write_file(self):
        """Kiểm tra hàm safe_write_file"""
        # Test ghi file mới
        new_file = os.path.join(self.test_dir, "new_file.txt")
        new_content = "Nội dung mới"
        result = ultis.safe_write_file(new_file, new_content)
        self.assertTrue(result)
        
        # Kiểm tra nội dung đã ghi
        with open(new_file, "r", encoding="utf-8") as f:
            content = f.read()
        self.assertEqual(content, new_content)
        
        # Test ghi file trong thư mục không tồn tại
        deep_file = os.path.join(self.test_dir, "deep", "path", "file.txt")
        result = ultis.safe_write_file(deep_file, new_content)
        self.assertTrue(result)
        self.assertTrue(os.path.exists(deep_file))
    
    def test_find_files_by_extension(self):
        """Kiểm tra hàm find_files_by_extension"""
        # Tìm file .py
        py_files = ultis.find_files_by_extension(self.test_dir, ["py"])
        self.assertEqual(len(py_files), 1)
        self.assertEqual(os.path.basename(py_files[0]), "test.py")
        
        # Tìm nhiều loại file
        files = ultis.find_files_by_extension(self.test_dir, ["py", "json"])
        self.assertEqual(len(files), 2)
        
        # Tìm file không tồn tại
        files = ultis.find_files_by_extension(self.test_dir, ["cpp"])
        self.assertEqual(len(files), 0)
    
    def test_sanitize_filename(self):
        """Kiểm tra hàm sanitize_filename"""
        # Test với tên file chứa ký tự không hợp lệ
        invalid_name = "file:with?invalid*chars.txt"
        valid_name = ultis.sanitize_filename(invalid_name)
        self.assertEqual(valid_name, "file_with_invalid_chars.txt")
        
        # Test với tên file quá dài
        long_name = "a" * 300 + ".txt"
        valid_name = ultis.sanitize_filename(long_name)
        self.assertLessEqual(len(valid_name), 255)
        
        # Test với tên file rỗng
        empty_name = ""
        valid_name = ultis.sanitize_filename(empty_name)
        self.assertEqual(valid_name, "untitled")


class TestUltisCodeAnalysis(unittest.TestCase):
    """Kiểm thử các chức năng phân tích code trong ultis.py"""
    
    def setUp(self):
        """Thiết lập môi trường test"""
        # Mẫu code để test
        self.sample_code = """
def factorial(n):
    \"\"\"Tính giai thừa của n.\"\"\"
    if n <= 1:
        return 1
    else:
        return n * factorial(n - 1)

# Hàm tính tổng
def sum_numbers(numbers):
    total = 0
    for num in numbers:
        total += num
    return total

# TODO: Cải thiện hiệu suất
"""
        
        self.complex_code = """
def nested_function(data):
    result = []
    for item in data:
        if item > 10:
            if item % 2 == 0:
                for i in range(item):
                    if i % 3 == 0:
                        if i > 5:
                            result.append(i)
    return result

def long_function():
    # Hàm này rất dài
    a = 1
    b = 2
    c = 3
    # ... nhiều dòng code ...
    # (giả lập 50+ dòng)
    for i in range(100):
        print(i)
    return a + b + c

x = 12345  # Magic number
"""
    
    def test_count_code_metrics(self):
        """Kiểm tra hàm count_code_metrics"""
        metrics = ultis.count_code_metrics(self.sample_code)
        
        # Kiểm tra các chỉ số cơ bản
        self.assertIn('total_lines', metrics)
        self.assertIn('code_lines', metrics)
        self.assertIn('comment_lines', metrics)
        self.assertIn('docstring_lines', metrics)
        
        # Kiểm tra các chỉ số mới
        self.assertIn('function_count', metrics)
        self.assertEqual(metrics['function_count'], 2)  # factorial và sum_numbers
        
        self.assertIn('todo_count', metrics)
        self.assertEqual(metrics['todo_count'], 1)  # 1 TODO
    
    def test_calculate_code_complexity(self):
        """Kiểm tra hàm calculate_code_complexity"""
        complexity = ultis.calculate_code_complexity(self.complex_code)
        
        # Kiểm tra các chỉ số phức tạp
        self.assertIn('cyclomatic_complexity', complexity)
        self.assertIn('nesting_depth', complexity)
        self.assertIn('complexity_score', complexity)
        
        # Kiểm tra giá trị
        self.assertGreater(complexity['nesting_depth'], 3)  # Độ sâu lồng nhau > 3
        self.assertGreater(complexity['cyclomatic_complexity'], 5)  # Độ phức tạp > 5
    
    def test_detect_code_smells(self):
        """Kiểm tra hàm detect_code_smells"""
        smells = ultis.detect_code_smells(self.complex_code)
        
        # Kiểm tra có phát hiện code smells
        self.assertIsInstance(smells, list)
        self.assertGreater(len(smells), 0)
        
        # Kiểm tra cấu trúc của code smell
        if smells:
            smell = smells[0]
            self.assertIn('type', smell)
            self.assertIn('line', smell)
            self.assertIn('message', smell)
            self.assertIn('severity', smell)
            
        # Kiểm tra phát hiện magic number
        has_magic_number = any(smell['type'] == 'magic_number' for smell in smells)
        self.assertTrue(has_magic_number)


class TestUltisSnapshot(unittest.TestCase):
    """Kiểm thử các chức năng snapshot trong ultis.py"""
    
    def setUp(self):
        """Thiết lập môi trường test"""
        # Tạo thư mục tạm thời cho test
        self.test_dir = tempfile.mkdtemp()
        self.test_file = os.path.join(self.test_dir, "test.py")
        
        # Nội dung file ban đầu
        self.initial_content = """
def hello():
    print("Hello, World!")
"""
        # Nội dung file sau khi thay đổi
        self.updated_content = """
def hello():
    print("Hello, World!")
    
def goodbye():
    print("Goodbye, World!")
"""
        
        # Tạo file test
        with open(self.test_file, "w", encoding="utf-8") as f:
            f.write(self.initial_content)
    
    def tearDown(self):
        """Dọn dẹp sau khi test"""
        # Xóa thư mục tạm thời
        shutil.rmtree(self.test_dir)
    
    def test_create_snapshot(self):
        """Kiểm tra hàm create_snapshot"""
        # Tạo snapshot
        snapshot = ultis.create_snapshot(self.test_file)
        
        # Kiểm tra cấu trúc snapshot
        self.assertIsInstance(snapshot, dict)
        self.assertIn('file_path', snapshot)
        self.assertIn('file_name', snapshot)
        self.assertIn('hash', snapshot)
        self.assertIn('content', snapshot)
        self.assertIn('metrics', snapshot)
        
        # Kiểm tra nội dung
        self.assertEqual(snapshot['content'], self.initial_content)
        self.assertEqual(snapshot['file_path'], self.test_file)
        self.assertEqual(snapshot['file_name'], os.path.basename(self.test_file))
    
    def test_compare_snapshots(self):
        """Kiểm tra hàm compare_snapshots"""
        # Tạo snapshot ban đầu
        initial_snapshot = ultis.create_snapshot(self.test_file)
        
        # Cập nhật file
        with open(self.test_file, "w", encoding="utf-8") as f:
            f.write(self.updated_content)
        
        # Tạo snapshot mới
        updated_snapshot = ultis.create_snapshot(self.test_file)
        
        # So sánh snapshots
        comparison = ultis.compare_snapshots(initial_snapshot, updated_snapshot)
        
        # Kiểm tra cấu trúc so sánh
        self.assertIsInstance(comparison, dict)
        self.assertIn('file_path', comparison)
        self.assertIn('is_significant', comparison)
        self.assertIn('diff', comparison)
        
        # Kiểm tra kết quả
        self.assertTrue(comparison['is_significant'])  # Thay đổi đáng kể
        self.assertIn('goodbye', comparison['diff'])  # Diff chứa hàm mới


class TestAIHelperCache(unittest.TestCase):
    """Kiểm thử cơ chế cache trong ai_helper.py"""
    
    def setUp(self):
        """Thiết lập môi trường test"""
        # Xóa cache hiện tại
        ai_helper.clear_cache()
        
        # Lưu trạng thái cache_enabled
        self.original_cache_enabled = ai_helper.config.cache_enabled
        
        # Bật cache
        ai_helper.config.cache_enabled = True
    
    def tearDown(self):
        """Dọn dẹp sau khi test"""
        # Khôi phục trạng thái cache_enabled
        ai_helper.config.cache_enabled = self.original_cache_enabled
        
        # Xóa cache
        ai_helper.clear_cache()
    
    def test_cache_operations(self):
        """Kiểm tra các hàm xử lý cache"""
        # Test tạo cache key
        prompt = "Test prompt"
        model = "test-model"
        temperature = 0.7
        
        key = ai_helper.get_cache_key(prompt, model, temperature)
        self.assertIsInstance(key, str)
        self.assertTrue(len(key) > 0)
        
        # Test lưu và lấy từ cache
        response = "Test response"
        ai_helper.cache_response(key, response)
        
        cached = ai_helper.get_cached_response(key)
        self.assertEqual(cached, response)
        
        # Test xóa cache
        ai_helper.clear_cache()
        cached = ai_helper.get_cached_response(key)
        self.assertIsNone(cached)
    
    def test_cache_expiration(self):
        """Kiểm tra hết hạn cache"""
        # Đặt thời gian sống cache ngắn
        original_ttl = ai_helper.config.cache_ttl
        ai_helper.config.cache_ttl = 0  # Hết hạn ngay lập tức
        
        # Tạo và lưu cache
        key = ai_helper.get_cache_key("test", "model", 0.5)
        ai_helper.cache_response(key, "response")
        
        # Kiểm tra cache đã hết hạn
        cached = ai_helper.get_cached_response(key)
        self.assertIsNone(cached)
        
        # Khôi phục thời gian sống cache
        ai_helper.config.cache_ttl = original_ttl


class TestAIHelperUtilities(unittest.TestCase):
    """Kiểm thử các tiện ích trong ai_helper.py"""
    
    def test_estimate_token_count(self):
        """Kiểm tra hàm estimate_token_count"""
        # Test với chuỗi ngắn
        short_text = "Hello, world!"
        count = ai_helper.estimate_token_count(short_text)
        self.assertIsInstance(count, int)
        self.assertGreater(count, 0)
        
        # Test với chuỗi dài
        long_text = "A" * 1000
        count = ai_helper.estimate_token_count(long_text)
        self.assertGreater(count, 200)  # Ước tính > 200 token
        
        # Test với chuỗi rỗng
        empty_text = ""
        count = ai_helper.estimate_token_count(empty_text)
        self.assertEqual(count, 0)


def run_tests():
    """Chạy tất cả các test"""
    # Tạo test suite
    test_suite = unittest.TestSuite()
    
    # Thêm các test case
    test_suite.addTest(unittest.defaultTestLoader.loadTestsFromTestCase(TestUltisFileOperations))
    test_suite.addTest(unittest.defaultTestLoader.loadTestsFromTestCase(TestUltisCodeAnalysis))
    test_suite.addTest(unittest.defaultTestLoader.loadTestsFromTestCase(TestUltisSnapshot))
    test_suite.addTest(unittest.defaultTestLoader.loadTestsFromTestCase(TestAIHelperCache))
    test_suite.addTest(unittest.defaultTestLoader.loadTestsFromTestCase(TestAIHelperUtilities))
    
    # Chạy test
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(test_suite)
    
    return result


if __name__ == "__main__":
    print("Kiểm thử các chức năng helper trong WindSurf Memory Tracker")
    print("=" * 70)
    
    result = run_tests()
    
    # Hiển thị kết quả tổng hợp
    print("\nKết quả kiểm thử:")
    print(f"Tổng số test: {result.testsRun}")
    print(f"Thành công: {result.testsRun - len(result.failures) - len(result.errors)}")
    print(f"Thất bại: {len(result.failures)}")
    print(f"Lỗi: {len(result.errors)}")
    
    # Thoát với mã lỗi phù hợp
    sys.exit(len(result.failures) + len(result.errors))
