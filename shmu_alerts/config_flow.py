import voluptuous as vol
import homeassistant.helpers.config_validation as cv
from homeassistant import config_entries

from .const import DOMAIN, DISTRICTS

class SHMUConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    VERSION = 1

    async def async_step_user(self, user_input=None):
        if user_input is not None:
            return self.async_create_entry(title="SHMU výstrahy", data=user_input)

        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema({
                vol.Required("districts", default=[]): vol.All(cv.ensure_list, [vol.In(DISTRICTS.keys())])
            }),
        )

    async def async_step_options(self, user_input=None):
        if user_input is not None:
            return self.async_create_entry(title="SHMU výstrahy - úprava", data=user_input)

        return self.async_show_form(
            step_id="options",
            data_schema=vol.Schema({
                vol.Required("districts", default=[]): vol.All(cv.ensure_list, [vol.In(DISTRICTS.keys())])
            }),
        )
