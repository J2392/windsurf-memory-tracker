#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
HTML Diff Generator
------------------
Module để tạo HTML diff từ văn bản diff thông thường.
Được sử dụng để hiển thị diff trong trình duyệt web.
"""

import os
import sys
from typing import List, Dict, Any, Optional


def generate_html_diff(diff_text: str) -> str:
    """Tạo HTML diff để hiển thị trong trình duyệt.
    
    Args:
        diff_text (str): Văn bản diff cần chuyển thành HTML
        
    Returns:
        str: HTML diff để hiển thị trong trình duyệt
    """
    lines = diff_text.split('\n')
    html_lines = ['<pre class="diff">']  # Thêm class để dễ dàng CSS
    
    for line in lines:
        if line.startswith('+'):
            # Dòng thêm vào
            html_lines.append(f'<span class="added">{html_escape(line)}</span>')
        elif line.startswith('-'):
            # Dòng bị xóa
            html_lines.append(f'<span class="removed">{html_escape(line)}</span>')
        elif line.startswith('@'):
            # Thông tin dòng
            html_lines.append(f'<span class="info">{html_escape(line)}</span>')
        else:
            # Dòng bình thường
            html_lines.append(html_escape(line))
    
    html_lines.append('</pre>')
    
    # Thêm CSS để định dạng
    css = '''
    <style>
    .diff {
        font-family: monospace;
        white-space: pre;
        margin: 0;
        padding: 10px;
        background-color: #f8f8f8;
        border: 1px solid #ddd;
        border-radius: 3px;
    }
    .added {
        background-color: #e6ffed;
        color: #22863a;
        display: block;
    }
    .removed {
        background-color: #ffeef0;
        color: #cb2431;
        display: block;
    }
    .info {
        color: #6f42c1;
        display: block;
    }
    </style>
    '''
    
    return css + '\n'.join(html_lines)


def html_escape(text: str) -> str:
    """Escape các ký tự đặc biệt trong HTML.
    
    Args:
        text (str): Văn bản cần escape
        
    Returns:
        str: Văn bản đã được escape
    """
    return text.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;').replace('"', '&quot;').replace("'", '&#39;')


def save_html_diff(diff_text: str, output_file: str) -> bool:
    """Lưu HTML diff vào file.
    
    Args:
        diff_text (str): Văn bản diff cần chuyển thành HTML
        output_file (str): Đường dẫn đến file output
        
    Returns:
        bool: True nếu lưu thành công, False nếu thất bại
    """
    try:
        html_content = generate_html_diff(diff_text)
        
        # Thêm HTML header và footer
        full_html = f'''<!DOCTYPE html>
<html lang="vi">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Diff Viewer</title>
</head>
<body>
    <h1>Diff Viewer</h1>
    {html_content}
</body>
</html>'''
        
        # Lưu vào file
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(full_html)
        
        return True
    except Exception as e:
        print(f"Lỗi khi lưu HTML diff: {str(e)}", file=sys.stderr)
        return False


def main():
    """Hàm main để chạy từ command line."""
    if len(sys.argv) < 2:
        print("Sử dụng: python html_diff_generator.py <diff_file> [output_file]")
        sys.exit(1)
    
    diff_file = sys.argv[1]
    output_file = sys.argv[2] if len(sys.argv) > 2 else "diff_output.html"
    
    try:
        with open(diff_file, 'r', encoding='utf-8') as f:
            diff_text = f.read()
        
        success = save_html_diff(diff_text, output_file)
        if success:
            print(f"HTML diff đã được lưu vào {output_file}")
        else:
            print("Không thể lưu HTML diff")
            sys.exit(1)
    except Exception as e:
        print(f"Lỗi: {str(e)}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
