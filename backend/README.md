# NewsWise Financial Backend

This is the backend service for the NewsWise Financial application, providing real-time financial news analysis, stock/fund information, and an AI-powered chatbot.

## Features

- Real-time news scraping from MoneyControl and Economic Times
- Stock and Mutual Fund data management
- Natural language processing for news analysis
- AI-powered chatbot for financial queries
- RESTful API endpoints

## Prerequisites

- Python 3.8+
- MongoDB
- Virtual environment (recommended)

## Setup

1. Create and activate a virtual environment:

```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

2. Install dependencies:

```bash
pip install -r requirements.txt
```

3. Install spaCy English model:

```bash
python -m spacy download en_core_web_sm
```

4. Make sure MongoDB is running locally on port 27017

## Running the Application

1. Start the FastAPI server:

```bash
uvicorn main:app --reload --port 8000
```

2. The API will be available at `http://localhost:8000`
3. API documentation will be available at `http://localhost:8000/docs`

## API Endpoints

### News

- GET `/api/news/recent` - Get recent news articles
- GET `/api/news/entity/{entity_name}` - Get news for specific entity
- POST `/api/news/refresh` - Refresh news data

### Stocks

- GET `/api/stocks/{symbol}` - Get stock information

### Funds

- GET `/api/funds/{scheme_name}` - Get fund information
- GET `/api/funds/{scheme_name}/holdings` - Get fund holdings

### Chat

- POST `/api/chat/query` - Process chat queries

## Environment Variables

Create a `.env` file in the root directory with the following variables:

```
MONGODB_URL=mongodb://localhost:27017
MODEL_CACHE_DIR=./model_cache
```

## Data Sources

The application uses the following data sources:

- `stock_data.csv` - Stock market data
- `cleaned_mutual_fund_data.csv` - Mutual fund information
- `mf_holdings_data.csv` - Mutual fund holdings data

## Important Note

The large data file `mf_holdings_data.csv` (159MB) is not included in this repository due to GitHub file size limits.
Please request this file separately or regenerate it using the data processing scripts if needed.

## Contributing

1. Fork the repository
2. Create a feature branch
3. Commit your changes
4. Push to the branch
5. Create a Pull Request
