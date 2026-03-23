#!/usr/bin/env python3
"""
KV Resizer Lite - 精简版
只保留核心出图功能
"""

from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
import os
import requests
import base64
import io
import urllib3
from PIL import Image

# 禁用 SSL 警告
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

app = Flask(__name__)
CORS(app)

# ========== 配置区域 ==========

API_CONFIG = {
    'base_url': 'https://ai.comfly.chat',
    'api_key': 'sk-xZ3fOyvenn3M3OXL39Fao3jmLTWrlCt5502jGVt1IHxfl9jE',
}

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# ========== 前端页面 ==========

@app.route('/')
def index():
    return send_from_directory('.', 'index.html')

@app.route('/api/generate', methods=['POST'])
def generate():
    """生成适配图片"""
    try:
        data = request.get_json()
        print(f'收到请求数据: {data}')
        
        kv_b64 = data.get('kv', '')
        width = data.get('width', 1920)
        height = data.get('height', 1080)
        color = data.get('color', '#ff0000')
        
        print(f'解析参数: size={width}x{height}')
        
        if not kv_b64:
            return jsonify({'error': '请上传KV图'}), 400
        
        # 步骤1：系统生成纯色背景（图1）
        print('步骤1: 系统生成纯色背景...')
        canvas_b64 = generate_solid_background(width, height, color)
        
        # 步骤2：调用 gemini-3.1-flash-image-preview-2k 生成
        print(f'步骤2: gemini-3.1-flash-image-preview-2k 生成...')
        result = call_gemini_flash(canvas_b64, kv_b64, width, height, color)
        
        if result:
            return jsonify({
                'success': True,
                'image': result
            })
        else:
            return jsonify({'error': '生成失败'}), 500
            
    except Exception as e:
        print(f'生成错误: {str(e)}')
        import traceback
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500


def generate_solid_background(width, height, color):
    """系统生成纯色背景图 - 无文字"""
    try:
        img = Image.new('RGB', (width, height), color)
        
        buffer = io.BytesIO()
        img.save(buffer, format='PNG')
        buffer.seek(0)
        
        return f'data:image/png;base64,{base64.b64encode(buffer.read()).decode()}'
        
    except Exception as e:
        print(f'生成背景失败: {e}')
        img = Image.new('RGB', (width, height), color)
        buffer = io.BytesIO()
        img.save(buffer, format='PNG')
        buffer.seek(0)
        return f'data:image/png;base64,{base64.b64encode(buffer.read()).decode()}'


def call_gemini_flash(canvas_b64, kv_b64, width, height, color):
    """调用 gemini-3.1-flash-image-preview-2k /v1/images/edits - 图生图"""
    
    headers = {
        'Authorization': f'Bearer {API_CONFIG["api_key"]}',
    }
    
    # 提取 base64 数据
    canvas_data = canvas_b64.split(',')[1] if ',' in canvas_b64 else canvas_b64
    kv_data = kv_b64.split(',')[1] if ',' in kv_b64 else kv_b64
    
    # 转换为文件对象
    canvas_file = io.BytesIO(base64.b64decode(canvas_data))
    canvas_file.name = 'canvas.png'
    
    kv_file = io.BytesIO(base64.b64decode(kv_data))
    kv_file.name = 'kv.png'
    
    # 提示词 - 让 AI 自动识别画布尺寸并填满
    prompt = f"""将图2的内容适配到图1的画布上，填满整个画布。

参考图说明：
- 图1：目标画布（{width}x{height} 像素）
- 图2：原始KV设计图

任务要求：
1. 读取图1的画布尺寸作为输出尺寸
2. 将图2的内容智能适配到图1的画布上
3. 填满整个画布，不要留黑边
4. 保持图2的画面元素和风格"""

    try:
        print(f'调用 gemini-3.1-flash-image-preview-2k...')
        print(f'画布尺寸: {width}x{height}')
        
        # multipart/form-data 格式
        files = [
            ('image', ('canvas.png', canvas_file, 'image/png')),
            ('image', ('kv.png', kv_file, 'image/png')),
        ]
        
        data = {
            'model': 'gemini-3.1-flash-image-preview-2k',
            'prompt': prompt,
            'response_format': 'url',
            'size': f'{width}x{height}',
        }
        
        print(f'请求参数: model=gemini-3.1-flash-image-preview-2k, prompt=...')
        
        # 创建会话并禁用 SSL 验证和代理
        session = requests.Session()
        session.trust_env = False  # 禁用环境变量代理
        session.verify = False
        
        # 彻底禁用所有代理
        session.proxies = {
            'http': None,
            'https': None
        }
        
        res = session.post(
            f'{API_CONFIG["base_url"]}/v1/images/edits',
            headers=headers,
            files=files,
            data=data,
            timeout=300
        )
        
        print(f'API 状态: {res.status_code}')
        
        if res.status_code != 200:
            print(f'API 错误: {res.text}')
            raise RuntimeError(f'Gemini API 请求失败（HTTP {res.status_code}）：{res.text[:500]}')
        
        response_data = res.json()
        
        # 获取图片 URL（兼容 data 为 list/dict 两种常见结构）
        payload_data = response_data.get('data')
        item = {}
        if isinstance(payload_data, list):
            item = payload_data[0] if payload_data else {}
        elif isinstance(payload_data, dict):
            item = payload_data

        image_url = item.get('url')
        b64_data = item.get('b64_json')

        if not image_url and b64_data:
            print('找到 b64_json')
            return f'data:image/png;base64,{b64_data}'

        if not image_url:
            raise RuntimeError(f'未找到图片url/b64_json，响应预览：{str(response_data)[:1000]}')
        
        print(f'图片 URL: {image_url[:80]}...')
        
        # 下载图片（禁用 SSL 验证）
        img_res = session.get(image_url, timeout=30)
        
        if img_res.status_code != 200:
            raise RuntimeError(f'下载图片失败（HTTP {img_res.status_code}）')
        
        print(f'下载成功: {len(img_res.content)} bytes')
        
        return f'data:image/png;base64,{base64.b64encode(img_res.content).decode()}'
        
    except Exception as e:
        print(f'调用错误: {e}')
        import traceback
        traceback.print_exc()
        raise


if __name__ == '__main__':
    print('=' * 50)
    print('KV Resizer Lite')
    print('=' * 50)
    print('精简版 - 只保留核心出图功能')
    print('=' * 50)
    
    app.run(host='0.0.0.0', port=5040, debug=True, use_reloader=False)
