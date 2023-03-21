import requests
import json

class EtherScan():
	def __init__(self, endpoint, api_token, *args, **kwargs):
		self.endpoint = endpoint
		self.api_token = api_token

	def get_block_number(self):
		try:
			params = {'module':'proxy', 'action':'eth_blockNumber', 'apikey':self.api_token}
			response = requests.get(self.endpoint, params=params)
			response = response.json()
			block = response['result']
			return int(block, 16)
		except Exception as e:
			return 0
