import re
import aiohttp
from datetime import timedelta
from homeassistant.helpers.entity import Entity
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.core import HomeAssistant
from homeassistant.config_entries import ConfigEntry
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .const import DOMAIN, DISTRICTS, ALERT_TYPES

URL = "https://www.shmu.sk/sk/?page=987&id=&d=0&jav=&roll=#tabs"

async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
):
    districts = entry.data.get("districts", [])
    session = aiohttp.ClientSession()
    coordinator = SHMUDataCoordinator(hass, session, districts)
    await coordinator.async_config_entry_first_refresh()

    entities = []
    for district in districts:
        for alert_type in ALERT_TYPES.values():
            entities.append(SHMUAlertSensor(district, alert_type, coordinator))

    async_add_entities(entities)

class SHMUAlertSensor(Entity):
    def __init__(self, district: str, alert_type: str, coordinator):
        self._district = district
        self._alert_type = alert_type
        self.coordinator = coordinator
        self._attr_name = f"SHMU {district} {alert_type.replace('_', ' ').title()}"
        self._attr_unique_id = f"shmu_{district.lower()}_{alert_type}"
        self._attr_native_unit_of_measurement = "stupen"

    @property
    def available(self):
        return self.coordinator.last_update_success

    @property
    def state(self):
        data = self.coordinator.data.get(self._district, {})
        return data.get(self._alert_type, 0)

    async def async_update(self):
        await self.coordinator.async_request_refresh()

class SHMUDataCoordinator(DataUpdateCoordinator):
    def __init__(self, hass, session, districts):
        super().__init__(
            hass,
            name="SHMU Alerts Coordinator",
            update_interval=timedelta(minutes=10),
        )
        self.session = session
        self.districts = districts

    async def _async_update_data(self):
        try:
            async with self.session.get(URL) as resp:
                html = await resp.text()
        except Exception as err:
            raise UpdateFailed(f"Error fetching SHMU page: {err}")

        data = {d: {} for d in self.districts}

        for district in self.districts:
            regex = rf"'{district}':\s*'(.*?)'"
            match = re.search(regex, html, re.DOTALL)
            if not match:
                continue
            raw = match.group(1)
            for key, alert_type in ALERT_TYPES.items():
                if f"{key}" in raw:
                    level_match = re.search(r"Stupeň:\s*<strong>(\d)\.<", raw)
                    if level_match:
                        level = int(level_match.group(1))
                        data[district][alert_type] = level
        return data
