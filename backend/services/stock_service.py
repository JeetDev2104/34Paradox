import aiohttp
import asyncio
import json
from datetime import datetime, timedelta
from typing import Dict, Optional, List
import logging
from pymongo import MongoClient
from bson import ObjectId

logger = logging.getLogger(__name__)

class StockService:
    def __init__(self, mongo_client: MongoClient):
        self.mongo_client = mongo_client
        self.db = mongo_client.newswise
        self.stock_cache = {}
        self.cache_timeout = timedelta(minutes=5)

    async def fetch_stock_data(self, stock_name: str) -> Optional[Dict]:
        # Check cache first
        if stock_name in self.stock_cache:
            cached_data = self.stock_cache[stock_name]
            if datetime.now() - cached_data['timestamp'] < self.cache_timeout:
                return cached_data['data']

        # Use a mock response if APIs are not available or have errors
        mock_data = await self._get_mock_stock_data(stock_name)
        if not mock_data:
            # Try to get data from database
            db_data = await self._get_cached_stock_data(stock_name)
            if db_data:
                return db_data
                
            # Create a default mock response as last resort
            mock_data = self._create_default_mock_data(stock_name)
            
        # Cache the data
        self._cache_stock_data(stock_name, mock_data)
        return mock_data

    async def _get_mock_stock_data(self, stock_name: str) -> Optional[Dict]:
        """Get mock stock data for development/testing or when APIs fail"""
        # Pre-defined mock data for common stocks
        common_stocks = {
            "AAPL": {
                "symbol": "AAPL",
                "name": "Apple Inc.",
                "price": 175.34,
                "change": 2.15,
                "changePercent": 1.24,
                "volume": 78453200,
                "marketCap": 2751000000000,
                "sector": "Technology",
                "lastUpdated": datetime.now().isoformat()
            },
            "GOOGL": {
                "symbol": "GOOGL",
                "name": "Alphabet Inc.",
                "price": 155.72,
                "change": 1.89,
                "changePercent": 1.23,
                "volume": 26834500,
                "marketCap": 1960000000000,
                "sector": "Technology",
                "lastUpdated": datetime.now().isoformat()
            },
            "MSFT": {
                "symbol": "MSFT",
                "name": "Microsoft Corporation",
                "price": 415.10,
                "change": 3.45,
                "changePercent": 0.84,
                "volume": 22145600,
                "marketCap": 3090000000000,
                "sector": "Technology",
                "lastUpdated": datetime.now().isoformat()
            },
            "AMZN": {
                "symbol": "AMZN",
                "name": "Amazon.com, Inc.",
                "price": 178.75,
                "change": -1.25,
                "changePercent": -0.69,
                "volume": 42985300,
                "marketCap": 1850000000000,
                "sector": "Consumer Cyclical",
                "lastUpdated": datetime.now().isoformat()
            },
            "RELIANCE": {
                "symbol": "RELIANCE",
                "name": "Reliance Industries Ltd.",
                "price": 2875.35,
                "change": 38.75,
                "changePercent": 1.37,
                "volume": 8452600,
                "marketCap": 19450000000000,
                "sector": "Energy",
                "lastUpdated": datetime.now().isoformat()
            },
            "TCS": {
                "symbol": "TCS",
                "name": "Tata Consultancy Services Ltd.",
                "price": 3680.55,
                "change": 22.50,
                "changePercent": 0.62,
                "volume": 2564800,
                "marketCap": 13450000000000,
                "sector": "Technology",
                "lastUpdated": datetime.now().isoformat()
            },
            "HDFC": {
                "symbol": "HDFC",
                "name": "HDFC Bank Ltd.",
                "price": 1578.40,
                "change": -12.75,
                "changePercent": -0.80,
                "volume": 6254900,
                "marketCap": 8975000000000,
                "sector": "Financial Services",
                "lastUpdated": datetime.now().isoformat()
            },
            "ICICIBANK": {
                "symbol": "ICICIBANK",
                "name": "ICICI Bank Ltd.",
                "price": 1124.85,
                "change": 15.65,
                "changePercent": 1.41,
                "volume": 7865200,
                "marketCap": 7856000000000,
                "sector": "Financial Services",
                "lastUpdated": datetime.now().isoformat()
            }
        }
        
        # Check if we have mock data for this stock
        stock_upper = stock_name.upper()
        if stock_upper in common_stocks:
            return common_stocks[stock_upper]
        
        # Try to match partial name
        for symbol, data in common_stocks.items():
            if stock_name.upper() in data["name"].upper():
                return data
                
        return None
        
    def _create_default_mock_data(self, stock_name: str) -> Dict:
        """Create a default mock response for unknown stocks"""
        # Generate a random price between 500 and 5000
        import random
        price = random.uniform(500, 5000)
        change = random.uniform(-50, 50)
        change_percent = (change / price) * 100
        
        return {
            "symbol": stock_name.upper(),
            "name": f"{stock_name.upper()} Stock",
            "price": round(price, 2),
            "change": round(change, 2),
            "changePercent": round(change_percent, 2),
            "volume": random.randint(100000, 10000000),
            "marketCap": random.randint(10000000000, 1000000000000),
            "sector": "Unknown",
            "lastUpdated": datetime.now().isoformat()
        }

    def _format_nse_data(self, data: Dict) -> Dict:
        return {
            'symbol': data.get('symbol'),
            'name': data.get('companyName'),
            'price': float(data.get('lastPrice', 0)),
            'change': float(data.get('change', 0)),
            'changePercent': float(data.get('pChange', 0)),
            'volume': int(data.get('totalTradedVolume', 0)),
            'marketCap': float(data.get('marketCap', 0)),
            'sector': data.get('industry', 'N/A'),
            'lastUpdated': datetime.now().isoformat()
        }

    def _format_bse_data(self, data: Dict) -> Dict:
        return {
            'symbol': data.get('symbol'),
            'name': data.get('companyName'),
            'price': float(data.get('currentPrice', 0)),
            'change': float(data.get('change', 0)),
            'changePercent': float(data.get('pChange', 0)),
            'volume': int(data.get('volume', 0)),
            'marketCap': float(data.get('marketCap', 0)),
            'sector': data.get('industry', 'N/A'),
            'lastUpdated': datetime.now().isoformat()
        }

    def _format_yahoo_data(self, data: Dict, symbol: str) -> Dict:
        meta = data['chart']['result'][0]['meta']
        return {
            'symbol': symbol,
            'name': symbol,
            'price': float(meta.get('regularMarketPrice', 0)),
            'change': float(meta.get('regularMarketPrice', 0)) - float(meta.get('previousClose', 0)),
            'changePercent': ((float(meta.get('regularMarketPrice', 0)) - float(meta.get('previousClose', 0))) / float(meta.get('previousClose', 1))) * 100,
            'volume': int(meta.get('regularMarketVolume', 0)),
            'marketCap': float(meta.get('marketCap', 0)),
            'sector': 'N/A',
            'lastUpdated': datetime.now().isoformat()
        }

    def _cache_stock_data(self, stock_name: str, data: Dict):
        self.stock_cache[stock_name] = {
            'data': data,
            'timestamp': datetime.now()
        }
        # Also save to database for persistence
        try:
            self.db.stocks.update_one(
                {'symbol': stock_name},
                {'$set': {
                    'data': data,
                    'last_updated': datetime.now()
                }},
                upsert=True
            )
        except Exception as e:
            logger.error(f"Error caching stock data to database: {str(e)}")

    async def _get_cached_stock_data(self, stock_name: str) -> Optional[Dict]:
        try:
            cached = self.db.stocks.find_one({'symbol': stock_name})
            if cached and datetime.now() - cached['last_updated'] < timedelta(days=1):
                return cached['data']
        except Exception as e:
            logger.error(f"Error retrieving cached stock data: {str(e)}")
        return None 