import google.generativeai as genai
import os
import logging
from typing import Dict, Any, List, Optional

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class GeminiService:
    def __init__(self):
        """Initialize the Gemini service with API key"""
        try:
            # First try to get API key from environment variable
            api_key = os.environ.get("GEMINI_API_KEY")
            
            if not api_key:
                # Fallback to looking for a file
                key_file_path = os.path.join(os.path.dirname(__file__), "../.env.gemini")
                if os.path.exists(key_file_path):
                    with open(key_file_path, "r") as f:
                        api_key = f.read().strip()
            
            if not api_key:
                logger.warning("No Gemini API key found. Gemini service will not be available.")
                self.is_available = False
                return
                
            # Configure the Gemini API
            genai.configure(api_key=api_key)
            
            # Initialize the model - updated to use current model
            self.model = genai.GenerativeModel('models/gemini-1.5-flash')
            self.is_available = True
            logger.info("Gemini service initialized successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize Gemini service: {str(e)}")
            self.is_available = False
    
    async def get_financial_insights(self, query: str, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Generate financial insights using the Gemini model
        
        Args:
            query: The user's financial query
            context: Optional additional context about financial information
            
        Returns:
            Dictionary containing the response and metadata
        """
        if not self.is_available:
            logger.warning("Gemini service is not available. Using fallback.")
            return {
                "response": None,
                "source": "fallback",
                "success": False
            }
            
        try:
            # Build the prompt with financial context
            prompt = self._build_prompt(query, context)
            
            # Call the Gemini API
            response = self.model.generate_content(prompt)
            
            return {
                "response": response.text,
                "source": "gemini",
                "success": True
            }
        except Exception as e:
            logger.error(f"Error calling Gemini API: {str(e)}")
            return {
                "response": None,
                "source": "error",
                "success": False,
                "error": str(e)
            }
    
    async def analyze_news(self, news_items: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Analyze financial news using Gemini for deeper insights
        
        Args:
            news_items: List of news items to analyze
            
        Returns:
            Dictionary with analysis and metadata
        """
        if not self.is_available or not news_items:
            return {
                "analysis": None,
                "source": "fallback",
                "success": False
            }
            
        try:
            # Create a news summary for analysis
            news_summary = "\n\n".join([
                f"Title: {item.get('title', 'Untitled')}\n"
                f"Summary: {item.get('summary', 'No summary')}\n"
                f"Source: {item.get('source', 'Unknown')}\n"
                f"Date: {item.get('date', 'Unknown')}"
                for item in news_items[:5]  # Limit to first 5 news items
            ])
            
            prompt = f"""
            As a financial expert, analyze the following news items and provide key insights:
            
            {news_summary}
            
            Please provide:
            1. Key market trends mentioned
            2. Potential impact on investors
            3. Sectors that might be affected
            4. A brief summary of the overall market sentiment
            """
            
            # Call the Gemini API
            response = self.model.generate_content(prompt)
            
            return {
                "analysis": response.text,
                "source": "gemini",
                "success": True
            }
        except Exception as e:
            logger.error(f"Error analyzing news with Gemini: {str(e)}")
            return {
                "analysis": None,
                "source": "error",
                "success": False
            }
    
    def _build_prompt(self, query: str, context: Optional[Dict[str, Any]] = None) -> str:
        """
        Build a prompt for the Gemini model with financial context
        
        Args:
            query: The user's query
            context: Additional context information
            
        Returns:
            Formatted prompt string
        """
        prompt_parts = [
            "You are a financial expert assistant providing accurate information about markets, stocks, mutual funds, and financial news. ",
            "Please provide factual, concise, and helpful responses."
        ]
        
        # Add the user's query
        prompt_parts.append(f"\n\nUser query: {query}")
        
        # Add context if available
        if context:
            context_parts = []
            
            # Add stock information if available
            if "stock" in context:
                stock = context["stock"]
                stock_info = f"Stock information for {stock.get('name', 'Unknown')}:\n"
                stock_info += f"Symbol: {stock.get('symbol', 'Unknown')}\n"
                stock_info += f"Price: ₹{stock.get('price', 'Unknown')}\n"
                stock_info += f"Change: {stock.get('change', 'Unknown')}%\n"
                context_parts.append(stock_info)
                
            # Add fund information if available
            if "fund" in context:
                fund = context["fund"]
                fund_info = f"Mutual Fund information for {fund.get('scheme_name', 'Unknown')}:\n"
                fund_info += f"NAV: ₹{fund.get('nav', 'Unknown')}\n"
                fund_info += f"Category: {fund.get('category', 'Unknown')}\n"
                fund_info += f"1Y Returns: {fund.get('1YReturns', 'Unknown')}%\n"
                context_parts.append(fund_info)
                
            # Add news items if available
            if "news" in context and context["news"]:
                news_info = "Recent news:\n"
                for i, news in enumerate(context["news"][:3]):
                    news_info += f"{i+1}. {news.get('title', 'Untitled')} ({news.get('source', 'Unknown')})\n"
                context_parts.append(news_info)
                
            # Add the context to the prompt
            if context_parts:
                prompt_parts.append("\n\nContext information:\n" + "\n".join(context_parts))
        
        # Instructions for the model
        prompt_parts.append("\n\nPlease provide a helpful, accurate, and concise response based on the above information. If you're uncertain about anything, acknowledge the limitations.")
        
        return "".join(prompt_parts)

# Initialize the service
gemini_service = GeminiService() 