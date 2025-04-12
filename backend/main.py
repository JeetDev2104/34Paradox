from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from services.chatbot import chatbot_service
from services.database import db_service
from services.news_scraper import news_scraper_service
import logging
from typing import List, Dict, Optional, Any
import json
import math
from fastapi.responses import JSONResponse
from bson.objectid import ObjectId
import fastapi.encoders
from pymongo import MongoClient
from datetime import datetime
import re
from services.stock_service import StockService

# Patch FastAPI's jsonable_encoder to handle ObjectId
original_jsonable_encoder = fastapi.encoders.jsonable_encoder
def patched_jsonable_encoder(obj, *args, **kwargs):
    if isinstance(obj, ObjectId):
        return str(obj)
    if isinstance(obj, dict):
        return {k: patched_jsonable_encoder(v, *args, **kwargs) for k, v in obj.items()}
    if isinstance(obj, list):
        return [patched_jsonable_encoder(i, *args, **kwargs) for i in obj]
    return original_jsonable_encoder(obj, *args, **kwargs)

# Replace FastAPI's jsonable_encoder with our patched version
fastapi.encoders.jsonable_encoder = patched_jsonable_encoder

# Custom JSON encoder to handle NaN and Infinity
class CustomJSONEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, float):
            if math.isnan(obj):
                return None
            elif math.isinf(obj):
                return None
        # Handle MongoDB ObjectId
        if isinstance(obj, ObjectId):
            return str(obj)
        # Handle lists with ObjectId values
        if isinstance(obj, list):
            return [self.default(item) for item in obj]
        # Handle dictionaries with ObjectId values
        if isinstance(obj, dict):
            return {key: self.default(value) for key, value in obj.items()}
        # Handle datetime objects
        if isinstance(obj, datetime):
            return obj.isoformat()
        try:
            return super(CustomJSONEncoder, self).default(obj)
        except TypeError:
            return str(obj)  # Convert any problematic types to strings as fallback

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="NewsWise Financial API")

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, replace with specific origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# MongoDB connection
client = MongoClient('mongodb://localhost:27017/')
db = client.newswise

# Initialize services
stock_service = StockService(client)

# Helper function to safely serialize MongoDB results
def safe_serialize(obj: Any) -> Any:
    """Safely serialize MongoDB objects to JSON-compatible format"""
    if isinstance(obj, ObjectId):
        return str(obj)
    elif isinstance(obj, list):
        return [safe_serialize(item) for item in obj]
    elif isinstance(obj, dict):
        return {key: safe_serialize(value) for key, value in obj.items()}
    elif isinstance(obj, float):
        if math.isnan(obj) or math.isinf(obj):
            return None
    return obj

# Override FastAPI's default JSONResponse
@app.middleware("http")
async def replace_response_with_custom_json(request, call_next):
    response = await call_next(request)
    
    if isinstance(response, JSONResponse):
        try:
            # Parse the response body to get the data
            data = json.loads(response.body.decode())
            # Pre-process data with our safe_serialize function
            serialized_data = safe_serialize(data)
            # Re-encode with our custom encoder
            response.body = json.dumps(
                serialized_data,
                cls=CustomJSONEncoder
            ).encode()
        except Exception as e:
            logger.error(f"Error in JSON serialization: {str(e)}")
    
    return response

class ChatQuery(BaseModel):
    query: str
    user_id: Optional[str] = "default"

class NewsRefreshOptions(BaseModel):
    sources: Optional[List[str]] = None

class EntityNewsQuery(BaseModel):
    entity: str
    days: Optional[int] = 30

class AdvancedSearchQuery(BaseModel):
    query: str
    entity_type: Optional[str] = None  # stock, fund, etf, news
    date_range: Optional[int] = 30  # days

@app.on_event("startup")
async def startup_event():
    """Initialize database connection and collections on startup"""
    try:
        await db_service.connect()
        await db_service.init_collections()
    except Exception as e:
        logger.error(f"Failed to initialize database: {str(e)}")
        raise e

@app.get("/")
async def root():
    """Root endpoint"""
    return {"message": "Welcome to NewsWise Financial API"}

@app.post("/api/chat/query")
async def process_chat_query(chat_query: ChatQuery):
    """Process a chat query and return relevant information"""
    try:
        return await chatbot_service.process_query(chat_query.query, chat_query.user_id)
    except Exception as e:
        logger.error(f"Error processing chat query: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/news/recent")
async def get_recent_news(limit: int = 20):
    """Get recent news articles"""
    try:
        return await db_service.get_recent_news(limit)
    except Exception as e:
        logger.error(f"Error fetching recent news: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/news/entity/{entity_name}")
async def get_news_by_entity(entity_name: str, days: int = 30):
    """Get news articles related to a specific entity"""
    try:
        news_items = await db_service.get_news_by_entity_advanced(entity_name, days)
        
        # If we don't have enough news, try to scrape more
        if len(news_items) < 5:
            additional_news = await news_scraper_service.search_company_news(entity_name, days)
            if additional_news:
                news_items.extend(additional_news)
                
        return news_items
    except Exception as e:
        logger.error(f"Error fetching news for entity {entity_name}: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/news/search")
async def search_news(query: AdvancedSearchQuery):
    """Search news using text search"""
    try:
        if query.entity_type == "news" or not query.entity_type:
            return await db_service.search_news(query.query)
        else:
            return await db_service.get_news_by_entity_advanced(query.query, query.date_range)
    except Exception as e:
        logger.error(f"Error searching news: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/news/refresh")
async def refresh_news(options: Optional[NewsRefreshOptions] = None):
    """Fetch fresh news from all sources"""
    try:
        count = await news_scraper_service.refresh_news()
        return {"message": f"Successfully fetched {count} news articles"}
    except Exception as e:
        logger.error(f"Error refreshing news: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/stocks/{symbol}")
async def get_stock_data(symbol: str):
    try:
        stock_data = await stock_service.fetch_stock_data(symbol)
        if stock_data:
            return {"status": "success", "data": stock_data}
        else:
            raise HTTPException(status_code=404, detail="Stock data not found")
    except Exception as e:
        logger.error(f"Error fetching stock data for {symbol}: {str(e)}")
        raise HTTPException(status_code=500, detail="Error retrieving stock information")

@app.get("/api/funds/{scheme_name}")
async def get_fund_info(scheme_name: str):
    """Get information about a specific mutual fund"""
    try:
        fund_info = await db_service.get_fund_info(scheme_name)
        if not fund_info:
            raise HTTPException(status_code=404, detail=f"Fund with name {scheme_name} not found")
        return fund_info
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching fund info for {scheme_name}: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/funds/{scheme_name}/holdings")
async def get_fund_holdings(scheme_name: str):
    """Get holdings data for a specific mutual fund"""
    try:
        holdings = await db_service.get_holdings_data(scheme_name)
        return holdings
    except Exception as e:
        logger.error(f"Error fetching holdings for {scheme_name}: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/etfs/{symbol}")
async def get_etf_info(symbol: str):
    """Get information about a specific ETF"""
    try:
        # Use the unified financial data getter
        financial_data = await db_service.get_financial_data_by_identifier(symbol)
        if not financial_data or financial_data["type"] != "etf":
            raise HTTPException(status_code=404, detail=f"ETF with symbol {symbol} not found")
        return financial_data["data"]
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching ETF info for {symbol}: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/financial-data/search")
async def unified_financial_search(query: AdvancedSearchQuery):
    """Search for any financial instrument by identifier"""
    try:
        financial_data = await db_service.get_financial_data_by_identifier(query.query)
        if not financial_data:
            raise HTTPException(status_code=404, detail=f"No financial data found for {query.query}")
            
        # If entity type specified, verify it matches
        if query.entity_type and financial_data["type"] != query.entity_type:
            raise HTTPException(
                status_code=404, 
                detail=f"Found {financial_data['type']} but requested {query.entity_type}"
            )
            
        return financial_data
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in unified financial search for {query.query}: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/chat")
async def process_chat(request: Dict[Any, Any]):
    try:
        message = request.get('message', '').strip()
        
        # Check if the message is a stock query
        stock_pattern = r'^(?:get |show |what is |price of |stock )?([A-Z]+)(?:\s+stock)?\s*(?:price|details|info)?\??$'
        stock_match = re.match(stock_pattern, message, re.IGNORECASE)
        
        if stock_match:
            symbol = stock_match.group(1).upper()
            stock_data = await stock_service.fetch_stock_data(symbol)
            
            if stock_data:
                response = (
                    f"Here's the latest information for {stock_data['name']} ({stock_data['symbol']}):\n"
                    f"Price: ₹{stock_data['price']:,.2f}\n"
                    f"Change: ₹{stock_data['change']:,.2f} ({stock_data['changePercent']:,.2f}%)\n"
                    f"Volume: {stock_data['volume']:,}\n"
                    f"Market Cap: ₹{stock_data['marketCap']:,.2f} Cr\n"
                    f"Sector: {stock_data['sector']}\n"
                    f"Last Updated: {stock_data['lastUpdated']}"
                )
            else:
                response = f"Sorry, I couldn't find any information for the stock symbol {symbol}."
        else:
            # Process regular chat messages here
            response = "I understand you're asking about something else. How can I help you?"
        
        return {
            "status": "success",
            "response": response,
            "timestamp": datetime.now().isoformat()
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/funds")
async def get_all_funds():
    """Get all mutual funds and ETFs from the dataset"""
    try:
        # Use mock data if CSV cannot be loaded
        try:
            funds = await db_service.load_mutual_fund_data()
            return {"status": "success", "data": funds}
        except Exception as e:
            logger.error(f"Error loading mutual fund data from CSV: {str(e)}")
            # Create mock data directly if method fails
            mock_funds = [
                {
                    "name": "HDFC Top 100 Fund",
                    "type": "Mutual Fund",
                    "nav": 850.25,
                    "aum": 21500,
                    "oneYearReturn": 15.8,
                    "threeYearReturn": 12.5,
                    "category": "Large Cap",
                    "riskLevel": "Moderate",
                    "amcName": "HDFC Asset Management Company Ltd"
                },
                {
                    "name": "Nifty BeES",
                    "type": "ETF",
                    "nav": 220.15,
                    "aum": 12800,
                    "oneYearReturn": 18.2,
                    "threeYearReturn": 14.7,
                    "category": "Index Fund",
                    "riskLevel": "Moderate",
                    "amcName": "Nippon India Asset Management Ltd"
                },
                {
                    "name": "SBI Blue Chip Fund",
                    "type": "Mutual Fund",
                    "nav": 65.78,
                    "aum": 32600,
                    "oneYearReturn": 16.4,
                    "threeYearReturn": 13.2,
                    "category": "Large Cap",
                    "riskLevel": "Moderate",
                    "amcName": "SBI Funds Management Ltd"
                },
                {
                    "name": "Axis Midcap Fund",
                    "type": "Mutual Fund",
                    "nav": 78.92,
                    "aum": 18700,
                    "oneYearReturn": 22.6,
                    "threeYearReturn": 17.8,
                    "category": "Mid Cap",
                    "riskLevel": "High",
                    "amcName": "Axis Asset Management Company Ltd"
                },
                {
                    "name": "ICICI Prudential Liquid Fund",
                    "type": "Mutual Fund",
                    "nav": 315.45,
                    "aum": 42800,
                    "oneYearReturn": 6.2,
                    "threeYearReturn": 5.8,
                    "category": "Debt Schemes",
                    "riskLevel": "Low",
                    "amcName": "ICICI Prudential Asset Management Company Ltd"
                }
            ]
            return {"status": "success", "data": mock_funds}
    except Exception as e:
        logger.error(f"Error fetching all funds: {str(e)}")
        raise HTTPException(status_code=500, detail="Error retrieving fund information")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001) 