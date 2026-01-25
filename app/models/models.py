from sqlmodel import SQLModel, Field, Column, ForeignKey, UniqueConstraint
from typing import Optional
from datetime import datetime
import uuid as uuid_lib
from sqlalchemy import DateTime, Text


class BaseTable(SQLModel):
    """所有数据库表的基础模型（非表模型，仅用于继承）"""
    id: Optional[int] = Field(
        default=None, # 通过设置为 Optional[int]、default=None，让 SQLModel 处理自增主键
        primary_key=True,
        description="自增主键"
    )

# 历史记录表
class ClipboardHistory(BaseTable, table=True):

    # __tablename__ = "ClipboardHistory"  # 显式指定表名
    raw_content: str = Field(
        sa_column=Column(Text), # 将 raw_content 定义为 TEXT 类型（适合存储长文本）
        description="原始JSON内容"
    )
    uuid: str = Field(
        default_factory=lambda: str(uuid_lib.uuid4()),  # 自动生成UUID
        nullable=False,
        unique=True,
        description="全局唯一标识符"
    )
    clipboard: str = Field(description="剪贴板内容")
    type: str = Field(nullable=False, description="记录类型: Text/Image/File")
    from_equipment: Optional[str] = Field(
        default=None,
        description="来源设备"
    )
    tag: Optional[str] = Field( # 声明为可选字段
        default=None,
        description="记录标签（可选）"
    )
    timestamp: datetime = Field(
        default_factory=datetime.utcnow,  # 自动设置当前时间
        sa_column=Column(DateTime(timezone=True)),
        description="记录时间"
    )
    checksum: Optional[str] = Field(
        default=None,
        description="文件内容的MD5校验和",
        index=True  # 创建索引加速查询
    )
    original_filename: Optional[str] = Field(
        default=None,
        description="原始文件名（仅用于File和Image类型）"
    )

    class Config:
        # 为时间戳字段创建索引，优化按时间筛选的性能
        indexes = [("timestamp_index", "timestamp")]

# 备份文件表
class BackupFile(BaseTable, table=True):

    __tablename__ = "backup_files"  # 显式指定表名
    checksum: str = Field(
        unique=True,  # 改为唯一约束而非主键
        index=True,   # 添加索引加速查询
        description="文件内容的MD5校验和"
    )
    filepath: str = Field(
        # unique=True,  # 确保文件路径唯一
        nullable=False,
        description="备份文件绝对路径"
    )
    size: int = Field(description="文件大小(字节)")

# 收藏记录表
class Favorite(BaseTable, table=True):

    __tablename__ = "favorites"  # 显式指定表名
    history_uuid: str = Field(
        foreign_key="clipboardhistory.uuid",  # 外键关联历史记录表
        nullable=False,
        description="关联的历史记录UUID"
    )
    folder_id: int = Field(
        foreign_key="folder.id",  # 外键关联收藏夹表
        description="所属收藏夹ID"
    )
    created_at: datetime = Field(
        default_factory=datetime.utcnow,  # 自动设置当前时间
        sa_column=Column(DateTime(timezone=True)),
        description="收藏时间"
    )

    # 唯一约束防止重复收藏（同一记录不能在同一个收藏夹收藏多次）
    __table_args__ = (
        UniqueConstraint('history_uuid', 'folder_id', name='_favorite_unique'),
    )

# 收藏夹表
class Folder(BaseTable, table=True):

    name: str = Field(nullable=False, description="收藏夹名称")
    parent_id: int = Field(
        default=0,
        foreign_key="folder.id",  # 自引用外键，实现多级结构
        description="父收藏夹ID（0为根）"
    )
    path: Optional[str] = Field(
        default=None,
        description="完整路径（如/a/b/）"
    )
