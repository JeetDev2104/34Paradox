import axios from "axios";

// Allow configuring the API base URL via environment variables or defaults
const API_BASE_URL =
  import.meta.env.VITE_API_BASE_URL || "http://localhost:8000/api";

export interface NewsItem {
  title: string;
  summary: string;
  sentiment: string;
  sentiment_score: number;
  entities: {
    companies: string[];
    sectors: string[];
    locations: string[];
    indices?: string[];
  };
  keywords: string[];
  date: string;
  source: string;
  url: string;
}

export interface StockInfo {
  symbol: string;
  name: string;
  price: number;
  change: number;
  changePercent: number;
  volume: number;
  marketCap: number;
  sector: string;
  industry?: string;
  exchange?: string;
  currency?: string;
  lastUpdated: string;
  dataSource?: string;
  status?: string; // "listed" or "non-listed"
  description?: string;

  // Non-listed company specific fields
  valuation?: string;
  lastFundingRound?: string;
  founded?: string;
  headquarters?: string;
  ceo?: string;

  // Public company specific fields
  pe?: number;
  eps?: number;
  dividend?: number;
  dividendYield?: number;
  high52Week?: number;
  low52Week?: number;

  // Historical data for charts
  historical?: Array<{
    date: string;
    price: number;
  }>;

  [key: string]: any;
}

export interface FundInfo {
  schemeName: string;
  schemeCode: string;
  category: string;
  fundFamily: string;
  nav: number;
  change: number;
  changePercent: number;
  aum: number;
  expenseRatio: number;
  riskRating: string;
  yearToDateReturn: number;
  oneYearReturn: number;
  threeYearReturn: number;
  fiveYearReturn: number;
  sinceInceptionReturn: number;
  managers: string[];
  launchDate: string;
  holdings?: FundHolding[];
}

export interface FundHolding {
  companyName: string;
  symbol: string;
  sector: string;
  percentage: number;
}

export interface ETFInfo {
  symbol: string;
  name: string;
  price: number;
  change: number;
  changePercent: number;
  volume: number;
  marketCap: number;
  aum: number;
  nav: number;
  expenseRatio: number;
  category: string;
  issuer: string;
  indexTracked: string;
  yearToDateReturn: number;
  oneYearReturn: number;
  threeYearReturn: number;
  fiveYearReturn: number;
  holdings?: FundHolding[];
}

export interface ChatQuery {
  query: string;
  session_id?: string;
}

export interface ChatResponse {
  answer: string;
  related_data?: any;
  sources?: string[];
  confidence?: number;
}

export interface AdvancedSearchQuery {
  query: string;
  entity_type?: string; // stock, fund, etc.
  date_range?: number; // days
}

export const api = {
  chat: {
    query: async (
      query: string,
      sessionId: string = "default"
    ): Promise<ChatResponse> => {
      const response = await axios.post(`${API_BASE_URL}/chat/query`, {
        query,
        user_id: sessionId,
      });
      return response.data;
    },
  },

  news: {
    getRecent: async (limit: number = 20) => {
      const response = await axios.get(
        `${API_BASE_URL}/news/recent?limit=${limit}`
      );
      return response.data;
    },

    getByEntity: async (entityName: string, days: number = 30) => {
      const response = await axios.get(
        `${API_BASE_URL}/news/entity/${entityName}?days=${days}`
      );
      return response.data;
    },

    search: async (query: AdvancedSearchQuery) => {
      const response = await axios.post(`${API_BASE_URL}/news/search`, query);
      return response.data;
    },

    refresh: async () => {
      const response = await axios.post(`${API_BASE_URL}/news/refresh`);
      return response.data;
    },
  },

  // Stock endpoints
  getStockInfo: async (symbol: string) => {
    try {
      // First try direct lookup by symbol
      const response = await axios.get<{ status: string; data: StockInfo }>(
        `${API_BASE_URL}/stocks/${symbol}`
      );
      return response;
    } catch (error) {
      console.error(`Error fetching stock info for ${symbol}:`, error);

      // If direct lookup failed, try a search-based approach
      try {
        const searchResponse = await axios.post(
          `${API_BASE_URL}/financial-data/search`,
          {
            query: symbol,
            entity_type: "stock",
          }
        );

        if (searchResponse.data && searchResponse.data.length > 0) {
          // Return the first match from search
          return { data: searchResponse.data[0] };
        }

        throw new Error("No stock data found");
      } catch (searchError) {
        console.error("Search fallback failed:", searchError);
        throw new Error(`Could not find stock data for ${symbol}`);
      }
    }
  },

  // Fund endpoints
  getFundInfo: async (schemeName: string) => {
    const response = await axios.get<FundInfo>(
      `${API_BASE_URL}/funds/${schemeName}`
    );
    return response.data;
  },

  getFundHoldings: async (schemeName: string) => {
    const response = await axios.get<FundHolding[]>(
      `${API_BASE_URL}/funds/${schemeName}/holdings`
    );
    return response.data;
  },

  getAllFunds: async () => {
    const response = await axios.get<FundInfo[]>(`${API_BASE_URL}/funds`);
    return response.data;
  },

  // ETF endpoints
  getETFInfo: async (symbol: string) => {
    const response = await axios.get<ETFInfo>(`${API_BASE_URL}/etfs/${symbol}`);
    return response.data;
  },

  getETFHoldings: async (symbol: string) => {
    const response = await axios.get<FundHolding[]>(
      `${API_BASE_URL}/etfs/${symbol}/holdings`
    );
    return response.data;
  },

  // Search endpoints
  searchFinancialData: async (query: AdvancedSearchQuery) => {
    const response = await axios.post(
      `${API_BASE_URL}/financial-data/search`,
      query
    );
    return response.data;
  },
};

export default api;
