#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Test kết nối với mô hình Qwen2.5-coder-3b-instruct
"""

import requests
import json
import time

def test_llm_connection(
    prompt="Xin chào, bạn là ai?", 
    endpoint="http://localhost:1234/v1/chat/completions", 
    model="qwen2.5-coder-3b-instruct"
):
    """
    Kiểm tra kết nối với mô hình LLM
    
    Args:
        prompt: Câu hỏi để gửi đến mô hình
        endpoint: Địa chỉ API endpoint
        model: Tên mô hình
        
    Returns:
        dict: Kết quả từ API hoặc thông báo lỗi
    """
    print(f"Đang kiểm tra kết nối đến {endpoint} với mô hình {model}...")
    
    payload = {
        "model": model,
        "messages": [{"role": "user", "content": prompt}],
        "stream": False,
        "temperature": 0.7,
        "max_tokens": 500
    }
    
    try:
        start_time = time.time()
        response = requests.post(endpoint, json=payload, timeout=60)
        end_time = time.time()
        
        print(f"Thời gian phản hồi: {end_time - start_time:.2f} giây")
        
        if response.status_code == 200:
            result = response.json()
            content = result["choices"][0]["message"]["content"]
            print("\n--- KẾT QUẢ THÀNH CÔNG ---")
            print(f"Status code: {response.status_code}")
            print(f"Response: {json.dumps(result, indent=2, ensure_ascii=False)[:500]}...")
            print("\n--- NỘI DUNG PHẢN HỒI ---")
            print(content)
            return {
                "success": True,
                "response": result,
                "content": content,
                "response_time": end_time - start_time
            }
        else:
            print("\n--- LỖI ---")
            print(f"Status code: {response.status_code}")
            print(f"Response: {response.text}")
            return {
                "success": False,
                "status_code": response.status_code,
                "error": response.text,
                "response_time": end_time - start_time
            }
    except requests.exceptions.ConnectionError:
        print("\n--- LỖI KẾT NỐI ---")
        print(f"Không thể kết nối đến {endpoint}")
        print("Vui lòng kiểm tra xem LMStudio/Ollama có đang chạy không và mô hình đã được tải chưa.")
        return {
            "success": False,
            "error": "Connection Error"
        }
    except requests.exceptions.Timeout:
        print("\n--- LỖI TIMEOUT ---")
        print("Yêu cầu bị timeout. Mô hình có thể đang xử lý quá lâu hoặc gặp vấn đề.")
        return {
            "success": False,
            "error": "Timeout"
        }
    except Exception as e:
        print("\n--- LỖI KHÔNG XÁC ĐỊNH ---")
        print(f"Lỗi: {str(e)}")
        return {
            "success": False,
            "error": str(e)
        }

def test_code_analysis():
    """Kiểm tra chức năng phân tích mã nguồn"""
    code_sample = """
def fibonacci(n):
    if n <= 0:
        return 0
    elif n == 1:
        return 1
    else:
        return fibonacci(n-1) + fibonacci(n-2)
    """
    
    prompt = f"Phân tích đoạn mã sau và đề xuất cách tối ưu hóa:\n```python\n{code_sample}\n```"
    return test_llm_connection(prompt=prompt)

if __name__ == "__main__":
    print("=== KIỂM TRA KẾT NỐI CƠ BẢN ===")
    basic_test = test_llm_connection()
    
    if basic_test["success"]:
        print("\n\n=== KIỂM TRA PHÂN TÍCH MÃ NGUỒN ===")
        code_test = test_code_analysis()
