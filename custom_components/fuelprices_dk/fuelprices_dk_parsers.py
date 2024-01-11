from __future__ import annotations
from .const import (
    PATH,
)

import logging
from bs4 import BeautifulSoup as BS
from datetime import datetime, timedelta
import requests
import shutil
import subprocess
import pytz

DK_TZ = pytz.timezone("Europe/Copenhagen")

_LOGGER: logging.Logger = logging.getLogger(__package__)
_LOGGER = logging.getLogger(__name__)


class FuelParser:
    """
    A class that contains methods for parsing fuel prices from various websites.

    Methods:
        goon(url, products): Retrieves fuel price data from the Go'On website.
        circlek(url, products): Retrieves fuel price data from the Circle K website.
        shell(url, products): Retrieves fuel price data from the Shell website.
        ok(url, products): Retrieves fuel price data from the OK website.
        oil(url, products): Retrieves fuel price data from the Oil website.
        ingo(url, products): Retrieves fuel price data from the Ingo website.
        q8(url, products): Retrieves fuel price data from the Q8 website.
        f24(url, products): Retrieves fuel price data from the f24 website.
    """

    def __init__(self):
        # Initialize a new session for the scrapings
        self._session = requests.Session()

    # GO'ON

    def goon(self, url, products):
        """
        Retrieves fuel prices from the Go'On website.

        Args:
            url (str): The URL of the Go'On website.
            products (list): A list of fuel products to retrieve prices for.

        Returns:
            dict: A dictionary containing the retrieved fuel prices.
        """
        # Test if SSOCR, Seven Segments OCR, is present
        ssocr_bin = shutil.which("ssocr")
        if not ssocr_bin:
            _LOGGER.error(
                "Ssocr not present - OCR of prices from Go'On not possible. " +
                "Will fetch 'listepriser'"
            )
            return self._goon_list_prices(url, products)
        return self._goon_ocr(url, products)

    # GO'ON - No SSOCR present, get the "listprices"
    def _goon_list_prices(self, url, products):
        # Fetch the prices using the table-scraper function
        products = self._get_data_from_table(url, products, 0, 7)
        # Since we are scraping "Listepriser" add 'priceType' : 'list' to the products
        # This is merely to send a message back to the API.
        products["priceType"] = "list"
        return products

    # GO'ON SSOCR present
    def _goon_ocr(self, url, products):
        # Filename for the image with the prices
        prices_file = "goon_prices.png"

        # Fetch the website with the prices
        r = self._get_website(url)
        html = self._get_html_soup(r)

        # Extract the url for the image with the prices and download the file
        pricelist_url = html.find("img", class_="lazyload")["data-src"]
        _LOGGER.debug("Latest Go'On price images is this: %s", pricelist_url)
        self._download_file(pricelist_url, prices_file, PATH)

        # Loop through the products
        for product_key, product_dict in products.items():
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
                    products[product_key] = self._add_price_to_product(
                        product_dict, out[0].strip().decode("utf-8")
                    )
        return products

    # CIRCLE K
    def circlek(self, url, products):
        """
        Retrieves fuel price data from Circle K website.

        Args:
            url (str): The URL of the Circle K website.
            products (list): A list of products to retrieve prices for.

        Returns:
            dict: A dictionary containing the fuel price data.
        """
        return self._get_data_from_table(url, products, 1, 2)

    # SHELL
    def shell(self, url, products):
        """
        Parses the fuel prices from the Shell website.

        Args:
            url (str): The URL of the Shell website.
            products (list): A list of fuel products to parse.

        Returns:
            dict: A dictionary containing the parsed fuel prices.

        Raises:
            SomeException: An exception that may occur during parsing.

        """
        return self._get_data_from_table(url, products, 0, -1)

    # OK
    def ok(self, url, products):
        """
        Parses the OK website to extract fuel prices for the given products.

        Args:
            url (str): The URL of the OK website.
            products (dict): A dictionary containing the products to extract prices for.

        Returns:
            dict: A dictionary containing the updated products with prices.
        """
        r = self._get_website(url)
        html = self._get_html_soup(r)

        rows = html.find_all("div", {"role": "row"})
        for product_key, product_dict in products.items():
            found = False
            for row in rows:
                if found:
                    continue
                cells = row.find_all("div", {"role": "gridcell"})
                if cells:
                    found = product_dict["name"] == self._clean_product_name(
                        cells[0].text)
                    if found:
                        products[product_key] = self._add_price_to_product(
                            product_dict, cells[1].text
                        )
        return products

    # OIL!
    def oil(self, url, products):
        """
        Parses the prices from the Oil website and updates the products dictionary.

        Args:
            url (str): The URL of the Oil website.
            products (dict): A dictionary containing the products and their details.

        Returns:
            dict: The updated products dictionary with the oil prices added.
        """
        r = self._get_website(url)
        html = self._get_html_soup(r)

        rows = html.find_all("tr")
        for product_key, product_dict in products.items():
            found = False
            for row in rows:
                if found:
                    continue
                cells = row.find_all("td")
                if cells:
                    found = product_dict["name"] == self._clean_product_name(
                        cells[0].text)
                    if found:
                        products[product_key] = self._add_price_to_product(
                            product_dict,
                            cells[2].text,
                        )
        return products

    # INGO
    def ingo(self, url, products):
        """
        Retrieves fuel price data from the Ingo website.

        Args:
            url (str): The URL of the Ingo website.
            products (list): A list of products to retrieve data for.

        Returns:
            dict: A dictionary containing the fuel price data.
        """
        return self._get_data_from_table(url, products, 1, 2)

    # Q8
    def q8(self, url, products):
        """
        Parses the fuel prices from the Q8 website.

        Args:
            url (str): The URL of the Q8 website.
            products (list): A list of fuel products to retrieve prices for.

        Returns:
            dict: A dictionary containing the fuel prices for the specified products.
        """
        return self._f24_q8(url, products)

    # F24
    def f24(self, url, products):
        """
        Parses fuel prices from the f24 website.

        Args:
            url (str): The URL of the f24 website.
            products (list): A list of products to retrieve prices for.

        Returns:
            dict: A dictionary containing the parsed fuel prices.
        """
        return self._f24_q8(url, products)

    def _f24_q8(self, url, products):
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
        for product_dict in products.values():
            # Add "Index" to the dictionary of the product
            product_dict["Index"] = index
            # Append the product to the list
            payload["FuelsIdList"].append(product_dict)
            # increment the index
            index += 1

        # Send our payload and headers to the URL as a POST
        r = self._session.post(url, headers=headers, data=str(payload))
        # _LOGGER.debug("URL: " + url + " [" + str(r.status_code) + "]")
        _LOGGER.debug("URL: %s [%s]", url, r.status_code)
        if r.status_code == 200:
            # Loop through the products
            for product_key, product_dict in products.items():
                # Extract the data of the product at the given Index from the dictionary
                # Remember we told the server in which order we wanted the data
                json_product = r.json()["Products"][product_dict["Index"]]
                # Get only the name and the price of the product
                products[product_key]["name"] = json_product["Name"]
                products[product_key]["price"] = self._clean_price(
                    json_product["PriceInclVATInclTax"]
                )
                dt = datetime.now(DK_TZ)
                products[product_key]["lastUpdate"] = dt.strftime(
                    "%d/%m/%Y, %H:%M:%S")
            return products
        return None

    def _get_website(self, url):
        r = self._session.get(url, timeout=5)
        # _LOGGER.debug("URL: " + url + " [" + str(r.status_code) + "]")
        _LOGGER.debug("URL: %s [%s]", url, r.status_code)
        if r.status_code != 200:
            return r.status_code
        return r

    def _get_html_soup(self, r, parser="html.parser"):
        if r.text:
            return BS(r.text, parser)
        return None

    def _get_data_from_table(self, url, products, product_col, price_col):
        r = self._get_website(url)
        html = self._get_html_soup(r)

        # Find all <tr> (rows) in the table
        # Loop through all the products with the Key and a dict as Value (Object)
        #     Set found to False
        #     Loop through all the Rows
        #         If we previously have found a product, scontinue with the next product
        #         Find all the <td> (cells)
        #         If number of cells is larger than 1
        #             Set found true/false whether we have found the product
        #             If found
        #                 Extract, and clean, and add the price to the products dict
        # Return the dict og products

        rows = html.find_all("tr")
        for product_key, product_dict in products.items():
            found = False
            for row in rows:
                if found:
                    continue
                cells = row.findAll("td")
                if cells:
                    found = product_dict["name"] == self._clean_product_name(
                        cells[product_col].text
                    )
                    if found:
                        products[product_key] = self._add_price_to_product(
                            product_dict, cells[price_col].text
                        )
        return products

    def _add_price_to_product(self, product_dict, product_price):
        product_dict.update({"price": self._clean_price(product_price)})
        dt = datetime.now(DK_TZ)
        product_dict.update({"lastUpdate": dt.strftime("%d/%m/%Y, %H:%M:%S")})
        return product_dict

    def _clean_product_name(self, product_name):
        product_name = product_name.replace("Beskrivelse: ", "")
        product_name = product_name.strip()
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

    def _download_file(self, url, filename, path):
        r = self._session.get(url, stream=True)
        with open(path + filename, "wb") as file:
            for block in r.iter_content(chunk_size=1024):
                if block:
                    file.write(block)
