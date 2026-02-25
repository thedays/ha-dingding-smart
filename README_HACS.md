# 叮叮智能门铃 - Home Assistant 集成

基于逆向的Python推送实现的Home Assistant自定义集成，支持叮叮智能门铃/摄像头的开门事件监控、远程开锁等功能。

## 功能特性

- ✅ 实时推送监听（基于SSL/TLS）
- ✅ 开门事件监控（指纹、密码、锁事件）
- ✅ 门铃呼叫通知
- ✅ 设备在线/离线状态
- ✅ 多种报警事件（PIR移动侦测、低电量、温度报警等）
- ✅ 完全脱离Android系统运行
- ✅ 丰富的传感器实体（电池、WiFi信号、版本等）
- ✅ 支持多设备管理

## HACS安装

### 通过HACS安装（推荐）

1. 打开HACS
2. 进入 "集成"
3. 点击右上角三个点 → "自定义仓库"
4. 添加自定义仓库：
   - 仓库：`thedays/ha-dingding-smart`
   - 类别：集成
   - 完整URL：`https://github.com/thedays/ha-dingding-smart`
5. 点击 "添加"
6. 在集成列表中找到 "叮叮智能门铃"
7. 点击 "下载"
8. 重启Home Assistant

### 手动安装

1. 下载最新版本的 `dingding_smart.zip`
2. 解压到Home Assistant的 `custom_components` 目录
3. 重启Home Assistant

## 配置

### 添加集成

1. 打开Home Assistant
2. 进入 "设置" → "设备与服务"
3. 点击 "添加集成"
4. 搜索 "dingding" 或 "叮叮智能"
5. 填写配置信息：
   - 用户名：叮叮智能App的登录账号（手机号）
   - 密码：叮叮智能App的登录密码
   - 服务器区域：选择服务器所在区域（中国/欧洲/美国）
6. 点击 "提交"

### 配置选项

| 字段 | 说明 | 示例 | 必填 |
|------|------|------|------|
| 用户名 | 钉钉智能App的登录账号 | `13800138000` | 是 |
| 密码 | 钉钉智能App的登录密码 | `your_password` | 是 |
| 服务器区域 | 选择服务器所在区域 | `中国` / `欧洲` / `美国` | 是 |

## 传感器

集成会为每个设备创建以下传感器：

| 传感器名称 | 说明 | 单位 | 图标 |
|-----------|------|------|------|
| **最新开门** | 最新开门事件 | - | `mdi:door-open` |
| **状态** | 设备在线状态 | - | `mdi:check-circle` |
| **在线** | 设备在线状态（布尔值） | - | `mdi:lan-connect` |
| **电池电量** | 设备电池电量 | % | `mdi:battery` |
| **WiFi信号** | WiFi信号强度 | dBm | `mdi:wifi` |
| **版本** | 设备固件版本 | - | `mdi:information` |
| **UID** | 设备唯一标识符 | - | `mdi:identifier` |
| **在线类型** | 设备连接类型 | - | `mdi:network` |
| **最后更新** | 设备最后更新时间 | - | `mdi:clock` |

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

### 开门时发送通知

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

### 门铃呼叫时播放声音

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

### 设备离线时报警

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

### 电池电量低时发送通知

```yaml
automation:
  - alias: "门铃电池电量低提醒"
    trigger:
      - platform: numeric_state
        entity_id: sensor.xiongmaobbdejia_battery
        below: 30
    action:
      - service: notify.mobile_app_your_phone
        data:
          title: "门铃电池电量低"
          message: "门铃设备电池电量仅剩 {{ states('sensor.xiongmaobbdejia_battery') }}%，请及时充电！"
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

## 开发

### 项目结构

```
ha-dingding-smart/
├── custom_components/
│   └── dingding_smart/
│       ├── __init__.py          # 主集成文件
│       ├── config_flow.py       # 配置流程
│       ├── manifest.json        # 集成清单
│       ├── sensor.py            # 传感器实体
│       └── strings.json         # 本地化字符串
├── hacs.json                  # HACS配置
├── README.md                  # 本文件
├── LICENSE                    # 许可证
└── DASHBOARD_EXAMPLES.md      # 仪表盘配置示例
```

### 贡献

欢迎提交Issue和Pull Request！

### 许可证

MIT License - 详见 [LICENSE](LICENSE) 文件

## 致谢

- 感谢钉钉智能门铃设备的支持
- 基于逆向的Python推送实现
- Home Assistant社区的支持

## 免责声明

本项目仅供学习和研究使用。请遵守相关法律法规和设备使用条款。

## 更新日志

### v1.0.0 (2024-02-23)

- ✨ 初始版本发布
- ✅ 支持登录和设备列表获取
- ✅ 实时推送监听
- ✅ 开门事件监控
- ✅ 丰富的传感器实体
- ✅ 支持多设备管理
- ✅ 完整的仪表盘配置示例
