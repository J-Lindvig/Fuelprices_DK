from __future__ import annotations

import logging
from datetime import datetime
from .fuelprices_dk_parsers import fuelParser		# Module containing parsers

_LOGGER: logging.Logger = logging.getLogger(__package__)
_LOGGER = logging.getLogger(__name__)

DEFAULT_PRICE_TYPE = "pump"
DIESEL = "diesel"
DIESEL_PLUS = "diesel+"
OCTANE_95 = "oktan 95"
OCTANE_95_PLUS = "oktan 95+"
OCTANE_100 = "oktan 100"
FUEL_COMPANIES = {
	"circlek": {
		"name": "Circle K",
		"url": "https://www.circlek.dk/",
		"products": {
			OCTANE_95: {"name": "miles95"},
			OCTANE_95_PLUS: {"name": "milesPLUS95"},
			DIESEL: {"name": "miles Diesel B7"},
			DIESEL_PLUS: {"name": "milesPLUS Diesel"},
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
		"url": "https://www.ok.dk/offentlig/produkter/braendstof/priser",
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
		"url": "https://www.shell.dk/customer-service/priser-pa-benzin-og-diesel.html",
		"products": {
			OCTANE_95: {"name": "Shell FuelSave Blyfri 95"},
			OCTANE_100: {"name": "Shell V-Power"},
			DIESEL: {"name": "Shell FuelSave Diesel"},
			DIESEL_PLUS: {"name": "Shell V-Power Diesel"},
		},
	},
}


class fuelprices:
	def __init__(self):
		self._fuelCompanies = {}

	def loadCompanies(self, companyKeys, productKeys):
		# If no companies is specified, use ALL companies
		if not companyKeys:
			companyKeys = FUEL_COMPANIES.keys()

		# If no product is specified, use ALL products
		if not productKeys:
			productKeys = self._getProductKeys()

		# Loop through all the companyKeys
		for companyKey in companyKeys:
			if companyKey in FUEL_COMPANIES.keys():
				_LOGGER.debug(
					"Adding fuelcompany: " + FUEL_COMPANIES[companyKey]["name"]
				)

				# Loop through all the products and remove the ones NOT specified
				for productKey in list(FUEL_COMPANIES[companyKey]["products"].keys()):
					if not productKey in productKeys:
						del FUEL_COMPANIES[companyKey]["products"][productKey]
					else:
						_LOGGER.debug(
							"Adding product to "
							+ FUEL_COMPANIES[companyKey]["name"]
							+ ": "
							+ FUEL_COMPANIES[companyKey]["products"][productKey]["name"]
						)

				self._fuelCompanies[companyKey] = fuelCompany(
					companyKey,
					FUEL_COMPANIES[companyKey]["name"],
					FUEL_COMPANIES[companyKey]["url"],
					FUEL_COMPANIES[companyKey]["products"],
					fuelParser(),
				)

	# Return a list of unique productKeys 
	def _getProductKeys(self):
		# Prepare a empty list
		productKeys = []
		# Loop through all the companies
		for company in FUEL_COMPANIES.values():
			# Add a list of the companys productKeys to the list
			productKeys.extend(list(company["products"].keys()))
		# Typecast the list to a set to remove duplicates
		productKeys = set(productKeys)
		# Return the set as a list
		return list(productKeys)

	# Refresh prices from all the products from all the companies
	def refresh(self):
		for company in self.getCompanies():
			company.refreshPrices()
		# for companyKey in self.getCompanyKeys():
		# 	self._fuelCompanies[companyKey].refreshPrices()

	def getCompany(self, companyKey):
		if self._companyExists(companyKey):
			return self._fuelCompanies[companyKey]

	def getCompanyKeys(self):
		return self._fuelCompanies.keys()

	def getCompanies(self):
		return self._fuelCompanies.values()

	def getCompanyName(self, companyKey):
		if self._companyExists(companyKey):
			return self._fuelCompanies[companyKey].getName()

	def getCompanyPrices(self, companyKey):
		if self._companyExists(companyKey):
			return self._fuelCompanies[companyKey].getPrices()

	def getCompanyProductsKeys(self, companyKey):
		if self._companyExists(companyKey):
			return self._fuelCompanies[companyKey].getProductsKeys()

	def _companyExists(self, companyKey):
		return companyKey in self.getCompanyKeys()


class fuelCompany:
	def __init__(self, key, name, url, products, parser):
		self._key = key										# Key of the company in the dict
		self._name = name									# Name of the company
		self._url = url										# URL to site with prices
		self._products = products							# Dictionary with products and prices
		self._parser = parser								# Instance of the parser module
		self._priceType = DEFAULT_PRICE_TYPE				# Default type of prices
		self._lastUpdate = int(datetime.now().timestamp())	# Current timestamp

	def getName(self):
		return self._name

	def getURL(self):
		return self._url

	# Refresh the companys prices
	def refreshPrices(self):
		_LOGGER.debug("Refreshing prices from: " + self._name)
		# Run the function, from the parser, with the same name as the companys key
		# Provide the URL and the dictionary with the products
		# Update the dictionary with products with the returned data
		self._products = getattr(self._parser, self._key)(self._url, self._products)
		# If the Key 'priceType' is present, extract it from the dict, else use DEFAULT_PRICE_TYPE
		self._priceType = self._products.pop("priceType", DEFAULT_PRICE_TYPE)
		# Update the timeetamp
		self._lastUpdate = int(datetime.now().timestamp())

	def getProductsKeys(self):
		return self._products.keys()

	def getProductName(self, productKey):
		return self._products[productKey]["name"]

	def getProductPrice(self, productKey):
		return self._products[productKey]["price"]

	def getPriceType(self):
		return self._priceType

	def getLastUpdate(self):
		return self._lastUpdate
