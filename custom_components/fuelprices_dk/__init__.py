from __future__ import annotations

import logging

from .fuelprices_dk_api import fuelprices

from .const import (
    DOMAIN,
    CONF_CLIENT,
    CONF_FUELCOMPANIES,
    CONF_FUELTYPES,
    CONF_PLATFORM,
)

_LOGGER: logging.Logger = logging.getLogger(__package__)
_LOGGER = logging.getLogger(__name__)


async def async_setup(hass, config):
    conf = config.get(DOMAIN)
    if conf is None:
        return True

    fuelCompanies = conf.get(CONF_FUELCOMPANIES, [])
    fuelTypes = conf.get(CONF_FUELTYPES, [])

    fuelPrices = fuelprices()
    fuelPrices.loadCompanies(fuelCompanies, fuelTypes)
    hass.data[DOMAIN] = {CONF_CLIENT: fuelPrices}

    # Add sensors
    hass.async_create_task(
        hass.helpers.discovery.async_load_platform(CONF_PLATFORM, DOMAIN, conf, config)
    )

    # Initialization was successful.
    return True
