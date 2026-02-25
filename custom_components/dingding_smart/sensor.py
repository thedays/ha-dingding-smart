"""钉钉智能门铃 - 传感器实体"""
import logging
from typing import Any

from homeassistant.components.sensor import SensorEntity, SensorDeviceClass
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import (
    PERCENTAGE,
    SIGNAL_STRENGTH_DECIBELS_MILLIWATT,
)
from homeassistant.core import HomeAssistant, Event
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from . import DOMAIN, DingDingCoordinator, EVENT_DOOR_UNLOCK

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
):
    """设置传感器实体"""
    coordinator = hass.data[DOMAIN][entry.entry_id]["coordinator"]
    devices = coordinator.devices

    entities = []

    # 为每个设备创建传感器
    for device in devices:
        uid = device.get("uid", "")
        name = device.get("name", f"设备 {uid}")

        entities.extend(
            [
                LastUnlockSensor(coordinator, uid, name),
                DeviceStatusSensor(coordinator, uid, name),
                DeviceOnlineSensor(coordinator, uid, name),
                DeviceBatterySensor(coordinator, uid, name),
                DeviceWifiSignalSensor(coordinator, uid, name),
                DeviceVersionSensor(coordinator, uid, name),
                DeviceUidSensor(coordinator, uid, name),
                DeviceOnlineTypeSensor(coordinator, uid, name),
                DeviceUpdateTimeSensor(coordinator, uid, name),
            ]
        )

    if not entities:
        _LOGGER.warning("未找到设备，未创建传感器")

    async_add_entities(entities)

    # 监听开门事件
    def handle_unlock_event(event: Event):
        """处理开门事件"""
        event_data = event.data
        coordinator.update_unlock_event(event_data)

    hass.bus.async_listen(EVENT_DOOR_UNLOCK, handle_unlock_event)


class LastUnlockSensor(CoordinatorEntity, SensorEntity):
    """最新开门事件传感器"""

    def __init__(self, coordinator: DingDingCoordinator, uid: str, name: str):
        super().__init__(coordinator)
        self._uid = uid
        self._name = name
        self._attr_unique_id = f"{DOMAIN}_{uid}_last_unlock"
        self._attr_name = f"{name} 最新开门"
        self._attr_icon = "mdi:door-open"

    @property
    def native_value(self):
        """获取传感器值"""
        event = self.coordinator.last_unlock_event
        if event and event.get("uid") == self._uid:
            method = event.get("method", "unknown")
            message = event.get("message", "")
            return f"{method}: {message}"
        return "无记录"

    @property
    def extra_state_attributes(self):
        """获取额外属性"""
        event = self.coordinator.last_unlock_event
        if event and event.get("uid") == self._uid:
            return {
                "method": event.get("method"),
                "message": event.get("message"),
                "alert": event.get("alert"),
                "name": event.get("name"),
            }
        return {}


class DeviceStatusSensor(CoordinatorEntity, SensorEntity):
    """设备状态传感器"""

    def __init__(self, coordinator: DingDingCoordinator, uid: str, name: str):
        super().__init__(coordinator)
        self._uid = uid
        self._name = name
        self._attr_unique_id = f"{DOMAIN}_{uid}_status"
        self._attr_name = f"{name} 状态"
        self._attr_icon = "mdi:check-circle"

    @property
    def native_value(self):
        """获取传感器值"""
        for device in self.coordinator.devices:
            if device.get("uid") == self._uid:
                return "在线"
        return "离线"

    @property
    def extra_state_attributes(self):
        """获取额外属性"""
        for device in self.coordinator.devices:
            if device.get("uid") == self._uid:
                return {
                    "uid": device.get("uid"),
                    "name": device.get("name"),
                    "product": device.get("product"),
                    "wifi": device.get("wifi"),
                    "timezone": device.get("time_zone"),
                }
        return {}


class DeviceOnlineSensor(CoordinatorEntity, SensorEntity):
    """设备在线状态传感器"""

    def __init__(self, coordinator: DingDingCoordinator, uid: str, name: str):
        super().__init__(coordinator)
        self._uid = uid
        self._name = name
        self._attr_unique_id = f"{DOMAIN}_{uid}_online"
        self._attr_name = f"{name} 在线"
        self._attr_icon = "mdi:lan-connect"

    @property
    def native_value(self):
        """获取传感器值"""
        for device in self.coordinator.devices:
            if device.get("uid") == self._uid:
                return True
        return False

    @property
    def extra_state_attributes(self):
        """获取额外属性"""
        for device in self.coordinator.devices:
            if device.get("uid") == self._uid:
                return {
                    "uid": device.get("uid"),
                    "name": device.get("name"),
                }
        return {}


class DeviceBatterySensor(CoordinatorEntity, SensorEntity):
    """设备电池电量传感器"""

    def __init__(self, coordinator: DingDingCoordinator, uid: str, name: str):
        super().__init__(coordinator)
        self._uid = uid
        self._name = name
        self._attr_unique_id = f"{DOMAIN}_{uid}_battery"
        self._attr_name = f"{name} 电池电量"
        self._attr_icon = "mdi:battery"
        self._attr_native_unit_of_measurement = PERCENTAGE
        self._attr_device_class = SensorDeviceClass.BATTERY

    @property
    def native_value(self):
        """获取传感器值"""
        for device in self.coordinator.devices:
            if device.get("uid") == self._uid:
                battery = device.get("battery", 0)
                return battery
        return None

    @property
    def extra_state_attributes(self):
        """获取额外属性"""
        for device in self.coordinator.devices:
            if device.get("uid") == self._uid:
                return {
                    "battery2": device.get("battery2"),
                    "battery_display_enabled": device.get("bat_display_en", 0),
                }
        return {}


class DeviceWifiSignalSensor(CoordinatorEntity, SensorEntity):
    """设备WiFi信号传感器"""

    def __init__(self, coordinator: DingDingCoordinator, uid: str, name: str):
        super().__init__(coordinator)
        self._uid = uid
        self._name = name
        self._attr_unique_id = f"{DOMAIN}_{uid}_wifi_signal"
        self._attr_name = f"{name} WiFi信号"
        self._attr_icon = "mdi:wifi"
        self._attr_native_unit_of_measurement = SIGNAL_STRENGTH_DECIBELS_MILLIWATT
        self._attr_device_class = SensorDeviceClass.SIGNAL_STRENGTH

    @property
    def native_value(self):
        """获取传感器值"""
        for device in self.coordinator.devices:
            if device.get("uid") == self._uid:
                rssi = device.get("rssi", 0)
                return rssi
        return None

    @property
    def extra_state_attributes(self):
        """获取额外属性"""
        for device in self.coordinator.devices:
            if device.get("uid") == self._uid:
                rssi = device.get("rssi", 0)
                signal_quality = "优秀"
                if rssi > -50:
                    signal_quality = "优秀"
                elif rssi > -60:
                    signal_quality = "良好"
                elif rssi > -70:
                    signal_quality = "一般"
                else:
                    signal_quality = "较差"
                
                return {
                    "rssi": rssi,
                    "signal_quality": signal_quality,
                    "wifi_level": device.get("wifi"),
                }
        return {}


class DeviceVersionSensor(CoordinatorEntity, SensorEntity):
    """设备版本传感器"""

    def __init__(self, coordinator: DingDingCoordinator, uid: str, name: str):
        super().__init__(coordinator)
        self._uid = uid
        self._name = name
        self._attr_unique_id = f"{DOMAIN}_{uid}_version"
        self._attr_name = f"{name} 版本"
        self._attr_icon = "mdi:information"

    @property
    def native_value(self):
        """获取传感器值"""
        for device in self.coordinator.devices:
            if device.get("uid") == self._uid:
                version = device.get("current_version", "未知")
                return version
        return "未知"

    @property
    def extra_state_attributes(self):
        """获取额外属性"""
        for device in self.coordinator.devices:
            if device.get("uid") == self._uid:
                return {
                    "current_version": device.get("current_version"),
                    "latest_version": device.get("latest_version"),
                    "update_available": device.get("current_version") != device.get("latest_version"),
                }
        return {}


class DeviceUidSensor(CoordinatorEntity, SensorEntity):
    """设备UID传感器"""

    def __init__(self, coordinator: DingDingCoordinator, uid: str, name: str):
        super().__init__(coordinator)
        self._uid = uid
        self._name = name
        self._attr_unique_id = f"{DOMAIN}_{uid}_uid"
        self._attr_name = f"{name} UID"
        self._attr_icon = "mdi:identifier"

    @property
    def native_value(self):
        """获取传感器值"""
        return self._uid

    @property
    def extra_state_attributes(self):
        """获取额外属性"""
        for device in self.coordinator.devices:
            if device.get("uid") == self._uid:
                return {
                    "uid": device.get("uid"),
                    "device_id": device.get("id"),
                    "name": device.get("name"),
                }
        return {}


class DeviceOnlineTypeSensor(CoordinatorEntity, SensorEntity):
    """设备在线类型传感器"""

    def __init__(self, coordinator: DingDingCoordinator, uid: str, name: str):
        super().__init__(coordinator)
        self._uid = uid
        self._name = name
        self._attr_unique_id = f"{DOMAIN}_{uid}_online_type"
        self._attr_name = f"{name} 在线类型"
        self._attr_icon = "mdi:network"

    @property
    def native_value(self):
        """获取传感器值"""
        for device in self.coordinator.devices:
            if device.get("uid") == self._uid:
                online_type = device.get("online_type", 0)
                type_map = {
                    0: "未知",
                    1: "WiFi",
                    2: "有线",
                    3: "4G",
                    20: "WiFi",
                }
                return type_map.get(online_type, f"类型{online_type}")
        return "未知"

    @property
    def extra_state_attributes(self):
        """获取额外属性"""
        for device in self.coordinator.devices:
            if device.get("uid") == self._uid:
                return {
                    "online_type": device.get("online_type"),
                    "device_type": device.get("device"),
                }
        return {}


class DeviceUpdateTimeSensor(CoordinatorEntity, SensorEntity):
    """设备更新时间传感器"""

    def __init__(self, coordinator: DingDingCoordinator, uid: str, name: str):
        super().__init__(coordinator)
        self._uid = uid
        self._name = name
        self._attr_unique_id = f"{DOMAIN}_{uid}_update_time"
        self._attr_name = f"{name} 最后更新"
        self._attr_icon = "mdi:clock"

    @property
    def native_value(self):
        """获取传感器值"""
        for device in self.coordinator.devices:
            if device.get("uid") == self._uid:
                update_time = device.get("dev_update_time", "")
                return update_time
        return "未知"

    @property
    def extra_state_attributes(self):
        """获取额外属性"""
        for device in self.coordinator.devices:
            if device.get("uid") == self._uid:
                return {
                    "update_time": device.get("dev_update_time"),
                    "time": device.get("time"),
                    "timezone": device.get("time_zone"),
                }
        return {}
