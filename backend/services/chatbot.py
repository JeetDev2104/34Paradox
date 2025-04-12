from transformers import pipeline
from typing import Dict, List, Optional, Tuple
import numpy as np
from .database import db_service
from .news_scraper import news_scraper_service
import logging
import re
import pandas as pd
import os
import math
import json

logger = logging.getLogger(__name__)

# Dictionary to store conversation state for each user session
conversation_states = {}

class ChatbotService:
    def __init__(self):
        # Load sentiment analysis model
        logger.info("Initializing sentiment analysis model...")
        self.sentiment_analyzer = pipeline("sentiment-analysis")
        logger.info("Sentiment analysis model initialized successfully")
        
        # Cache for entity names from database
        self.company_names = []
        self.fund_names = []
        self.tickers = []
        self.sectors = []
        
    def _sanitize_float_values(self, data):
        """Sanitize float values to handle NaN and Infinity"""
        if isinstance(data, dict):
            for key, value in data.items():
                if isinstance(value, float):
                    if math.isnan(value) or math.isinf(value):
                        data[key] = None
                elif isinstance(value, (dict, list)):
                    data[key] = self._sanitize_float_values(value)
        elif isinstance(data, list):
            for i, item in enumerate(data):
                if isinstance(item, float):
                    if math.isnan(item) or math.isinf(item):
                        data[i] = None
                elif isinstance(item, (dict, list)):
                    data[i] = self._sanitize_float_values(item)
        return data
    
    def _is_simple_entity_query(self, query: str) -> Tuple[bool, Optional[str]]:
        """Check if the query is just an entity name without specific request"""
        # Clean the query
        clean_query = re.sub(r'[^\w\s]', '', query).strip().lower()
        words = clean_query.split()
        
        # If query has more than 3 words, it's likely not just an entity name
        if len(words) > 3:
            return False, None
            
        # Check for exact matches in our entity lists
        for company in self.company_names:
            if company and company.lower() == clean_query:
                return True, company
                
        for fund in self.fund_names:
            if fund and fund.lower() == clean_query:
                return True, fund
                
        for ticker in self.tickers:
            if ticker and ticker.lower() == clean_query:
                return True, ticker
        
        # For short queries, check for partial matches too
        if len(words) <= 2:
            for company in self.company_names:
                if company and clean_query in company.lower():
                    return True, company
                    
            for fund in self.fund_names:
                if fund and clean_query in fund.lower():
                    return True, fund
        
        return False, None
        
    def _init_conversation_state(self, session_id: str) -> Dict:
        """Initialize conversation state for a session"""
        conversation_states[session_id] = {
            "state": "initial",
            "entity": None,
            "entity_type": None,
            "last_query": None,
            "awaiting": None
        }
        return conversation_states[session_id]
        
    def _get_conversation_state(self, session_id: str) -> Dict:
        """Get conversation state for a session"""
        if session_id not in conversation_states:
            return self._init_conversation_state(session_id)
        return conversation_states[session_id]
        
    def _detect_comparison_intent(self, query: str) -> Tuple[bool, List[str]]:
        """Detect if query is asking for a comparison between entities"""
        comparison_keywords = [
            "compare", "comparison", "vs", "versus", "or", 
            "difference between", "which is better"
        ]
        
        query_lower = query.lower()
        has_comparison = any(keyword in query_lower for keyword in comparison_keywords)
        
        if not has_comparison:
            return False, []
            
        # Extract entities
        entities = self._extract_entities(query)
        
        # Check if we have multiple entities or "and" in the query
        if len(entities) >= 2 or " and " in query_lower:
            return True, entities
            
        return False, []
    
    async def load_entities_from_csv(self):
        """Load entity names from CSV files for better entity extraction"""
        
        # Load company names and tickers from stock data
        if os.path.exists("stock_data.csv"):
            try:
                stock_df = pd.read_csv("stock_data.csv")
                
                # Extract company names
                if 'name' in stock_df.columns:
                    self.company_names = stock_df['name'].dropna().unique().tolist()
                
                # Extract tickers
                if 'ticker' in stock_df.columns:
                    self.tickers = stock_df['ticker'].dropna().unique().tolist()
                
                # Extract sectors
                if 'sector' in stock_df.columns:
                    self.sectors = stock_df['sector'].dropna().unique().tolist()
                
                logger.info(f"Loaded {len(self.company_names)} companies, {len(self.tickers)} tickers, and {len(self.sectors)} sectors from stock data")
            except Exception as e:
                logger.error(f"Error loading stock data: {str(e)}")
        
        # Load fund names from mutual fund data
        if os.path.exists("cleaned_mutual_fund_data.csv"):
            try:
                fund_df = pd.read_csv("cleaned_mutual_fund_data.csv")
                
                # Extract fund names
                if 'schemeName' in fund_df.columns:
                    self.fund_names = fund_df['schemeName'].dropna().unique().tolist()
                
                # Add AMC names
                if 'amcName' in fund_df.columns:
                    self.company_names.extend(fund_df['amcName'].dropna().unique().tolist())
                    self.company_names = list(set(self.company_names))
                
                logger.info(f"Loaded {len(self.fund_names)} fund names from mutual fund data")
            except Exception as e:
                logger.error(f"Error loading mutual fund data: {str(e)}")
                
        # Add common banks and financial institutions if not already in list
        common_banks = [
            "HDFC Bank", "ICICI Bank", "SBI", "Axis Bank", "Kotak Mahindra Bank",
            "Bank of Baroda", "Punjab National Bank", "Canara Bank", "IndusInd Bank",
            "Yes Bank", "IDFC Bank", "Federal Bank", "RBL Bank", "South Indian Bank"
        ]
        
        for bank in common_banks:
            if bank not in self.company_names:
                self.company_names.append(bank)
        
        logger.info(f"Entity extraction initialized with {len(self.company_names)} companies and {len(self.fund_names)} funds")
    
    def _extract_entities(self, query: str) -> List[str]:
        """Extract entities from the query using loaded company names, funds, tickers, and sectors"""
        entities = []
        query_lower = query.lower()
        
        # Look for exact stock tickers (uppercase words 1-5 chars)
        tickers = re.findall(r'\b[A-Z]{1,5}\b', query)
        entities.extend(tickers)
        
        # Look for company names in the query
        for company in self.company_names:
            if company and company.lower() in query_lower:
                entities.append(company)
        
        # Look for fund names in the query
        for fund in self.fund_names:
            if fund and fund.lower() in query_lower:
                entities.append(fund)
        
        # Look for sector names in the query
        for sector in self.sectors:
            if sector and sector.lower() in query_lower:
                entities.append(sector)
        
        # Add some common sectors if mentioned
        common_sectors = ['Technology', 'Finance', 'Healthcare', 'Energy', 'Consumer', 'Banking']
        for sector in common_sectors:
            if sector.lower() in query_lower:
                entities.append(sector)
        
        return list(set(entities))
    
    def _analyze_sentiment(self, text: str) -> Dict:
        try:
            result = self.sentiment_analyzer(text)[0]
            return {
                "sentiment": result["label"],
                "score": result["score"]
            }
        except Exception as e:
            logger.error(f"Error in sentiment analysis: {str(e)}")
            return {"sentiment": "neutral", "score": 0.5}
    
    async def process_query(self, query: str, session_id: str = "default") -> Dict:
        """Process a user query and return relevant information"""
        try:
            logger.info(f"Processing query: {query}")
            
            # Load entities if not already loaded
            if not self.company_names and not self.fund_names:
                await self.load_entities_from_csv()
            
            # Get or initialize conversation state
            state = self._get_conversation_state(session_id)
            
            # Update conversation state with current query
            state["last_query"] = query
            
            # Check if this is a comparison request
            is_comparison, comparison_entities = self._detect_comparison_intent(query)
            if is_comparison and len(comparison_entities) >= 2:
                logger.info(f"Detected comparison request between: {comparison_entities}")
                return await self._handle_comparison_request(comparison_entities)
            
            # Check if we're in the middle of an entity type conversation
            if state["state"] == "awaiting_entity_type" and state["entity"]:
                entity_types = ["stock", "mutual fund", "fund", "etf"]
                specified_type = None
                
                # Check if user specified an entity type
                for et in entity_types:
                    if et.lower() in query.lower():
                        specified_type = et
                        break
                
                if specified_type:
                    # User specified a type, get data for it
                    logger.info(f"User specified {specified_type} for entity {state['entity']}")
                    
                    # Handle "fund" and "mutual fund" consistently
                    if specified_type == "mutual fund" or specified_type == "fund":
                        entity_type = "fund"
                    else:
                        entity_type = specified_type
                    
                    # Reset state
                    state["state"] = "initial"
                    
                    return await self._get_entity_data(state["entity"], entity_type)
                else:
                    # User didn't clearly specify what type of data they want
                    return {
                        "answer": f"Would you like information about {state['entity']} as a stock, mutual fund, or ETF?",
                        "confidence": 0.9,
                        "is_prompt": True,
                        "related_news": [],
                        "financial_data": {}
                    }
            
            # Check if this is just an entity name
            is_entity_only, entity_name = self._is_simple_entity_query(query)
            
            if is_entity_only and entity_name:
                # User entered just an entity name, ask for clarification
                logger.info(f"Detected entity-only query: {entity_name}")
                
                # Update state
                state["entity"] = entity_name
                state["state"] = "awaiting_entity_type"
                
                return {
                    "answer": f"I found information about {entity_name}. Would you like details about it as a stock, mutual fund, or ETF?",
                    "confidence": 0.9,
                    "is_prompt": True,
                    "related_news": [],
                    "financial_data": {}
                }
                
            # Handle specific question patterns
            response = await self.handle_specific_questions(query)
            if response:
                # Reset state since this was a complete query
                state["state"] = "initial"
                
                # Sanitize float values
                if "financial_data" in response:
                    response["financial_data"] = self._sanitize_float_values(response["financial_data"])
                    
                return response
                
            # Extract relevant entities
            entities = self._extract_entities(query)
            logger.info(f"Extracted entities: {entities}")
            
            # If no entities found, try to extract keywords
            if not entities:
                keywords = query.lower().split()
                logger.info(f"No entities found, using keywords: {keywords}")
                
                # Try to match keywords with company names or fund names
                for company in self.company_names:
                    if company and any(kw in company.lower() for kw in keywords if len(kw) > 3):
                        entities.append(company)
                
                for fund in self.fund_names:
                    if fund and any(kw in fund.lower() for kw in keywords if len(kw) > 3):
                        entities.append(fund)
            
            # Get relevant news and financial data
            news_items = []
            financial_data = {}
            
            for entity in entities:
                # Get news related to the entity
                entity_news = await db_service.get_news_by_entity_advanced(entity)
                if entity_news:
                    news_items.extend(entity_news)
                
                # Try to get financial data
                financial_item = await db_service.get_financial_data_by_identifier(entity)
                if financial_item:
                    financial_data[financial_item["type"]] = financial_item["data"]
                    
                    # Get holdings for funds
                    if financial_item["type"] == "fund":
                        holdings = await db_service.get_holdings_data(entity)
                        if holdings:
                            financial_data["holdings"] = holdings[:10]
            
            # If looking for news specifically, get recent news
            if "news" in query.lower() and not news_items:
                recent_news = await db_service.get_recent_news(5)
                if recent_news:
                    news_items = recent_news
            
            # If still no news or minimal financial data, search external sources
            if (len(news_items) < 2 or not financial_data) and not is_entity_only:
                external_news = await self._search_external_news(query)
                if external_news:
                    # Add external news to our results with a source tag
                    for news in external_news:
                        if "source" in news:
                            news["source"] = f"[External] {news['source']}"
                    news_items.extend(external_news)
            
            # Generate response
            response = self._generate_response(query, news_items, financial_data)
            
            # Reset state
            state["state"] = "initial"
            
            # Sanitize float values
            financial_data = self._sanitize_float_values(financial_data)
            
            return {
                "answer": response,
                "confidence": 0.85 if entities or news_items or financial_data else 0.5,
                "related_news": news_items[:5],
                "financial_data": financial_data
            }
            
        except Exception as e:
            logger.error(f"Error processing query: {str(e)}")
            return {
                "answer": "I apologize, but I encountered an error processing your query. Please try again.",
                "confidence": 0,
                "related_news": [],
                "financial_data": {}
            }
    
    async def handle_specific_questions(self, query: str) -> Optional[Dict]:
        """Handle specific question patterns with customized responses"""
        try:
            query_lower = query.lower()
            
            # Check if this is a "why did X up/down today" question
            stock_movement_match = re.search(r'why did ([a-z0-9\s]+) (up|down|rise|fall|jump|drop|surge|plunge|increase|decrease) (today|yesterday|this week|last week|this month)', query_lower)
            if stock_movement_match:
                company_name = stock_movement_match.group(1).strip()
                direction = stock_movement_match.group(2)
                time_period = stock_movement_match.group(3)
                
                return await self._handle_stock_movement_question(company_name, direction, time_period)
            
            # Check if this is a "what happened to X this week/month" question
            market_event_match = re.search(r'what happened to ([a-z0-9\s]+) (today|yesterday|this week|last week|this month)', query_lower)
            if market_event_match:
                entity_name = market_event_match.group(1).strip()
                time_period = market_event_match.group(2)
                
                return await self._handle_market_event_question(entity_name, time_period)
            
            # Check if this is a question about macro news affecting funds/sectors
            macro_news_match = re.search(r'(macro|economic|global) news (impact|affecting|hitting) ([a-z0-9\s\-]+) (funds|stocks|etfs|sector)', query_lower)
            if macro_news_match:
                news_type = macro_news_match.group(1)
                action = macro_news_match.group(2)
                entity = macro_news_match.group(3).strip()
                asset_type = macro_news_match.group(4)
                
                return await self._handle_macro_news_question(news_type, action, entity, asset_type)
            
            # Check if this is a question about quarterly results
            quarterly_results_match = re.search(r'(what does|how was) the last quarter (for|say for|results for) ([a-z0-9\s]+)', query_lower)
            if quarterly_results_match:
                question_type = quarterly_results_match.group(1)
                context = quarterly_results_match.group(2)
                company_name = quarterly_results_match.group(3).strip()
                
                return await self._handle_quarterly_results_question(company_name)
        except Exception as e:
            logger.error(f"Error in handle_specific_questions: {str(e)}")
            # Return a fallback response instead of passing the exception up
            return {
                "answer": f"I couldn't process your specific question. Please try asking in a different way.",
                "confidence": 0.5,
                "related_news": [],
                "financial_data": {}
            }
            
        return None
        
    async def _handle_stock_movement_question(self, company_name: str, direction: str, time_period: str) -> Dict:
        """Handle a question about stock movement"""
        try:
            # Normalize company name
            normalized_company = self._normalize_entity_name(company_name)
            
            # Look for relevant news about the company
            news_items = await db_service.get_news_by_entity_advanced(normalized_company, days=30)
            
            # If no news found, try to scrape some
            if len(news_items) < 3:
                additional_news = await news_scraper_service.search_company_news(normalized_company)
                if additional_news:
                    news_items.extend(additional_news)
                    
            # Try to get financial data
            financial_data = await self._get_entity_data(normalized_company, entity_type="stock")
            
            # If no financial data found in database, use a better fallback response
            if not financial_data or 'data' not in financial_data:
                fallback_response = f"I couldn't find specific market data for {company_name} in our database. However, based on general market trends and news sentiment, {company_name} has likely been affected by broader market movements. For real-time stock information, please check financial portals like NSE or BSE."
                
                return {
                    "answer": fallback_response,
                    "confidence": 0.7,
                    "related_news": news_items[:3] if news_items else [],
                    "financial_data": {}
                }
                                    
            # Generate a response based on the collected data
            response = self._generate_response("stock movement", news_items, financial_data)
            
            return {
                "answer": response,
                "confidence": 0.9,
                "related_news": news_items[:3],
                "financial_data": financial_data
            }
        except Exception as e:
            logger.error(f"Error in stock movement question: {str(e)}")
            return {
                "answer": f"I couldn't find specific information about {company_name}'s recent stock movements. Please try asking in a different way or check financial news sources for the latest updates.",
                "confidence": 0.5,
                "related_news": [],
                "financial_data": {}
            }
        
    async def _handle_market_event_question(self, entity_name: str, time_period: str) -> Dict:
        """Handle questions about what happened to a market entity in a period"""
        # Check if entity is an index like Nifty
        is_index = entity_name.lower() in ["nifty", "nifty 50", "nifty50", "sensex", "bse", "nse"]
        
        # Get days based on time period
        days = 1 if time_period == "today" else 2 if time_period == "yesterday" else 7 if "week" in time_period else 30
        
        # Get news
        news_items = await db_service.get_news_by_entity_advanced(entity_name, days)
        
        # If we don't have enough news, try to scrape more
        if len(news_items) < 3:
            from .news_scraper import news_scraper_service
            additional_news = await news_scraper_service.search_company_news(entity_name, days)
            if additional_news:
                await db_service.store_scraped_news(additional_news)
                news_items.extend(additional_news)
                
        # Get financial data
        financial_data = await db_service.get_financial_data_by_identifier(entity_name)
        entity_data = financial_data["data"] if financial_data else None
        entity_type = financial_data["type"] if financial_data else None
        
        # Build the answer
        answer_parts = []
        
        # Add performance information if available
        if entity_data:
            performance_text = ""
            if entity_type == "stock":
                if "1DReturns" in entity_data and time_period == "today":
                    change = float(entity_data["1DReturns"])
                    direction = "up" if change > 0 else "down"
                    performance_text = f"{entity_name} moved {direction} by {abs(change):.2f}% today."
                elif "1WReturns" in entity_data and "week" in time_period:
                    change = float(entity_data["1WReturns"])
                    direction = "up" if change > 0 else "down"
                    performance_text = f"{entity_name} moved {direction} by {abs(change):.2f}% this week."
                    
            if performance_text:
                answer_parts.append(performance_text)
                
        # Add news summary
        if news_items:
            if is_index:
                answer_parts.append(f"\nHere's what happened with {entity_name} {time_period}:")
            else:
                answer_parts.append(f"\nRecent news about {entity_name}:")
                
            for idx, news in enumerate(news_items[:3]):
                date_str = news.get("date", "").split("T")[0] if news.get("date") else ""
                answer_parts.append(f"{idx+1}. {news.get('title')} ({date_str})")
                if idx == 0 and news.get("summary"):  # Add summary for the first news item
                    answer_parts.append(f"   {news.get('summary')}")
        else:
            answer_parts.append(f"I couldn't find specific news about {entity_name} for {time_period}.")
            
        # Combine everything
        answer = "\n".join(answer_parts)
        
        return {
            "answer": answer,
            "confidence": 0.8,
            "related_news": news_items[:5],
            "financial_data": {entity_type: entity_data} if entity_data else {}
        }
        
    async def _handle_macro_news_question(self, news_type: str, action: str, entity: str, asset_type: str) -> Dict:
        """Handle questions about macro news impacting funds or sectors"""
        # Get news items
        search_terms = [news_type, entity, asset_type]
        news_items = []
        
        for term in search_terms:
            term_news = await db_service.search_news(term)
            news_items.extend(term_news)
            
        # Deduplicate news
        unique_news = []
        seen_titles = set()
        for news in news_items:
            if news.get("title") not in seen_titles:
                seen_titles.add(news.get("title"))
                unique_news.append(news)
                
        news_items = unique_news
        
        # Filter for relevance - keep only news that mentions both macro factors and the entity
        relevant_news = []
        for news in news_items:
            title = news.get("title", "").lower()
            summary = news.get("summary", "").lower()
            text = title + " " + summary
            
            is_macro = any(term in text for term in ["economic", "economy", "macro", "global", "market", "fed", "rbi", "interest rate", "inflation"])
            mentions_entity = entity.lower() in text or asset_type.lower() in text
            
            if is_macro and mentions_entity:
                relevant_news.append(news)
                
        # Build response
        if not relevant_news:
            answer = f"I couldn't find specific information about {news_type} news affecting {entity} {asset_type}. Try a broader search or different keywords."
            return {
                "answer": answer,
                "confidence": 0.5,
                "related_news": news_items[:5],
                "financial_data": {}
            }
            
        answer_parts = []
        answer_parts.append(f"Here's how {news_type} news is affecting {entity} {asset_type}:")
        
        for idx, news in enumerate(relevant_news[:3]):
            date_str = news.get("date", "").split("T")[0] if news.get("date") else ""
            sentiment = f" ({news.get('sentiment', 'neutral').capitalize()})" if news.get("sentiment") else ""
            answer_parts.append(f"{idx+1}. {news.get('title')}{sentiment} ({date_str})")
            if idx == 0 and news.get("summary"):
                answer_parts.append(f"   {news.get('summary')}")
                
        answer = "\n".join(answer_parts)
        
        return {
            "answer": answer,
            "confidence": 0.8,
            "related_news": relevant_news[:5],
            "financial_data": {}
        }
        
    async def _handle_quarterly_results_question(self, company_name: str) -> Dict:
        """Handle questions about a company's quarterly results"""
        # Try to find the best matching company name
        best_match = None
        for name in self.company_names:
            if name and company_name in name.lower():
                best_match = name
                break
                
        if best_match:
            company_name = best_match
            
        # Get news about quarterly results
        search_terms = [f"{company_name} quarterly results", f"{company_name} earnings", f"{company_name} q1", f"{company_name} q2", f"{company_name} q3", f"{company_name} q4"]
        all_news = []
        
        for term in search_terms:
            news_items = await db_service.search_news(term)
            all_news.extend(news_items)
            
        # Deduplicate
        unique_news = []
        seen_titles = set()
        for news in all_news:
            if news.get("title") not in seen_titles:
                seen_titles.add(news.get("title"))
                unique_news.append(news)
                
        # Filter for relevance - must mention earnings, results, quarter, or financial performance
        quarterly_news = []
        for news in unique_news:
            title = news.get("title", "").lower()
            summary = news.get("summary", "").lower()
            text = title + " " + summary
            
            if any(term in text for term in ["quarter", "quarterly", "earnings", "results", "profit", "revenue", "financial performance"]):
                quarterly_news.append(news)
                
        # If we still don't have enough news, try to scrape more
        if len(quarterly_news) < 2:
            from .news_scraper import news_scraper_service
            for term in search_terms:
                additional_news = await news_scraper_service.search_company_news(term)
                if additional_news:
                    # Filter and add to results
                    for news in additional_news:
                        title = news.get("title", "").lower()
                        summary = news.get("summary", "").lower()
                        text = title + " " + summary
                        
                        if any(term in text for term in ["quarter", "quarterly", "earnings", "results", "profit", "revenue"]):
                            # Add to database and results if not already there
                            if news.get("title") not in seen_titles:
                                seen_titles.add(news.get("title"))
                                quarterly_news.append(news)
                    
                    # Stop if we have enough
                    if len(quarterly_news) >= 3:
                        break
                        
        # Get financial data
        financial_data = await db_service.get_financial_data_by_identifier(company_name)
        
        # Build response
        answer_parts = []
        
        if not quarterly_news:
            answer = f"I couldn't find specific information about {company_name}'s last quarterly results. Try asking about a different company or check back later for updates."
            return {
                "answer": answer,
                "confidence": 0.5,
                "related_news": [],
                "financial_data": financial_data if financial_data else {}
            }
            
        answer_parts.append(f"Here's information about {company_name}'s last quarter results:")
        
        for idx, news in enumerate(quarterly_news[:3]):
            date_str = news.get("date", "").split("T")[0] if news.get("date") else ""
            sentiment = f" ({news.get('sentiment', 'neutral').capitalize()})" if news.get("sentiment") else ""
            answer_parts.append(f"{idx+1}. {news.get('title')}{sentiment} ({date_str})")
            if news.get("summary"):
                answer_parts.append(f"   {news.get('summary')}")
                
        answer = "\n".join(answer_parts)
        
        return {
            "answer": answer,
            "confidence": 0.9,
            "related_news": quarterly_news[:5],
            "financial_data": financial_data if financial_data else {}
        }
    
    def _generate_response(self, query: str, news_items: List[Dict], financial_data: Dict) -> str:
        """Generate a natural language response based on news and financial data"""
        query_lower = query.lower()
        
        # Check if we have any data to work with
        has_news = len(news_items) > 0
        has_financial_data = bool(financial_data)
        
        # Categorize available news by source (internal vs external)
        internal_news = [news for news in news_items if not news.get("source", "").startswith("[External]")]
        external_news = [news for news in news_items if news.get("source", "").startswith("[External]")]
        
        # Determine if query is asking about specific types of information
        is_news_query = any(word in query_lower for word in ["news", "update", "latest", "report", "announcement"])
        is_price_query = any(word in query_lower for word in ["price", "value", "worth", "cost", "rate"])
        is_performance_query = any(word in query_lower for word in ["performance", "return", "gain", "growth"])
        
        # Start building the response
        response_parts = []
        
        # If we have financial data and the query is about price or performance
        if has_financial_data and (is_price_query or is_performance_query):
            # Handle stock data
            if "stock" in financial_data:
                stock = financial_data["stock"]
                stock_name = stock.get("name", "the stock")
                
                if is_price_query and "price" in stock:
                    response_parts.append(f"The current price of {stock_name} is ₹{stock['price']}.")
                    
                if is_performance_query:
                    if "1DReturns" in stock:
                        change = stock["1DReturns"]
                        direction = "up" if change > 0 else "down"
                        response_parts.append(f"{stock_name} is {direction} by {abs(change):.2f}% today.")
                        
                    if "1YReturns" in stock:
                        yearly = stock["1YReturns"]
                        response_parts.append(f"The 1-year return is {yearly:.2f}%.")
            
            # Handle fund data
            elif "fund" in financial_data:
                fund = financial_data["fund"]
                fund_name = fund.get("scheme_name", "the fund")
                
                if is_price_query and "nav" in fund:
                    response_parts.append(f"The current NAV of {fund_name} is ₹{fund['nav']}.")
                    
                if is_performance_query:
                    if "1YReturns" in fund:
                        yearly = fund["1YReturns"]
                        response_parts.append(f"The 1-year return is {yearly:.2f}%.")
        
        # If we have news and query is about news or if no specific financial data was found
        if has_news and (is_news_query or not response_parts):
            # First use internal news
            if internal_news:
                news = internal_news[0]  # Take the first news item
                response_parts.append(f"According to {news.get('source', 'recent news')}, {news.get('title', 'there are updates available')}.")
                
                if len(internal_news) > 1:
                    response_parts.append(f"There are {len(internal_news)} more related news items available.")
            
            # Then add external news if available and not already covered
            if external_news:
                ext_news = external_news[0]  # Take the first external news
                source = ext_news.get('source', 'external sources').replace("[External] ", "")
                title = ext_news.get('title', 'additional information is available')
                summary = ext_news.get('summary', '')
                url = ext_news.get('url', '')
                
                # Add the title from the external source
                response_parts.append(f"{source} reports: {title}")
                
                # Add a summary if available
                if summary and len(summary) > 10:  # Ensure it's not an empty or tiny summary
                    response_parts.append(f"Summary: {summary}")
                
                # Mention the source URL for reference
                if url:
                    response_parts.append(f"For more details, refer to: {url}")
                
                if len(external_news) > 1:
                    response_parts.append(f"I found {len(external_news) - 1} additional news sources with relevant information.")
        
        # If we still don't have a response, provide a generic answer
        if not response_parts:
            if is_news_query:
                response_parts.append("I couldn't find any recent news matching your query. You might want to try a more specific question.")
            elif is_price_query or is_performance_query:
                response_parts.append("I don't have the specific financial data you're looking for. Please try asking about a specific stock or fund.")
            else:
                response_parts.append("I don't have enough information to answer your query. Please try a more specific question about stocks, funds, or market news.")
        
        # Join the response parts into a single string
        return " ".join(response_parts)

    async def _get_entity_data(self, entity_name: str, entity_type: str = None) -> Dict:
        """Get data for a specific entity with specified type"""
        financial_data = {}
        news_items = []
        
        # Normalize entity name for better matching
        normalized_entity = entity_name.lower()
        # Remove common suffixes like Ltd., Limited, etc.
        normalized_entity = re.sub(r'\s+(ltd\.?|limited|corp\.?|corporation|inc\.?)$', '', normalized_entity)
        
        logger.info(f"Looking for entity data: {entity_name} (normalized: {normalized_entity}), type: {entity_type}")
        
        # Try to get financial data
        if entity_type:
            # If type is specified, get data for that specific type
            if entity_type == "stock":
                # Try exact match first
                stock_data = await db_service.get_stock_info(entity_name)
                
                # If not found, try with normalized name
                if not stock_data:
                    stock_data = await db_service.get_stock_info(normalized_entity)
                
                # If still not found, try with just the first word (for companies like HDFC, SBI)
                if not stock_data and ' ' in normalized_entity:
                    first_word = normalized_entity.split()[0]
                    stock_data = await db_service.get_stock_info(first_word)
                
                if stock_data:
                    financial_data["stock"] = stock_data
            elif entity_type == "fund" or entity_type == "mutual fund":
                # Similar approach for funds
                fund_data = await db_service.get_fund_info(entity_name)
                
                if not fund_data:
                    fund_data = await db_service.get_fund_info(normalized_entity)
                
                if fund_data:
                    financial_data["fund"] = fund_data
            elif entity_type == "etf":
                etf_data = await db_service.get_financial_data_by_identifier(entity_name)
                if not etf_data:
                    etf_data = await db_service.get_financial_data_by_identifier(normalized_entity)
                
                if etf_data and etf_data["type"] == "etf":
                    financial_data["etf"] = etf_data["data"]
        else:
            # Otherwise try the unified getter
            financial_item = await db_service.get_financial_data_by_identifier(entity_name)
            if not financial_item:
                financial_item = await db_service.get_financial_data_by_identifier(normalized_entity)
                
            if not financial_item and ' ' in normalized_entity:
                first_word = normalized_entity.split()[0]
                financial_item = await db_service.get_financial_data_by_identifier(first_word)
                
            if financial_item:
                financial_data[financial_item["type"]] = financial_item["data"]
                
                # Get holdings data for funds
                if financial_item["type"] == "fund":
                    holdings = await db_service.get_holdings_data(entity_name)
                    if holdings:
                        financial_data["holdings"] = holdings[:10]
                        
        # Get news for the entity
        entity_news = await db_service.get_news_by_entity_advanced(entity_name)
        if entity_news:
            news_items = entity_news
            
        # Sanitize data
        financial_data = self._sanitize_float_values(financial_data)
        
        # Prepare response based on what we found
        entity_type_display = entity_type if entity_type else (
            list(financial_data.keys())[0] if financial_data else "entity")
            
        if entity_type_display == "fund":
            entity_type_display = "mutual fund"
            
        if financial_data:
            data_key = list(financial_data.keys())[0]
            entity_data = financial_data[data_key]
            
            # Format name for display
            display_name = entity_name
            if "name" in entity_data:
                display_name = entity_data["name"]
            elif "scheme_name" in entity_data:
                display_name = entity_data["scheme_name"]
                
            answer_parts = [f"Here's information about {display_name} ({entity_type_display}):"]
            
            # Add key metrics based on entity type
            if data_key == "stock":
                if "price" in entity_data:
                    answer_parts.append(f"Price: ₹{entity_data['price']}")
                if "change" in entity_data and "changePercent" in entity_data:
                    sign = "+" if entity_data["change"] > 0 else ""
                    answer_parts.append(f"Change: {sign}{entity_data['change']} ({sign}{entity_data['changePercent']}%)")
            elif data_key == "fund":
                if "nav" in entity_data:
                    answer_parts.append(f"NAV: ₹{entity_data['nav']}")
                if "category" in entity_data:
                    answer_parts.append(f"Category: {entity_data['category']}")
                
            # Add news summary
            if news_items:
                answer_parts.append("\nRecent news:")
                for i, news in enumerate(news_items[:3]):
                    answer_parts.append(f"{i+1}. {news.get('title', 'Untitled')}")
                    
            answer = "\n".join(answer_parts)
        else:
            answer = f"I couldn't find specific information about {entity_name} as a {entity_type_display}."
            
        return {
            "answer": answer,
            "confidence": 0.9 if financial_data else 0.5,
            "related_news": news_items[:5],
            "financial_data": financial_data
        }
    
    async def _handle_comparison_request(self, entities: List[str]) -> Dict:
        """Compare multiple financial entities"""
        try:
            logger.info(f"Handling comparison between: {entities}")
            
            if len(entities) < 2:
                return None  # Not enough entities to compare
            
            # Limit to first two entities for clearer comparison
            entities = entities[:2]
            comparison_data = []
            
            for entity in entities:
                # Get financial data for entity
                financial_item = await db_service.get_financial_data_by_identifier(entity)
                if financial_item:
                    comparison_data.append({
                        "entity": entity,
                        "type": financial_item["type"],
                        "data": financial_item["data"]
                    })
            
            # Check if we have data for both entities
            if len(comparison_data) < 2:
                return {
                    "answer": f"I couldn't find enough information to compare {' and '.join(entities)}.",
                    "confidence": 0.6,
                    "related_news": [],
                    "financial_data": {},
                }
            
            # Check if entities are of the same type
            if comparison_data[0]["type"] != comparison_data[1]["type"]:
                return {
                    "answer": f"I can't directly compare {comparison_data[0]['entity']} ({comparison_data[0]['type']}) with {comparison_data[1]['entity']} ({comparison_data[1]['type']}) as they are different types of financial instruments.",
                    "confidence": 0.8,
                    "related_news": [],
                    "financial_data": {},
                }
            
            # Generate comparison based on entity type
            entity_type = comparison_data[0]["type"]
            entity1 = comparison_data[0]["data"]
            entity2 = comparison_data[1]["data"]
            
            # Get display names
            name1 = entity1.get("name", entity1.get("scheme_name", comparison_data[0]["entity"]))
            name2 = entity2.get("name", entity2.get("scheme_name", comparison_data[1]["entity"]))
            
            # Prepare tabular comparison data
            table_data = {
                "headers": ["Metric", name1, name2, "Difference/Notes"],
                "rows": []
            }
            
            answer_parts = [f"Comparison between {name1} and {name2} ({entity_type}):"]
            
            # Compare metrics based on entity type
            if entity_type == "stock":
                # Price comparison
                if "price" in entity1 and "price" in entity2:
                    price1 = entity1["price"]
                    price2 = entity2["price"]
                    price_diff = price1 - price2
                    
                    table_data["rows"].append({
                        "metric": "Current Price (₹)",
                        "value1": f"{price1:,.2f}",
                        "value2": f"{price2:,.2f}",
                        "difference": f"{abs(price_diff):,.2f} ({name1 if price1 > price2 else name2} higher)"
                    })
                    
                    answer_parts.append(f"Price: {name1} ₹{price1:,.2f} vs {name2} ₹{price2:,.2f}")
                
                # Performance metrics
                for period, label in [
                    ("1DReturns", "1-Day Return"),
                    ("1WReturns", "1-Week Return"),
                    ("1MReturns", "1-Month Return"),
                    ("3MReturns", "3-Month Return"),
                    ("1YReturns", "1-Year Return")
                ]:
                    if period in entity1 and period in entity2:
                        val1 = entity1[period]
                        val2 = entity2[period]
                        
                        if val1 is not None and val2 is not None:
                            diff = val1 - val2
                            better = name1 if val1 > val2 else name2
                            
                            table_data["rows"].append({
                                "metric": f"{label} (%)",
                                "value1": f"{val1:+.2f}%",
                                "value2": f"{val2:+.2f}%",
                                "difference": f"{abs(diff):.2f}% ({better} better)"
                            })
                
                # Market cap if available
                if "market_cap" in entity1 and "market_cap" in entity2:
                    mc1 = entity1["market_cap"]
                    mc2 = entity2["market_cap"]
                    
                    if mc1 and mc2:
                        mc_diff = mc1 - mc2
                        larger = name1 if mc1 > mc2 else name2
                        
                        table_data["rows"].append({
                            "metric": "Market Cap (₹ Cr)",
                            "value1": f"{mc1:,.2f}",
                            "value2": f"{mc2:,.2f}",
                            "difference": f"{larger} is larger by {abs(mc1/mc2 - 1):.1%}"
                        })
                
                # P/E ratio
                if "pe_ratio" in entity1 and "pe_ratio" in entity2:
                    pe1 = entity1["pe_ratio"]
                    pe2 = entity2["pe_ratio"]
                    
                    if pe1 and pe2:
                        pe_diff = pe1 - pe2
                        lower_pe = name1 if pe1 < pe2 else name2
                        
                        table_data["rows"].append({
                            "metric": "P/E Ratio",
                            "value1": f"{pe1:.2f}",
                            "value2": f"{pe2:.2f}",
                            "difference": f"{lower_pe} has lower P/E by {abs(pe_diff):.2f}"
                        })
            
            elif entity_type == "fund":
                # NAV comparison
                if "nav" in entity1 and "nav" in entity2:
                    nav1 = entity1["nav"]
                    nav2 = entity2["nav"]
                    nav_diff = nav1 - nav2
                    
                    table_data["rows"].append({
                        "metric": "Current NAV (₹)",
                        "value1": f"{nav1:,.2f}",
                        "value2": f"{nav2:,.2f}",
                        "difference": f"₹{abs(nav_diff):,.2f} difference"
                    })
                    
                    answer_parts.append(f"NAV: {name1} ₹{nav1:,.2f} vs {name2} ₹{nav2:,.2f}")
                
                # Performance metrics
                for period, label in [
                    ("1DReturns", "1-Day Return"),
                    ("1WReturns", "1-Week Return"),
                    ("1MReturns", "1-Month Return"),
                    ("3MReturns", "3-Month Return"),
                    ("1YReturns", "1-Year Return")
                ]:
                    if period in entity1 and period in entity2:
                        val1 = entity1[period]
                        val2 = entity2[period]
                        
                        if val1 is not None and val2 is not None:
                            diff = val1 - val2
                            better = name1 if val1 > val2 else name2
                            
                            table_data["rows"].append({
                                "metric": f"{label} (%)",
                                "value1": f"{val1:+.2f}%",
                                "value2": f"{val2:+.2f}%",
                                "difference": f"{abs(diff):.2f}% ({better} better)"
                            })
                
                # Category comparison
                if "category" in entity1 and "category" in entity2:
                    cat1 = entity1["category"] 
                    cat2 = entity2["category"]
                    
                    table_data["rows"].append({
                        "metric": "Category",
                        "value1": cat1,
                        "value2": cat2,
                        "difference": "Same category" if cat1 == cat2 else "Different categories"
                    })
                    
                # Expense ratio
                if "expense_ratio" in entity1 and "expense_ratio" in entity2:
                    er1 = entity1["expense_ratio"]
                    er2 = entity2["expense_ratio"]
                    
                    if er1 and er2:
                        er_diff = er1 - er2
                        lower = name1 if er1 < er2 else name2
                        
                        table_data["rows"].append({
                            "metric": "Expense Ratio (%)",
                            "value1": f"{er1:.2f}%",
                            "value2": f"{er2:.2f}%",
                            "difference": f"{lower} has lower expense by {abs(er_diff):.2f}%"
                        })
            
            # Sanitize data for JSON
            for item in comparison_data:
                item["data"] = self._sanitize_float_values(item["data"])
            
            # Return comparison data
            return {
                "answer": "\n".join(answer_parts),
                "confidence": 0.9,
                "related_news": [],
                "financial_data": {},
                "comparison_data": comparison_data,
                "table_data": table_data
            }
            
        except Exception as e:
            logger.error(f"Error handling comparison: {str(e)}")
            return {
                "answer": f"I encountered an error comparing {' and '.join(entities)}.",
                "confidence": 0.5,
                "related_news": [],
                "financial_data": {}
            }

    async def _search_external_news(self, query: str, limit: int = 5) -> List[Dict]:
        """Search for news from external sources"""
        try:
            logger.info(f"Searching external news for: {query}")
            
            # Use the news_scraper service to get news from external sources
            external_news = await news_scraper_service.search_news(query, limit)
            
            if not external_news:
                # Try with a simpler query if specific query doesn't yield results
                simplified_query = ' '.join(query.split()[:3])
                if simplified_query != query:
                    external_news = await news_scraper_service.search_news(simplified_query, limit)
            
            return external_news
        except Exception as e:
            logger.error(f"Error searching external news: {str(e)}")
            return []

chatbot_service = ChatbotService() 