from __future__ import annotations

import logging

from .fuelprices_dk_api import FuelPrices

from .const import (
    DOMAIN,
    CONF_CLIENT,
    CONF_FUELCOMPANIES,
    CONF_FUELTYPES,
    CONF_UPDATE_INTERVAL,
    CONF_PLATFORM,
    UPDATE_INTERVAL,
)

_LOGGER: logging.Logger = logging.getLogger(__package__)
_LOGGER = logging.getLogger(__name__)


async def async_setup(hass, config):
    # Get the configuration
    conf = config.get(DOMAIN)
    # If no config, abort
    if conf is None:
        return True

    # Extract companies and fuueltypes from the config, defult to empty list
    fuel_companies = conf.get(CONF_FUELCOMPANIES, [])
    fuel_types = conf.get(CONF_FUELTYPES, [])
    update_interval = conf.get(CONF_UPDATE_INTERVAL, UPDATE_INTERVAL)

    _LOGGER.debug("fuelCompanies: %s", fuel_companies)
    _LOGGER.debug("fuelTypes: %s", fuel_types)

    # Initialize a instance of the fuelprices API
    fuel_prices = FuelPrices()
    # Load the data using the config
    fuel_prices.load_companies(fuel_companies, fuel_types)
    # Store the client in the hass data stack
    hass.data[DOMAIN] = {
        CONF_CLIENT: fuel_prices,
        CONF_UPDATE_INTERVAL: update_interval
    }

    # Add sensors
    hass.async_create_task(
        hass.helpers.discovery.async_load_platform(
            CONF_PLATFORM, DOMAIN, conf, config)
    )

    # Initialization was successful.
    return True
