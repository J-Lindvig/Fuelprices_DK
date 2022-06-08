from __future__ import annotations

import logging
from bs4 import BeautifulSoup as BS
from datetime import datetime, timedelta
import os
import requests
import shutil
import subprocess

from .const import (
    PATH,
)

_LOGGER: logging.Logger = logging.getLogger(__package__)
_LOGGER = logging.getLogger(__name__)


class fuelParser:
    def __init__(self):
        self._session = requests.Session()

    # GO'ON
    def goon(self, url, products):
        # Test if SSOCR, Seven Segments OCR, is present
        ssocr_bin = shutil.which("ssocr")
        if not ssocr_bin:
            _LOGGER.error(
                "Ssocr not present - OCR of prices from Go'On not possible. Will fetch 'listepriser'"
            )
            return self._goon_listPrices(url, products)
        return self._goon_ocr(url, products)

    def _goon_listPrices(self, url, products):
        # Fetch the prices
        # Since we are scraping "Listepriser" add 'priceType' : 'list' to the products
        # This is merely to send a message back to the API.
        products = self._getDataFromTable(url, products, 0, 7)
        products["priceType"] = "list"
        return products

    def _goon_ocr(self, url, products):
        # Filename for the image with the prices
        prices_file = "goon_prices.png"

        # Fetch the website with the prices
        r = self._get_website(url)
        html = self._get_html_soup(r)

        # Extract the url for the image with the prices
        # And download the fil
        pricelist_url = html.find("img", class_="lazyload")["data-src"]
        _LOGGER.debug("Latest Go'On price images is this: " + pricelist_url)
        self._download_file(pricelist_url, prices_file, PATH)

        # Loop through the products
        for productKey, productDict in products.items():
            ocr_cmd = (
                ["ssocr"]
                + ["-d5"]
                + ["-t20"]
                + ["make_mono", "invert", "-D"]
                + ["crop"]
                + productDict["ocr_crop"]
                + [PATH + prices_file]
            )
            # Perform OCR on the cropped image
            with subprocess.Popen(
                ocr_cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE
            ) as ocr:
                out = ocr.communicate()
                if out[0] != b"":
                    _LOGGER.debug(
                        products[productKey]["name"]
                        + ": "
                        + str(out[0].strip().decode("utf-8"))
                    )
                    products[productKey] = self._addPriceToProduct(
                        productDict, out[0].strip().decode("utf-8")
                    )
        return products

    # CIRCLE K
    def circlek(self, url, products):
        return self._getDataFromTable(url, products, 1, -1)

    # SHELL
    def shell(self, url, products):
        return self._getDataFromTable(url, products, 0, -1)

    # OK
    def ok(self, url, products):
        r = self._get_website(url)
        html = self._get_html_soup(r)

        rows = html.find_all("div", {"role": "row"})
        for productKey, productDict in products.items():
            found = False
            for row in rows:
                if found:
                    continue
                cells = row.find_all("div", {"role": "gridcell"})
                if cells:
                    found = productDict["name"] == self._cleanProductName(cells[0].text)
                    if found:
                        products[productKey] = self._addPriceToProduct(
                            productDict, cells[1].text
                        )
        return products

    # OIL!
    def oil(self, url, products):
        r = self._get_website(url)
        html = self._get_html_soup(r)

        rows = html.find_all("tr")
        for productKey, productDict in products.items():
            found = False
            for row in rows:
                if found:
                    continue
                cells = row.find_all("td")
                if cells:
                    found = productDict["name"] == self._cleanProductName(cells[0].text)
                    if found:
                        priceSegments = cells[2].findAll(
                            "span", style=["text-align:right;", "text-align:left;"]
                        )
                        products[productKey] = self._addPriceToProduct(
                            productDict,
                            priceSegments[0].text + "." + priceSegments[1].text,
                        )
        return products

    # INGO
    def ingo(self, url, products):
        return self._getDataFromTable(url, products, 1, 2)

    # Q8
    def q8(self, url, products):
        return self._f24_q8(url, products)

    # F24
    def f24(self, url, products):
        return self._f24_q8(url, products)

    def _f24_q8(self, url, products):
        now = datetime.now()
        payload = {}
        payload["FuelsIdList"] = list(products.values())
        payload["FromDate"] = int((now - timedelta(days=31)).timestamp())
        payload["ToDate"] = int(now.timestamp())
        headers = {"Content-Type": "application/json"}

        r = self._session.post(url, headers=headers, data=str(payload))
        if r.status_code == 200:
            for productKey, productDict in products.items():
                json_product = r.json()["Products"][productDict["Index"]]
                products[productKey]["name"] = json_product["Name"]
                products[productKey]["price"] = self._cleanPrice(
                    json_product["PriceInclVATInclTax"]
                )
            return products

    def _get_website(self, url):
        r = self._session.get(url)
        if r.status_code != 200:
            return r.status_code
        return r

    def _get_html_soup(self, r, parser="html.parser"):
        if r.text:
            return BS(r.text, "html.parser")

    def _getDataFromTable(self, url, products, productCol, priceCol):
        r = self._get_website(url)
        html = self._get_html_soup(r)

        """
		Find all <tr> (rows) in the table
		Loop through all the products with the Key and a dict as Value (Object)
			Set found to False
			Loop through all the Rows
				If we previously have found a product, scontinue with the next product
				Find all the <td> (cells)
				If number of cells is larger than 1
					Set found true/false whether we have found the product
					If found
						Extract, and clean, and add the price to the products dict
		Return the dict og products
		"""
        rows = html.find_all("tr")
        for productKey, productDict in products.items():
            found = False
            for row in rows:
                if found:
                    continue
                cells = row.findAll("td")
                if cells:
                    found = productDict["name"] == self._cleanProductName(
                        cells[productCol].text
                    )
                    if found:
                        products[productKey] = self._addPriceToProduct(
                            productDict, cells[priceCol].text
                        )
        return products

    def _addPriceToProduct(self, productDict, productPrice):
        productDict.update({"price": self._cleanPrice(productPrice)})
        return productDict

    def _cleanProductName(self, productName):
        productName = productName.replace("Beskrivelse: ", "")
        productName = productName.strip()
        return productName

    def _cleanPrice(self, price):
        price = str(price)  # Typecast to String
        price = price.replace("Pris inkl. moms: ", "")  # Remove 'Pris inkl. moms: '
        price = price.replace(" kr.", "")  # Remove ' kr.'
        price = price.replace(",", ".")  # Replace ',' with '.'
        price = price.strip()  # Remove leading or trailing whitespaces
        return float("{:.2f}".format(float(price)))  # Return the price with 2 decimals

    def _download_file(self, url, filename, path):
        r = self._session.get(url, stream=True)
        with open(path + filename, "wb") as file:
            for block in r.iter_content(chunk_size=1024):
                if block:
                    file.write(block)
