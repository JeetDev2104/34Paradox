import logging
import aiohttp
import asyncio
import re
import json
from typing import List, Dict, Optional
from datetime import datetime, timedelta
import os
from bs4 import BeautifulSoup
import random
from .database import db_service
from services.sentiment_analysis import SentimentAnalysisService
from services.entity_extraction import EntityExtractionService

logger = logging.getLogger(__name__)

# User agent rotation to avoid being blocked
USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.1.1 Safari/605.1.15",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:89.0) Gecko/20100101 Firefox/89.0",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/92.0.4515.107 Safari/537.36"
]

# Initialize the sentiment analysis service
sentiment_analysis_service = SentimentAnalysisService()
entity_extraction_service = EntityExtractionService()

class NewsScraperService:
    def __init__(self):
        self.sources = [
            {
                "name": "MoneyControl",
                "url": "https://www.moneycontrol.com/news/business/markets/",
                "article_selector": ".article_list",
                "title_selector": "h2",
                "summary_selector": ".article_desc",
                "link_selector": "h2 a",
                "date_selector": ".article_schedule"
            },
            {
                "name": "Economic Times",
                "url": "https://economictimes.indiatimes.com/markets/stocks/news",
                "article_selector": ".eachStory",
                "title_selector": "h3",
                "summary_selector": ".desc",
                "link_selector": "a",
                "date_selector": ".date-format"
            },
            {
                "name": "LiveMint",
                "url": "https://www.livemint.com/market/stock-market-news",
                "article_selector": ".headline",
                "title_selector": "h2",
                "summary_selector": "p",
                "link_selector": "a",
                "date_selector": ".dateline"
            }
        ]
        
        # List of known non-listed entities to filter out false stock information
        self.non_listed_entities = [
            'oyo', 'swiggy', 'zomato', 'byjus', 'ola', 'paytm', 'flipkart', 
            'meesho', 'dunzo', 'upgrad', 'unacademy', 'cred', 'grofers', 'bigbasket',
            'zerodha', 'groww', 'pharmeasy', 'udaan', 'policybazaar', 'lenskart',
            'delhivery', 'xiaomi', 'oneplus'
        ]
    
    async def fetch_page(self, url: str) -> Optional[str]:
        """Fetch a webpage with headers rotation"""
        headers = {
            "User-Agent": random.choice(USER_AGENTS),
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.5",
            "Referer": "https://www.google.com/",
            "DNT": "1",
            "Connection": "keep-alive",
            "Upgrade-Insecure-Requests": "1"
        }
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url, headers=headers, timeout=30) as response:
                    if response.status == 200:
                        return await response.text()
                    else:
                        logger.error(f"Failed to fetch {url}: {response.status}")
                        return None
        except Exception as e:
            logger.error(f"Error fetching {url}: {str(e)}")
            return None
            
    def extract_entities(self, title: str, summary: str) -> Dict:
        """Extract entities from news title and summary"""
        # This is a simple extraction - a more advanced version would use NER models
        entities = {
            "companies": [],
            "sectors": [],
            "indices": [],
            "locations": []
        }
        
        # Common Indian indices
        indices = ["Nifty", "Nifty50", "Nifty 50", "Sensex", "BSE", "NSE"]
        for index in indices:
            if index in title or index in summary:
                entities["indices"].append(index)
                
        # Common sectors
        sectors = [
            "Banking", "Finance", "IT", "Technology", "Pharma", "Auto", "FMCG",
            "Consumer Goods", "Energy", "Oil", "Gas", "Metal", "Mining", "Telecom"
        ]
        for sector in sectors:
            if sector in title or sector in summary:
                entities["sectors"].append(sector)
                
        # Common locations
        locations = ["India", "US", "China", "EU", "Europe", "Global"]
        for location in locations:
            if location in title or location in summary:
                entities["locations"].append(location)
                
        # Try to extract company names - this is simplified
        # A better approach would use a pre-trained NER model
        company_patterns = [
            r'([A-Z][a-z]+\s+[A-Z][a-z]+\s+(?:Ltd|Limited|Inc|Corp))',
            r'([A-Z][a-z]*(?:\s[A-Z][a-z]*){1,3})'
        ]
        
        text = f"{title} {summary}"
        for pattern in company_patterns:
            companies = re.findall(pattern, text)
            entities["companies"].extend(companies)
        
        # Deduplicate
        for key in entities:
            entities[key] = list(set(entities[key]))
            
        return entities
        
    def analyze_sentiment(self, text: str) -> Dict:
        """Basic sentiment analysis for news"""
        # A more advanced version would use a pre-trained model
        positive_words = ["gain", "rise", "surge", "jump", "positive", "growth", "profit", "up", "high", "strong"]
        negative_words = ["loss", "fall", "drop", "decline", "negative", "down", "weak", "pressure", "concern", "fear"]
        
        text_lower = text.lower()
        positive_count = sum(1 for word in positive_words if word in text_lower)
        negative_count = sum(1 for word in negative_words if word in text_lower)
        
        if positive_count > negative_count:
            sentiment = "positive"
            score = min(0.5 + (positive_count - negative_count) * 0.1, 0.9)
        elif negative_count > positive_count:
            sentiment = "negative"
            score = max(0.5 - (negative_count - positive_count) * 0.1, 0.1)
        else:
            sentiment = "neutral"
            score = 0.5
            
        return {
            "sentiment": sentiment,
            "sentiment_score": score
        }
        
    async def parse_source(self, source: Dict) -> List[Dict]:
        """Parse a single news source"""
        news_items = []
        
        html = await self.fetch_page(source["url"])
        if not html:
            return news_items
            
        soup = BeautifulSoup(html, 'html.parser')
        
        try:
            articles = soup.select(source["article_selector"])
            for article in articles[:10]:  # Limit to first 10 articles
                try:
                    # Extract title
                    title_elem = article.select_one(source["title_selector"])
                    if not title_elem:
                        continue
                    title = title_elem.get_text().strip()
                    
                    # Extract summary
                    summary_elem = article.select_one(source["summary_selector"])
                    summary = summary_elem.get_text().strip() if summary_elem else ""
                    
                    # Extract link
                    link_elem = article.select_one(source["link_selector"])
                    link = link_elem.get("href") if link_elem else ""
                    if link and not link.startswith("http"):
                        link = f"https://{source['url'].split('/')[2]}{link}"
                    
                    # Extract date
                    date_elem = article.select_one(source["date_selector"])
                    date_str = date_elem.get_text().strip() if date_elem else ""
                    
                    # Parse date (this will vary by source format)
                    try:
                        # Try to parse the date, or use current date if parsing fails
                        date = datetime.now().isoformat()
                        if date_str:
                            # Simple date parsing - would need to be adapted for each source
                            if "ago" in date_str.lower():
                                # Handle relative dates like "2 hours ago"
                                date = datetime.now().isoformat()
                            else:
                                # Try some common formats
                                for fmt in ["%d %b %Y", "%b %d, %Y", "%Y-%m-%d"]:
                                    try:
                                        date = datetime.strptime(date_str, fmt).isoformat()
                                        break
                                    except ValueError:
                                        continue
                    except Exception as e:
                        logger.error(f"Error parsing date {date_str}: {str(e)}")
                        date = datetime.now().isoformat()
                        
                    # Extract entities
                    entities = self.extract_entities(title, summary)
                    
                    # Analyze sentiment
                    sentiment_analysis = self.analyze_sentiment(f"{title} {summary}")
                    
                    # Extract keywords (simplified)
                    keywords = []
                    for word in f"{title} {summary}".lower().split():
                        if len(word) > 4 and word not in ["about", "there", "their", "after", "before"]:
                            keywords.append(word)
                    keywords = list(set(keywords))[:10]
                    
                    news_item = {
                        "title": title,
                        "summary": summary,
                        "url": link,
                        "source": source["name"],
                        "date": date,
                        "entities": entities,
                        "sentiment": sentiment_analysis["sentiment"],
                        "sentiment_score": sentiment_analysis["sentiment_score"],
                        "keywords": keywords
                    }
                    
                    news_items.append(news_item)
                    
                except Exception as e:
                    logger.error(f"Error parsing article from {source['name']}: {str(e)}")
                    continue
                    
        except Exception as e:
            logger.error(f"Error parsing source {source['name']}: {str(e)}")
            
        return news_items
        
    async def fetch_news_from_all_sources(self) -> List[Dict]:
        """Fetch news from all sources concurrently"""
        tasks = [self.parse_source(source) for source in self.sources]
        results = await asyncio.gather(*tasks)
        
        # Also fetch from Google News for general market news
        google_results = await self.fetch_google_news("stock market finance news india", days=3, max_results=15)
        
        # Flatten results
        all_news = []
        for source_news in results:
            all_news.extend(source_news)
            
        # Add Google News results
        all_news.extend(google_results)
        
        logger.info(f"Fetched {len(all_news)} news items from all sources")
        return all_news
        
    async def refresh_news(self) -> int:
        """Fetch fresh news and store in database"""
        try:
            news_items = await self.fetch_news_from_all_sources()
            if news_items:
                count = await db_service.store_scraped_news(news_items)
                return count
            return 0
        except Exception as e:
            logger.error(f"Error refreshing news: {str(e)}")
            return 0
            
    async def search_company_news(self, company_name: str, days: int = 30) -> List[Dict]:
        """Search for news about a specific company"""
        try:
            # First try to get from database
            news_items = await db_service.get_news_by_entity_advanced(company_name, days)
            
            # If we don't have enough news, try to get from Google News
            if len(news_items) < 5:
                # Check if this is a non-listed entity
                is_non_listed = any(entity.lower() in company_name.lower() for entity in self.non_listed_entities)
                
                # For non-listed entities, add clarification in the search
                search_query = company_name
                if is_non_listed:
                    search_query = f"{company_name} private company funding"
                    
                # Get news from Google
                google_news = await self.fetch_google_news(search_query, days=days, max_results=10)
                
                if google_news:
                    # Store in database and add to results
                    await db_service.store_scraped_news(google_news)
                    news_items.extend(google_news)
            
            # Remove duplicates
            seen_urls = set()
            unique_news_items = []
            
            for item in news_items:
                url = item.get('url', '')
                if url and url not in seen_urls:
                    seen_urls.add(url)
                    unique_news_items.append(item)
            
            return unique_news_items[:20]  # Limit to 20 items
        except Exception as e:
            logger.error(f"Error searching company news for {company_name}: {str(e)}")
            return []

    async def search_news(self, query: str, limit: int = 10) -> List[Dict]:
        """Search for news articles based on the query"""
        try:
            # Search in database first
            db_results = await db_service.search_news(query, limit)
            
            # If we have enough results, return them
            if len(db_results) >= limit:
                return db_results[:limit]
                
            # Otherwise, also search in Google News
            google_results = await self.fetch_google_news(query, days=30, max_results=limit)
            
            # Store the new results in the database
            if google_results:
                await db_service.store_scraped_news(google_results)
                
            # Combine results, prioritizing database results
            all_results = db_results + [r for r in google_results if r.get('url') not in [dr.get('url') for dr in db_results]]
            
            return all_results[:limit]
        except Exception as e:
            logger.error(f"Error searching news: {str(e)}")
            return []
    
    async def fetch_google_news(self, query: str, days: int = 7, max_results: int = 10) -> List[Dict]:
        """Fetch news from Google News search"""
        try:
            # Format query for Google News search
            query = query.replace(' ', '+')
            
            # Adjust query for financial news
            if not any(term in query.lower() for term in ['finance', 'stock', 'market', 'invest']):
                query += '+finance+stock+market'
                
            # Calculate date range in required Google format
            today = datetime.now()
            if days > 0:
                past_date = today - timedelta(days=days)
                date_range = f"&tbs=cdr:1,cd_min:{past_date.strftime('%m/%d/%Y')},cd_max:{today.strftime('%m/%d/%Y')}"
            else:
                date_range = ""
                
            # Construct URL with date range
            url = f"https://news.google.com/search?q={query}{date_range}&hl=en-US&gl=US&ceid=US:en"
            
            html = await self.fetch_page(url)
            if not html:
                logger.error(f"Failed to fetch Google News for query: {query}")
                return []
                
            # Parse Google News results
            soup = BeautifulSoup(html, 'html.parser')
            articles = soup.select('article')
            
            results = []
            count = 0
            
            for article in articles:
                if count >= max_results:
                    break
                    
                try:
                    # Extract elements
                    title_elem = article.select_one('h3 a')
                    time_elem = article.select_one('time')
                    source_elem = article.select_one('div[data-n-aus]')
                    
                    if not (title_elem and time_elem):
                        continue
                        
                    title = title_elem.text
                    
                    # Extract href and construct full URL
                    article_url = title_elem.get('href', '')
                    if article_url.startswith('./'):
                        article_url = 'https://news.google.com/' + article_url[2:]
                    
                    # Extract source and date
                    source = source_elem.text if source_elem else "Google News"
                    
                    # Parse date
                    if time_elem.get('datetime'):
                        published_date = datetime.fromisoformat(time_elem.get('datetime')).isoformat()
                    else:
                        # If no datetime attribute, use the text content (like "4 hours ago")
                        time_text = time_elem.text
                        published_date = self._parse_relative_time(time_text)
                        
                    # Generate summary by scraping the target article when possible
                    summary = await self._fetch_article_summary(article_url)
                    if not summary:
                        # If we couldn't get the summary, use the title as a fallback
                        summary = title
                        
                    # Run sentiment analysis
                    sentiment_analysis = sentiment_analysis_service.analyze_text(title + " " + summary)
                    
                    # Extract entities
                    entities = entity_extraction_service.extract_entities(title + " " + summary)
                    
                    # Extract keywords
                    keywords = entity_extraction_service.extract_keywords(title + " " + summary)
                    
                    news_item = {
                        "title": title,
                        "summary": summary,
                        "url": article_url,
                        "source": source,
                        "date": published_date,
                        "entities": entities,
                        "sentiment": sentiment_analysis["sentiment"],
                        "sentiment_score": sentiment_analysis["sentiment_score"],
                        "keywords": keywords
                    }
                    
                    # Filter out articles about non-listed companies falsely presented as stocks
                    if not self._validate_news_item(news_item):
                        continue
                        
                    results.append(news_item)
                    count += 1
                    
                except Exception as e:
                    logger.error(f"Error parsing Google News article: {str(e)}")
                    continue
                    
            return results
                
        except Exception as e:
            logger.error(f"Error in Google News search for {query}: {str(e)}")
            return []
            
    def _parse_relative_time(self, time_text: str) -> str:
        """Parse relative time strings like '4 hours ago' into ISO format dates"""
        now = datetime.now()
        try:
            if 'min' in time_text:
                minutes = int(re.search(r'(\d+)', time_text).group(1))
                date = now - timedelta(minutes=minutes)
            elif 'hour' in time_text:
                hours = int(re.search(r'(\d+)', time_text).group(1))
                date = now - timedelta(hours=hours)
            elif 'day' in time_text:
                days = int(re.search(r'(\d+)', time_text).group(1))
                date = now - timedelta(days=days)
            elif 'week' in time_text:
                weeks = int(re.search(r'(\d+)', time_text).group(1))
                date = now - timedelta(weeks=weeks)
            elif 'month' in time_text:
                months = int(re.search(r'(\d+)', time_text).group(1))
                date = now - timedelta(days=months*30)  # Approximation
            else:
                date = now
            return date.isoformat()
        except Exception:
            return now.isoformat()
            
    async def _fetch_article_summary(self, url: str) -> str:
        """Fetch and extract a summary from the article content"""
        try:
            html = await self.fetch_page(url)
            if not html:
                return ""
                
            soup = BeautifulSoup(html, 'html.parser')
            
            # Try various ways to find the article body
            article_body = None
            for selector in ['article', '.article-body', '.article-content', '.content', '.story-content', 'p']:
                article_body = soup.select(selector)
                if article_body and len(article_body) > 1:
                    break
                    
            if not article_body:
                # Find all paragraphs as a fallback
                article_body = soup.find_all('p')
                
            # Extract text from paragraphs
            paragraphs = []
            for elem in article_body:
                if elem.name == 'p' and elem.text and len(elem.text) > 50:  # Only substantial paragraphs
                    paragraphs.append(elem.text.strip())
                    
            if paragraphs:
                # Take first paragraph or a combination of the first few
                summary = ' '.join(paragraphs[:2])
                # Limit length
                if len(summary) > 500:
                    summary = summary[:497] + "..."
                return summary
                
            # If no good paragraphs found, look for meta description
            meta_desc = soup.find('meta', {'name': 'description'}) or soup.find('meta', {'property': 'og:description'})
            if meta_desc and meta_desc.get('content'):
                return meta_desc.get('content')
                
            return ""
                
        except Exception as e:
            logger.error(f"Error fetching article summary for {url}: {str(e)}")
            return ""
            
    def _validate_news_item(self, news_item: Dict) -> bool:
        """Validate a news item to filter out articles about non-listed entities presented as stocks"""
        title = news_item['title'].lower()
        summary = news_item['summary'].lower()
        content = title + " " + summary
        
        # Extract company entities
        companies = news_item['entities'].get('companies', [])
        
        # Check for non-listed entities
        for entity in self.non_listed_entities:
            # If the entity is mentioned
            if entity.lower() in content:
                # And it appears to be presented as a stock
                stock_terms = ['stock price', 'share price', 'stock', 'listed', 'ipo price', 'market price']
                if any(term in content for term in stock_terms):
                    # Check if the article clarifies it's not listed
                    clarifications = ['not listed', 'not publicly traded', 'private company', 
                                     'planning ipo', 'upcoming ipo', 'pre-ipo', 'preparing for ipo']
                    if not any(clarify in content for clarify in clarifications):
                        # If no clarification, this might be misleading
                        return False
        
        return True

    def _generate_simulated_news(self, query: str, limit: int) -> List[Dict]:
        """Generate simulated news for demo purposes when API is not available"""
        results = []
        
        # Clean query for URL
        clean_query = re.sub(r'[^a-zA-Z0-9]', '-', query.lower())
        
        # Today's date for URL
        today = datetime.now().strftime("%Y-%m-%d")
        
        # List of potential news sources
        sources = ["Bloomberg", "Reuters", "CNBC", "Forbes", "Financial Times", "The Economic Times", "Mint", "Business Standard"]
        
        # URL templates for simulated news articles
        url_templates = [
            "https://www.{source}.com/markets/stocks/{date}/{query}-news.html",
            "https://www.{source}.com/finance/{date}/{query}-update.html",
            "https://www.{source}.com/investing/{query}/{date}/article.html",
            "https://www.{source}.com/news/markets/{date}/{query}.html",
            "https://www.{source}.com/business/{query}-{date}.html"
        ]
        
        # Replace with actual domain URLs
        domain_mapping = {
            "Bloomberg": "bloomberg.com",
            "Reuters": "reuters.com",
            "CNBC": "cnbc.com",
            "Forbes": "forbes.com",
            "Financial Times": "ft.com",
            "The Economic Times": "economictimes.indiatimes.com",
            "Mint": "livemint.com",
            "Business Standard": "business-standard.com"
        }

        # Templates for news titles and summaries with placeholders
        templates = [
            {
                "title": "{query} Shows Strong Performance in Recent Trading Session",
                "summary": "Shares of {query} demonstrated robust performance in today's trading session, attracting investor attention amid positive market sentiment and strong sectoral trends."
            },
            {
                "title": "Analysts Upgrade {query} Rating Citing Growth Potential",
                "summary": "Investment firms have revised their outlook on {query}, upgrading their ratings based on the company's strong fundamentals and promising growth trajectory in its core business segments."
            },
            {
                "title": "{query} Announces Quarterly Results Above Market Expectations",
                "summary": "{query} reported quarterly earnings that exceeded analyst estimates, driven by stronger-than-anticipated revenue growth and effective cost management strategies implemented by leadership."
            },
            {
                "title": "Market Volatility Impacts {query} Share Price",
                "summary": "Amid broader market fluctuations, {query} experienced price movements as investors assessed the implications of economic indicators on future performance prospects."
            },
            {
                "title": "{query} Expands Operations with Strategic Acquisition",
                "summary": "In a move to strengthen its market position, {query} announced the acquisition of a complementary business, expected to drive synergies and expand its product offerings in key markets."
            },
            {
                "title": "Investors React to {query}'s New Product Announcement",
                "summary": "The market responded to {query}'s latest product launch, which analysts believe could significantly impact the company's revenue stream and competitive positioning in the industry."
            },
            {
                "title": "Economic Outlook Raises Questions for {query} Growth Strategy",
                "summary": "With shifting economic conditions, market observers are closely monitoring how {query}'s growth strategy will adapt to navigate potential challenges while capitalizing on emerging opportunities."
            },
            {
                "title": "{query} Addresses Regulatory Challenges in Key Markets",
                "summary": "Leadership at {query} outlined their approach to addressing evolving regulatory requirements, emphasizing compliance while maintaining focus on strategic business objectives."
            },
            {
                "title": "Dividend Announcement Boosts Investor Interest in {query}",
                "summary": "{query} announced a dividend payment that signals management's confidence in financial stability and commitment to delivering shareholder value despite market uncertainties."
            },
            {
                "title": "Technical Analysis: {query} Approaches Key Resistance Levels",
                "summary": "Chart patterns indicate {query} is testing important technical levels that could determine price direction in upcoming trading sessions, according to market technicians and analysts."
            }
        ]
        
        # Check if this is a non-listed entity
        if any(entity in query.lower() for entity in self.non_listed_entities):
            # Use appropriate templates for non-listed companies
            non_listed_templates = [
                {
                    "title": "{query} Secures New Funding Round from Investors",
                    "summary": "Private company {query} has raised a significant funding round from venture capital firms, valuing the company at a premium to its previous valuation and enabling expansion plans."
                },
                {
                    "title": "{query} IPO Rumors Surface Again in Financial Markets",
                    "summary": "Speculation about a potential public offering for {query} has resurfaced, though the company has not confirmed plans to list shares on any exchange in the immediate future."
                },
                {
                    "title": "Privately-Held {query} Expands Market Presence",
                    "summary": "{query}, which remains privately owned, announced significant expansion into new markets as it continues to grow its business operations outside the public markets."
                },
                {
                    "title": "{query} Valuation Soars in Private Market Transactions",
                    "summary": "Recent private market transactions have reportedly valued {query} significantly higher than previous rounds, though the company remains unlisted on public exchanges."
                },
                {
                    "title": "Analysts Speculate on {query}'s Potential Market Value",
                    "summary": "While {query} is not publicly traded, financial analysts have attempted to estimate what its market capitalization might be if it were to pursue a public listing."
                }
            ]
            templates = non_listed_templates
        
        # Generate news items
        for i in range(min(limit, len(templates))):
            template = templates[i]
            source_name = random.choice(sources)
            source_domain = domain_mapping.get(source_name, source_name.lower().replace(" ", "") + ".com")
            
            # Replace placeholders with the query
            title = template["title"].replace("{query}", query)
            summary = template["summary"].replace("{query}", query)
            
            # Generate URL with source-specific domain and date
            url_template = url_templates[i % len(url_templates)]
            url = url_template.replace("{source}", source_domain).replace("{date}", today).replace("{query}", clean_query)
            
            # Generate a random date in the last 7 days
            days_ago = random.randint(0, 7)
            news_date = (datetime.now() - timedelta(days=days_ago)).isoformat()
            
            # Generate a sentiment between 0.3 and 0.7
            sentiment_score = 0.3 + (random.random() * 0.4)
            sentiment = "negative" if sentiment_score < 0.45 else ("positive" if sentiment_score > 0.55 else "neutral")
            
            results.append({
                "title": title,
                "summary": summary,
                "date": news_date,
                "source": source_name,  # Capitalize for display
                "url": url,
                "sentiment": sentiment,
                "sentiment_score": sentiment_score
            })
        
        return results

# Initialize the service
news_scraper_service = NewsScraperService() 