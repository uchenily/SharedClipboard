import eventlet
# eventlet.monkey_patch()
import json
from flask import request, jsonify, send_file, Blueprint, render_template
from config import config
from app.db.database import ServerGet, ServerSet, add_history_item_from_json, init_db
from app.models.models import BackupFile, ClipboardHistory, Folder, Favorite
from sqlmodel import Session, select
import os
import uuid as uuid_lib
import hashlib

api = Blueprint('api', __name__)

# 创建 ServerGet 实例
history_db = ServerGet()

# 主页 UI 路由
@api.route('/')
def index():
    return render_template('index.html', active_page='history')

@api.route('/favorites')
def favorites():
    """展示收藏页面"""
    # 暂时只渲染模板，数据可能通过API加载
    return render_template('favorites.html', active_page='favorites')

@api.route('/settings')
def settings():
    return render_template('settings.html')

@api.route('/collections')
def collections():
    # 需要实现获取收藏夹逻辑
    return render_template('collections.html')

# 主页列表专用分页API
@api.route('/api/history')
def api_history_paginated():
    try:
        # 解析分页参数
        limit = int(request.args.get('limit', 30))
        offset = int(request.args.get('offset', 0))
        # 限制参数范围
        limit = max(1, min(limit, 100))
        offset = max(0, offset)

        # 使用实例调用方法
        result = history_db.get_history_paginated(limit=limit, offset=offset)

        print("::DEBUG::", "API /api/history called with limit:", limit, "offset:", offset)

        return jsonify({'success': True, 'data': result})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

# 添加下载文件的API
@api.route('/api/download')
def download_file():
    checksum = request.args.get('checksum')
    if not checksum:
        return "缺少参数", 400

    # 调用数据库层获取文件路径，不直接操作数据库
    file_path = history_db.get_file_path_by_checksum(checksum)

    if not file_path:
        return "文件不存在或已丢失", 404

    # 发送文件
    return send_file(file_path, as_attachment=True)

# 粘贴文本API
@api.route('/api/paste/text', methods=['POST'])
def paste_text():
    try:
        data = request.get_json()
        if not data or 'content' not in data:
            return jsonify({'success': False, 'error': '缺少内容参数'}), 400

        content = data['content']
        if not content.strip():
            return jsonify({'success': False, 'error': '内容不能为空'}), 400

        # 构造JSON数据格式
        json_data = {
            "Type": "Text",
            "Clipboard": content,
            "From": "Web",
            "Tag": "手动粘贴"
        }

        # 添加到数据库
        engine = init_db()
        new_id = add_history_item_from_json(json_data, engine)

        if new_id:
            return jsonify({'success': True, 'id': new_id})
        else:
            return jsonify({'success': False, 'error': '添加失败'}), 500

    except Exception as e:
        print(f"文本粘贴错误: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

# 粘贴图片API
@api.route('/api/paste/image', methods=['POST'])
def paste_image():
    try:
        if 'file' not in request.files:
            return jsonify({'success': False, 'error': '没有文件'}), 400

        file = request.files['file']
        if file.filename == '':
            return jsonify({'success': False, 'error': '文件名为空'}), 400

        # 读取文件内容并计算MD5
        file_bytes = file.read()
        checksum = hashlib.md5(file_bytes).hexdigest()

        # 生成唯一文件名
        file_ext = os.path.splitext(file.filename)[1] if file.filename else '.png'
        unique_filename = f"{uuid_lib.uuid4()}{file_ext}"
        backup_path = os.path.join(config.BACKUP_DIR, unique_filename)

        # 确保备份目录存在
        os.makedirs(config.BACKUP_DIR, exist_ok=True)

        # 保存文件
        with open(backup_path, 'wb') as f:
            f.write(file_bytes)

        # 构造JSON数据格式
        json_data = {
            "Type": "Image",
            "Clipboard": checksum,
            "File": unique_filename,
            "From": "Web",
            "Tag": "手动粘贴"
        }

        # 添加到数据库
        engine = init_db()

        # 检查备份文件是否已存在
        with Session(engine) as session:
            exists = session.exec(select(BackupFile).where(BackupFile.checksum == checksum)).first()
            if not exists:
                backup = BackupFile(
                    checksum=checksum,
                    filepath=backup_path,
                    size=len(file_bytes)
                )
                session.add(backup)
                session.commit()

        # 直接创建数据库记录，以便设置原始文件名
        with Session(engine) as session:
            history_item = ClipboardHistory(
                raw_content=json.dumps(json_data),
                type="Image",
                clipboard=checksum,  # 对于图片，clipboard字段存储checksum
                from_equipment="Web",
                tag="手动粘贴",
                checksum=checksum,
                original_filename=file.filename  # 存储原始文件名
            )
            session.add(history_item)
            session.commit()
            new_id = history_item.id

        if new_id:
            return jsonify({'success': True, 'id': new_id})
        else:
            return jsonify({'success': False, 'error': '添加失败'}), 500

    except Exception as e:
        print(f"图片粘贴错误: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

# 粘贴文件API
@api.route('/api/paste/file', methods=['POST'])
def paste_file():
    try:
        if 'file' not in request.files:
            return jsonify({'success': False, 'error': '没有文件'}), 400

        file = request.files['file']
        if file.filename == '':
            return jsonify({'success': False, 'error': '文件名为空'}), 400

        # 读取文件内容并计算MD5
        file_bytes = file.read()
        checksum = hashlib.md5(file_bytes).hexdigest()

        # 生成唯一文件名
        file_ext = os.path.splitext(file.filename)[1] if file.filename else ''
        unique_filename = f"{uuid_lib.uuid4()}{file_ext}"
        backup_path = os.path.join(config.BACKUP_DIR, unique_filename)

        # 确保备份目录存在
        os.makedirs(config.BACKUP_DIR, exist_ok=True)

        # 保存文件
        with open(backup_path, 'wb') as f:
            f.write(file_bytes)

        # 构造JSON数据格式
        json_data = {
            "Type": "File",
            "Clipboard": file.filename,  # 对于文件，Clipboard字段存储原始文件名
            "File": unique_filename,
            "From": "Web",
            "Tag": "手动粘贴"
        }

        # 添加到数据库
        engine = init_db()

        # 检查备份文件是否已存在
        with Session(engine) as session:
            exists = session.exec(select(BackupFile).where(BackupFile.checksum == checksum)).first()
            if not exists:
                backup = BackupFile(
                    checksum=checksum,
                    filepath=backup_path,
                    size=len(file_bytes)
                )
                session.add(backup)
                session.commit()

        # 直接创建数据库记录，以便设置原始文件名
        with Session(engine) as session:
            history_item = ClipboardHistory(
                raw_content=json.dumps(json_data),
                type="File",
                clipboard=file.filename,  # 剪贴板内容存储原始文件名
                from_equipment="Web",
                tag="手动粘贴",
                checksum=checksum,
                original_filename=file.filename  # 存储原始文件名
            )
            session.add(history_item)
            session.commit()
            new_id = history_item.id

        if new_id:
            return jsonify({'success': True, 'id': new_id})
        else:
            return jsonify({'success': False, 'error': '添加失败'}), 500

    except Exception as e:
        print(f"文件粘贴错误: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

# 删除记录API
@api.route('/api/delete/<string:uuid>', methods=['DELETE'])
def delete_record(uuid):
    try:
        engine = init_db()

        with Session(engine) as session:
            # 查找记录
            record = session.exec(select(ClipboardHistory).where(ClipboardHistory.uuid == uuid)).first()

            if not record:
                return jsonify({'success': False, 'error': '记录不存在'}), 404

            # 检查是否有其他记录使用相同的备份文件
            if record.checksum:
                other_records = session.exec(
                    select(ClipboardHistory).where(
                        ClipboardHistory.checksum == record.checksum,
                        ClipboardHistory.uuid != uuid
                    )
                ).all()

                # 如果没有其他记录使用该备份文件，删除备份文件
                if not other_records:
                    backup_file = session.exec(
                        select(BackupFile).where(BackupFile.checksum == record.checksum)
                    ).first()

                    if backup_file:
                        # 删除物理文件
                        try:
                            if os.path.exists(backup_file.filepath):
                                os.remove(backup_file.filepath)
                        except Exception as e:
                            print(f"删除备份文件失败: {e}")

                        # 删除备份文件记录
                        session.delete(backup_file)

            # 删除历史记录
            session.delete(record)
            session.commit()

        return jsonify({'success': True, 'message': '记录已删除'})

    except Exception as e:
        print(f"删除记录错误: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

# 搜索API
@api.route('/api/search', methods=['GET'])
def search_records():
    try:
        query = request.args.get('q', '').strip()
        limit = int(request.args.get('limit', 30))
        offset = int(request.args.get('offset', 0))

        # 限制参数范围
        limit = max(1, min(limit, 100))
        offset = max(0, offset)

        if not query:
            # 如果没有搜索词，返回普通的历史记录
            result = history_db.get_history_paginated(limit=limit, offset=offset)
            return jsonify({'success': True, 'data': result, 'query': query})

        # 有搜索词，进行搜索
        # 使用现有的分页方法获取所有数据，然后在内存中搜索
        result = history_db.get_history_paginated(limit=200, offset=0)  # 获取更多数据用于搜索

        filtered_records = []
        query_lower = query.lower()

        for record in result['records']:
            # 搜索文本内容
            content = record.get('content') or ''
            content_match = content.lower().find(query_lower) != -1

            # 搜索文件名
            filename = record.get('file_name') or ''
            filename_match = filename.lower().find(query_lower) != -1

            # 搜索时间戳
            timestamp = record.get('timestamp') or ''
            timestamp_match = timestamp.lower().find(query_lower) != -1

            # 搜索来源和标签
            source = record.get('source') or ''
            source_match = source.lower().find(query_lower) != -1

            tag = record.get('tag') or ''
            tag_match = tag.lower().find(query_lower) != -1

            if content_match or filename_match or timestamp_match or source_match or tag_match:
                filtered_records.append(record)

        # 应用分页
        total_count = len(filtered_records)
        paginated_records = filtered_records[offset:offset + limit]

        return jsonify({
            'success': True,
            'data': {
                'records': paginated_records,
                'total': total_count,
                'limit': limit,
                'offset': offset
            },
            'query': query
        })

    except Exception as e:
        print(f"搜索错误: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500
