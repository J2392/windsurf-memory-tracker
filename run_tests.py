#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Script chạy tất cả các test cho WindSurf Memory Tracker

Chạy với lệnh: python run_tests.py
"""

import unittest
import sys
import os
import time
import colorama
from colorama import Fore, Style
from PyQt6.QtWidgets import QApplication

# Import các test case
from test_models import TestProject, TestUser, TestTask, TestFile, TestSnapshot, TestActivity
from test_drag_drop import TestDragDrop
from test_ai_helper import TestAIConfig, TestRetryDecorator, TestValidatePrompt, TestCallLocalModel, TestAIHelper

def run_all_tests():
    """Chạy tất cả các test case"""
    # Khởi tạo màu sắc cho terminal
    colorama.init()
    
    # Khởi tạo ứng dụng Qt
    app = QApplication.instance() or QApplication(sys.argv)
    
    # Tạo test suite
    test_suite = unittest.TestSuite()
    
    # Thêm các test case vào suite
    print(f"{Fore.CYAN}\n=== Thêm các test case vào test suite ==={Style.RESET_ALL}")
    
    # Test cho models.py
    print(f"{Fore.YELLOW}\n>> Thêm test cho models.py{Style.RESET_ALL}")
    test_suite.addTest(unittest.makeSuite(TestProject))
    test_suite.addTest(unittest.makeSuite(TestUser))
    test_suite.addTest(unittest.makeSuite(TestTask))
    test_suite.addTest(unittest.makeSuite(TestFile))
    test_suite.addTest(unittest.makeSuite(TestSnapshot))
    test_suite.addTest(unittest.makeSuite(TestActivity))
    
    # Test cho drag_drop
    print(f"{Fore.YELLOW}\n>> Thêm test cho drag_drop.py{Style.RESET_ALL}")
    test_suite.addTest(unittest.makeSuite(TestDragDrop))
    
    # Test cho ai_helper.py
    print(f"{Fore.YELLOW}\n>> Thêm test cho ai_helper.py{Style.RESET_ALL}")
    test_suite.addTest(unittest.makeSuite(TestAIConfig))
    test_suite.addTest(unittest.makeSuite(TestRetryDecorator))
    test_suite.addTest(unittest.makeSuite(TestValidatePrompt))
    test_suite.addTest(unittest.makeSuite(TestCallLocalModel))
    test_suite.addTest(unittest.makeSuite(TestAIHelper))
    
    # Chạy test và trả về kết quả
    print(f"{Fore.CYAN}\n=== Bắt đầu chạy các test ==={Style.RESET_ALL}")
    start_time = time.time()
    test_runner = unittest.TextTestRunner(verbosity=2)
    result = test_runner.run(test_suite)
    end_time = time.time()
    
    return result, end_time - start_time

if __name__ == "__main__":
    print(f"{Fore.GREEN}=== Bắt đầu chạy kiểm thử WindSurf Memory Tracker ==={Style.RESET_ALL}")
    result, duration = run_all_tests()
    
    # Hiển thị kết quả
    print(f"{Fore.GREEN}\n=== Kết quả kiểm thử ==={Style.RESET_ALL}")
    success_count = result.testsRun - len(result.errors) - len(result.failures)
    success_rate = (success_count / result.testsRun) * 100 if result.testsRun > 0 else 0
    
    print(f"Tổng số test: {Fore.CYAN}{result.testsRun}{Style.RESET_ALL}")
    print(f"Thành công: {Fore.GREEN}{success_count}{Style.RESET_ALL} ({success_rate:.1f}%)")
    print(f"Thất bại: {Fore.RED}{len(result.failures)}{Style.RESET_ALL}")
    print(f"Lỗi: {Fore.RED}{len(result.errors)}{Style.RESET_ALL}")
    print(f"Thời gian chạy: {Fore.YELLOW}{duration:.2f}{Style.RESET_ALL} giây")
    
    # Hiển thị kết luận
    if len(result.failures) == 0 and len(result.errors) == 0:
        print(f"\n{Fore.GREEN}\u2714 Tất cả các test đều thành công!{Style.RESET_ALL}")
    else:
        print(f"\n{Fore.RED}\u2718 Có test thất bại hoặc lỗi!{Style.RESET_ALL}")
    
    # Thoát với mã lỗi phù hợp
    sys.exit(len(result.failures) + len(result.errors))
