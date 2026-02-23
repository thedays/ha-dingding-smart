# 钉钉智能门铃 - Home Assistant 集成

基于逆向的Python推送实现的Home Assistant自定义集成，支持钉钉智能门铃/摄像头的开门事件监控、远程开锁等功能。

## 功能特性

- ✅ 实时推送监听（基于SSL/TLS）
- ✅ 开门事件监控（指纹、密码、锁事件）
- ✅ 门铃呼叫通知
- ✅ 设备在线/离线状态
- ✅ 多种报警事件（PIR移动侦测、低电量、温度报警等）
- ✅ 完全脱离Android系统运行

## 安装

### 1. 复制集成文件

将 `custom_components/dingding_smart` 目录复制到你的Home Assistant配置目录：

```bash
# 默认配置目录
cp -r custom_components/dingding_smart ~/.homeassistant/custom_components/

# 对于Docker安装
cp -r custom_components/dingding_smart /path/to/your/homeassistant/config/custom_components/

# 对于Home Assistant OS
# 通过Samba或SSH复制到/config/custom_components/目录
```

### 2. 重启Home Assistant

```bash
# 如果使用Docker
docker restart homeassistant

# 如果使用Home Assistant OS
# 在界面中点击 "设置" -> "系统" -> "重启"
```

### 3. 添加集成

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
```

## 测试

### 1. 测试登录功能

```bash
cd /path/to/dingding_smart/homeassistant

# 方法1：使用命令行参数
python3 test_login.py --username 13800138000 --password your_password

# 方法2：使用配置文件
cp config.example.json config.json
# 编辑config.json填入你的信息
python3 test_login.py --config config.json
```

### 2. 测试推送连接

```bash
# 方法1：使用默认服务器
python3 test_push.py

# 方法2：指定服务器
python3 test_push.py --host chnpush.lancens.com --port 11001

# 方法3：使用配置文件
python3 test_push.py --config config.json
```

### 3. 测试结果说明

- 登录测试成功：显示设备列表
- 推送测试成功：显示"Push connected successfully"消息
- 如有错误：检查错误信息并参考故障排除部分

## 事件

集成会触发以下Home Assistant事件：

### 开门事件

**事件名**: `dingding_smart_door_unlock`

**数据**:
```json
{
  "uid": "device_uid",
  "method": "fingerprint|password|lock",
  "message": "开门消息",
  "alert": "提示信息",
  "name": "设备名称"
}
```

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

### 2. 门铃呼叫时播放声音

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

### 3. 设备离线时报警

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

### 4. 指纹开锁时记录日志

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

## 技术细节

### 推送协议

- **协议**: SSL/TLS over TCP
- **端口**: 11001
- **消息格式**: 8字节消息头 + JSON数据体
- **字节序**: 小端序
- **心跳超时**: 130秒
- **重连机制**: 自动重连，最大重试次数5次

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
4. **事件处理**: 解析推送消息并转换为Home Assistant事件
5. **状态同步**: 定期同步设备状态

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
│       └── strings.json         # 本地化字符串
├── test_login.py                # 登录测试脚本
├── test_push.py                 # 推送测试脚本
├── config.example.json          # 配置文件示例
└── README.md                    # 本文件
```

### 开发环境设置

1. 克隆项目到本地
2. 安装依赖（如果需要）
3. 修改代码后测试
4. 提交Pull Request

### 贡献

欢迎提交Issue和Pull Request！

## 许可证

本项目仅供学习和研究使用。

## 致谢

- 感谢钉钉智能门铃设备的支持
- 基于逆向的Python推送实现
- Home Assistant社区的支持
