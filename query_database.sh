#!/bin/bash

# 数据库查询脚本
# 用于查询剪贴板历史数据库中的所有信息

# 获取脚本所在目录
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
DB_PATH="$SCRIPT_DIR/db/clipboard_history.db"

# 检查数据库文件是否存在
if [ ! -f "$DB_PATH" ]; then
    echo "错误: 数据库文件不存在: $DB_PATH"
    exit 1
fi

echo "=========================================="
echo "剪贴板历史数据库查询结果"
echo "数据库路径: $DB_PATH"
echo "查询时间: $(date)"
echo "=========================================="

# 检查是否安装了sqlite3
if ! command -v sqlite3 &> /dev/null; then
    echo "错误: 未安装 sqlite3 命令行工具"
    echo "请安装 sqlite3: sudo apt-get install sqlite3"
    exit 1
fi

# 查询所有表名
echo ""
echo "=== 数据库表结构 ==="
sqlite3 "$DB_PATH" ".tables"

echo ""
echo "=== 表的详细信息 ==="
sqlite3 "$DB_PATH" ".schema"

# 查询表中的总记录数
echo ""
echo "=== 记录统计 ==="
TOTAL_RECORDS=$(sqlite3 "$DB_PATH" "SELECT COUNT(*) FROM clipboardhistory;")
echo "总记录数: $TOTAL_RECORDS"

# 按类型统计
echo ""
echo "=== 按类型统计 ==="
sqlite3 "$DB_PATH" "
SELECT 
    type as '类型',
    COUNT(*) as '数量',
    ROUND(COUNT(*) * 100.0 / (SELECT COUNT(*) FROM clipboardhistory), 2) || '%' as '占比'
FROM clipboardhistory 
GROUP BY type 
ORDER BY COUNT(*) DESC;"

# 按来源设备统计
echo ""
echo "=== 按来源设备统计 ==="
sqlite3 "$DB_PATH" "
SELECT 
    CASE 
        WHEN from_equipment IS NULL OR from_equipment = '' THEN '未知设备'
        ELSE from_equipment 
    END as '设备',
    COUNT(*) as '数量'
FROM clipboardhistory 
GROUP BY from_equipment 
ORDER BY COUNT(*) DESC;"

# 查询最近10条记录
echo ""
echo "=== 最近10条记录 ==="
sqlite3 "$DB_PATH" "
SELECT 
    id as 'ID',
    substr(clipboard, 1, 50) || 
    CASE 
        WHEN length(clipboard) > 50 THEN '...'
        ELSE ''
    END as '剪贴板内容',
    type as '类型',
    CASE 
        WHEN from_equipment IS NULL OR from_equipment = '' THEN '未知'
        ELSE from_equipment 
    END as '来源设备',
    timestamp as '时间'
FROM clipboardhistory 
ORDER BY timestamp DESC 
LIMIT 10;"

# 查询时间范围
echo ""
echo "=== 时间范围 ==="
sqlite3 "$DB_PATH" "
SELECT 
    MIN(timestamp) as '最早记录时间',
    MAX(timestamp) as '最新记录时间',
    julianday(MAX(timestamp)) - julianday(MIN(timestamp)) as '天数差'
FROM clipboardhistory;"

# 查询有标签的记录
echo ""
echo "=== 有标签的记录 ==="
TAGGED_COUNT=$(sqlite3 "$DB_PATH" "SELECT COUNT(*) FROM clipboardhistory WHERE tag IS NOT NULL AND tag != '';")
echo "有标签的记录数: $TAGGED_COUNT"

if [ "$TAGGED_COUNT" -gt 0 ]; then
    echo "标签分布:"
    sqlite3 "$DB_PATH" "
    SELECT 
        tag as '标签',
        COUNT(*) as '数量'
    FROM clipboardhistory 
    WHERE tag IS NOT NULL AND tag != ''
    GROUP BY tag 
    ORDER BY COUNT(*) DESC;"
fi

# 数据库文件大小
echo ""
echo "=== 数据库信息 ==="
DB_SIZE=$(du -h "$DB_PATH" | cut -f1)
echo "数据库文件大小: $DB_SIZE"

# 显示UUID统计
echo ""
echo "=== UUID统计 ==="
sqlite3 "$DB_PATH" "
SELECT 
    COUNT(DISTINCT uuid) as '唯一UUID数量',
    CASE 
        WHEN COUNT(DISTINCT uuid) = COUNT(*) THEN '无重复'
        ELSE '存在重复'
    END as 'UUID状态'
FROM clipboardhistory;"

echo ""
echo "=========================================="
echo "查询完成"
echo "=========================================="