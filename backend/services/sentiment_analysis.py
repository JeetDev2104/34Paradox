import logging
import re
from typing import Dict, List, Tuple

logger = logging.getLogger(__name__)

class SentimentAnalysisService:
    def __init__(self):
        # Positive and negative word lists for basic sentiment analysis
        self.positive_words = [
            "gain", "rise", "surge", "jump", "positive", "growth", "profit", 
            "up", "high", "strong", "improve", "increase", "upbeat", "rally",
            "bullish", "recover", "boost", "optimistic", "opportunity", "success"
        ]
        self.negative_words = [
            "loss", "fall", "drop", "decline", "negative", "down", "weak", 
            "pressure", "concern", "fear", "crisis", "risk", "bearish", "worry",
            "plunge", "crash", "danger", "threat", "recession", "trouble"
        ]
        
        # Load spaCy model for advanced NLP if available
        try:
            import spacy
            self.nlp = spacy.load("en_core_web_sm")
            self.has_spacy = True
            logger.info("SpaCy model loaded successfully for advanced sentiment analysis")
        except (ImportError, OSError):
            self.has_spacy = False
            logger.warning("SpaCy model not available, using basic sentiment analysis only")
    
    def analyze_text(self, text: str) -> Dict:
        """
        Analyze the sentiment of a text.
        
        Args:
            text: The text to analyze
            
        Returns:
            A dictionary with sentiment analysis results
        """
        if not text:
            return {
                "sentiment": "neutral",
                "sentiment_score": 0.5,
                "confidence": 0.3
            }
        
        # Try advanced analysis with spaCy if available
        if self.has_spacy:
            try:
                return self._analyze_with_spacy(text)
            except Exception as e:
                logger.error(f"Error in spaCy sentiment analysis: {str(e)}")
        
        # Fall back to basic word-based analysis
        return self._analyze_basic(text)
    
    def _analyze_basic(self, text: str) -> Dict:
        """Basic sentiment analysis based on word counting"""
        text_lower = text.lower()
        
        # Count positive and negative words
        positive_count = sum(1 for word in self.positive_words if word in text_lower)
        negative_count = sum(1 for word in self.negative_words if word in text_lower)
        
        # Calculate sentiment score (0.0 to 1.0)
        if positive_count > negative_count:
            sentiment = "positive"
            score = min(0.5 + (positive_count - negative_count) * 0.1, 0.95)
            confidence = min(0.3 + (positive_count + negative_count) * 0.05, 0.7)
        elif negative_count > positive_count:
            sentiment = "negative"
            score = max(0.5 - (negative_count - positive_count) * 0.1, 0.05)
            confidence = min(0.3 + (positive_count + negative_count) * 0.05, 0.7)
        else:
            sentiment = "neutral"
            score = 0.5
            confidence = 0.3
            
        return {
            "sentiment": sentiment,
            "sentiment_score": round(score, 2),
            "confidence": round(confidence, 2)
        }
    
    def _analyze_with_spacy(self, text: str) -> Dict:
        """Advanced sentiment analysis using spaCy"""
        doc = self.nlp(text)
        
        # Extract emotions and sentiments using linguistic patterns
        positive_markers = 0
        negative_markers = 0
        
        # Check for negation patterns
        negation_terms = ["not", "no", "never", "neither", "nor", "without"]
        
        for sent in doc.sents:
            for token in sent:
                # Check for positive/negative words
                if token.text.lower() in self.positive_words:
                    # Check if the token is negated
                    if any(neg in [t.text.lower() for t in token.lefts] for neg in negation_terms):
                        negative_markers += 1
                    else:
                        positive_markers += 1
                        
                elif token.text.lower() in self.negative_words:
                    # Check if the token is negated
                    if any(neg in [t.text.lower() for t in token.lefts] for neg in negation_terms):
                        positive_markers += 1
                    else:
                        negative_markers += 1
        
        # Calculate final sentiment
        if positive_markers > negative_markers:
            sentiment = "positive"
            score = min(0.5 + (positive_markers - negative_markers) * 0.1, 0.95)
            confidence = min(0.4 + (positive_markers + negative_markers) * 0.05, 0.8)
        elif negative_markers > positive_markers:
            sentiment = "negative"
            score = max(0.5 - (negative_markers - positive_markers) * 0.1, 0.05)
            confidence = min(0.4 + (positive_markers + negative_markers) * 0.05, 0.8)
        else:
            sentiment = "neutral"
            score = 0.5
            confidence = 0.4
            
        return {
            "sentiment": sentiment,
            "sentiment_score": round(score, 2),
            "confidence": round(confidence, 2)
        }
        
    def analyze_financial_text(self, text: str) -> Dict:
        """
        Specialized sentiment analysis for financial texts
        
        Args:
            text: The financial text to analyze
            
        Returns:
            Dictionary with sentiment and financial implication
        """
        base_sentiment = self.analyze_text(text)
        financial_terms = self._extract_financial_terms(text)
        
        financial_impact = "neutral"
        if base_sentiment["sentiment"] == "positive" and any(term in ["profit", "growth", "earnings"] for term in financial_terms):
            financial_impact = "bullish"
        elif base_sentiment["sentiment"] == "negative" and any(term in ["loss", "debt", "decline"] for term in financial_terms):
            financial_impact = "bearish"
            
        return {
            **base_sentiment,
            "financial_impact": financial_impact,
            "financial_terms": financial_terms[:5]  # Return top 5 terms
        }
    
    def _extract_financial_terms(self, text: str) -> List[str]:
        """Extract important financial terms from text"""
        financial_terms = [
            "profit", "loss", "revenue", "earnings", "dividend", "sales",
            "growth", "debt", "merger", "acquisition", "IPO", "stock", "shares",
            "market", "investment", "interest rates", "inflation", "economy"
        ]
        
        found_terms = []
        text_lower = text.lower()
        for term in financial_terms:
            if term in text_lower:
                found_terms.append(term)
                
        return found_terms 