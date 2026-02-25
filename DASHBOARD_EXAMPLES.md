# 叮叮智能门铃 - 仪表盘配置示例

## 概述

本文件展示了如何在Home Assistant仪表盘中显示叮叮智能门铃的设备信息。

## 可用的传感器

为每个设备创建以下传感器：

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

## 仪表盘配置示例

### 方法1：使用Lovelace UI编辑器

1. 打开Home Assistant
2. 进入 "概览" (Overview)
3. 点击右上角三个点 → "编辑仪表盘"
4. 点击右上角 "+" 添加卡片
5. 选择 "手动卡片" 或使用以下配置

### 方法2：直接编辑YAML配置

在 `lovelace.yaml` 或通过UI编辑器添加以下卡片：

```yaml
title: 叮叮智能门铃
views:
  - title: 设备概览
    path: default_view
    cards:
      # 设备信息卡片
      - type: entities
        title: 熊猫BB的家 - 设备信息
        show_header_toggle: false
        entities:
          - entity: sensor.xiongmaobbdejia_status
            name: 状态
          - entity: sensor.xiongmaobbdejia_online
            name: 在线
          - entity: sensor.xiongmaobbdejia_online_type
            name: 在线类型
          - entity: sensor.xiongmaobbdejia_uid
            name: 设备UID

      # 电池和信号卡片
      - type: gauge
        title: 电池电量
        entity: sensor.xiongmaobbdejia_battery
        min: 0
        max: 100
        unit: '%'
        severity:
          green: 60
          yellow: 30
          red: 10

      - type: gauge
        title: WiFi信号
        entity: sensor.xiongmaobbdejia_wifi_signal
        min: -100
        max: -30
        unit: 'dBm'
        severity:
          green: -60
          yellow: -70
          red: -80

      # 版本信息卡片
      - type: entities
        title: 版本信息
        show_header_toggle: false
        entities:
          - entity: sensor.xiongmaobbdejia_version
            name: 当前版本
          - entity: sensor.xiongmaobbdejia_version
            attribute: latest_version
            name: 最新版本
          - entity: sensor.xiongmaobbdejia_version
            attribute: update_available
            name: 有更新

      # 最新开门事件卡片
      - type: entities
        title: 最新开门事件
        show_header_toggle: false
        entities:
          - entity: sensor.xiongmaobbdejia_last_unlock
            name: 最新开门
          - entity: sensor.xiongmaobbdejia_last_unlock
            attribute: method
            name: 开门方式
          - entity: sensor.xiongmaobbdejia_last_unlock
            attribute: message
            name: 消息
          - entity: sensor.xiongmaobbdejia_last_unlock
            attribute: alert
            name: 提示

      # WiFi信号详情卡片
      - type: entities
        title: WiFi信号详情
        show_header_toggle: false
        entities:
          - entity: sensor.xiongmaobbdejia_wifi_signal
            name: 信号强度
          - entity: sensor.xiongmaobbdejia_wifi_signal
            attribute: signal_quality
            name: 信号质量
          - entity: sensor.xiongmaobbdejia_wifi_signal
            attribute: wifi_level
            name: WiFi等级

      # 最后更新时间卡片
      - type: entities
        title: 更新时间
        show_header_toggle: false
        entities:
          - entity: sensor.xiongmaobbdejia_update_time
            name: 最后更新
          - entity: sensor.xiongmaobbdejia_update_time
            attribute: time
            name: 首次添加时间
          - entity: sensor.xiongmaobbdejia_update_time
            attribute: timezone
            name: 时区

  - title: 历史记录
    path: history
    cards:
      # 历史图表
      - type: history-graph
        title: 电池电量历史
        entities:
          - entity: sensor.xiongmaobbdejia_battery
            name: 电池电量

      - type: history-graph
        title: WiFi信号历史
        entities:
          - entity: sensor.xiongmaobbdejia_wifi_signal
            name: WiFi信号

      - type: logbook
        title: 开门事件日志
        entities:
          - sensor.xiongmaobbdejia_last_unlock
        hours_to_show: 24
```

## 使用Mushroom卡片（推荐）

如果你安装了Mushroom Cards，可以使用更美观的卡片：

```yaml
title: 钉钉智能门铃
views:
  - title: 设备概览
    path: default_view
    cards:
      # 使用Mushroom卡片
      - type: custom:mushroom-chips-card
        chips:
          - type: entity
            entity: sensor.xiongmaobbdejia_status
            icon: mdi:check-circle
            content_info: none
          - type: entity
            entity: sensor.xiongmaobbdejia_battery
            icon: mdi:battery
            content_info: state
          - type: entity
            entity: sensor.xiongmaobbdejia_wifi_signal
            icon: mdi:wifi
            content_info: state

      - type: custom:mushroom-entity-card
        entity: sensor.xiongmaobbdejia_status
        name: 设备状态
        icon: mdi:doorbell
        icon_color: green

      - type: custom:mushroom-entity-card
        entity: sensor.xiongmaobbdejia_battery
        name: 电池电量
        icon: mdi:battery
        icon_color: |
          {% if states(config.entity) | int > 60 %}
            green
          {% elif states(config.entity) | int > 30 %}
            orange
          {% else %}
            red
          {% endif %}

      - type: custom:mushroom-entity-card
        entity: sensor.xiongmaobbdejia_wifi_signal
        name: WiFi信号
        icon: mdi:wifi
        icon_color: |
          {% if states(config.entity) | int > -60 %}
            green
          {% elif states(config.entity) | int > -70 %}
            orange
          {% else %}
            red
          {% endif %}
```

## 自动化示例

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

### 设备离线时发送通知

```yaml
automation:
  - alias: "门铃设备离线提醒"
    trigger:
      - platform: state
        entity_id: sensor.xiongmaobbdejia_online
        to: 'off'
        for:
          minutes: 5
    action:
      - service: notify.mobile_app_your_phone
        data:
          title: "门铃设备离线"
          message: "门铃设备已离线超过5分钟，请检查网络连接！"
```

### WiFi信号差时发送通知

```yaml
automation:
  - alias: "门铃WiFi信号差提醒"
    trigger:
      - platform: numeric_state
        entity_id: sensor.xiongmaobbdejia_wifi_signal
        below: -70
        for:
          minutes: 10
    action:
      - service: notify.mobile_app_your_phone
        data:
          title: "门铃WiFi信号差"
          message: "门铃设备WiFi信号较弱（{{ states('sensor.xiongmaobbdejia_wifi_signal') }} dBm），请检查WiFi连接！"
```

## 提示

1. **实体ID格式**: 传感器实体ID格式为 `sensor.{设备名称拼音}_{传感器类型}`
   - 例如: `sensor.xiongmaobbdejia_battery`
   - 可以在Home Assistant的"开发者工具" → "状态"中查看实际实体ID

2. **多设备支持**: 如果有多个设备，每个设备都会创建一组传感器

3. **自动更新**: 传感器数据会自动更新，无需手动刷新

4. **历史记录**: 可以在Home Assistant的"历史记录"页面查看传感器的历史数据

5. **自定义卡片**: 可以根据需要自定义卡片样式和布局
