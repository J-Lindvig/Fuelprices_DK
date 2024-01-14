from __future__ import annotations

import logging
from datetime import datetime, timedelta
import shutil
import subprocess
from bs4 import BeautifulSoup as BS
import requests
import pytz

from .const import (
    PATH,
)

DK_TZ = pytz.timezone("Europe/Copenhagen")

# from .fuelprices_dk_parsers import FuelParser  # Module containing parsers

_LOGGER: logging.Logger = logging.getLogger(__package__)
_LOGGER = logging.getLogger(__name__)

DEFAULT_PRICE_TYPE = "pump"
# DIESEL = "diesel"
# DIESEL_PLUS = "diesel+"
# ELECTRIC = "electric"
OCTANE_95 = "oktan 95"
# OCTANE_95_PLUS = "oktan 95+"
# OCTANE_100 = "oktan 100"


class FuelPrices:
    """Class to manage fuel prices from different companies."""

    # All the supported companies
    company_keys: [str] = [
        'circlek',
        'f24',
        'goon',
        'ingo',
        'oil',
        'ok',
        'q8',
        'shell'
    ]

    _companies: dict[str, FuelCompany]

    def __init__(self):
        self._companies = {}

    def load_companies(self, subscribe_companies: [str], subscribe_products: [str]):
        """Load fuel companies and their products"""

        if not subscribe_companies:
            subscribe_companies = self.company_keys

        for k in subscribe_companies:
            c = FuelCompany.factory(k, subscribe_products)
            if c is not None:
                self._companies[k] = c

    @property
    def companies(self) -> dict[str, FuelCompany]:
        return self._companies

    def refresh(self):
        """
        Refreshes the prices for all companies.
        """
        for _, company in self.companies.items():
            company.refresh_prices()


class FuelCompany:
    """
    Represents a fuel company.

    Attributes:
        _name (str): The name of the fuel company.
        _url (str): The URL of the fuel company's website.
        _products (dict[str, dict]): A dictionary of products offered by the fuel company.
        _key (str): The key representing the fuel company.
    """

    _name: str | None = None
    _url: str | None = None
    _products: dict[str, dict]
    # _key: str | None = None

    _price_type: str = DEFAULT_PRICE_TYPE

    """ 
    The keys of the products that we subscribe to, e.g. "oktan 95", "oktan 100", "diesel", "diesel+"
    """

    def __init__(
            self, subscribe_products: [str] = None
    ):

        self._session = requests.Session()
        self._session.headers.update({
            'User-Agent': "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            + "AppleWebKit/537.36 (KHTML, like Gecko) "
            + "Chrome/80.0.3987.149 Safari/537.36"
        })

        # if subscribe_products is supplied, remove all products from _products that
        # are not in subscribe_products
        if subscribe_products is not None:
            self._products = {
                k: v for k, v in self._products.items() if k in subscribe_products
            }

        # Also, make a simpler, reverse look index of the products
        self.products_name_key_idx = {
            v['name']: k for k, v in self._products.items()
        }

    @classmethod
    def factory(cls, company_key: str, subscribe_products: [str]) -> FuelCompany | None:
        """
        Factory method to create an instance of a FuelCompany subclass based on the company_key.

        Args:
            company_key (str): The key representing the fuel company.
            product_keys ([str]): The keys representing the products.

        Returns:
            FuelCompany | None: FuelCompany subclass instance if company_key is valid or None
        """
        class_name = __class__.__name__+company_key.capitalize()

        if class_name in globals():
            fuel_company = globals()[class_name](subscribe_products)
            return fuel_company

        _LOGGER.warning("Unknown company key: %s", company_key)
        return None

    @property
    def name(self):
        return self._name

    @property
    def products(self):
        return self._products

    @property
    def url(self):
        return self._url

    @property
    def price_type(self):
        return self._price_type

    def refresh_prices(self):
        """
        Refreshes the company's prices by running the function from the parser module
        with the same name as the company's key. Updates the dictionary with products
        with the returned data.
        """
        _LOGGER.warning("Refreshing prices from %s unsupported", self.name)

    def _get_website(self):
        r = self._session.get(self._url, timeout=5)
        r.raise_for_status()
        return r

    def _get_html_soup(self, r, parser="html.parser"):
        if r.text:
            return BS(r.text, parser)
        return None

    def _clean_product_name(self, product_name):
        product_name = product_name.replace("Beskrivelse: ", "")
        product_name = product_name.strip()
        if product_name[-1] == ".":
            product_name = product_name[:-1]

        return product_name

    def _clean_price(self, price):
        price = str(price)  # Typecast to String
        # Remove 'Pris inkl. moms: '
        price = price.replace("Pris inkl. moms: ", "")
        price = price.replace(" kr.", "")  # Remove ' kr.'
        price = price.replace(",", ".")  # Replace ',' with '.'
        price = price.strip()  # Remove leading or trailing whitespaces
        # Return the price with 2 decimals
        return f"{float(price):.2f}"

    def _set_price(self, product_key, price_string):
        self._products[product_key]["price"] = self._clean_price(price_string)
        dt = datetime.now(DK_TZ)
        self._products[product_key]["last_update"] = dt.strftime(
            "%d/%m/%Y, %H:%M:%S")

    def _get_data_from_table(self, product_col, price_col):
        r = self._get_website()
        html = self._get_html_soup(r)

        rows = html.find_all("tr")

        for row in rows:
            cells = row.findAll("td")
            if cells:
                product_name = self._clean_product_name(
                    cells[product_col].text)
                if (
                    product_name in self.products_name_key_idx.keys()
                        and 'price' not in self.products[self.products_name_key_idx[product_name]]
                ):
                    self._set_price(
                        self.products_name_key_idx[product_name], cells[price_col].text
                    )

    def _download_file(self, url, filename, path):
        r = self._session.get(url, stream=True)
        r.raise_for_status()
        with open(path + filename, "wb") as file:
            for block in r.iter_content(chunk_size=1024):
                if block:
                    file.write(block)


class FuelCompanyOk(FuelCompany):

    _name: str = "OK"
    _url: str = "https://www.ok.dk/offentlig/produkter/braendstof/priser/vejledende-standerpriser"
    _products: dict[str, dict] = {
        OCTANE_95: {
            "name": "Blyfri 95"
        },
        "oktan 100": {
            "name": "Oktan 100"
        },
        "diesel": {
            "name": "Diesel"
        }
    }

    def refresh_prices(self):
        """
        Parses the OK website to extract fuel prices for the given products.

        Args:
            url (str): The URL of the OK website.
            products (dict): A dictionary containing the products to extract prices for.

        Returns:
            dict: A dictionary containing the updated products with prices.
        """

        r = self._get_website()
        html = self._get_html_soup(r)

        rows = html.find_all("div", {"role": "row"})

        for row in rows:
            cells = row.find_all("div", {"role": "gridcell"})
            if cells:
                product_name = self._clean_product_name(cells[0].text)
                if product_name in self.products_name_key_idx.keys():
                    self._set_price(
                        self.products_name_key_idx[product_name], cells[1].text)


class FuelCompanyShell(FuelCompany):

    _name: str = "Shell"
    _url: str = "https://shellservice.dk/wp-json/shell-wp/v2/daily-prices"

    _products = {
        OCTANE_95: {"name": "Shell FuelSave 95 oktan"},
        "oktan 100": {"name": "Shell V-Power 100 oktan"},
        "diesel": {"name": "Shell FuelSave Diesel"},
        "diesel+": {"name": "Shell V-Power Diesel"}
    }

    def refresh_prices(self):
        r = self._get_website()

        try:
            json = r.json()

        except requests.exceptions.JSONDecodeError as e:
            _LOGGER.error("Error parsing JSON from Shell: %s", e)
            raise e

        for product in json["results"]["products"]:
            if product["name"] in self.products_name_key_idx.keys():
                self._set_price(
                    self.products_name_key_idx[product["name"]],
                    product["price_incl_vat"]
                )


class FuelCompanyCirclek(FuelCompany):

    _name: str = "Circle K"
    _url: str = "https://www.circlek.dk/priser"

    _products = {
        OCTANE_95: {"name": "miles95"},
        "oktan 95+": {"name": "miles+95"},
        "diesel":  {"name": "miles Diesel"},
        "diesel+": {"name": "miles+ Diesel"},
        "electric": {"name": "El Lynlader"}
    }

    def refresh_prices(self):
        self._get_data_from_table(1, 2)


class FuelCompanyF24(FuelCompany):

    _name: str = "F24"
    _url: str = "https://www.f24.dk/-/api/PriceViewProduct/GetPriceViewProducts"

    _products = {
        OCTANE_95: {"name": "GoEasy 95 E10", "ProductCode": 22253},
        "oktan 95+": {"name": "GoEasy 95 Extra E5", "ProductCode": 22603},
        "diesel":  {"name": "GoEasy Diesel", "ProductCode": 24453},
        "diesel+": {"name": "GoEasy Diesel Extra", "ProductCode": 24338},
    }

    def refresh_prices(self):
        # F24 and Q8 returns JSON and expects us to ask with a payload in JSON
        headers = {"Content-Type": "application/json"}
        # Let us prepare a nice payload
        now = datetime.now()
        payload = {}
        # F24/Q8 wish to have a "FromDate", we use today - 31 days as timestamp
        payload["FromDate"] = int((now - timedelta(days=31)).timestamp())
        # Today as timestamp
        payload["ToDate"] = int(now.timestamp())
        # Lets cook up some wanted fueltypes with a empty list
        payload["FuelsIdList"] = []
        # We can control the order of the returned data with a Index
        index = 0
        # Loop through the products
        for product_dict in self._products.values():
            # Add "Index" to the dictionary of the product
            product_dict["Index"] = index
            # Append the product to the list
            payload["FuelsIdList"].append(product_dict)
            # increment the index
            index += 1

        # Send our payload and headers to the URL as a POST
        r = self._session.post(self._url, headers=headers, data=str(payload))
        r.raise_for_status()

        # Loop through the products
        for product_key, product_dict in self._products.items():
            # Extract the data of the product at the given Index from the dictionary
            # Remember we told the server in which order we wanted the data
            json_product = r.json()["Products"][product_dict["Index"]]
            # Get only the name and the price of the product

            self._set_price(
                product_key, json_product["PriceInclVATInclTax"])


class FuelCompanyQ8(FuelCompanyF24):

    _name: str = "Q8"
    _url: str = "https://www.q8.dk/-/api/PriceViewProduct/GetPriceViewProducts"

    _products = {
        OCTANE_95: {"name": "GoEasy 95 E10", "ProductCode": 22251},
        "oktan 95+": {"name": "GoEasy 95 Extra E5", "ProductCode": 22601},
        "diesel":  {"name": "GoEasy Diesel", "ProductCode": 24451},
        "diesel+": {"name": "GoEasy Diesel Extra", "ProductCode": 24337},
    }


class FuelCompanyIngo(FuelCompany):

    _name: str = "Ingo"
    _url: str = "https://www.ingo.dk/br%C3%A6ndstofpriser/aktuelle-br%C3%A6ndstofpriser"

    _products = {
        OCTANE_95: {"name": "Benzin 95"},
        "oktan 95+": {"name": "UPGRADE 95"},
        "diesel":  {"name": "Diesel"},
    }

    def refresh_prices(self):
        self._get_data_from_table(1, 2)


class FuelCompanyOil(FuelCompany):

    _name: str = "OIL!"
    _url: str = "https://www.oil-tankstationer.dk/de-gaeldende-braendstofpriser/"

    _products = {
        OCTANE_95: {"name": "95 E10"},
        "oktan 95+": {"name": "PREMIUM 98"},
        "diesel":  {"name": "Diesel"},
    }

    def refresh_prices(self):
        r = self._get_website()
        html = self._get_html_soup(r)
        rows = html.find_all("tr")
        for row in rows:
            cells = row.find_all("td")
            if cells:
                product_name = self._clean_product_name(cells[0].text)
                if product_name in self.products_name_key_idx.keys():
                    self._set_price(
                        self.products_name_key_idx[product_name], cells[2].text)


class FuelCompanyGoon(FuelCompany):

    _name: str = "Go' on"
    _url: str = "https://goon.nu/priser/#Aktuellelistepriser"

    _products = {
        OCTANE_95: {"name": "Blyfri 95", "ocr_crop": ["58", "232", "134", "46"]},
        "diesel":  {"name": "Transportdiesel", "ocr_crop": ["58", "289", "134", "46"]},
    }

    def refresh_prices(self):
        # Test if SSOCR, Seven Segments OCR, is present
        ssocr_bin = shutil.which("ssocr")
        if not ssocr_bin:
            _LOGGER.error(
                "Ssocr not present - OCR of prices from Go'On not possible. " +
                "Will fetch 'listepriser'"
            )
            self._goon_list_prices()
        else:
            self._goon_ocr()

    # GO'ON - No SSOCR present, get the "listprices"
    def _goon_list_prices(self):
        # Fetch the prices using the table-scraper function
        self._get_data_from_table(0, 7)
        # Since we are scraping "Listepriser" add 'priceType' : 'list' to the products
        # This is merely to send a message back to the API.
        self._price_type = "list"

    # GO'ON SSOCR present

    def _goon_ocr(self):
        # Filename for the image with the prices
        prices_file = "goon_prices.png"

        # Fetch the website with the prices
        r = self._get_website()
        html = self._get_html_soup(r)

        # Extract the url for the image with the prices and download the file
        pricelist_url = html.find("img", class_="lazyload")["data-src"]
        _LOGGER.debug("Latest Go'On price images is this: %s", pricelist_url)
        self._download_file(pricelist_url, prices_file, PATH)

        # # Loop through the products
        for product_key, product_dict in self._products.items():
            # Create a command for the SSOCR
            ocr_cmd = (
                ["ssocr"]
                + ["-d5"]
                + ["-t20"]
                + ["make_mono", "invert", "-D"]
                + ["crop"]
                + product_dict["ocr_crop"]
                + [PATH + prices_file]
            )
            # Perform OCR on the cropped image
            with subprocess.Popen(
                ocr_cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE
            ) as ocr:
                out = ocr.communicate()
                if out[0] != b"":
                    _LOGGER.debug(
                        "%s: %s", product_dict["name"], out[0].strip().decode("utf-8"))
                    self._set_price(
                        product_key, out[0].strip().decode("utf-8"))
