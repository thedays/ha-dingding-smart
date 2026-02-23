"""钉钉智能门铃 - 配置流"""
import logging
import voluptuous as vol

from homeassistant import config_entries
from homeassistant.const import CONF_USERNAME, CONF_PASSWORD
from homeassistant.data_entry_flow import FlowResult

from . import DOMAIN, REGION_CN, REGION_EU, REGION_US, CONF_SERVER_REGION

_LOGGER = logging.getLogger(__name__)

STEP_USER_DATA_SCHEMA = vol.Schema(
    {
        vol.Required(CONF_USERNAME): str,
        vol.Required(CONF_PASSWORD): str,
        vol.Required(CONF_SERVER_REGION, default=REGION_CN): vol.In(
            [REGION_CN, REGION_EU, REGION_US]
        ),
    }
)


class DingDingConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """钉钉智能配置流"""

    VERSION = 1

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """处理用户步骤"""
        errors = {}

        if user_input is not None:
            try:
                # 验证登录
                from . import DingDingAPI

                api = DingDingAPI(
                    user_input[CONF_USERNAME],
                    user_input[CONF_PASSWORD],
                    user_input[CONF_SERVER_REGION],
                )

                success = await api.login()
                if not success:
                    errors["base"] = "auth_error"
                else:
                    # 获取设备列表
                    devices = await api.get_device_list()
                    if not devices:
                        errors["base"] = "no_devices"
                    else:
                        # 保存配置
                        await self.async_set_unique_id(user_input[CONF_USERNAME])
                        self._abort_if_unique_id_configured()

                        return self.async_create_entry(
                            title="钉钉智能门铃",
                            data=user_input,
                        )

            except Exception as err:
                _LOGGER.error("配置失败: %s", err)
                errors["base"] = "unknown_error"

        return self.async_show_form(
            step_id="user",
            data_schema=STEP_USER_DATA_SCHEMA,
            errors=errors,
        )
