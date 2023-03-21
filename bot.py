from telegram import Update
from telegram import ReplyKeyboardMarkup, ReplyKeyboardRemove
from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from telegram.constants import ParseMode
from telegram.ext import (
	Application,
	CommandHandler,
	CallbackQueryHandler,
	ContextTypes,
	ConversationHandler,
	MessageHandler,
	filters,
)

# Mute CallbackQueryHandler in ConversationHandler
from warnings import filterwarnings
from telegram.warnings import PTBUserWarning
filterwarnings(action="ignore", message=r".*CallbackQueryHandler", category=PTBUserWarning)

# My imports
import re
from utils.arbitrum import Arbitrum
from utils.coinmarketcap import CoinMarketCap
from utils.etherscan import EtherScan
from utils import config

# Web3 connection with Arbitrum mainnet
arbitrum = Arbitrum(
	mainnet_rpc = config.ARBITRUM_MAINNET_RPC,
	contract_abi = config.ARBITRUM_FOUNDATION_ABI,
	contract_address = config.ARBITRUM_FOUNDATION_ADDRESS)

# CoinMarketCap API
coinmarketcap = CoinMarketCap(
	endpoint = config.COINMARKETCAP_ENDPOINT,
	api_token = config.COINMARKETCAP_API_TOKEN)

# EtherScan API
etherscan = EtherScan(
	endpoint = config.ETHERSCAN_ENDPOINT,
	api_token = config.ETHERSCAN_API_TOKEN)

# Bot conversation states:
WALLET_VALIDATION_STATE = "WALLET_VALIDATION_STATE"

# Bot keyboard markups:
markup = ReplyKeyboardMarkup([
	["Countdown", "Check wallets"],
	["README"]],
	one_time_keyboard=True,
	resize_keyboard=True)


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
	await update.message.reply_text("What do you want me display?", reply_markup=markup, parse_mode=ParseMode.HTML)


async def countdown(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
	block = etherscan.get_block_number()
	start = config.CLAIM_START_BLOCK
	text = f"Current block is [{block}]. {start-block} blocks left until claim."
	await update.message.reply_text(text, reply_markup=markup, parse_mode=ParseMode.HTML)


async def readme(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
	await update.message.reply_text(
		"@ArbitrumDropBot is an <b>open-source Telegram bot</b> that allows for easy tracking and management of Arbitrum airdrops.\n"
		"\n"
		"1. Check Wallets\n"
		"After clicking the <b>[Check Wallets]</b> button, you need to submit a list of wallets you want to check. Each wallet should be on a new line.\n"
		"<pre>Example: ---------------------------------</pre>\n"
		"<pre>0x0000000000000000000000000000000000000000</pre>\n"
		"<pre>0x1111111111111111111111111111111111111111</pre>\n"
		"<pre>0x2222222222222222222222222222222222222222</pre>\n"
		"<pre>..........................................</pre>\n"
		"<pre>0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFF</pre>\n"
		"<pre>------------------------------------------</pre>\n"
		"After submitting the list, the bot will provide you with the following results for each wallet:\n"
		"- The number of ARB tokens that can be claimed for each individual wallet.\n"
		"- The total balance of the airdrop across all wallets.\n"
		"\n"
		"2. Countdown\n"
		"After clicking the <b>[Countdown]</b> button, the bot will display the current block number and how many blocks are left until the claim starts.\n"
		"\n"
		"Contact me: @devalexon\n"
		"GitHub: https://github.com/gamechanges/ArbitrumDropBot",
		reply_markup = markup,
		parse_mode = ParseMode.HTML)


#==================================================================================================
# Check Wallet Conversation Start =================================================================
#==================================================================================================
async def check_wallets_step1(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
	reply_markup = InlineKeyboardMarkup([[InlineKeyboardButton("Cancel", callback_data="check_wallets_end")]])
	trash = await update.message.reply_text(
		"Send me a list of wallets you want to check.\n\n"
		"<b>Example:</b>\n"
		"<pre>0x1111111111111111111111111111111111111111</pre>\n"
		"<pre>0x2222222222222222222222222222222222222222</pre>\n"
		"<pre>0x3333333333333333333333333333333333333333</pre>\n",
		reply_markup = reply_markup,
		parse_mode = ParseMode.HTML)
	#==============================================================================================
	# Bcoz I need to remove InlineKeyboardMarkup later
	context.user_data["trash"] = {}
	context.user_data["trash"]["chat_id"] = trash.chat_id
	context.user_data["trash"]["message_id"] = trash.message_id
	#==============================================================================================
	return "CHECK_WALLETS_STATE"


async def check_wallets_step2(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
	# await context.bot.delete_message(chat_id=context.user_data["trash"]["chat_id"], message_id=context.user_data["trash"]["message_id"])
	await context.bot.edit_message_reply_markup(chat_id=context.user_data["trash"]["chat_id"], message_id=context.user_data["trash"]["message_id"])
	#==============================================================================================
	# For loop preparation
	yellow_pages = update.message.text.strip().replace(';', ' ').replace(',', ' ').replace('\n', ' ').split()
	regex = r'^0x[a-fA-F0-9]{40}$'
	regex = re.compile(regex)
	text = ""
	trash = []
	total_arb = 0
	provider = arbitrum.get_provider()
	#==============================================================================================
	# Checking wallets
	for address in yellow_pages:
		if not address in trash:
			if regex.match(address):
				eth = arbitrum.get_eth_balance(address, provider=provider)
				arb = arbitrum.get_arb_balance(address, provider=provider)
				eth_price = coinmarketcap.get_eth_price()
				usd = round(eth * eth_price, 2)
				total_arb += arb
				emoji = "✅" if arb else "❌"
				text += f"{emoji} {address}\n"
				text += f"$ETH: {eth} (${usd})\n"
				text += f"$ARB: {arb}\n\n"
			else:
				text += f"❌ {address}\n"
				text += f"Invalid address\n\n"
			trash.append(address)
	#==============================================================================================
	text += "🌟 <b>Total:</b>\n"
	text += f"$ARB: {total_arb}\n\n"
	#==============================================================================================
	block = etherscan.get_block_number()
	start = config.CLAIM_START_BLOCK
	text += f"<i>PS: current block is [{block}]. {start-block} blocks left until claim.</i>"
	await update.message.reply_text(text, reply_markup=markup, parse_mode=ParseMode.HTML)
	return ConversationHandler.END
	

async def check_wallets_end(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
	query = update.callback_query
	await query.answer()
	await context.bot.delete_message(chat_id=query.message.chat_id, message_id=query.message.message_id)
	await query.message.reply_text("What do you want me display?", reply_markup=markup)
	return ConversationHandler.END
#==================================================================================================
# Check Wallet Conversation End ===================================================================
#==================================================================================================



def main() -> None:
	"""Run the bot."""
	# Create the Application and pass it your bot's token.
	application = Application.builder().token(config.TELEGRAM_API_TOKEN).build()

	# Commannd "/start" handler
	application.add_handler(CommandHandler("start", start))

	# Message "Countdown" handler
	application.add_handler(MessageHandler(filters.Regex("^Countdown$"), countdown))

	# Message "README" handler
	application.add_handler(MessageHandler(filters.Regex("^README$"), readme))

	# [Check Wallets] Conversation handler
	check_wallets_conversation = ConversationHandler(
		entry_points = [MessageHandler(filters.Regex("^Check wallets$"), check_wallets_step1)],
		states = {
			"CHECK_WALLETS_STATE": [
				MessageHandler(filters.TEXT & ~(filters.COMMAND), check_wallets_step2),
			],
		},
		fallbacks = [CallbackQueryHandler(check_wallets_end, pattern=r'^check_wallets_end$')],
	)
	application.add_handler(check_wallets_conversation)

	# Run the bot until the user presses Ctrl-C
	application.run_polling()



if __name__ == "__main__":
	print("Bot is alive.")
	main()