import logging
import re
from typing import Dict, List, Set

logger = logging.getLogger(__name__)

class EntityExtractionService:
    def __init__(self):
        # Initialize known entities lists
        self.known_companies = [
            "Reliance", "TCS", "HDFC", "Infosys", "ICICI", "HUL", "ITC", "SBI",
            "Bharti Airtel", "L&T", "Axis Bank", "Kotak", "Adani", "Wipro", "HCL",
            "Sun Pharma", "Asian Paints", "Bajaj Finance", "Maruti", "Titan"
        ]
        
        self.known_indices = [
            "Nifty", "Nifty50", "Nifty 50", "Sensex", "BSE", "NSE", "Bank Nifty",
            "Nifty Bank", "Dow Jones", "S&P 500", "Nasdaq", "FTSE", "DAX", "Hang Seng"
        ]
        
        self.known_sectors = [
            "Banking", "Finance", "IT", "Technology", "Pharma", "Automotive", "Auto",
            "FMCG", "Consumer Goods", "Energy", "Oil", "Gas", "Metal", "Mining", 
            "Telecom", "Real Estate", "Healthcare", "Insurance", "Cement", "Manufacturing"
        ]
        
        self.locations = [
            "India", "US", "USA", "China", "EU", "Europe", "UK", "Japan", "Russia",
            "Brazil", "Australia", "Canada", "Germany", "France", "Italy", "Spain",
            "Mumbai", "Delhi", "Bangalore", "Chennai", "Hyderabad", "Kolkata", "Pune"
        ]
        
        # Company name patterns
        self.company_patterns = [
            r'([A-Z][a-z]*(?:\s[A-Z][a-z]*){1,2}\s+(?:Ltd|Limited|Inc|Corp|Company))',
            r'([A-Z][a-z]+\s+[A-Z][a-z]+\s+(?:Ltd|Limited|Inc|Corp))',
            r'([A-Z][a-zA-Z]*(?:\s[A-Z][a-zA-Z]*){0,2})'
        ]
        
        # Load spaCy model for NER if available
        try:
            import spacy
            self.nlp = spacy.load("en_core_web_sm")
            self.has_spacy = True
            logger.info("SpaCy model loaded successfully for entity extraction")
        except (ImportError, OSError):
            self.has_spacy = False
            logger.warning("SpaCy model not available, using regex-based entity extraction only")
    
    def extract_entities(self, title: str, summary: str) -> Dict:
        """
        Extract entities from news title and summary
        
        Args:
            title: News title
            summary: News summary
            
        Returns:
            Dictionary with extracted entities
        """
        # Use spaCy if available
        if self.has_spacy:
            try:
                return self._extract_with_spacy(title, summary)
            except Exception as e:
                logger.error(f"Error in spaCy entity extraction: {str(e)}")
        
        # Fall back to regex-based extraction
        return self._extract_with_regex(title, summary)
    
    def _extract_with_regex(self, title: str, summary: str) -> Dict:
        """Extract entities using regex patterns"""
        entities = {
            "companies": [],
            "sectors": [],
            "indices": [],
            "locations": []
        }
        
        text = f"{title} {summary}"
        
        # Extract known entities
        for index in self.known_indices:
            if index in text:
                entities["indices"].append(index)
                
        for sector in self.known_sectors:
            if sector in text:
                entities["sectors"].append(sector)
                
        for location in self.locations:
            if location in text:
                entities["locations"].append(location)
        
        # Extract companies - both known and from patterns
        for company in self.known_companies:
            if company in text:
                entities["companies"].append(company)
                
        # Extract companies using patterns
        for pattern in self.company_patterns:
            found_companies = re.findall(pattern, text)
            entities["companies"].extend(found_companies)
        
        # Deduplicate
        for key in entities:
            entities[key] = list(set(entities[key]))
            
        return entities
    
    def _extract_with_spacy(self, title: str, summary: str) -> Dict:
        """Extract entities using spaCy NER"""
        entities = {
            "companies": [],
            "sectors": [],
            "indices": [],
            "locations": []
        }
        
        # Process text with spaCy
        text = f"{title} {summary}"
        doc = self.nlp(text)
        
        # Extract named entities
        for ent in doc.ents:
            if ent.label_ == "ORG":
                entities["companies"].append(ent.text)
            elif ent.label_ == "GPE" or ent.label_ == "LOC":
                entities["locations"].append(ent.text)
        
        # Add known entities
        for index in self.known_indices:
            if index in text:
                entities["indices"].append(index)
                
        for sector in self.known_sectors:
            if sector in text:
                entities["sectors"].append(sector)
        
        # Deduplicate
        for key in entities:
            entities[key] = list(set(entities[key]))
            
        return entities
    
    def is_company_name(self, text: str) -> bool:
        """
        Check if the given text is likely a company name
        
        Args:
            text: Text to check
            
        Returns:
            True if likely a company name, False otherwise
        """
        # Check if it's a known company
        if text in self.known_companies:
            return True
            
        # Check patterns
        for pattern in self.company_patterns:
            if re.match(pattern, text):
                return True
                
        # Use spaCy as a last resort
        if self.has_spacy:
            doc = self.nlp(text)
            for ent in doc.ents:
                if ent.label_ == "ORG":
                    return True
                    
        return False
        
    def extract_company_from_text(self, text: str) -> List[str]:
        """
        Extract company names from text
        
        Args:
            text: The text to extract from
            
        Returns:
            List of company names
        """
        companies = []
        
        # Check for known companies
        for company in self.known_companies:
            if company in text:
                companies.append(company)
                
        # Extract using patterns
        for pattern in self.company_patterns:
            found = re.findall(pattern, text)
            companies.extend(found)
            
        # Use spaCy if available
        if self.has_spacy:
            doc = self.nlp(text)
            for ent in doc.ents:
                if ent.label_ == "ORG":
                    companies.append(ent.text)
                    
        # Deduplicate
        return list(set(companies))
        
    def filter_non_listed_companies(self, companies: List[str], non_listed_entities: List[str]) -> List[str]:
        """
        Filter out known non-listed companies
        
        Args:
            companies: List of company names
            non_listed_entities: List of known non-listed entities
            
        Returns:
            Filtered list of companies
        """
        return [company for company in companies if not any(
            non_listed.lower() in company.lower() for non_listed in non_listed_entities
        )] 