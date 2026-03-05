"""
叮叮智能门铃 - Home Assistant集成
支持开门事件监控、远程开锁等功能
基于逆向的Python推送实现
"""
import asyncio
import json
import logging
import socket
import ssl
import struct
import threading
import time
import random
import platform
from dataclasses import dataclass
from typing import Any, Callable, Optional, Dict

import aiohttp
import voluptuous as vol

from homeassistant.config_entries import ConfigEntry, ConfigEntryNotReady
from homeassistant.const import (
    CONF_PASSWORD,
    CONF_USERNAME,
    Platform,
)
from homeassistant.core import HomeAssistant, Event, HomeAssistantError
from homeassistant.helpers import config_validation as cv
from homeassistant.helpers.entity import DeviceInfo
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator

_LOGGER = logging.getLogger(__name__)

DOMAIN = "dingding_smart"
PLATFORMS = [Platform.SENSOR, Platform.BINARY_SENSOR]

# 配置常量
CONF_SERVER_REGION = "server_region"
CONF_DEVICE_UID = "device_uid"
CONF_USER_ID = "user_id"
CONF_IMEI = "imei"
CONF_TOKEN = "token"
CONF_REFLASH_KEY = "reflash_key"
CONF_LOGOUT_STATUS = "logout_status"
CONF_TIME = "time"

# 服务器区域
REGION_CN = "cn"
REGION_EU = "eu"
REGION_US = "us"

# 服务器配置
SERVERS = {
    REGION_CN: {
        "api_host": "https://chniot.lancens.com:6448/",
        "push_host": "chnpush.lancens.com",
        "push_port": 11001,  # 推送端口
    },
    REGION_EU: {
        "api_host": "https://euriot.lancens.com:6448/",
        "push_host": "eurpush.lancens.com",
        "push_port": 11001,
    },
    REGION_US: {
        "api_host": "https://usaiot.lancens.com:6448/",
        "push_host": "usapush.lancens.com",
        "push_port": 11001,
    },
}

# 推送事件类型
PUSH_TYPE_PIR = "0"
PUSH_TYPE_CALL = "1"
PUSH_TYPE_FINGERPRINT_UNLOCK = "2"
PUSH_TYPE_PASSWORD_UNLOCK = "3"
PUSH_TYPE_LOW_POWER = "4"
PUSH_TYPE_UART = "5"
PUSH_TYPE_LOCK = "6"
PUSH_TYPE_LOW_TEMP_ALARM = "8"
PUSH_TYPE_HIGH_TEMP_ALARM = "9"
PUSH_TYPE_SOUND_ALARM = "10"
PUSH_TYPE_OFFLINE = "20"
PUSH_TYPE_ONLINE = "21"
PUSH_TYPE_TRANSFER = "100"

# Home Assistant事件
EVENT_DOOR_UNLOCK = f"{DOMAIN}_door_unlock"
EVENT_DOOR_CALL = f"{DOMAIN}_door_call"
EVENT_DOOR_OFFLINE = f"{DOMAIN}_door_offline"
EVENT_DOOR_ONLINE = f"{DOMAIN}_door_online"
EVENT_ALARM = f"{DOMAIN}_alarm"

CONFIG_SCHEMA = vol.Schema(
    {
        DOMAIN: vol.Schema(
            {
                vol.Required(CONF_USERNAME): cv.string,
                vol.Required(CONF_PASSWORD): cv.string,
                vol.Required(CONF_SERVER_REGION, default=REGION_CN): vol.In(
                    [REGION_CN, REGION_EU, REGION_US]
                ),
                vol.Optional(CONF_DEVICE_UID): cv.string,
                vol.Optional(CONF_USER_ID): cv.positive_int,
                vol.Optional(CONF_IMEI): cv.string,
            }
        )
    },
    extra=vol.ALLOW_EXTRA,
)


async def async_setup(hass: HomeAssistant, config: dict):
    """设置钉钉智能集成"""
    if DOMAIN not in config:
        return True

    hass.data.setdefault(DOMAIN, {})
    hass.data[DOMAIN]["config"] = config[DOMAIN]

    return True


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry):
    """设置配置项"""
    config = entry.data
    username = config[CONF_USERNAME]
    password = config[CONF_PASSWORD]
    region = config.get(CONF_SERVER_REGION, REGION_CN)
    device_uid = config.get(CONF_DEVICE_UID)
    user_id = config.get(CONF_USER_ID, 0)
    imei = config.get(CONF_IMEI)
    token = config.get(CONF_TOKEN)
    reflash_key = config.get(CONF_REFLASH_KEY)
    logout_status = config.get(CONF_LOGOUT_STATUS)
    time = config.get(CONF_TIME)

    # 创建API客户端
    api_client = DingDingAPI(username, password, region)
    
    # 从配置中加载持久化的token
    if token:
        api_client.token = token
        api_client.user_id = user_id
        api_client.reflash_key = reflash_key
        api_client.logout_status = logout_status
        api_client.time = time
        _LOGGER.info("从配置中加载token成功, 用户ID: %s", user_id)

    # 创建推送监听器（使用逆向的实现）
    push_listener = PushListener(
        hass,
        api_client,
        SERVERS[region]["push_host"],
        SERVERS[region]["push_port"],
        device_uid,
        user_id,
        imei,
    )

    # 创建协调器
    coordinator = DingDingCoordinator(hass, api_client, push_listener)

    hass.data.setdefault(DOMAIN, {})
    hass.data[DOMAIN][entry.entry_id] = {
        "api": api_client,
        "push": push_listener,
        "coordinator": coordinator,
    }

    # 尝试登录
    try:
        await coordinator.async_refresh()
        
        # 登录成功后更新配置，保存token
        if api_client.token:
            new_config = {
                CONF_USER_ID: api_client.user_id,
                CONF_TOKEN: api_client.token,
                CONF_REFLASH_KEY: api_client.reflash_key,
                CONF_LOGOUT_STATUS: api_client.logout_status,
                CONF_TIME: api_client.time,
            }
            # 合并现有配置
            updated_config = {**config, **new_config}
            # 使用正确的方法更新配置
            hass.config_entries.async_update_entry(entry, data=updated_config)
            _LOGGER.info("token已持久化保存")
    except Exception as err:
        _LOGGER.error("登录失败: %s", err)
        raise ConfigEntryNotReady from err

    # 设置平台
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

    # 启动推送监听
    await push_listener.async_start()

    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry):
    """卸载配置项"""
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    if unload_ok:
        data = hass.data[DOMAIN].pop(entry.entry_id)
        await data["push"].async_stop()

    return unload_ok


class DingDingAPI:
    """钉钉智能API客户端"""

    def __init__(self, username: str, password: str, region: str = REGION_CN):
        self.username = username
        self.password = password
        self.region = region
        self.token = None
        self.user_id = None
        self.reflash_key = None
        self.logout_status = None
        self.time = None
        self._session: Optional[aiohttp.ClientSession] = None

    @property
    def api_host(self) -> str:
        """获取API主机地址"""
        return SERVERS[self.region]["api_host"]

    async def _get_session(self) -> aiohttp.ClientSession:
        """获取或创建HTTP会话"""
        if self._session is None or self._session.closed:
            self._session = aiohttp.ClientSession()
        return self._session

    async def login(self) -> bool:
        """登录"""
        _LOGGER.info("=" * 60)
        _LOGGER.info("开始登录流程")
        _LOGGER.info("=" * 60)
        _LOGGER.info("用户名: %s", self.username)
        _LOGGER.info("API主机: %s", self.api_host)
        
        session = await self._get_session()
        url = f"{self.api_host}v1/api/user/login"

        headers = {
            "Accept": "application/json",
            "Content-Type": "application/json",
            "Connection": "close",
            "formal": "formal",
        }

        data = {"username": self.username, "password": self.password}

        try:
            _LOGGER.info("发送登录请求到: %s", url)
            async with session.post(url, headers=headers, json=data) as resp:
                _LOGGER.info("登录响应状态码: %s", resp.status)
                _LOGGER.info("登录响应头: %s", dict(resp.headers))
                
                if 200 <= resp.status < 300:
                    try:
                        result = await resp.json()
                        _LOGGER.info("登录响应内容: %s", result)
                        if isinstance(result, dict) and "token" in result:
                            # 只支持直接包含token的格式
                            self.token = result.get("token")
                            self.user_id = result.get("id")  # 使用id字段作为user_id
                            self.reflash_key = result.get("reflash_key")
                            self.logout_status = result.get("logout_status")
                            self.time = result.get("time")
                            _LOGGER.info("=" * 60)
                            _LOGGER.info("登录成功")
                            _LOGGER.info("=" * 60)
                            _LOGGER.info("用户ID: %s", self.user_id)
                            _LOGGER.info("Token: %s", self.token[:10] + "..." if self.token else "无")
                            _LOGGER.info("Token长度: %s", len(self.token) if self.token else 0)
                            _LOGGER.info("Reflash Key: %s", self.reflash_key)
                            _LOGGER.info("Logout Status: %s", self.logout_status)
                            _LOGGER.info("Time: %s", self.time)
                            _LOGGER.info("=" * 60)
                            return True
                        _LOGGER.error("登录响应格式错误，缺少token: %s", result)
                        return False
                    except Exception as e:
                        _LOGGER.error("解析登录响应失败: %s", e)
                        return False
                response_text = await resp.text()
                _LOGGER.error("登录失败: %s", response_text)
                return False
        except Exception as err:
            _LOGGER.error("登录异常: %s", err)
            return False

    async def get_device_list(self) -> list:
        """获取设备列表"""
        if not self.token:
            _LOGGER.info("token为空，开始登录")
            if not await self.login():
                _LOGGER.error("登录失败，无法获取设备列表")
                return []
        _LOGGER.info("使用token: %s", self.token[:10] + "..." if self.token else "无")

        session = await self._get_session()
        url = f"{self.api_host}v1/api/user/device"

        headers = {
            "baseUrl": "formal",
            "Accept": "application/json",
            "Content-Type": "application/json",
            "Connection": "close",
            "bundleid": "com.lancens.wxdoorbell",
            "Token": self.token
        }
        _LOGGER.info("请求头: %s", {k: v for k, v in headers.items() if k != "Token"})
        _LOGGER.info("Token头长度: %s", len(headers.get("Token", "")))
        _LOGGER.info("Token值: %s", self.token[:10] + "..." if self.token else "无")

        try:
            async with session.get(url, headers=headers) as resp:
                _LOGGER.info("获取设备列表响应状态码: %s", resp.status)
                _LOGGER.info("响应头: %s", dict(resp.headers))
                
                if 200 <= resp.status < 300:
                    # 先读取响应内容
                    response_text = await resp.text()
                    _LOGGER.info("响应内容: %s", response_text[:100] + "..." if len(response_text) > 100 else response_text)
                    
                    # 检查内容类型
                    content_type = resp.headers.get("Content-Type", "")
                    _LOGGER.info("内容类型: %s", content_type)
                    
                    # 尝试解析为JSON
                    try:
                        result = json.loads(response_text)
                        _LOGGER.info("成功解析为JSON")
                        # 检查响应内容是否包含错误
                        if isinstance(result, dict) and result.get("message") == "no token":
                            _LOGGER.warning("Token无效，尝试重新登录")
                            if await self.login():
                                _LOGGER.info("重新登录成功，新token: %s", self.token[:10] + "..." if self.token else "无")
                                headers["Token"] = self.token
                                async with session.get(url, headers=headers) as resp2:
                                    _LOGGER.info("重试获取设备列表响应状态码: %s", resp2.status)
                                    if resp2.status == 200:
                                        return await resp2.json()
                                    _LOGGER.error("重试获取设备列表失败: %s", await resp2.text())
                                    return []
                            _LOGGER.error("重新登录失败，无法获取设备列表")
                            return []
                        _LOGGER.info("返回设备列表")
                        return result
                    except json.JSONDecodeError:
                        _LOGGER.error("响应不是有效的JSON，内容类型: %s", content_type)
                        _LOGGER.error("响应内容: %s", response_text[:200] + "..." if len(response_text) > 200 else response_text)
                        return []
                elif resp.status in [401, 400]:
                    # 401: Unauthorized, 400: Bad Request (可能包含no token错误)
                    response_text = await resp.text()
                    _LOGGER.info("响应内容: %s", response_text)
                    
                    # 检查响应内容是否包含no token错误
                    if "no token" in response_text:
                        _LOGGER.warning("Token无效，尝试重新登录")
                        if await self.login():
                            _LOGGER.info("重新登录成功，新token: %s", self.token[:10] + "..." if self.token else "无")
                            headers["Token"] = self.token
                            async with session.get(url, headers=headers) as resp2:
                                _LOGGER.info("重试获取设备列表响应状态码: %s", resp2.status)
                                if resp2.status == 200:
                                    return await resp2.json()
                                _LOGGER.error("重试获取设备列表失败: %s", await resp2.text())
                                return []
                        _LOGGER.error("重新登录失败，无法获取设备列表")
                        return []
                    elif resp.status == 401:
                        # Token过期或无效，重新登录
                        _LOGGER.warning("Token已过期，尝试重新登录")
                        if await self.login():
                            # 重新登录成功，重试获取设备列表
                            _LOGGER.info("重新登录成功，新token: %s", self.token[:10] + "..." if self.token else "无")
                            headers["Token"] = self.token
                            async with session.get(url, headers=headers) as resp2:
                                _LOGGER.info("重试获取设备列表响应状态码: %s", resp2.status)
                                if resp2.status == 200:
                                    return await resp2.json()
                                _LOGGER.error("重试获取设备列表失败: %s", await resp2.text())
                                return []
                        _LOGGER.error("重新登录失败，无法获取设备列表")
                        return []
                    else:
                        _LOGGER.error("获取设备列表失败，状态码: %s, 响应: %s", resp.status, response_text)
                        return []
                else:
                    response_text = await resp.text()
                    _LOGGER.error("获取设备列表失败，状态码: %s, 响应: %s", resp.status, response_text)
                    return []
        except Exception as err:
            _LOGGER.error("获取设备列表异常: %s", err)
            return []

    async def close(self):
        """关闭会话"""
        if self._session and not self._session.closed:
            await self._session.close()
            self._session = None

    async def bind_push_token(self, push_token: str) -> bool:
        """绑定推送Token到服务器"""
        if not self.token:
            _LOGGER.error("Token为空，无法绑定推送Token")
            return False

        session = await self._get_session()
        
        # 绑定来电推送token
        bind_call_url = f"{self.api_host}v1/api/user/token"
        bind_call_data = {
            "push_token": push_token,
            "push_platform": "android",
            "language": "zh",
            "os_token": "",
            "os": "Android",
            "os_push_version": 1,
            "bundleid": "com.lancens.wxdoorbell",
            "phone_model": "phone:Xiaomi_Mi_10/App:钉钉智能_1.0.0/Android_11"
        }

        headers = {
            "baseUrl": "formal",
            "Accept": "application/json",
            "Content-Type": "application/json",
            "Connection": "close",
            "bundleid": "com.lancens.wxdoorbell",
            "Token": self.token
        }

        try:
            # 绑定来电推送token
            _LOGGER.info("绑定来电推送token...")
            async with session.post(bind_call_url, headers=headers, json=bind_call_data) as resp:
                if 200 <= resp.status < 300:
                    result = await resp.json()
                    _LOGGER.info("绑定来电推送token响应: %s", result)
                    if result.get("message") != "success":
                        _LOGGER.error("绑定来电推送token失败: %s", result)
                        return False
                else:
                    _LOGGER.error("绑定来电推送token失败: %s", await resp.text())
                    return False

            # 绑定消息推送token
            bind_notify_url = f"{self.api_host}v1/api/user/message/token"
            _LOGGER.info("绑定消息推送token...")
            async with session.post(bind_notify_url, headers=headers, json=bind_call_data) as resp:
                if 200 <= resp.status < 300:
                    result = await resp.json()
                    _LOGGER.info("绑定消息推送token响应: %s", result)
                    if result.get("message") != "success":
                        _LOGGER.error("绑定消息推送token失败: %s", result)
                        return False
                else:
                    _LOGGER.error("绑定消息推送token失败: %s", await resp.text())
                    return False

            _LOGGER.info("推送Token绑定成功")
            return True
        except Exception as err:
            _LOGGER.error("绑定推送Token异常: %s", err)
            return False


class PushListener:
    """推送监听器（基于逆向的Python实现）"""

    FLAG_PUSH_CLIENT_TOKEN = "token"
    keepAlive = True
    release = True

    # 命令常量
    CMD_HEARTBEAT = 0
    CMD_REGISTER = 1
    CMD_TOKEN = 2
    CMD_PUSH = 3

    def __init__(
        self,
        hass: HomeAssistant,
        api: DingDingAPI,
        push_host: str,
        push_port: int,
        device_uid: Optional[str] = None,
        user_id: int = 0,
        imei: Optional[str] = None,
    ):
        self.hass = hass
        self.api = api
        self.push_host = push_host
        self.push_port = push_port
        self.device_uid = device_uid
        self.user_id = user_id
        self.imei = imei
        self.push_token = None
        self.http_token = None

        self._push_thread: Optional[threading.Thread] = None
        self._ssl_socket: Optional[ssl.SSLSocket] = None
        self._socket_lock = threading.Lock()
        self._stop_event = threading.Event()
        self._ssl_context = self._create_ssl_context()
        self._bind_completed = False

        # 生成注册信息
        self._register_info = self._get_register_info()

    def _create_ssl_context(self):
        """创建自定义SSL安全上下文"""
        # 使用更基础的方式创建SSL上下文
        context = ssl.SSLContext()
        
        # 禁用证书验证（临时解决方案）
        context.check_hostname = False
        context.verify_mode = ssl.CERT_NONE
        
        # 启用所有TLS版本
        try:
            # 尝试使用TLSVersion常量
            context.min_version = ssl.TLSVersion.TLSv1
            context.max_version = ssl.TLSVersion.TLSv1_3
        except AttributeError:
            # 兼容旧版本Python
            context.min_version = ssl.TLSVersion.TLSv1 if hasattr(ssl, 'TLSVersion') else ssl.PROTOCOL_TLSv1
            context.max_version = ssl.TLSVersion.TLSv1_3 if hasattr(ssl, 'TLSVersion') else ssl.PROTOCOL_TLSv1_2
        
        # 禁用SSLv3
        context.options |= ssl.OP_NO_SSLv3
        
        # 禁用证书验证（再次确认）
        context.verify_mode = ssl.CERT_NONE
        context.check_hostname = False
        
        # 使用更宽松的密码套件
        try:
            context.set_ciphers('DEFAULT@SECLEVEL=1')
        except ssl.SSLError:
            # 如果设置失败，使用默认密码套件
            _LOGGER.warning("无法设置自定义密码套件，使用默认值")
        
        return context

    def _get_register_info(self) -> str:
        """获取注册信息"""
        # 使用真实的IMEI（如果提供）
        if self.imei:
            imei = self.imei
        else:
            imei = self._generate_random_string(12)
        
        # 生成随机IMSI
        imsi = self._generate_random_string(12)

        register_data = {
            "imei": imei,
            "imsi": imsi,
            "type": "Android",
            "brand": "Xiaomi",
            "bundle_id": "com.lancens.wxdoorbell",
        }

        return json.dumps(register_data, separators=(",", ":"))

    def _generate_random_string(self, length: int) -> str:
        """生成随机字符串"""
        return "".join(
            random.choices(
                "0123456789abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ",
                k=length,
            )
        )

    async def async_start(self):
        """启动推送监听"""
        if self._push_thread and self._push_thread.is_alive():
            return

        self._stop_event.clear()
        self._push_thread = threading.Thread(
            target=self._push_loop, name="DingDingPushThread", daemon=True
        )
        self._push_thread.start()
        _LOGGER.info("推送监听器已启动")

    async def async_stop(self):
        """停止推送监听"""
        self._stop_event.set()
        self._disconnect()

        if self._push_thread:
            self._push_thread.join(timeout=5)

        _LOGGER.info("推送监听器已停止")

    def _push_loop(self):
        """推送线程主循环"""
        PushListener.release = False
        _LOGGER.info("推送线程已启动")

        while not self._stop_event.is_set():
            try:
                # 建立连接
                if not self._connect():
                    time.sleep(2)
                    continue

                # 发送注册信息
                if not self._send_register():
                    self._disconnect()
                    continue

                # 主消息循环
                self._message_loop()

            except Exception as e:
                _LOGGER.error("推送循环异常: %s", e)
                self._disconnect()
                time.sleep(5)

        PushListener.release = True
        _LOGGER.info("推送线程已停止")

    def _connect(self) -> bool:
        """连接到推送服务器"""
        try:
            _LOGGER.info("连接到推送服务器: %s:%d", self.push_host, self.push_port)

            client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            client_socket.settimeout(10)

            # 创建SSL socket
            self._ssl_socket = self._ssl_context.wrap_socket(
                client_socket, server_hostname=self.push_host
            )

            # 建立连接
            self._ssl_socket.connect((self.push_host, self.push_port))
            self._ssl_socket.settimeout(130)

            _LOGGER.info("已连接到推送服务器")
            return True

        except ssl.SSLError as e:
            _LOGGER.error("SSL握手失败: %s", e)
            return False
        except socket.error as e:
            _LOGGER.error("连接失败: %s", e)
            return False
        except Exception as e:
            _LOGGER.error("连接异常: %s", e)
            return False

    def _disconnect(self):
        """断开连接"""
        with self._socket_lock:
            if self._ssl_socket:
                try:
                    self._ssl_socket.close()
                except:
                    pass
                self._ssl_socket = None

        _LOGGER.info("已断开连接")

    def _send_register(self) -> bool:
        """发送注册信息"""
        try:
            register_data = self._register_info.encode("utf-8")
            _LOGGER.info("发送注册信息: %s", self._register_info)
            result = self._send_message(self.CMD_REGISTER, register_data)
            if result:
                _LOGGER.info("注册信息发送成功")
            else:
                _LOGGER.error("注册信息发送失败")
            return result
        except Exception as e:
            _LOGGER.error("发送注册信息失败: %s", e)
            return False

    def _message_loop(self):
        """主消息处理循环"""
        while not self._stop_event.is_set() and self._ssl_socket:
            try:
                # 接收消息头（8字节）
                header = self._receive_data(8)
                if not header:
                    _LOGGER.warning("服务器关闭连接")
                    break

                # 解析命令和长度（小端序）
                cmd, length = struct.unpack("<II", header)
                _LOGGER.debug("收到命令: %d, 长度: %d", cmd, length)

                # 接收消息体
                data = self._receive_data(length) if length > 0 else b""

                # 处理消息
                self._handle_message(cmd, data)

                # 发送心跳响应
                if self._ssl_socket:
                    if not self._send_heartbeat():
                        _LOGGER.warning("发送心跳响应失败，连接可能已断开")
                        break

            except socket.timeout:
                _LOGGER.info("发送心跳包")
                if self._ssl_socket:
                    if not self._send_heartbeat():
                        _LOGGER.warning("发送心跳包失败，连接可能已断开")
                        break
                else:
                    _LOGGER.warning("连接已断开，无法发送心跳包")
                    break
            except (ConnectionResetError, BrokenPipeError):
                _LOGGER.warning("连接丢失")
                break
            except Exception as e:
                _LOGGER.error("消息循环异常: %s", e)
                break

    def _handle_message(self, cmd: int, data: bytes):
        """处理接收到的消息"""
        try:
            _LOGGER.debug("收到消息: cmd=%d, data_length=%d", cmd, len(data))
            
            if cmd == self.CMD_TOKEN:
                _LOGGER.info("收到CMD_TOKEN命令")
                token_data = json.loads(data.decode("utf-8"))
                _LOGGER.debug("Token数据: %s", token_data)
                token = token_data.get(self.FLAG_PUSH_CLIENT_TOKEN, "")
                self.push_token = token
                _LOGGER.info("收到token: %s", token)
                
                # 收到token后，绑定到服务器
                asyncio.run_coroutine_threadsafe(
                    self._bind_push_token(),
                    self.hass.loop
                )

            elif cmd == self.CMD_PUSH:
                _LOGGER.info("收到CMD_PUSH命令")
                push_data = data.decode("utf-8")
                push_info = json.loads(push_data)
                _LOGGER.info("收到推送: %s", push_info)

                # 在Home Assistant事件循环中处理推送
                self.hass.loop.call_soon_threadsafe(
                    lambda: self._handle_push_info(push_info)
                )

            elif cmd == self.CMD_HEARTBEAT:
                _LOGGER.debug("收到CMD_HEARTBEAT命令")
                _LOGGER.debug("收到心跳响应")

            else:
                _LOGGER.warning("未知命令: %d", cmd)

        except json.JSONDecodeError:
            _LOGGER.error("JSON解析失败")
        except UnicodeDecodeError:
            _LOGGER.error("数据解码失败")

    async def _bind_push_token(self):
        """绑定推送token到服务器"""
        if not self.push_token:
            _LOGGER.error("推送token为空，无法绑定")
            return

        if not self.api.token:
            _LOGGER.error("API token为空，无法绑定推送token")
            return

        if self._bind_completed:
            _LOGGER.debug("推送token已绑定，跳过重复绑定")
            return

        _LOGGER.info("开始绑定推送token到服务器")
        success = await self.api.bind_push_token(self.push_token)
        if success:
            _LOGGER.info("推送token绑定成功")
            self._bind_completed = True
        else:
            _LOGGER.error("推送token绑定失败")

    def _handle_push_info(self, push_info: dict):
        """处理推送信息（在Home Assistant事件循环中）"""
        event_type = push_info.get("type")
        uid = push_info.get("uid")
        message = push_info.get("message", "")
        alert = push_info.get("alert", "")
        name = push_info.get("name", "")

        # 检查aps字段中的消息内容
        if "aps" in push_info:
            aps = push_info.get("aps", {})
            if message == "" and "message" in aps:
                message = aps.get("message", "")
            if alert == "" and "alert" in aps:
                alert = aps.get("alert", "")
            if name == "" and "name" in aps:
                name = aps.get("name", "")

        # 过滤设备UID
        if self.device_uid and uid != self.device_uid:
            return

        _LOGGER.info("处理推送事件: type=%s, uid=%s, message=%s, alert=%s, name=%s", event_type, uid, message, alert, name)

        # 触发Home Assistant事件
        if event_type == PUSH_TYPE_FINGERPRINT_UNLOCK:
            self._fire_event(
                EVENT_DOOR_UNLOCK,
                {
                    "uid": uid,
                    "method": "fingerprint",
                    "message": message,
                    "alert": alert,
                    "name": name,
                },
            )
        elif event_type == PUSH_TYPE_PASSWORD_UNLOCK:
            self._fire_event(
                EVENT_DOOR_UNLOCK,
                {
                    "uid": uid,
                    "method": "password",
                    "message": message,
                    "alert": alert,
                    "name": name,
                },
            )
        elif event_type == PUSH_TYPE_LOCK:
            # 门锁事件 - 从message或alert中判断开锁方法
            unlock_method = "lock"
            combined_message = message + " " + alert
            if "指纹开锁" in combined_message:
                unlock_method = "fingerprint"
            elif "密码开锁" in combined_message:
                unlock_method = "password"
            elif "门内开锁" in combined_message:
                unlock_method = "inside_lock"
                
            self._fire_event(
                EVENT_DOOR_UNLOCK,
                {
                    "uid": uid,
                    "method": unlock_method,
                    "message": message,
                    "alert": alert,
                    "name": name,
                },
            )
        elif event_type == PUSH_TYPE_CALL:
            self._fire_event(
                EVENT_DOOR_CALL,
                {
                    "uid": uid,
                    "message": message,
                    "alert": alert,
                    "name": name,
                },
            )
        elif event_type == PUSH_TYPE_OFFLINE:
            self._fire_event(
                EVENT_DOOR_OFFLINE,
                {
                    "uid": uid,
                    "message": message,
                    "alert": alert,
                    "name": name,
                },
            )
        elif event_type == PUSH_TYPE_ONLINE:
            self._fire_event(
                EVENT_DOOR_ONLINE,
                {
                    "uid": uid,
                    "message": message,
                    "alert": alert,
                    "name": name,
                },
            )
        elif event_type in [
            PUSH_TYPE_PIR,
            PUSH_TYPE_LOW_POWER,
            PUSH_TYPE_LOW_TEMP_ALARM,
            PUSH_TYPE_HIGH_TEMP_ALARM,
            PUSH_TYPE_SOUND_ALARM,
        ]:
            self._fire_event(
                EVENT_ALARM,
                {
                    "uid": uid,
                    "type": event_type,
                    "message": message,
                    "alert": alert,
                    "name": name,
                },
            )

    def _fire_event(self, event_type: str, event_data: dict):
        """触发Home Assistant事件"""
        self.hass.bus.async_fire(event_type, event_data)
        _LOGGER.debug("触发事件: %s, 数据: %s", event_type, event_data)

    async def _bind_push_token(self):
        """绑定推送Token到服务器"""
        if self._bind_completed:
            return
        
        if not self.push_token:
            _LOGGER.warning("没有可用的push_token，无法绑定")
            return

        try:
            _LOGGER.info("开始绑定推送Token到服务器")
            
            # 步骤1: 登录获取http_token
            if not self.api.token:
                await self.api.login()
            
            self.http_token = self.api.token
            if not self.http_token:
                _LOGGER.error("登录失败，无法获取http_token")
                return

            _LOGGER.info("登录成功，获取到http_token")

            # 步骤2: 绑定来电推送token
            call_success = await self._bind_call_push_token()
            if not call_success:
                _LOGGER.error("绑定来电推送token失败，停止绑定流程")
                return

            # 步骤3: 绑定消息推送token
            notify_success = await self._bind_notify_push_token()
            if not notify_success:
                _LOGGER.error("绑定消息推送token失败，停止绑定流程")
                return

            self._bind_completed = True
            _LOGGER.info("推送Token绑定完成")

        except Exception as e:
            _LOGGER.error("绑定推送Token失败: %s", e)

    async def _bind_call_push_token(self):
        """绑定来电推送token"""
        if not self.http_token or not self.push_token:
            return

        url = f"{self.api.api_host}v1/api/user/token"
        
        headers = {
            "baseUrl": "formal",
            "Accept": "application/json",
            "Content-Type": "application/json",
            "Connection": "close",
            "bundleid": "com.lancens.wxdoorbell",
            "Token": self.http_token
        }

        data = {
            "push_token": self.push_token,
            "push_platform": "android",
            "language": "zh",
            "os_token": "",
            "os": "Android",
            "os_push_version": 1,
            "bundleid": "com.lancens.wxdoorbell",
            "phone_model": "phone:Xiaomi_Mi_10/App:钉钉智能_1.0.0/Android_11"
        }

        try:
            session = await self.api._get_session()
            async with session.post(url, json=data, headers=headers) as resp:
                if 200 <= resp.status < 300:
                    result = await resp.json()
                    if result.get("message") == "success":
                        _LOGGER.info("绑定来电推送token成功")
                        return True
                    else:
                        _LOGGER.error("绑定来电推送token失败: %s", result)
                        return False
                else:
                    _LOGGER.error("绑定来电推送token失败: HTTP %s", resp.status)
                    return False
        except Exception as e:
            _LOGGER.error("绑定来电推送token异常: %s", e)
            return False

    async def _bind_notify_push_token(self):
        """绑定消息推送token"""
        if not self.http_token or not self.push_token:
            return

        url = f"{self.api.api_host}v1/api/user/message/token"
        
        headers = {
            "baseUrl": "formal",
            "Accept": "application/json",
            "Content-Type": "application/json",
            "Connection": "close",
            "bundleid": "com.lancens.wxdoorbell",
            "Token": self.http_token
        }

        data = {
            "push_token": self.push_token,
            "push_platform": "android",
            "language": "zh",
            "os_token": "",
            "os": "Android",
            "os_push_version": 1,
            "bundleid": "com.lancens.wxdoorbell",
            "phone_model": "phone:Xiaomi_Mi_10/App:钉钉智能_1.0.0/Android_11"
        }

        try:
            session = await self.api._get_session()
            async with session.post(url, json=data, headers=headers) as resp:
                if 200 <= resp.status < 300:
                    result = await resp.json()
                    if result.get("message") == "success":
                        _LOGGER.info("绑定消息推送token成功")
                        return True
                    else:
                        _LOGGER.error("绑定消息推送token失败: %s", result)
                        return False
                else:
                    _LOGGER.error("绑定消息推送token失败: HTTP %s", resp.status)
                    return False
        except Exception as e:
            _LOGGER.error("绑定消息推送token异常: %s", e)
            return False

    def _send_message(self, cmd: int, data: bytes) -> bool:
        """发送消息到服务器"""
        with self._socket_lock:
            if not self._ssl_socket:
                return False

            try:
                # 构造消息头（小端序）
                header = struct.pack("<II", cmd, len(data))
                self._ssl_socket.sendall(header + data)
                _LOGGER.debug("发送命令: %d, 长度: %d", cmd, len(data))
                return True
            except (OSError, BrokenPipeError) as e:
                _LOGGER.error("发送失败: %s", e)
                self._disconnect()
                return False

    def _send_heartbeat(self) -> bool:
        """发送心跳包"""
        return self._send_message(self.CMD_HEARTBEAT, b"")

    def _receive_data(self, length: int) -> bytes:
        """接收指定长度的数据"""
        data = b""
        while len(data) < length:
            chunk = self._ssl_socket.recv(length - len(data))
            if not chunk:
                return None
            data += chunk
        return data


class DingDingCoordinator(DataUpdateCoordinator):
    """钉钉智能数据协调器"""

    def __init__(
        self,
        hass: HomeAssistant,
        api: DingDingAPI,
        push_listener: PushListener,
    ):
        self.api = api
        self.push_listener = push_listener
        self.devices = []
        self.last_unlock_event = None

        super().__init__(
            hass,
            _LOGGER,
            name=DOMAIN,
            update_interval=None,
        )

    async def _async_update_data(self) -> dict:
        """更新数据"""
        # 登录
        if not self.api.token:
            if not await self.api.login():
                _LOGGER.error("登录失败，无法获取设备列表")
                return {"devices": [], "last_unlock": self.last_unlock_event}

        # 获取设备列表
        self.devices = await self.api.get_device_list()

        return {
            "devices": self.devices,
            "last_unlock": self.last_unlock_event,
        }

    def update_unlock_event(self, event_data: dict):
        """更新最新开门事件"""
        self.last_unlock_event = event_data
        # 在Home Assistant事件循环中更新监听器
        self.hass.loop.call_soon_threadsafe(
            lambda: self.async_update_listeners()
        )
