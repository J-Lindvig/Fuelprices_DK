from __future__ import annotations

import logging
from datetime import datetime

import requests
from .fuelprices_dk_parsers import FuelParser  # Module containing parsers

_LOGGER: logging.Logger = logging.getLogger(__package__)
_LOGGER = logging.getLogger(__name__)

DEFAULT_PRICE_TYPE = "pump"
DIESEL = "diesel"
DIESEL_PLUS = "diesel+"
ELECTRIC = "electric"
OCTANE_95 = "oktan 95"
OCTANE_95_PLUS = "oktan 95+"
OCTANE_100 = "oktan 100"
FUEL_COMPANIES = {
    "circlek": {
        "name": "Circle K",
        "url": "https://www.circlek.dk/priser",
        "products": {
            OCTANE_95: {"name": "miles95."},
            OCTANE_95_PLUS: {"name": "miles+95."},
            DIESEL: {"name": "miles Diesel."},
            DIESEL_PLUS: {"name": "miles+ Diesel."},
            ELECTRIC: {"name": "El Lynlader."},
        },
    },
    "f24": {
        "name": "F24",
        "url": "https://www.f24.dk/-/api/PriceViewProduct/GetPriceViewProducts",
        "products": {
            OCTANE_95: {"name": "GoEasy 95 E10", "ProductCode": 22253},
            OCTANE_95_PLUS: {"name": "GoEasy 95 Extra E5", "ProductCode": 22603},
            DIESEL: {"name": "GoEasy Diesel", "ProductCode": 24453},
            DIESEL_PLUS: {"name": "GoEasy Diesel Extra", "ProductCode": 24338},
        },
    },
    "goon": {
        "name": "Go' on",
        "url": "https://goon.nu/priser/#Aktuellelistepriser",
        "products": {
            OCTANE_95: {"name": "Blyfri 95", "ocr_crop": ["58", "232", "134", "46"]},
            DIESEL: {"name": "Transportdiesel", "ocr_crop": ["58", "289", "134", "46"]},
        },
    },
    "ingo": {
        "name": "ingo",
        "url": "https://www.ingo.dk/br%C3%A6ndstofpriser/aktuelle-br%C3%A6ndstofpriser",
        "products": {
            OCTANE_95: {"name": "Benzin 95"},
            OCTANE_95_PLUS: {"name": "UPGRADE 95"},
            DIESEL: {"name": "Diesel"},
        },
    },
    "oil": {
        "name": "OIL! tank & go",
        "url": "https://www.oil-tankstationer.dk/de-gaeldende-braendstofpriser/",
        "products": {
            OCTANE_95: {"name": "95 E10"},
            OCTANE_95_PLUS: {"name": "PREMIUM 98"},
            DIESEL: {"name": "Diesel"},
        },
    },
    "ok": {
        "name": "OK",
        "url": "https://www.ok.dk/offentlig/produkter/braendstof/priser/vejledende-standerpriser",
        "products": {
            OCTANE_95: {"name": "Blyfri 95"},
            OCTANE_100: {"name": "Oktan 100"},
            DIESEL: {"name": "Diesel"},
        },
    },
    "q8": {
        "name": "Q8",
        "url": "https://www.q8.dk/-/api/PriceViewProduct/GetPriceViewProducts",
        "products": {
            OCTANE_95: {"name": "GoEasy 95 E10", "ProductCode": 22251},
            OCTANE_95_PLUS: {"name": "GoEasy 95 Extra E5", "ProductCode": 22601},
            DIESEL: {"name": "GoEasy Diesel", "ProductCode": 24451},
            DIESEL_PLUS: {"name": "GoEasy Diesel Extra", "ProductCode": 24337},
        },
    },
    "shell": {
        "name": "Shell",
        "url": "https://shellservice.dk/wp-json/shell-wp/v2/daily-prices",
        "products": {
            OCTANE_95: {"name": "Shell FuelSave 95 oktan"},
            OCTANE_100: {"name": "Shell V-Power 100 oktan"},
            DIESEL: {"name": "Shell FuelSave Diesel"},
            DIESEL_PLUS: {"name": "Shell V-Power Diesel"},
        },
    },
}


class FuelPrices:
    """Class to manage fuel prices from different companies."""

    def __init__(self):
        self._fuel_companies = {}

    def load_companies(self, company_keys, product_keys):
        """Load fuel companies and their products.

        Args:
            companyKeys (list): List of company keys to load. If empty, load all companies.
            productKeys (list): List of product keys to load. If empty, load all products.
        """

        # If no companies is specified, use ALL companies
        if not company_keys:
            company_keys = FUEL_COMPANIES.keys()

        # If no product is specified, use ALL products
        if not product_keys:
            product_keys = self._get_product_keys()

        # Loop through all the companyKeys
        for company_key in company_keys:
            if company_key in FUEL_COMPANIES.keys():
                _LOGGER.debug(
                    "Adding fuelcompany: %s", FUEL_COMPANIES[company_key]["name"]
                )

                # Loop through all the products and remove the ones NOT specified
                for product_key in list(FUEL_COMPANIES[company_key]["products"].keys()):
                    if product_key not in product_keys:
                        del FUEL_COMPANIES[company_key]["products"][product_key]
                    else:
                        _LOGGER.debug(
                            "Adding product to %s: %s",
                            FUEL_COMPANIES[company_key]["name"],
                            FUEL_COMPANIES[company_key]["products"][product_key]["name"],
                        )

                self._fuel_companies[company_key] = FuelCompany(
                    company_key,
                    FUEL_COMPANIES[company_key]["name"],
                    FUEL_COMPANIES[company_key]["url"],
                    FUEL_COMPANIES[company_key]["products"],
                    FuelParser(),
                )

    # Return a list of unique productKeys
    def _get_product_keys(self):
        # Prepare a empty list
        product_keys = []
        # Loop through all the companies
        for company in FUEL_COMPANIES.values():
            # Add a list of the companys productKeys to the list
            product_keys.extend(list(company["products"].keys()))
        # Typecast the list to a set to remove duplicates
        product_keys = set(product_keys)
        # Return the set as a list
        return list(product_keys)

    def refresh(self):
        """
        Refreshes the prices for all companies.
        """
        for company in self.get_companies():
            company.refresh_prices()

    def get_company(self, company_key) -> FuelCompany:
        """
        Retrieves the fuel company information based on the provided company key.

        Args:
            company_key (str): The key of the fuel company.

        Returns:
            dict: The fuel company information.

        Raises:
            KeyError: If the provided company key does not exist.
        """
        if self._company_exists(company_key):
            return self._fuel_companies[company_key]

        raise KeyError(f"Company key {company_key} does not exist")

    def get_company_keys(self):
        """
        Returns the keys of the fuel companies stored in the _fuel_companies dictionary.

        Returns:
            list: A list of keys representing the fuel companies.
        """
        return self._fuel_companies.keys()

    def get_companies(self):
        """
        Returns a list of all fuel companies.

        Returns:
            list: A list of all fuel companies.
        """
        return self._fuel_companies.values()

    def get_company_name(self, company_key):
        """
        Get the name of the fuel company based on the company key.

        Args:
            company_key (str): The key of the fuel company.

        Returns:
            str: The name of the fuel company.

        Raises:
            KeyError: If the company key does not exist.
        """
        if self._company_exists(company_key):
            return self._fuel_companies[company_key].get_name()

        raise KeyError(f"Company key {company_key} does not exist")

    # def get_company_prices(self, company_key):
    #     """
    #     Get the prices for a specific fuel company.

    #     Args:
    #         company_key (str): The key of the fuel company.

    #     Returns:
    #         dict: A dictionary containing the prices for the fuel company.

    #     Raises:
    #         KeyError: If the company key does not exist.
    #     """
    #     if self._company_exists(company_key):
    #         return self._fuel_companies[company_key].get_prices()

    #     raise KeyError(f"Company key {company_key} does not exist")

    def get_company_products_keys(self, company_key) -> list[str]:
        """
        Returns the product keys for a given company.

        Args:
            company_key (str): The key of the company.

        Returns:
            list: A list of product keys for the company.

        Raises:
            KeyError: If the company key does not exist.
        """
        if self._company_exists(company_key):
            return self._fuel_companies[company_key].get_products_keys()

        raise KeyError(f"Company key {company_key} does not exist")

    def _company_exists(self, company_key):
        return company_key in self.get_company_keys()


class FuelCompany:
    """
    Represents a fuel company with its key, name, URL, products, parser, and price type.

    Attributes:
        _key (str): Key of the company in the dictionary.
        _name (str): Name of the company.
        _url (str): URL to the site with prices.
        _products (dict): Dictionary with products and prices.
        _parser (obj): Instance of the parser module.
        _priceType (str): Default type of prices.
    """

    def __init__(self, key, name, url, products, parser):
        self._key = key  # Key of the company in the dict
        self._name = name  # Name of the company
        self._url = url  # URL to site with prices
        self._products = products  # Dictionary with products and prices
        self._parser = parser  # Instance of the parser module
        self._price_type = DEFAULT_PRICE_TYPE  # Default type of prices

    def get_name(self):
        return self._name

    def get_url(self):
        return self._url

    # Refresh the company's prices
    def refresh_prices(self):
        """
        Refreshes the company's prices by running the function from the parser module
        with the same name as the company's key. Updates the dictionary with products
        with the returned data.
        """
        try:
            _LOGGER.debug("Refreshing prices from: %s", self._name)
            self._products = getattr(self._parser, self._key)(
                self._url, self._products)
            _LOGGER.debug("products: %s", self._products)
            self._price_type = self._products.pop(
                "priceType", DEFAULT_PRICE_TYPE)
        except requests.exceptions.HTTPError as e:
            _LOGGER.error("Error refreshing prices from %s: %s", self._name, e)
        except requests.exceptions.JSONDecodeError as e:
            _LOGGER.error(
                "Error parsing response JSON from %s: %s", self._name, e)

    def get_products_keys(self):
        return self._products.keys()

    def get_product_name(self, product_key):
        return self._products[product_key]["name"]

    def get_product_price(self, product_key):
        """
        Get the price of a specific product.

        Args:
            product_key (str): The key of the product.

        Returns:
            float: The price of the product.

        """
        _LOGGER.debug("productDict: %s", self._products[product_key])
        return self._products[product_key]["price"]

    def get_product_last_update(self, product_key):
        return self._products[product_key]["lastUpdate"]

    def get_price_type(self):
        return self._price_type
