import requests
import json

class CoinMarketCap():
	def __init__(self, endpoint, api_token, *args, **kwargs):
		self.endpoint = endpoint
		self.api_token = api_token
		self.headers = {
			'Accepts': 'application/json',
			'X-CMC_PRO_API_KEY': self.api_token,
		}

	def get_eth_price(self):
		try:
			params = {'start':'2', 'limit':'1', 'convert':'USD'}
			response = requests.get(self.endpoint, headers=self.headers, params=params)
			response = response.json()
			response = response['data'][0]['quote']['USD']['price']
			return int(response)
		except Exception as e:
			return 0
	