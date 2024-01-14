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

    update_interval = hass.data[DOMAIN][CONF_UPDATE_INTERVAL]

    # Define a update function
    async def async_update_data():
        # Retrieve the client stored in the hass data stack
        fuel_prices = hass.data[DOMAIN][CONF_CLIENT]
        # Loop through the fuelcompanies and call the refresh function
        # Sleep for 3 seconds
        for _, company in fuel_prices.companies.items():
            await hass.async_add_executor_job(company.refresh_prices)
            await asyncio.sleep(3)

    # Create a coordinator
    coordinator = DataUpdateCoordinator(
        hass,
        _LOGGER,
        name=CONF_PLATFORM,
        update_method=async_update_data,
        update_interval=timedelta(minutes=update_interval),
    )

    # Immediate refresh
    await coordinator.async_request_refresh()

    # Add the sensors to Home Assistant
    entities = []
    fuel_prices = hass.data[DOMAIN][CONF_CLIENT]

    for company_key, company in fuel_prices.companies.items():

        for product_key, _ in company.products.items():

            # Create a instance of the FuelPriceSensor and append it to the list
            entities.append(FuelPriceSensor(
                hass, coordinator, company_key, product_key))
    # Add all the sensors to Home Assistant
    async_add_entities(entities)


class FuelPriceSensor(SensorEntity):
    def __init__(self, hass, coordinator, company_key, product_key) -> None:
        self._hass = hass
        self._coordinator = coordinator
        self._fuel_company = hass.data[DOMAIN][CONF_CLIENT].companies[company_key]
        self._company_name = self._fuel_company.name
        self._product_name = self._fuel_company.products[product_key]["name"]
        self._product_key = product_key
        self._icon = "mdi:gas-station"
        self._attr_state_class = SensorStateClass.MEASUREMENT

        # Some companies put their name into the product, which leads to double names
        # Strip the name and whitespaces
        if self._company_name in self._product_name:
            self._product_name = self._product_name.replace(
                self._company_name, "").strip()

    @property
    def name(self):
        return self._company_name + " " + self._product_name

    @property
    def icon(self):
        return self._icon

    @property
    def state(self) -> float:
        return float(self._fuel_company.products[self._product_key]["price"])

    @property
    def extra_state_attributes(self):
        attr = {}
        attr["company_name"] = self._company_name
        attr["source"] = self._fuel_company.url
        attr["product_name"] = self._product_name
        attr["product_type"] = self._product_key
        attr["price_type"] = self._fuel_company.price_type
        attr["last_update"] = self._fuel_company.products[self._product_key]["last_update"]
        attr[ATTR_ATTRIBUTION] = CREDITS
        return attr

    @property
    def unique_id(self):
        return self._company_name + " " + self._product_key

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
