import { subDays, format } from "date-fns";

// Types
export interface StockData {
  id: string;
  symbol: string;
  name: string;
  price: number;
  change: number;
  changePercent: number;
  marketCap: number;
  volume: number;
  sector: string;
  historicalData: HistoricalDataPoint[];
}

export interface HistoricalDataPoint {
  date: string;
  price: number;
}

export interface NewsItem {
  id: string;
  title: string;
  source: string;
  date: string;
  summary: string;
  url: string;
  sentiment: "positive" | "negative" | "neutral";
  relevantStocks: string[]; // stock symbols
  impactScore: number; // -10 to 10, how much it impacts stocks
}

// Generate historical data for the past 30 days
const generateHistoricalData = (basePrice: number): HistoricalDataPoint[] => {
  const historicalData: HistoricalDataPoint[] = [];
  let currentPrice = basePrice;

  for (let i = 30; i >= 0; i--) {
    const date = format(subDays(new Date(), i), "yyyy-MM-dd");
    // Add some randomness to the price
    const change = (Math.random() - 0.48) * (basePrice * 0.03);
    currentPrice += change;

    historicalData.push({
      date,
      price: parseFloat(currentPrice.toFixed(2)),
    });
  }

  return historicalData;
};

// Mock Stock Data
export const mockStocks: StockData[] = [
  {
    id: "1",
    symbol: "HDFC",
    name: "HDFC Bank Limited",
    price: 1450.75,
    change: -28.35,
    changePercent: -1.92,
    marketCap: 8125000000000,
    volume: 7821450,
    sector: "Banking",
    historicalData: generateHistoricalData(1450),
  },
  {
    id: "2",
    symbol: "INFY",
    name: "Infosys Limited",
    price: 1752.3,
    change: 24.8,
    changePercent: 1.43,
    marketCap: 7354000000000,
    volume: 5462130,
    sector: "Information Technology",
    historicalData: generateHistoricalData(1720),
  },
  {
    id: "3",
    symbol: "RELIANCE",
    name: "Reliance Industries Limited",
    price: 2568.45,
    change: -12.75,
    changePercent: -0.49,
    marketCap: 17456000000000,
    volume: 4123789,
    sector: "Energy",
    historicalData: generateHistoricalData(2580),
  },
  {
    id: "4",
    symbol: "TATAMOTORS",
    name: "Tata Motors Limited",
    price: 876.2,
    change: 15.4,
    changePercent: 1.79,
    marketCap: 2932000000000,
    volume: 8945672,
    sector: "Automotive",
    historicalData: generateHistoricalData(860),
  },
  {
    id: "5",
    symbol: "JOTHYLABS",
    name: "Jyothy Labs Limited",
    price: 326.85,
    change: 12.35,
    changePercent: 3.93,
    marketCap: 120000000000,
    volume: 2134567,
    sector: "Consumer Goods",
    historicalData: generateHistoricalData(314),
  },
  {
    id: "6",
    symbol: "ICICIBANK",
    name: "ICICI Bank Limited",
    price: 1023.45,
    change: 5.25,
    changePercent: 0.52,
    marketCap: 7125000000000,
    volume: 5623450,
    sector: "Banking",
    historicalData: generateHistoricalData(1018),
  },
];

// Mock ETFs and Funds
export const mockFunds = [
  {
    id: "101",
    symbol: "NIFTYBEES",
    name: "Nippon India ETF Nifty BeES",
    price: 235.45,
    change: -3.2,
    changePercent: -1.34,
    aum: 45670000000,
    category: "Index Fund",
    historicalData: generateHistoricalData(238),
  },
  {
    id: "102",
    symbol: "TECHETF",
    name: "Technology Sector ETF",
    price: 187.75,
    change: -5.4,
    changePercent: -2.79,
    aum: 12450000000,
    category: "Sector ETF",
    historicalData: generateHistoricalData(193),
  },
];

// Mock News Data
export const mockNews: NewsItem[] = [
  {
    id: "n1",
    title: "HDFC Bank Q4 Results: Net Profit Below Expectations",
    source: "Financial Times India",
    date: format(subDays(new Date(), 0), "MMM dd, yyyy"),
    summary:
      "HDFC Bank reported a lower-than-expected net profit for Q4, causing shares to drop. Analysts cite higher provisions for bad loans as a key concern.",
    url: "#",
    sentiment: "negative",
    relevantStocks: ["HDFC"],
    impactScore: -7,
  },
  {
    id: "n2",
    title: "RBI Increases Repo Rate by 25 bps",
    source: "Economic Times",
    date: format(subDays(new Date(), 1), "MMM dd, yyyy"),
    summary:
      "The Reserve Bank of India increased the repo rate by 25 basis points to 6.50%, affecting banking and financial stocks nationwide.",
    url: "#",
    sentiment: "negative",
    relevantStocks: ["HDFC", "RELIANCE"],
    impactScore: -5,
  },
  {
    id: "n3",
    title:
      "Infosys Wins Major Digital Transformation Deal with European Retailer",
    source: "Business Standard",
    date: format(subDays(new Date(), 2), "MMM dd, yyyy"),
    summary:
      "Infosys announced a significant multi-year contract with a leading European retailer for digital transformation services valued at over $200 million.",
    url: "#",
    sentiment: "positive",
    relevantStocks: ["INFY"],
    impactScore: 8,
  },
  {
    id: "n4",
    title: "Tata Motors Unveils New EV Strategy, Shares Rally",
    source: "Auto News India",
    date: format(subDays(new Date(), 2), "MMM dd, yyyy"),
    summary:
      "Tata Motors revealed an ambitious plan to launch 10 new electric vehicles by 2025, driving the stock to a 52-week high.",
    url: "#",
    sentiment: "positive",
    relevantStocks: ["TATAMOTORS"],
    impactScore: 8,
  },
  {
    id: "n5",
    title: "Global Chip Shortage Impacting Tech Sector ETFs",
    source: "Market Watch",
    date: format(subDays(new Date(), 3), "MMM dd, yyyy"),
    summary:
      "The ongoing semiconductor shortage continues to affect technology funds and ETFs, with many showing volatility due to supply chain concerns.",
    url: "#",
    sentiment: "negative",
    relevantStocks: ["TECHETF"],
    impactScore: -6,
  },
  {
    id: "n6",
    title: "Jyothy Labs Posts Impressive Q3 Results, Shares Up",
    source: "Industry Weekly",
    date: format(subDays(new Date(), 0), "MMM dd, yyyy"),
    summary:
      "Jyothy Labs reported strong Q3 results with a 15% increase in revenue and 22% growth in net profit, exceeding market expectations.",
    url: "#",
    sentiment: "positive",
    relevantStocks: ["JOTHYLABS"],
    impactScore: 7,
  },
];

// Mock Responses for ChatBot
export const mockChatResponses: Record<string, string> = {
  default:
    "I can help you understand market movements and news that affect stocks and funds. Try asking about specific stocks or recent market events.",

  "hdfc bank":
    "HDFC Bank is down 1.92% today primarily due to lower-than-expected Q4 results reported yesterday. The bank's net profit missed analyst estimates by approximately 3.5%, with higher provisions for non-performing assets being a key concern. Additionally, the RBI's recent repo rate increase has put pressure on banking stocks across the board.",

  "tech etf":
    "Tech-focused ETFs have been underperforming this week, with a decline of 2.79%. This is largely attributed to the ongoing global semiconductor shortage affecting supply chains. Recent news about production delays from major chip manufacturers has increased volatility in the tech sector.",

  "jyothy labs":
    "Jyothy Labs is up 3.93% today following the release of strong Q3 results. The company reported a 15% year-over-year revenue increase and 22% growth in net profit, exceeding market expectations. Analysts have responded by upgrading their outlook, citing successful product innovations and effective cost management strategies.",

  nifty:
    "The Nifty index is showing weakness today, down by approximately 1.34%. This decline is primarily driven by banking sector weakness following HDFC Bank's disappointing results and the recent RBI rate hike. Additionally, global factors including rising U.S. Treasury yields and concerns about inflation are contributing to cautious market sentiment.",

  "market outlook":
    "The current market outlook remains cautiously optimistic but volatile. Banking and financial sectors are under pressure due to monetary policy tightening. Technology stocks show mixed performance due to supply chain issues. However, consumer goods companies like Jyothy Labs are showing resilience with strong quarterly results. Investors should monitor upcoming earnings reports and central bank policy decisions for further direction.",
};

// Function to get relevant news for a stock
export const getRelevantNews = (symbol: string): NewsItem[] => {
  return mockNews.filter((news) => news.relevantStocks.includes(symbol));
};

// Function to get mock AI response about a stock
export const getAIExplanation = (query: string): string => {
  const lowerQuery = query.toLowerCase();

  // Check for specific matches
  for (const key of Object.keys(mockChatResponses)) {
    if (lowerQuery.includes(key.toLowerCase())) {
      return mockChatResponses[key];
    }
  }

  // Default response
  return mockChatResponses.default;
};
