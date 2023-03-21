from web3 import Web3
from eth_account import Account
import requests


class Arbitrum():
	def __init__(self, mainnet_rpc, contract_abi, contract_address, *args, **kwargs):
		self.mainnet_rpc = mainnet_rpc
		self.contract_abi = contract_abi
		self.contract_address = contract_address

	def get_provider(self):
		return Web3(Web3.HTTPProvider(self.mainnet_rpc))

	def get_eth_balance(self, address, provider=None):
		try:
			w3 = provider if provider else self.get_provider()
			balance = w3.eth.get_balance(address)
			balance = w3.from_wei(balance, 'ether')
			return balance
		except Exception as e:
			return 0

	def get_arb_balance(self, address, provider=None):
		try:
			w3 = provider if provider else self.get_provider()
			contract = w3.eth.contract(address=self.contract_address, abi=self.contract_abi)
			balance = contract.functions.claimableTokens(address).call()
			balance = w3.from_wei(balance, 'ether')
			return balance
		except Exception as e:
			return 0

	def get_total_balance(self, wallets:list):
		provider = self.get_provider()
		eth = sum([self.get_eth_balance(wallet, provider=provider) for wallet in wallets])
		arb = sum([self.get_arb_balance(wallet, provider=provider) for wallet in wallets])
		return eth, arb
