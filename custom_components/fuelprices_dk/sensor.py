from __future__ import annotations

import logging

from homeassistant.const import DEVICE_CLASS_MONETARY, ATTR_ATTRIBUTION
from .const import (
    CONF_CLIENT,
    CONF_PLATFORM,
    CREDITS,
    DOMAIN,
    UPDATE_INTERVAL,
)


from datetime import timedelta

from homeassistant.components.sensor import SensorEntity
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator

_LOGGER: logging.Logger = logging.getLogger(__package__)
_LOGGER = logging.getLogger(__name__)


async def async_setup_platform(hass, config, async_add_entities, discovery_info=None):
    """Setup sensor platform"""

    async def async_update_data():
        # try:
        fuelPrices = hass.data[DOMAIN][CONF_CLIENT]
        await hass.async_add_executor_job(fuelPrices.refresh)
        # except Exception as e:
        #    raise UpdateFailed(f"Error communicating with server: {e}")

    coordinator = DataUpdateCoordinator(
        hass,
        _LOGGER,
        name=CONF_PLATFORM,
        update_method=async_update_data,
        update_interval=timedelta(minutes=UPDATE_INTERVAL),
    )

    # Immediate refresh
    await coordinator.async_request_refresh()

    entities = []
    fuelPrices = hass.data[DOMAIN][CONF_CLIENT]
    for companyKey in fuelPrices.getCompanyKeys():
        for productKey in fuelPrices.getCompanyProductsKeys(companyKey):
            entities.append(GasPriceSensor(hass, coordinator, companyKey, productKey))
    async_add_entities(entities)


class GasPriceSensor(SensorEntity):
    def __init__(self, hass, coordinator, companyKey, productKey) -> None:
        self._hass = hass
        self._coordinator = coordinator
        self._fuelCompany = hass.data[DOMAIN][CONF_CLIENT].getCompany(companyKey)
        self._companyName = self._fuelCompany.getName()
        self._productName = self._fuelCompany.getProductName(productKey)
        self._productKey = productKey
        self._icon = "mdi:gas-station"

        # Some companies put their name into the product, which leads to double names
        # Strip the name and whitespaces
        if self._companyName in self._productName:
            self._productName = self._productName.replace(self._companyName, "").strip()

    @property
    def name(self):
        return self._companyName + " " + self._productName

    @property
    def icon(self):
        return self._icon

    @property
    def state(self):
        return self._fuelCompany.getProductPrice(self._productKey)

    @property
    def extra_state_attributes(self):
        attr = {}
        attr["company_name"] = self._companyName
        attr["source"] = self._fuelCompany.getURL()
        attr["product_name"] = self._productName
        attr["price_type"] = self._fuelCompany.getPriceType()
        attr["last_update"] = self._fuelCompany.getLastUpdate()
        attr[ATTR_ATTRIBUTION] = CREDITS
        return attr

    @property
    def unique_id(self):
        return self._companyName + " " + self._productKey

    @property
    def device_class(self):
        return DEVICE_CLASS_MONETARY

    @property
    def should_poll(self):
        """No need to poll. Coordinator notifies entity of updates."""
        return False

    @property
    def available(self):
        """Return if entity is available."""
        return self._coordinator.last_update_success

    async def async_update(self):
        """Update the entity. Only used by the generic entity update service."""
        await self._coordinator.async_request_refresh()

    async def async_added_to_hass(self):
        """When entity is added to hass."""
        self.async_on_remove(
            self._coordinator.async_add_listener(self.async_write_ha_state)
        )
