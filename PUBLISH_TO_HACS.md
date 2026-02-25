# 发布到GitHub和HACS指南

本指南将帮助你将叮叮智能门铃集成发布到GitHub并通过HACS安装。

## 📋 前置要求

- GitHub账号
- 已安装Home Assistant
- 已安装HACS

## 🚀 步骤1：创建GitHub仓库

### 1.1 创建新仓库

1. 访问 https://github.com/new
2. 填写仓库信息：
   - **仓库名称**: `ha-dingding-smart` (推荐)
   - **描述**: 叮叮智能门铃 - Home Assistant集成
   - **可见性**: Public (公开，HACS需要)
   - **初始化仓库**: ✅ 添加README文件
3. 点击 "Create repository"

### 1.2 上传文件

#### 方法A：通过GitHub网页上传

1. 在仓库页面点击 "uploading an existing file"
2. 拖拽以下文件到上传区域：
   ```
   custom_components/
   ├── dingding_smart/
   │   ├── __init__.py
   │   ├── config_flow.py
   │   ├── manifest.json
   │   ├── sensor.py
   │   └── strings.json
   hacs.json
   README.md
   LICENSE
   DASHBOARD_EXAMPLES.md
   ```
3. 填写提交信息：
   - "Initial release v1.0.0"
4. 点击 "Commit changes"

#### 方法B：通过Git命令行上传

```bash
# 1. 初始化Git仓库
cd /Users/k/Documents/project/钉钉智能/homeassistant
git init

# 2. 添加所有文件
git add .

# 3. 提交更改
git commit -m "Initial release v1.0.0"

# 4. 添加远程仓库（替换为你的用户名）
git remote add origin https://github.com/thedays/ha-dingding-smart.git

# 5. 推送到GitHub
git branch -M main
git push -u origin main
```

## 📦 步骤2：创建GitHub Release

### 2.1 创建标签

```bash
# 创建并推送标签
git tag v1.0.0
git push origin v1.0.0
```

### 2.2 生成zip文件

**生成只包含文件的zip文件**（推荐）：

```bash
# 删除旧的zip文件（如果存在）
rm -f dingding_smart.zip

# 进入组件目录
cd custom_components/dingding_smart

# 删除缓存目录
rm -rf __pycache__

# 直接压缩文件到根目录
zip -r ../../dingding_smart.zip sensor.py __init__.py manifest.json strings.json config_flow.py

# 返回上级目录
cd ../..

# 查看生成的文件
ls -la dingding_smart.zip

# 验证zip文件内容
unzip -l dingding_smart.zip
```

**压缩结果**：
```
dingding_smart.zip
├── sensor.py
├── __init__.py
├── manifest.json
├── strings.json
└── config_flow.py
```

### 2.3 创建Release

1. 在GitHub仓库页面，点击 "Releases"
2. 点击 "Create a new release"
3. 填写信息：
   - **Tag**: `v1.0.0`
   - **Release title**: `v1.0.0 - 初始版本`
   - **Description**:
     ```markdown
     ## 🎉 初始版本发布

     ### ✨ 新功能
     - 支持登录和设备列表获取
     - 实时推送监听（基于SSL/TLS）
     - 开门事件监控（指纹、密码、锁事件）
     - 门铃呼叫通知
     - 设备在线/离线状态
     - 多种报警事件（PIR移动侦测、低电量、温度报警等）
     - 丰富的传感器实体（电池、WiFi信号、版本等）
     - 支持多设备管理

     ### 📦 安装
     - 通过HACS安装（推荐）
     - 手动安装

     ### 📖 文档
     - [README](https://github.com/thedays/ha-dingding-smart/blob/main/README.md)
     - [仪表盘配置示例](https://github.com/thedays/ha-dingding-smart/blob/main/DASHBOARD_EXAMPLES.md)

     ### ⚠️ 注意
     - 本项目仅供学习和研究使用
     - 请遵守相关法律法规和设备使用条款
     ```
4. 点击 "Publish release"

## 🏠 步骤3：添加到HACS

### 3.1 提交到HACS

1. 访问 https://hacs.xyz/
2. 点击右上角 "Submit custom integration"
3. 填写信息：
   - **Category**: Integration
   - **Full name of the repository**: `thedays/ha-dingding-smart`
   - **Home Assistant version**: `2023.1.0`
   - **Description**: 钉钉智能门铃 - Home Assistant集成，支持开门事件监控、远程开锁等功能
   - **Link to documentation**: `https://github.com/thedays/ha-dingding-smart/blob/main/README.md`
   - **Link to your GitHub repository**: `https://github.com/thedays/ha-dingding-smart`
4. 点击 "Submit"

### 3.2 等待审核

HACS团队会审核你的提交，通常需要几天时间。审核通过后，用户就可以在HACS中搜索并安装你的集成了。

## 📱 步骤4：用户如何安装

### 通过HACS安装（审核通过后）

1. 打开HACS
2. 进入 "集成"
3. 搜索 "dingding smart" 或 "钉钉智能"
4. 点击 "下载"
5. 重启Home Assistant

### 通过自定义仓库安装（立即可用）

1. 打开HACS
2. 进入 "集成"
3. 点击右上角三个点 → "自定义仓库"
4. 添加自定义仓库：
   - 仓库：`thedays/ha-dingding-smart`
   - 类别：集成
   - 完整URL：`https://github.com/thedays/ha-dingding-smart`
5. 点击 "添加"
6. 在集成列表中找到 "钉钉智能门铃"
7. 点击 "下载"
8. 重启Home Assistant

## 🔧 步骤5：更新hacs.json

记得将 `hacs.json` 中的 `codeowners` 字段更新为你的GitHub用户名：

```json
{
  "codeowners": ["thedays"],
  ...
}
```

## 📝 步骤6：更新README.md

确保README.md包含以下信息：

- ✅ 功能特性列表
- ✅ HACS安装说明
- ✅ 手动安装说明
- ✅ 配置说明
- ✅ 传感器列表
- ✅ 事件列表
- ✅ 自动化示例
- ✅ 故障排除
- ✅ 技术细节

## 🎯 步骤7：测试安装

在发布前，建议先测试安装：

1. 创建一个测试用的Home Assistant实例（如Docker）
2. 通过自定义仓库安装集成
3. 测试所有功能：
   - 登录
   - 获取设备列表
   - 推送连接
   - 传感器显示
   - 事件触发
4. 确认无误后再正式发布

## 📊 步骤8：维护和更新

### 发布新版本

1. 更新代码
2. 更新 `manifest.json` 中的版本号
3. 更新 `README.md` 中的更新日志
4. 创建新的Git标签：
   ```bash
   git tag v1.1.0
   git push origin v1.1.0
   ```
5. 在GitHub创建新的Release
6. HACS会自动检测到新版本

### 处理Issue

- 及时回复用户的问题
- 记录常见问题到FAQ
- 根据用户反馈改进功能

## 🌟 步骤9：推广

### 推广渠道

- Home Assistant社区论坛
- Reddit r/homeassistant
- 微博、知乎等中文社区
- 技术博客

### 推广内容

- 集成的功能特性
- 使用教程
- 自动化示例
- 用户反馈

## 📋 检查清单

发布前检查：

- [ ] 所有文件已上传到GitHub
- [ ] `hacs.json` 配置正确
- [ ] `manifest.json` 版本号正确
- [ ] README.md 完整且准确
- [ ] LICENSE 文件存在
- [ ] 已创建GitHub Release
- [ ] 已提交到HACS
- [ ] 已测试安装和功能
- [ ] 代码中无敏感信息（如密码、Token等）

## 🎉 完成！

恭喜！你的集成已经成功发布到GitHub和HACS。用户现在可以通过HACS轻松安装和使用你的集成了。

## 📞 获取帮助

如果遇到问题：

- HACS文档：https://hacs.xyz/docs/
- Home Assistant文档：https://www.home-assistant.io/docs/
- GitHub社区：https://github.com/home-assistant/core/issues

## 🙏 致谢

感谢你为Home Assistant社区做出贡献！
