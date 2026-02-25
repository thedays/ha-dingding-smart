# 钉钉智能门铃 - Home Assistant 集成

基于逆向的Python推送实现的Home Assistant自定义集成，支持钉钉智能门铃/摄像头的开门事件监控、远程开锁等功能。

## 功能特性

- ✅ 实时推送监听（基于SSL/TLS）
- ✅ 开门事件监控（指纹、密码、门内开锁）
- ✅ 门铃呼叫通知
- ✅ 设备在线/离线状态
- ✅ 多种报警事件（PIR移动侦测、低电量、温度报警等）
- ✅ 门锁状态传感器（自动5秒恢复）
- ✅ 完全脱离Android系统运行
- ✅ Token持久化存储
- ✅ 线程安全的事件处理

## GitHub仓库

📦 **GitHub地址**: https://github.com/thedays/ha-dingding-smart

## 安装

### 方法1：通过HACS安装（推荐）

1. 打开Home Assistant
2. 进入 "HACS" → "集成"
3. 点击 "浏览并下载集成"
4. 搜索 "dingding" 或 "钉钉智能"
5. 点击安装
6. 重启Home Assistant

### 方法2：手动安装

将 `custom_components/dingding_smart` 目录复制到你的Home Assistant配置目录：

```bash
# 默认配置目录
cp -r custom_components/dingding_smart ~/.homeassistant/custom_components/

# 对于Docker安装
cp -r custom_components/dingding_smart /path/to/your/homeassistant/config/custom_components/

# 对于Home Assistant OS
# 通过Samba或SSH复制到/config/custom_components/目录
```

### 3. 重启Home Assistant

```bash
# 如果使用Docker
docker restart homeassistant

# 如果使用Home Assistant OS
# 在界面中点击 "设置" -> "系统" -> "重启"
```

### 4. 添加集成

1. 打开Home Assistant
2. 进入 "设置" → "设备与服务"
3. 点击 "添加集成"
4. 搜索 "dingding" 或 "钉钉智能"
5. 填写配置信息：
   - 用户名：钉钉智能App的登录账号（手机号）
   - 密码：钉钉智能App的登录密码
   - 服务器区域：选择服务器所在区域（中国/欧洲/美国）
6. 点击 "提交"

## 配置

### 基本配置

| 字段 | 说明 | 示例 |
|------|------|------|
| 用户名 | 钉钉智能App的登录账号 | `13800138000` |
| 密码 | 钉钉智能App的登录密码 | `your_password` |
| 服务器区域 | 选择服务器所在区域 | `中国` / `欧洲` / `美国` |

### 可选配置

在 `configuration.yaml` 中添加以下可选配置：

```yaml
dingding_smart:
  username: 13800138000
  password: your_password
  server_region: cn  # cn, eu, us
  device_uid: "your_device_uid"  # 可选：只监听指定设备
  user_id: 12742576  # 可选：用户ID
  imei: "your_imei"  # 可选：设备IMEI号，用于推送绑定
```

## 实体

### 传感器实体

集成会为每个设备创建以下传感器：

| 实体ID | 名称 | 说明 |
|---------|------|------|
| `sensor.{device_name}_battery` | 电池电量 | 设备电池电量百分比 |
| `sensor.{device_name}_wifi_signal` | WiFi信号 | 设备WiFi信号强度 |
| `sensor.{device_name}_status` | 设备状态 | 设备当前状态 |
| `sensor.{device_name}_last_unlock` | 最后开锁 | 最后一次开锁事件信息 |
| `binary_sensor.{device_name}_door_lock` | 门锁状态 | 门锁开关状态（5秒自动恢复） |

### 门锁状态传感器

门锁状态传感器会在检测到开锁事件时自动变为"开锁"状态，5秒后自动恢复为"关锁"状态。

**支持的开锁方法**：
- `fingerprint` - 指纹开锁
- `password` - 密码开锁
- `inside_lock` - 门内开锁

## 事件

集成会触发以下Home Assistant事件：

### 开门事件

**事件名**: `dingding_smart_door_unlock`

**数据**:
```json
{
  "uid": "device_uid",
  "method": "fingerprint|password|inside_lock",
  "message": "开门消息",
  "alert": "提示信息",
  "name": "设备名称"
}
```

**开锁方法**:
- `fingerprint`: 指纹开锁
- `password`: 密码开锁
- `inside_lock`: 门内开锁

### 门铃呼叫事件

**事件名**: `dingding_smart_door_call`

**数据**:
```json
{
  "uid": "device_uid",
  "message": "呼叫消息",
  "alert": "提示信息",
  "name": "设备名称"
}
```

### 设备离线事件

**事件名**: `dingding_smart_door_offline`

**数据**:
```json
{
  "uid": "device_uid",
  "message": "离线消息",
  "alert": "提示信息",
  "name": "设备名称"
}
```

### 设备上线事件

**事件名**: `dingding_smart_door_online`

**数据**:
```json
{
  "uid": "device_uid",
  "message": "上线消息",
  "alert": "提示信息",
  "name": "设备名称"
}
```

### 报警事件

**事件名**: `dingding_smart_alarm`

**数据**:
```json
{
  "uid": "device_uid",
  "type": "0|4|8|9|10",
  "message": "报警消息",
  "alert": "提示信息",
  "name": "设备名称"
}
```

**报警类型**:
- `0`: PIR移动侦测
- `4`: 低电量
- `8`: 低温报警
- `9`: 高温报警
- `10`: 声音报警

## 自动化示例

### 1. 开门时发送通知

```yaml
automation:
  - alias: "门铃开门通知"
    trigger:
      - platform: event
        event_type: dingding_smart_door_unlock
    action:
      - service: notify.mobile_app_your_phone
        data:
          title: "门铃开门通知"
          message: "检测到开门事件！方式: {{ trigger.event.data.method }}"
```

### 2. 门内开锁时发送通知

```yaml
automation:
  - alias: "门内开锁提醒"
    trigger:
      - platform: event
        event_type: dingding_smart_door_unlock
    condition:
      - condition: template
        value_template: "{{ trigger.event.data.method == 'inside_lock' }}"
    action:
      - service: notify.mobile_app_your_phone
        data:
          title: "门内开锁"
          message: "有人在门内开锁了！"
```

### 3. 门铃呼叫时播放声音

```yaml
automation:
  - alias: "门铃呼叫提醒"
    trigger:
      - platform: event
        event_type: dingding_smart_door_call
    action:
      - service: media_player.play_media
        target:
          entity_id: media_player.speaker
        data:
          media_content_id: "doorbell_sound.mp3"
          media_content_type: music
```

### 4. 设备离线时报警

```yaml
automation:
  - alias: "门铃离线报警"
    trigger:
      - platform: event
        event_type: dingding_smart_door_offline
    action:
      - service: notify.mobile_app_your_phone
        data:
          title: "门铃离线警告"
          message: "门铃设备 {{ trigger.event.data.name }} 已离线！"
```

### 5. 指纹开锁时记录日志

```yaml
automation:
  - alias: "指纹开锁记录"
    trigger:
      - platform: event
        event_type: dingding_smart_door_unlock
    condition:
      - condition: template
        value_template: "{{ trigger.event.data.method == 'fingerprint' }}"
    action:
      - service: logbook.log
        data:
          name: "门铃"
          message: "指纹开锁 - {{ trigger.event.data.name }}"
```

## 故障排除

### 登录失败

**错误**: `auth_error`

**解决方法**:
- 检查用户名和密码是否正确
- 确认账号可以在钉钉智能App中正常登录
- 检查服务器区域是否选择正确

### 未找到设备

**错误**: `no_devices`

**解决方法**:
- 确认账号下已绑定设备
- 在钉钉智能App中检查设备是否在线
- 尝试重新登录钉钉智能App

### 推送连接失败

**症状**: 无法接收推送消息

**解决方法**:
- 检查网络连接
- 确认推送服务器地址和端口正确
- 查看Home Assistant日志获取详细错误信息
- 尝试使用测试脚本单独测试推送连接

### SSL连接错误

**症状**: `SSL handshake failed`

**解决方法**:
- 检查系统时间是否正确
- 确认防火墙没有阻止SSL连接
- 尝试重启Home Assistant
- 查看日志确认SSL证书验证已禁用

### 门锁状态不更新

**症状**: 门锁状态一直显示开锁

**解决方法**:
- 检查Home Assistant日志是否有错误
- 确认推送服务已连接
- 查看事件日志确认收到开门事件
- 重启Home Assistant

## 技术细节

### 推送协议

- **协议**: SSL/TLS over TCP
- **端口**: 11001
- **消息格式**: 8字节消息头 + JSON数据体
- **字节序**: 小端序
- **心跳超时**: 130秒
- **重连机制**: 自动重连，最大重试次数5次
- **SSL证书**: 已禁用证书验证（兼容性优化）

### 消息头格式

```
[0-3]   命令类型 (CMD) - 4字节，小端序
[4-7]   数据长度 (LENGTH) - 4字节，小端序
```

### 命令类型

| 命令 | 值 | 说明 |
|------|-----|------|
| CMD_HEARTBEAT | 0 | 心跳 |
| CMD_REGISTER | 1 | 注册 |
| CMD_TOKEN | 2 | Token |
| CMD_PUSH | 3 | 推送 |

### 实现原理

1. **认证流程**: 通过模拟钉钉智能App的登录请求获取token
2. **设备发现**: 使用token获取用户绑定的设备列表
3. **推送连接**: 建立SSL/TLS连接到推送服务器
4. **Token绑定**: 将推送Token绑定到API服务器
5. **事件处理**: 解析推送消息并转换为Home Assistant事件
6. **状态同步**: 定期同步设备状态
7. **持久化存储**: Token和配置信息持久化存储

## 开发

### 项目结构

```
homeassistant/
├── custom_components/
│   └── dingding_smart/
│       ├── __init__.py          # 主集成文件
│       ├── config_flow.py       # 配置流程
│       ├── manifest.json        # 集成清单
│       ├── sensor.py            # 传感器实体
│       ├── binary_sensor.py     # 二进制传感器实体
│       └── strings.json         # 本地化字符串
├── README.md                    # 本文件
└── dingding_smart.zip         # 发布包
```

### 开发环境设置

1. 克隆项目到本地
2. 安装依赖（如果需要）
3. 修改代码后测试
4. 提交Pull Request

### 贡献

欢迎提交Issue和Pull Request！

## 版本历史

### v1.0.12 (2026-02-25)
- ✅ 优化门锁状态自动恢复时间为5秒
- ✅ 添加中文方法显示

### v1.0.11 (2026-02-25)
- ✅ 调整门锁状态恢复时间为5秒

### v1.0.10 (2026-02-25)
- ✅ 修复推送服务和线程安全问题
- ✅ 新增门锁状态传感器
- ✅ 完全禁用SSL证书验证

### v1.0.9 (2026-02-24)
- ✅ Token持久化存储
- ✅ 优化API请求处理

## 许可证

本项目仅供学习和研究使用。

## 致谢

- 感谢钉钉智能门铃设备的支持
- 基于逆向的Python推送实现
- Home Assistant社区的支持

---

## 📱 小红书发布指南

### 发布内容示例

**标题**: 🚪 把钉钉智能门铃接入Home Assistant，实现智能门铃监控！

**正文**:

终于把钉钉智能门铃成功接入Home Assistant了！🎉

✨ 主要功能：
✅ 实时推送监听 - 基于SSL/TLS协议
✅ 开门事件监控 - 支持指纹、密码、门内开锁
✅ 门铃呼叫通知 - 实时接收门铃呼叫
✅ 设备状态监控 - 在线/离线、电池电量、WiFi信号
✅ 门锁状态传感器 - 自动5秒恢复
✅ 多种报警事件 - PIR移动侦测、低电量、温度报警等
✅ Token持久化 - 重启后自动登录
✅ 线程安全 - 稳定可靠

📦 GitHub项目：https://github.com/thedays/ha-dingding-smart

🔧 安装方式：
1. 通过HACS安装（推荐）
2. 手动安装：下载zip文件，复制到custom_components目录

📝 配置简单：
- 用户名：钉钉智能App账号
- 密码：钉钉智能App密码
- 服务器区域：选择中国/欧洲/美国

🎯 支持的事件：
- 指纹开锁
- 密码开锁
- 门内开锁
- 门铃呼叫
- 设备离线/上线
- PIR移动侦测
- 低电量报警
- 温度报警

💡 自动化示例：
- 开门时发送手机通知
- 门铃呼叫时播放声音
- 设备离线时报警
- 门内开锁提醒

#智能家居 #HomeAssistant #钉钉智能 #门铃 #DIY #自动化

### 标签建议

#智能家居 #HomeAssistant #钉钉智能 #门铃 #智能门锁 #DIY #自动化 #物联网 #HomeAssistant集成

### 图片建议

可以制作以下类型的图片用于小红书发布：

1. **Home Assistant界面截图** - 显示集成后的设备列表和传感器
2. **自动化配置截图** - 显示自动化规则配置
3. **事件日志截图** - 显示开门事件记录
4. **架构图** - 展示集成的工作原理
5. **功能对比图** - 对比集成前后的功能差异

---

**GitHub**: https://github.com/thedays/ha-dingding-smart
