# KV Resizer Lite

精简版 - 只保留核心出图功能

## 功能
- 上传 KV 图片
- 选择尺寸比例（16:9, 9:16, 4:3, 3:4, 1:1）
- 选择背景颜色
- 选择长边尺寸（1080px - 4K）
- AI 生成适配图片
- 下载生成结果

## 启动方式

### Mac
双击 `启动.command`

### 手动启动
```bash
cd ~/Desktop/KV-Resizer-Lite
python3 app.py
```

## 访问
启动后打开浏览器访问: http://127.0.0.1:5035

## 文件说明
- `app.py` - 后端服务
- `index.html` - 前端页面
- `uploads/` - 上传文件目录
- `results/` - 生成结果目录
