"""叮叮智能门铃 - 二进制传感器实体"""
import logging
from datetime import datetime, timedelta

from homeassistant.components.binary_sensor import BinarySensorEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, Event, callback
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from . import DOMAIN, DingDingCoordinator, EVENT_DOOR_UNLOCK

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
):
    """设置二进制传感器实体"""
    coordinator = hass.data[DOMAIN][entry.entry_id]["coordinator"]
    devices = coordinator.devices

    entities = []

    # 为每个设备创建二进制传感器
    for device in devices:
        uid = device.get("uid", "")
        name = device.get("name", f"设备 {uid}")

        entities.extend(
            [
                DoorLockSensor(coordinator, uid, name),
                OutsideDoorUnlockSensor(coordinator, uid, name),
            ]
        )

    async_add_entities(entities)


class DoorLockSensor(CoordinatorEntity, BinarySensorEntity):
    """门内开锁状态传感器"""

    def __init__(self, coordinator: DingDingCoordinator, uid: str, name: str):
        super().__init__(coordinator)
        self._uid = uid
        self._name = name
        self._attr_unique_id = f"{DOMAIN}_{uid}_door_lock"
        self._attr_name = f"{name} 门内开锁状态"
        self._attr_icon = "mdi:door-closed"
        self._is_unlocked = False
        self._last_unlock_time = None
        self._cancel_timer = None

    @property
    def is_on(self):
        """返回门内开锁状态（True表示门内开锁）"""
        return self._is_unlocked

    @callback
    def _handle_door_unlock_event(self, event: Event):
        """处理门内开锁事件"""
        if event.data.get("uid") == self._uid:
            method = event.data.get("method", "unknown")
            
            # 只处理门内开锁事件
            if method == "inside_lock":
                self._is_unlocked = True
                self._last_unlock_time = datetime.now()
                method_display = "门内开锁"
                
                _LOGGER.info(
                    "门内开锁状态更新: %s - 开锁",
                    self._name
                )
                self.async_write_ha_state()
                
                # 取消之前的定时器
                if self._cancel_timer:
                    self._cancel_timer()
                
                # 5秒后自动恢复为关闭状态
                self._cancel_timer = self.hass.loop.call_later(
                    5, 
                    self._auto_lock
                )

    @callback
    def _auto_lock(self):
        """自动恢复为关闭状态"""
        self._is_unlocked = False
        _LOGGER.info("门内开锁状态更新: %s - 自动恢复为关闭", self._name)
        self.async_write_ha_state()
        self._cancel_timer = None

    @callback
    def _handle_coordinator_update(self) -> None:
        """处理协调器更新"""
        # 监听开门事件
        if not hasattr(self, "_event_listener"):
            self._event_listener = self.hass.bus.async_listen(
                EVENT_DOOR_UNLOCK, 
                self._handle_door_unlock_event
            )
        self.async_write_ha_state()

    async def async_added_to_hass(self):
        """当实体添加到Home Assistant时"""
        await super().async_added_to_hass()
        # 监听开门事件
        self._event_listener = self.hass.bus.async_listen(
            EVENT_DOOR_UNLOCK, 
            self._handle_door_unlock_event
        )


class OutsideDoorUnlockSensor(CoordinatorEntity, BinarySensorEntity):
    """门外开门状态传感器"""

    def __init__(self, coordinator: DingDingCoordinator, uid: str, name: str):
        super().__init__(coordinator)
        self._uid = uid
        self._name = name
        self._attr_unique_id = f"{DOMAIN}_{uid}_outside_door_unlock"
        self._attr_name = f"{name} 门外开锁状态"
        self._attr_icon = "mdi:door-open"
        self._is_unlocked = False
        self._last_unlock_time = None
        self._cancel_timer = None

    @property
    def is_on(self):
        """返回门外开门状态（True表示门外开锁）"""
        return self._is_unlocked

    @callback
    def _handle_door_unlock_event(self, event: Event):
        """处理门外开锁事件"""
        if event.data.get("uid") == self._uid:
            method = event.data.get("method", "unknown")
            
            # 只处理门外开锁事件（指纹、密码）
            if method in ["fingerprint", "password"]:
                self._is_unlocked = True
                self._last_unlock_time = datetime.now()
                
                method_display = method
                if method == "fingerprint":
                    method_display = "指纹开锁"
                elif method == "password":
                    method_display = "密码开锁"
                
                _LOGGER.info(
                    "门外开门状态更新: %s - 开锁 (方法: %s)",
                    self._name,
                    method_display
                )
                self.async_write_ha_state()
                
                # 取消之前的定时器
                if self._cancel_timer:
                    self._cancel_timer()
                
                # 5秒后自动恢复为关闭状态
                self._cancel_timer = self.hass.loop.call_later(
                    5, 
                    self._auto_reset
                )

    @callback
    def _auto_reset(self):
        """自动恢复为关闭状态"""
        self._is_unlocked = False
        _LOGGER.info("门外开门状态更新: %s - 自动恢复为关闭", self._name)
        self.async_write_ha_state()
        self._cancel_timer = None

    @callback
    def _handle_coordinator_update(self) -> None:
        """处理协调器更新"""
        # 监听开门事件
        if not hasattr(self, "_event_listener"):
            self._event_listener = self.hass.bus.async_listen(
                EVENT_DOOR_UNLOCK, 
                self._handle_door_unlock_event
            )
        self.async_write_ha_state()

    async def async_added_to_hass(self):
        """当实体添加到Home Assistant时"""
        await super().async_added_to_hass()
        # 监听开锁事件
        self.async_on_remove(
            self.hass.bus.async_listen(EVENT_DOOR_UNLOCK, self._handle_door_unlock_event)
        )

    async def async_will_remove_from_hass(self):
        """当实体从Home Assistant移除时"""
        # 取消定时器
        if self._cancel_timer:
            self._cancel_timer()
        await super().async_will_remove_from_hass()

    @property
    def extra_state_attributes(self):
        """获取额外属性"""
        attrs = {}
        for device in self.coordinator.devices:
            if device.get("uid") == self._uid:
                attrs["uid"] = device.get("uid")
                attrs["name"] = device.get("name")
                if self._last_unlock_time:
                    attrs["last_unlock_time"] = self._last_unlock_time.isoformat()
                attrs["last_unlock_method"] = device.get("last_unlock_method", "unknown")
                break
        return attrs
