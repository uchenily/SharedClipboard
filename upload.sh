#!/usr/bin/env bash

# 文件上传脚本
# 用法: ./upload.sh <文件路径>

ENDPOINT=${ENDPOINT}
# 配置API地址
API_URL="http://${ENDPOINT}/api/paste/file"

# 检查是否提供了文件路径
if [ $# -eq 0 ]; then
    echo "用法: $0 <文件路径>"
    exit 1
fi

# 获取文件路径
FILE_PATH="$1"

# 检查文件是否存在
if [ ! -f "$FILE_PATH" ]; then
    echo "错误: 文件不存在: $FILE_PATH"
    exit 1
fi

# 检查文件是否可读
if [ ! -r "$FILE_PATH" ]; then
    echo "错误: 文件不可读: $FILE_PATH"
    exit 1
fi

# 获取文件名
FILE_NAME=$(basename "$FILE_PATH")

# 显示文件信息
echo "正在上传文件: $FILE_NAME"
echo "文件大小: $(du -h "$FILE_PATH" | cut -f1)"

# 上传文件
echo "上传中..."
response=$(curl -s -X POST "$API_URL" -F "file=@$FILE_PATH")

# 显示结果
if [ $? -eq 0 ]; then
    echo "✓ 上传成功!"
    echo "服务器响应:"
    echo "$response"
else
    echo "✗ 上传失败!"
    exit 1
fi
