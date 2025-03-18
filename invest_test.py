#!/usr/bin/python3
import os
import requests
import logging
import sqlite

invest_flag = True
api_key = ""
stock_prices = {}
logger = logging.getLogger(__name__)

try:
  api_key = os.environ.get("FINAZON_API_KEY")
except KeyError as e:
  invest_flag = False
  logger.error(f"Finazon APIKEY not found in environment variable {e}")
except Exception as e:
  invest_flag = False
  logger.error(f"Unknown exception occurred trying to read 'FINAZON_API_KEY' environment variable - {e}")

def update_stock_price(ticker):
  if not invest_flag:
    logger.warn(f"Invest flag disabled.")
    return

  params = {
    'apikey': api_key,
    'ticker': ticker
  }

  try:
    response = requests.get(f"https://api.finazon.io/latest/finazon/us_stocks_essential/price", params=params)
    data = response.json()
  except Exception as e:
    logger.error(f"Unknown error occurred trying to get price for stock '{ticker}' - {e}")

  try:
    stock_prices[ticker] = data['p']
  except Exception as e:
    logger.error(f"Unknown error getting stock price from response - {e}")

def _create_tables(self):
  with self._get_connection() as conn:
      conn.execute('''
          CREATE TABLE IF NOT EXISTS investments (
              user_id INTEGER PRIMARY KEY,
              stock TEXT,
              amount REAL,
              last_daily TEXT
          )
      ''')
      conn.commit()


if __name__ == "__main__":
  logging.basicConfig(level=logging.INFO)
  update_stock_price("AAPL")
  logger.info(f"AAPL price: {stock_prices['AAPL']}")
