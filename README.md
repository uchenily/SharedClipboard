# SyncClipboardWebHistory

[SyncClipboard](https://github.com/Jeric-X/SyncClipboard) 的在线剪贴板历史记录管理系统

## 🌟 主要功能

- **📋 剪贴板历史记录** - 浏览和管理所有剪贴板内容
- **🖼️ 图片直接复制** - 支持将图片直接复制到系统剪贴板
- **📝 文本快速粘贴** - 使用 Ctrl+V 直接粘贴文本到历史记录
- **🖼️ 图片快速粘贴** - 使用 Ctrl+V 直接粘贴图片到历史记录
- **🔍 内容预览** - 支持文本预览、图片缩略图和文件信息
- **⭐ 收藏功能** - 标记重要的剪贴板内容
- **📄 分页浏览** - 高效浏览大量历史记录
- **🔍 类型筛选** - 按文本、图片、文件类型筛选
- **💾 文件下载** - 支持图片和文件的下载功能

## 🚀 新增功能 (v2.0)

### 剪贴板粘贴功能
- **快捷键粘贴**: 使用 `Ctrl+V` 直接粘贴文本或图片到历史记录
- **智能识别**: 自动识别粘贴内容类型（文本/图片）
- **实时更新**: 粘贴成功后自动刷新历史记录，新内容显示在顶部
- **状态反馈**: 提供粘贴处理中的视觉反馈和结果通知

### 图片剪贴板功能
- **一键复制**: 点击"复制图片"按钮直接复制到系统剪贴板
- **快捷操作**: `Ctrl+点击图片` 快速复制图片
- **模态框复制**: 图片预览窗口中也支持复制功能
- **浏览器兼容**: 自动检测浏览器支持，不支持的浏览器提示使用下载

### 技术实现
- **Clipboard API**: 使用现代浏览器的 `navigator.clipboard.write()` 和 `ClipboardItem` 对象
- **文件处理**: 支持图片文件的MD5校验和备份管理
- **异步操作**: 使用 async/await 处理文件复制和粘贴操作
- **错误处理**: 完善的错误捕获和用户友好的错误提示

## 📖 使用指南

### 粘贴内容
1. **文本粘贴**: 复制文本后，在页面按 `Ctrl+V`
2. **图片粘贴**: 复制图片后，在页面按 `Ctrl+V`
3. **自动识别**: 系统会自动识别内容类型并添加到历史记录

### 复制图片
1. **按钮复制**: 点击图片记录的"复制图片"按钮
2. **快捷复制**: 按住 `Ctrl/Cmd` 键点击图片
3. **预览复制**: 在图片预览窗口中点击"复制图片"按钮

### 浏览器兼容性
- ✅ Chrome 66+
- ✅ Firefox 63+
- ✅ Safari 13.1+
- ✅ Edge 79+
- ⚠️ 旧版本浏览器不支持图片剪贴板功能，会提示使用下载

# 警告

基本上只有最基础的功能，通过浏览器展示历史记录，无法进行收藏等一系列操作

# 效果
![alt text](Learn/Texture/Sample.png)


# 运行
1. SyncClipboard 使用 webdav 同步，将仓库放在 `SyncClipboard.json` 文件相同目录
2. 推荐：打开“自动删除服务器上的临时文件”![alt text](ar51i3aq.at0.png)
3. 安装依赖：
```bash
pip install -r requirements.txt
```
4. 运行脚本
```bash
python3 start.py
```
## 配置文件
[配置文件](config.py)：
```python
class Config:
    # 基本路径配置
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))
    
    # JSON 文件路径
    SYNC_CLIPBOARD_JSON_FILE = "SyncClipboard.json" # 同步文件名
    SYNC_CLIPBOARD_JSON_PATH = os.path.join(BASE_DIR, SYNC_CLIPBOARD_JSON_FILE) # 主同步文件路径
    

    # 数据库配置
    DB_PATH = os.path.join(BASE_DIR, "db", "clipboard_history.db")
    DB_LOG_ENABLED = True  # 是否启用数据库日志

    # 备份配置
    BACKUP_DIR_FOLDER = "backup"  # 当前文件夹下，备份文件夹名称

    BACKUP_DIR = os.path.join(BASE_DIR, BACKUP_DIR_FOLDER)
    
    # 网页配置
    TEMPLATES_DIR = os.path.join(BASE_DIR, "templates")
    STATIC_DIR = os.path.join(BASE_DIR, "static")
    
    # 历史文件删除配置
    MAX_FOLDER_SIZE = "1G"  # 支持格式: "100MB", "2GB", "512KB", "1024B"
    CHECK_INTERVAL = 60  # 检查间隔（秒）
    FOLDER_TO_MONITOR = os.path.join(BASE_DIR, BACKUP_DIR_FOLDER)  # 替换为要监控的文件夹路径，一般和备份文件夹相同
```


# todo

## web
- [x] 历史记录页面
- [x] 剪贴板粘贴功能 (Ctrl+V)
- [x] 图片剪贴板复制功能
- [ ] 收藏页面
  - [ ] 分组收藏
- [ ] 在线修改设施

## 数据监控
- [x] 监控 `SyncClipboard.json` 文件
- [x] 控制备份文件大小
- [ ] 使用硬链接备份文件

## webdav
- [ ] 添加 webdav 功能，直接启动服务端

## docker
- [ ] 打包 docker

## 🛠️ API 接口

### 剪贴板粘贴接口
- `POST /api/paste/text` - 粘贴文本到历史记录
  ```json
  {
    "content": "文本内容",
    "type": "Text"
  }
  ```
- `POST /api/paste/image` - 粘贴图片到历史记录
  ```form
  file: 图片文件
  type: "Image"
  ```

### 历史记录接口
- `GET /api/history?limit=30&offset=0` - 获取分页历史记录
- `GET /api/download?checksum=xxx` - 下载文件

### 响应格式
```json
{
  "success": true,
  "data": {
    "records": [...],
    "total": 100,
    "limit": 30,
    "offset": 0
  }
}
```

# 开发
## 文件结构

```
.
├── backup/             # 备份文件位置
├── clipboard_history_OneFile.py  # 单文件版本，运行后会生成html页面
├── config.py           # 配置文件   
├── database.py         # 数据库相关函数
├── db
│   └── clipboard_history.db  # 历史数据库
├── file                # 备份文件存储目录
├── history_service.py  # 剪贴板监控部分
├── requirements.txt    # 依赖库
├── start.py            # 启动文件
├── SyncClipboard.json  # SyncClipboard 剪贴板同步文件
├── templates           # web 模板
│   ├── base.html
│   ├── favorites.html
│   ├── index.html
│   └── settings.html
└── web_server.py       # web 服务器
```


## 数据库：
![alt text](Learn/Texture/Main_DB.png)

## 🎯 技术栈

- **后端**: Flask + SQLModel + SQLite
- **前端**: HTML5 + JavaScript + Tailwind CSS
- **数据库**: SQLite (轻量级，适合个人使用)
- **文件处理**: Python hashlib + shutil
- **实时通信**: Flask-SocketIO (用于历史记录更新通知)
- **文件监控**: Python watchdog (监控 SyncClipboard.json 变化)

## 🔧 开发环境

### 依赖安装
```bash
pip install -r requirements.txt
```

### 主要依赖
- `flask` - Web框架
- `sqlmodel` - ORM数据库操作
- `flask-socketio` - 实时通信
- `watchdog` - 文件监控
- `eventlet` - 异步支持

### 启动服务
```bash
python3 start.py
```
服务将在 `http://localhost:5000` 启动

## 📁 项目结构

```
.
├── backup/                    # 备份文件位置
├── clipboard_history_OneFile.py  # 单文件版本，运行后会生成html页面
├── config.py                  # 配置文件   
├── database.py                # 数据库相关函数
├── db/
│   └── clipboard_history.db   # 历史数据库
├── file/                      # SyncClipboard文件存储目录
├── history_service.py         # 剪贴板监控部分
├── requirements.txt           # 依赖库
├── start.py                   # 启动文件
├── SyncClipboard.json         # SyncClipboard 剪贴板同步文件
├── templates/                 # web 模板
│   ├── base.html              # 基础模板
│   ├── favorites.html         # 收藏页面
│   ├── index.html             # 主页面(包含粘贴功能)
│   └── settings.html          # 设置页面
├── static/                    # 静态资源
│   └── js/
│       └── main.js           # 前端JavaScript
└── web_server.py              # web 服务器(包含粘贴API)
```

## 🔄 工作流程

1. **SyncClipboard** 生成 `SyncClipboard.json` 文件
2. **history_service.py** 监控文件变化，自动更新数据库
3. **web_server.py** 提供Web界面和API接口
4. **前端页面** 支持Ctrl+V粘贴和图片复制功能
5. **数据库** 存储历史记录和文件备份信息

## 🐛 故障排除

### 粘贴功能不工作
- 检查浏览器是否支持Clipboard API
- 确保页面有焦点（点击页面任意位置）
- 检查控制台是否有JavaScript错误

### 图片复制失败
- 确保使用支持的浏览器版本
- 检查图片文件是否损坏
- 尝试使用下载功能作为替代方案

### 历史记录不更新
- 检查 `SyncClipboard.json` 文件是否存在
- 确认 `history_service.py` 正在运行
- 查看服务器日志获取错误信息
