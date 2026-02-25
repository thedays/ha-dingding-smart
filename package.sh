#!/bin/bash

# 叮叮智能门铃集成 - 打包脚本
# 用于创建HACS安装包

set -e

# 配置
VERSION="1.0.12"
PACKAGE_NAME="dingding_smart"
ZIP_NAME="${PACKAGE_NAME}.zip"

echo "========================================="
echo "叮叮智能门铃集成 - 打包脚本"
echo "========================================="
echo ""

# 清理旧的打包文件
echo "🧹 清理旧的打包文件..."
rm -f "${ZIP_NAME}"
echo "✅ 清理完成"
echo ""

# 创建临时目录
echo "📁 创建临时目录..."
TEMP_DIR="temp_package"
rm -rf "${TEMP_DIR}"
mkdir -p "${TEMP_DIR}/custom_components/${PACKAGE_NAME}"
echo "✅ 临时目录创建完成"
echo ""

# 复制文件
echo "📦 复制文件..."
cp -r custom_components/${PACKAGE_NAME}/* "${TEMP_DIR}/custom_components/${PACKAGE_NAME}/"
cp hacs.json "${TEMP_DIR}/"
cp README_HACS.md "${TEMP_DIR}/README.md"
cp LICENSE "${TEMP_DIR}/"
echo "✅ 文件复制完成"
echo ""

# 创建ZIP包
echo "📦 创建ZIP包..."
cd "${TEMP_DIR}"
zip -r "../${ZIP_NAME}" *
cd ..
echo "✅ ZIP包创建完成: ${ZIP_NAME}"
echo ""

# 清理临时目录
echo "🧹 清理临时目录..."
rm -rf "${TEMP_DIR}"
echo "✅ 清理完成"
echo ""

# 显示包信息
echo "========================================="
echo "打包完成！"
echo "========================================="
echo "包名: ${ZIP_NAME}"
echo "版本: ${VERSION}"
echo "文件列表:"
unzip -l "${ZIP_NAME}"
echo ""
echo "========================================="
echo ""
echo "📌 下一步："
echo "1. 将 ${ZIP_NAME} 上传到GitHub Release"
echo "2. 或使用以下命令推送到GitHub："
echo ""
echo "   git add ."
echo "   git commit -m 'Release v${VERSION}'"
echo "   git tag v${VERSION}"
echo "   git push origin main"
echo "   git push origin v${VERSION}"
echo ""
