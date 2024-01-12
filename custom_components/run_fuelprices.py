#!/bin/env python

import logging
from fuelprices_dk import FuelPrices

logging.basicConfig(level=logging.DEBUG)
_LOGGER: logging.Logger = logging.getLogger(__package__)
_LOGGER = logging.getLogger(__name__)

f = FuelPrices()
f.load_companies([], [])
f.refresh()

for company_key in f.get_company_keys():
    print(f"{company_key=}")
    for product_key in f.get_company_products_keys(company_key):
        print(f"{product_key=}")
        try:
            print(f"price: {f.get_company(
                company_key).get_product_price(product_key)}")
        except KeyError:
            print("No price!")
