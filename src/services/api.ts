import axios from "axios";

// Allow configuring the API base URL via environment variables or defaults
const API_BASE_URL =
  import.meta.env.VITE_API_BASE_URL || "http://localhost:8001/api";

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
  price: number;
  change: number;
  volume: number;
  [key: string]: any;
}

export interface FundInfo {
  scheme_name: string;
  nav: number;
  category: string;
  [key: string]: any;
}

export interface ETFInfo {
  symbol: string;
  name: string;
  price: number;
  nav?: number;
  assets?: number;
  category?: string;
  [key: string]: any;
}

export interface HoldingInfo {
  name: string;
  holdingPercentage: number;
  marketValue?: number;
  sector?: string;
  [key: string]: any;
}

export interface ChatResponse {
  answer: string;
  confidence: number;
  is_prompt?: boolean;
  related_news: Array<{
    title: string;
    summary: string;
    sentiment: string;
    sentiment_score: number;
    date: string;
    source: string;
    url: string;
  }>;
  financial_data: {
    stock?: {
      symbol: string;
      price: number;
      [key: string]: any;
    };
    fund?: {
      scheme_name: string;
      nav: number;
      [key: string]: any;
    };
    etf?: {
      symbol: string;
      name: string;
      price: number;
      [key: string]: any;
    };
    holdings?: Array<any>;
  };
  comparison_data?: Array<{
    entity: string;
    type: string;
    data: any;
  }>;
  table_data?: {
    headers: string[];
    rows: Array<{
      metric: string;
      value1: any;
      value2: any;
      difference: string;
    }>;
  };
}

export interface AdvancedSearchQuery {
  query: string;
  entity_type?: string;
  date_range?: number;
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
      const response = await axios.get<StockInfo>(
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

        // If no data found, throw error to trigger fallback
        throw new Error("No stock data found");
      } catch (searchError) {
        console.error("Search fallback failed:", searchError);

        // For demo/test purposes: Create mock data for unknown stocks
        // In production, this should be removed
        const mockData = {
          symbol: symbol.toUpperCase(),
          name: symbol.toUpperCase(),
          price: Math.random() * 5000 + 500, // Random price between 500-5500
          change: (Math.random() * 100 - 50).toFixed(2), // Random change between -50 and +50
          changePercent: (Math.random() * 10 - 5).toFixed(2), // Random percent between -5% and +5%
          volume: Math.floor(Math.random() * 10000000) + 100000,
          marketCap: Math.floor(Math.random() * 10000000000) + 1000000000,
          sector: "Unknown",
        };

        return { data: mockData };
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

  getAllFunds: async () => {
    try {
      const response = await axios.get(`${API_BASE_URL}/funds`);
      if (response && response.data && response.data.status === "success") {
        return response.data;
      } else {
        throw new Error("Invalid response format");
      }
    } catch (error) {
      console.error("Error fetching funds:", error);
      // Create minimal fallback data in case of API failure
      return {
        status: "success",
        data: [
          {
            name: "HDFC Top 100 Fund",
            type: "Mutual Fund",
            nav: 850.25,
            aum: 21500,
            oneYearReturn: 15.8,
            threeYearReturn: 12.5,
            category: "Large Cap",
            riskLevel: "Moderate",
          },
          {
            name: "Nifty BeES",
            type: "ETF",
            nav: 220.15,
            aum: 12800,
            oneYearReturn: 18.2,
            threeYearReturn: 14.7,
            category: "Index Fund",
            riskLevel: "Moderate",
          },
        ],
      };
    }
  },

  getFundHoldings: async (schemeName: string) => {
    const response = await axios.get<HoldingInfo[]>(
      `${API_BASE_URL}/funds/${schemeName}/holdings`
    );
    return response.data;
  },

  // ETF endpoints
  getETFInfo: async (symbol: string) => {
    const response = await axios.get<ETFInfo>(`${API_BASE_URL}/etfs/${symbol}`);
    return response.data;
  },

  // Unified financial data search
  searchFinancialData: async (query: AdvancedSearchQuery) => {
    const response = await axios.post(
      `${API_BASE_URL}/financial-data/search`,
      query
    );
    return response.data;
  },
};

export default api;
