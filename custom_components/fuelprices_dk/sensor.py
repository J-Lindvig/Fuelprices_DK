from __future__ import annotations

import asyncio
import logging

from homeassistant.const import ATTR_ATTRIBUTION
from .const import (
    CONF_CLIENT,
    CONF_UPDATE_INTERVAL,
    CONF_PLATFORM,
    CREDITS,
    DOMAIN,
)

from datetime import timedelta

from homeassistant.components.sensor import (
    SensorEntity,
    SensorStateClass,
    SensorDeviceClass,
)
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator

_LOGGER: logging.Logger = logging.getLogger(__package__)
_LOGGER = logging.getLogger(__name__)


async def async_setup_platform(hass, config, async_add_entities, discovery_info=None):

    updateInterval = hass.data[DOMAIN][CONF_UPDATE_INTERVAL]

    # Define a update function
    async def async_update_data():
        # Retrieve the client stored in the hass data stack
        fuelPrices = hass.data[DOMAIN][CONF_CLIENT]
        # Loop through the fuelcompanies and call the refresh function
        # Sleep for 3 seconds
        for company in fuelPrices.getCompanies():
            await hass.async_add_executor_job(company.refreshPrices)
            await asyncio.sleep(3)

    # Create a coordinator
    coordinator = DataUpdateCoordinator(
        hass,
        _LOGGER,
        name=CONF_PLATFORM,
        update_method=async_update_data,
        update_interval=timedelta(minutes=updateInterval),
    )

    # Immediate refresh
    await coordinator.async_request_refresh()

    # Add the sensors to Home Assistant
    entities = []
    fuelPrices = hass.data[DOMAIN][CONF_CLIENT]
    for companyKey in fuelPrices.getCompanyKeys():
        for productKey in fuelPrices.getCompanyProductsKeys(companyKey):
            # Create a instance of the FuelPriceSensor and append it to the list
            entities.append(FuelPriceSensor(hass, coordinator, companyKey, productKey))
    # Add all the sensors to Home Assistant
    async_add_entities(entities)


class FuelPriceSensor(SensorEntity):
    def __init__(self, hass, coordinator, companyKey, productKey) -> None:
        self._hass = hass
        self._coordinator = coordinator
        self._fuelCompany = hass.data[DOMAIN][CONF_CLIENT].getCompany(companyKey)
        self._companyName = self._fuelCompany.getName()
        self._productName = self._fuelCompany.getProductName(productKey)
        self._productKey = productKey
        self._icon = "mdi:gas-station"
        self._attr_state_class = SensorStateClass.MEASUREMENT

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
    def state(self) -> float:
        return float(self._fuelCompany.getProductPrice(self._productKey))

    @property
    def extra_state_attributes(self):
        attr = {}
        attr["company_name"] = self._companyName
        attr["source"] = self._fuelCompany.getURL()
        attr["product_name"] = self._productName
        attr["product_type"] = self._productKey
        attr["price_type"] = self._fuelCompany.getPriceType()
        attr["last_update"] = self._fuelCompany.getProductLastUpdate(self._productKey)
        attr[ATTR_ATTRIBUTION] = CREDITS
        return attr

    @property
    def unique_id(self):
        return self._companyName + " " + self._productKey

    @property
    def device_class(self):
        return SensorDeviceClass.MONETARY

    @property
    def state_class(self) -> str:
        """Return the state class of the sensor."""
        return self._attr_state_class

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
