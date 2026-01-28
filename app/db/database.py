import os
import shutil
import hashlib
import json
from sqlmodel import SQLModel, create_engine, Session, select, func, delete
from typing import Optional
from config import config
from app.models.models import ClipboardHistory, BackupFile, Folder, Favorite
from app.db.cache import cache

def init_db(): # 初始化数据库
    # 确保数据库目录存在
    db_dir = os.path.dirname(config.DB_PATH) # 获取父目录
    if not os.path.exists(db_dir):
        os.makedirs(db_dir, exist_ok=True)  # 递归创建目录
        print(f"Created database directory: {db_dir}")

    # 确保备份目录存在
    bkp_dir = config.BACKUP_DIR
    if not os.path.exists(bkp_dir):
        os.makedirs(bkp_dir, exist_ok=True)  # 递归创建目录
        print(f"Created database directory: {bkp_dir}")


    db_exists = os.path.exists(config.DB_PATH)

    # 创建SQLite数据库引擎
    # echo=True 参数启用SQL日志（生产环境应设为False）
    sqlite_url = f"sqlite:///{config.DB_PATH}"  # 数据库连接地址
    engine = create_engine(sqlite_url, echo=config.DB_LOG_ENABLED)  # 创建引擎

    # 创建所有表（如果不存在）
    SQLModel.metadata.create_all(engine)

    # 初始化收藏夹根目录（仅当首次创建数据库时）
    if not db_exists:
        with Session(engine) as session:
            # 创建根收藏夹
            root_folder = Folder(name="Root", parent_id=None, path="/") # 使用 None 而不是 0 作为外键，避免约束报错
            session.add(root_folder)
            session.commit()

            # 更新根收藏夹的path（自引用需要）
            # 路径格式为 /ID/，例如 /1/
            root_folder.path = f"/{root_folder.id}/"
            session.add(root_folder)
            session.commit()

    return engine

def add_history_item_from_json(data: dict, engine=None):
    """
    将SyncClipboard.json的内容写入数据库，自动处理文本、文件、图片类型。
    :param data: 解析后的JSON字典
    :param engine: 可选，传入SQLModel数据库引擎，否则自动init_db
    """
    if engine is None:
        engine = init_db()
    with Session(engine) as session:
        item_type = data.get("Type", "")
        file_name = data.get("File", "")
        clipboard = data.get("Clipboard", "")
        from_equipment = data.get("From", None)
        tag = data.get("Tag", None)
        raw_content = json.dumps(data, ensure_ascii=False)
        checksum = None

        # 处理文件/图片类型
        if item_type in ["File", "Image"] and file_name:
            # clipboard字段本身就是MD5，无需再算
            checksum = clipboard
            src_path = os.path.join(os.path.dirname(config.SYNC_CLIPBOARD_JSON_PATH), "file", file_name)
            exists = session.exec(select(BackupFile).where(BackupFile.checksum == checksum)).first()
            backup_name = file_name
            backup_path = os.path.join(config.BACKUP_DIR, backup_name)
            os.makedirs(config.BACKUP_DIR, exist_ok=True)
            if not exists and os.path.exists(src_path):
                # 文件名冲突且内容不同，加后缀
                base, ext = os.path.splitext(file_name)
                count = 1
                while os.path.exists(backup_path):
                    # 检查已存在的文件内容是否相同
                    with open(backup_path, "rb") as f:
                        if hashlib.md5(f.read()).hexdigest() == checksum:
                            break
                    backup_name = f"{base}_{count}{ext}"
                    backup_path = os.path.join(config.BACKUP_DIR, backup_name)
                    count += 1
                if not os.path.exists(backup_path):
                    shutil.copy2(src_path, backup_path)
                size = os.path.getsize(backup_path)
                backup = BackupFile(
                    checksum=checksum,
                    filepath=backup_path,
                    size=size
                )
                session.add(backup)
            elif not os.path.exists(src_path):
                print(f"文件未找到: {src_path}")

        # group类型（多文件压缩包），需要计算MD5
        elif item_type == "Group" and file_name:
            src_path = os.path.join(os.path.dirname(config.SYNC_CLIPBOARD_JSON_PATH), "file", file_name)
            if os.path.exists(src_path):
                with open(src_path, "rb") as f:
                    file_bytes = f.read()
                    checksum = hashlib.md5(file_bytes).hexdigest()
                exists = session.exec(select(BackupFile).where(BackupFile.checksum == checksum)).first()
                backup_name = file_name
                backup_path = os.path.join(config.BACKUP_DIR, backup_name)
                os.makedirs(config.BACKUP_DIR, exist_ok=True)
                if not exists:
                    base, ext = os.path.splitext(file_name)
                    count = 1
                    while os.path.exists(backup_path):
                        with open(backup_path, "rb") as f:
                            if hashlib.md5(f.read()).hexdigest() == checksum:
                                break
                        backup_name = f"{base}_{count}{ext}"
                        backup_path = os.path.join(config.BACKUP_DIR, backup_name)
                        count += 1
                    if not os.path.exists(backup_path):
                        shutil.copy2(src_path, backup_path)
                    size = os.path.getsize(backup_path)
                    backup = BackupFile(
                        checksum=checksum,
                        filepath=backup_path,
                        size=size
                    )
                    session.add(backup)
            else:
                print(f"文件未找到: {src_path}")

        # 写入历史表
        history = ClipboardHistory(
            raw_content=raw_content,
            clipboard=clipboard,
            type=item_type,
            from_equipment=from_equipment,
            tag=tag,
            checksum=checksum
        )
        session.add(history)
        session.commit()
        cache.invalidate_history()
        if checksum:
            cache.invalidate_file_path(checksum)
        return history.id

class ServerGet:
    def __init__(self):
        self.engine = create_engine(f"sqlite:///{config.DB_PATH}", echo=False)

    # 主页列表专用查询（仅按时间排序，无筛选）
    def get_history_paginated(self, limit: int = 30, offset: int = 0) -> dict:
        """仅按时间倒序返回指定偏移量和数量的记录，包含总条数"""
        cached = cache.get_history_page(limit, offset)
        if cached is not None:
            return cached
        with Session(self.engine) as session:
            # 基础查询：按时间倒序（最新在前）
            base_query = select(ClipboardHistory).order_by(ClipboardHistory.timestamp.desc())

            # 获取总记录数
            total_count = session.exec(select(func.count()).select_from(base_query.subquery())).first()

            # 获取分页数据
            results = session.exec(base_query.offset(offset).limit(limit)).all()

            # 转换为前端可用格式
            records = []
            for item in results:
                    # 优先使用 original_filename，如果没有则从原始JSON解析（兼容旧数据）
                    file_name = item.original_filename
                    if not file_name:
                        try:
                            raw_data = json.loads(item.raw_content)
                            file_name = raw_data.get("File", None)
                        except json.JSONDecodeError:
                            pass

                    # 检查是否为收藏
                    is_favorite = session.exec(
                        select(Favorite).where(Favorite.history_uuid == item.uuid)
                    ).first() is not None

                    records.append({ # for 循环中添加代码
                        'id': item.id,
                        'uuid': item.uuid,
                        'type': item.type,
                        'timestamp': item.timestamp.strftime('%Y-%m-%d %H:%M:%S'),
                        'source': item.from_equipment,
                        'tag': item.tag,  # 添加标签信息
                        'is_favorite': is_favorite,
                        'content': item.clipboard if item.type == 'Text' else None,
                        'file_name': file_name,
                        'checksum': item.checksum
                    })

            payload = {
                'records': records,
                'total': total_count,
                'limit': limit,
                'offset': offset
            }
            cache.set_history_page(limit, offset, payload)
            return payload


    # 下载接口，根据checksum获取文件路径
    def get_file_path_by_checksum(self, checksum: str) -> Optional[str]:
        """根据文件校验和获取文件路径"""
        hit, cached_path = cache.get_file_path(checksum)
        if hit:
            return cached_path
        with Session(self.engine) as session:
            backup = session.exec(select(BackupFile).where(BackupFile.checksum == checksum)).first()
            if backup and os.path.exists(backup.filepath):
                cache.set_file_path(checksum, backup.filepath)
                return backup.filepath
            cache.set_file_path(checksum, None)
            return None

    # 根据 ID 获取历史记录
    def get_history_by_id(self, history_id: int):
        cached = cache.get_history_by_id(history_id)
        if cached is not None:
            return cached
        with Session(self.engine) as session: # 通过 Session 类创建一个数据库会话（session），self.engine 是数据库引擎（已在类中初始化），用于建立与数据库的连接。with 语句确保会话使用完毕后自动关闭，释放资源。
            # 使用 SQLModel 的 select 方法构建查询语句，指定查询 ClipboardHistory 模型（对应数据库表），并通过 where 条件筛选出 id 等于 history_id 的记录。
            statement = select(ClipboardHistory).where(ClipboardHistory.id == history_id)
            result = session.exec(statement).first() # 通过会话的 exec 方法执行查询语句，first() 方法获取查询结果中的第一条记录（因为 id 通常是唯一的，所以最多只有一条结果）。

            if result:
                # 将结果转换为字典格式
                payload = {
                    'id': result.id,
                    'uuid': result.uuid,
                    'type': result.type,
                    'clipboard': result.clipboard,
                    'from_equipment': result.from_equipment,
                    'tag': result.tag,
                    'timestamp': result.timestamp.isoformat(),
                    'checksum': result.checksum,
                    'raw_content': result.raw_content
                }
                cache.set_history_by_id(history_id, payload)
                return payload
            return None

class ServerSet:
    def __init__(self):
        self.engine = create_engine(f"sqlite:///{config.DB_PATH}", echo=False)
