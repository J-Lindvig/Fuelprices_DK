#!/bin/env python

import logging
from fuelprices_dk import FuelPrices

logging.basicConfig(level=logging.DEBUG)
_LOGGER: logging.Logger = logging.getLogger(__package__)
_LOGGER = logging.getLogger(__name__)

f = FuelPrices()
f.load_companies(None, None)
f.refresh()

for company_key, company in f.companies.items():
    print(f"{company_key=} {company.name}")
    # print(f"{c.name=}")
    # print(f"{c.key=}")

    print(f"{company.products=}")

    for product_key, product in company.products.items():
        print(f"{product_key=} {product['name']=}")


# print('-' * 80)

# print(f"{f._companies}")

# for c in f.companies:
#     print(f"{c.name=}")
# for product_key in f.get_company_products_keys(company_key):
#     print(f"{product_key=}")
# try:
#     print(f"price: {f.get_company(
#         company_key).get_product_price(product_key)}")
# except KeyError:
#     print("No price!")
