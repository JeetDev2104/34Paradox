import React, { useState, useEffect } from "react";
import FinancialChart from "@/components/FinancialChart";
import NewsCard from "@/components/NewsCard";
import ChatInterface from "@/components/ChatInterface";
import {
  mockStocks,
  mockNews,
  getRelevantNews,
  mockFunds,
} from "@/utils/mockData";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { ChevronUp, ChevronDown, Search } from "lucide-react";
import api from "@/services/api";
import { Input } from "@/components/ui/input";
import axios from "axios";

// Define a union type for all financial instruments
interface FinancialInstrument {
  id: string;
  symbol: string;
  name: string;
  price: number;
  change: number;
  changePercent: number;
  historicalData: { date: string; price: number }[];
  type: "stock" | "mutualfund" | "etf";
  // Optional fields that might be specific to certain types
  marketCap?: number;
  volume?: number;
  sector?: string;
  nav?: number;
  aum?: number;
  category?: string;
  riskLevel?: string;
}

const Dashboard: React.FC = () => {
  // Convert mockStocks to FinancialInstrument type
  const stocksAsInstruments: FinancialInstrument[] = mockStocks.map(
    (stock) => ({
      ...stock,
      type: "stock",
    })
  );

  // Convert mockFunds to FinancialInstrument type
  const fundsAsInstruments: FinancialInstrument[] = mockFunds.map((fund) => ({
    id: fund.id,
    symbol: fund.symbol,
    name: fund.name,
    price: fund.price,
    change: fund.change,
    changePercent: fund.changePercent,
    historicalData: fund.historicalData,
    type: fund.category.toLowerCase().includes("etf") ? "etf" : "mutualfund",
    nav: fund.price,
    aum: fund.aum,
    category: fund.category,
  }));

  // Combine all financial instruments
  const allInstruments = [...stocksAsInstruments, ...fundsAsInstruments];

  const [selectedInstrument, setSelectedInstrument] =
    useState<FinancialInstrument>(allInstruments[0]);
  const [relevantNews, setRelevantNews] = useState([]);
  const [loading, setLoading] = useState(false);
  const [recentNews, setRecentNews] = useState([]);
  const [apiAvailable, setApiAvailable] = useState(false);
  const [searchQuery, setSearchQuery] = useState("");
  const [activeTab, setActiveTab] = useState("relevant-news");
  const [searchResults, setSearchResults] = useState<FinancialInstrument[]>([]);
  const [searchPerformed, setSearchPerformed] = useState(false);
  const [instrumentTypeFilter, setInstrumentTypeFilter] = useState<
    "all" | "stock" | "mutualfund" | "etf"
  >("all");

  // Check if API is available and fetch initial data
  useEffect(() => {
    const fetchInitialData = async () => {
      try {
        setLoading(true);
        // Try to get recent news from API
        try {
          const newsResponse = await axios.get(
            `${
              import.meta.env.VITE_API_BASE_URL || "http://localhost:8001/api"
            }/news/recent?limit=10`
          );
          if (newsResponse && newsResponse.data) {
            // Handle potential nested data structure
            const newsData = Array.isArray(newsResponse.data)
              ? newsResponse.data
              : newsResponse.data.data || [];

            if (newsData.length > 0) {
              setRecentNews(newsData);
              setApiAvailable(true);

              // Fetch news for the selected instrument
              try {
                const instrumentNewsResponse = await axios.get(
                  `${
                    import.meta.env.VITE_API_BASE_URL ||
                    "http://localhost:8001/api"
                  }/news/entity/${selectedInstrument.symbol}`
                );
                if (instrumentNewsResponse && instrumentNewsResponse.data) {
                  // Handle potential nested data structure
                  const instrumentNewsData = Array.isArray(
                    instrumentNewsResponse.data
                  )
                    ? instrumentNewsResponse.data
                    : instrumentNewsResponse.data.data || [];

                  if (instrumentNewsData.length > 0) {
                    setRelevantNews(instrumentNewsData);
                  } else {
                    // Fallback to mock data
                    setRelevantNews(getRelevantNews(selectedInstrument.symbol));
                  }
                } else {
                  // Fallback to mock data
                  setRelevantNews(getRelevantNews(selectedInstrument.symbol));
                }
              } catch (error) {
                console.error("Error fetching instrument news:", error);
                // Fallback to mock data
                setRelevantNews(getRelevantNews(selectedInstrument.symbol));
              }
            } else {
              throw new Error("No news data available");
            }
          } else {
            throw new Error("Invalid API response format");
          }
        } catch (error) {
          console.error("Error fetching news:", error);
          // Fallback to mock data
          setRecentNews(mockNews);
          setRelevantNews(getRelevantNews(selectedInstrument.symbol));
        }
      } catch (error) {
        console.error("Error in initial data fetch:", error);
        // If API fails, we keep using mock data
        setRecentNews(mockNews);
        setRelevantNews(getRelevantNews(selectedInstrument.symbol));
      } finally {
        setLoading(false);
      }
    };

    fetchInitialData();
  }, []);

  const handleSearch = async (query: string) => {
    if (!query.trim()) return;

    console.log("Search query:", query);
    setSearchQuery(query);
    setSearchPerformed(true);
    setLoading(true);

    try {
      // Call the API endpoint to get stock data
      const response = await axios.get(
        `${
          import.meta.env.VITE_API_BASE_URL || "http://localhost:8001/api"
        }/stocks/${query.trim()}`
      );

      if (
        response &&
        response.data &&
        response.data.status === "success" &&
        response.data.data
      ) {
        console.log("API response:", response.data);
        // Create a financial instrument from the API response
        const stockData = response.data.data; // Access the nested data property
        const apiStockInstrument: FinancialInstrument = {
          id: `api-${stockData.symbol}`,
          symbol: stockData.symbol,
          name: stockData.name || stockData.symbol,
          price: stockData.price,
          change: stockData.change || 0,
          changePercent: stockData.changePercent || 0,
          historicalData:
            stockData.historicalData ||
            generateDummyHistoricalData(stockData.price),
          type: "stock",
          marketCap: stockData.marketCap,
          volume: stockData.volume,
          sector: stockData.sector || "N/A",
        };

        setSearchResults([apiStockInstrument]);
        setSelectedInstrument(apiStockInstrument);
        setActiveTab("relevant-news");

        // Fetch news for this stock
        try {
          const newsResponse = await axios.get(
            `${
              import.meta.env.VITE_API_BASE_URL || "http://localhost:8001/api"
            }/news/entity/${stockData.symbol}`
          );
          if (newsResponse && newsResponse.data) {
            // Handle potential nested data structure
            const newsData = Array.isArray(newsResponse.data)
              ? newsResponse.data
              : newsResponse.data.data || [];

            if (newsData.length > 0) {
              setRelevantNews(newsData);
            } else {
              setRelevantNews([]);
            }
          } else {
            setRelevantNews([]);
          }
        } catch (newsError) {
          console.error("Error fetching news:", newsError);
          setRelevantNews([]);
        }
      } else {
        throw new Error("No stock data found or invalid response format");
      }
    } catch (error) {
      console.error("Error fetching stock data:", error);

      // Fallback: search in mock data if API call fails
      const matches = allInstruments.filter(
        (instrument) =>
          instrument.symbol.toLowerCase().includes(query.toLowerCase()) ||
          instrument.name.toLowerCase().includes(query.toLowerCase())
      );

      // Apply type filter if needed
      const filteredMatches =
        instrumentTypeFilter === "all"
          ? matches
          : matches.filter(
              (instrument) => instrument.type === instrumentTypeFilter
            );

      setSearchResults(filteredMatches);

      // If matches found, select the first match
      if (filteredMatches.length > 0) {
        handleInstrumentSelect(filteredMatches[0].id);
      } else {
        // Create a generic instrument for the search query
        const genericStockInstrument: FinancialInstrument = {
          id: `search-${query}`,
          symbol: query.toUpperCase(),
          name: `${query.toUpperCase()} (Search Result)`,
          price: 0,
          change: 0,
          changePercent: 0,
          historicalData: generateDummyHistoricalData(1000),
          type: "stock",
          sector: "Unknown",
        };

        setSearchResults([genericStockInstrument]);
        setSelectedInstrument(genericStockInstrument);
        setRelevantNews([]);
      }
    } finally {
      setLoading(false);
    }
  };

  const handleInstrumentSelect = async (instrumentId: string) => {
    const instrument = allInstruments.find((item) => item.id === instrumentId);
    if (instrument) {
      setSelectedInstrument(instrument);
      setLoading(true);

      try {
        // Fetch news for this instrument using direct API call
        const newsResponse = await axios.get(
          `${
            import.meta.env.VITE_API_BASE_URL || "http://localhost:8001/api"
          }/news/entity/${instrument.symbol}`
        );
        if (newsResponse && newsResponse.data) {
          // Handle potential nested data format
          const newsData = Array.isArray(newsResponse.data)
            ? newsResponse.data
            : newsResponse.data.data || [];

          if (newsData.length > 0) {
            setRelevantNews(newsData);
          } else {
            // Fallback to mock data if no news found
            setRelevantNews(getRelevantNews(instrument.symbol));
          }
        } else {
          // Fallback to mock data if no news found
          setRelevantNews(getRelevantNews(instrument.symbol));
        }
      } catch (error) {
        console.error("Error fetching instrument news:", error);
        // Fallback to mock data
        setRelevantNews(getRelevantNews(instrument.symbol));
      } finally {
        setLoading(false);
      }

      // Switch to relevant news tab when selecting a new instrument
      setActiveTab("relevant-news");

      // Clear search state after selecting
      setSearchPerformed(false);
      setSearchResults([]);
    }
  };

  // Filter instruments to display based on search and type filter
  const instrumentsToDisplay =
    searchPerformed && searchResults.length > 0
      ? searchResults
      : instrumentTypeFilter === "all"
      ? allInstruments.slice(0, 6)
      : allInstruments
          .filter((instrument) => instrument.type === instrumentTypeFilter)
          .slice(0, 6);

  // Generate dummy historical data for stocks not in our database
  const generateDummyHistoricalData = (
    basePrice: number
  ): { date: string; price: number }[] => {
    const data = [];
    const today = new Date();
    let currentPrice = basePrice;

    for (let i = 30; i >= 0; i--) {
      const date = new Date(today);
      date.setDate(today.getDate() - i);

      // Add some randomness to price
      const change = (Math.random() - 0.48) * (basePrice * 0.03);
      currentPrice += change;

      data.push({
        date: date.toISOString().split("T")[0],
        price: Math.max(currentPrice, basePrice * 0.7), // Ensure price doesn't go too low
      });
    }

    return data;
  };

  return (
    <div className="py-6 px-4 md:px-6">
      <div className="mb-6">
        <h1 className="text-2xl font-bold mb-2">Market Insights Dashboard</h1>
        <p className="text-gray-600">
          Market analysis powered by AI, connecting news events to financial
          market movements.
        </p>
      </div>

      <div className="mb-6">
        <div className="relative max-w-md mx-auto">
          <div className="absolute inset-y-0 left-3 flex items-center pointer-events-none">
            <Search className="h-4 w-4 text-gray-400" />
          </div>
          <Input
            type="text"
            placeholder="Search SEBI registered stocks (e.g., RELIANCE, HDFC, TCS)"
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            onKeyDown={(e) => {
              if (e.key === "Enter") {
                handleSearch(searchQuery);
              }
            }}
            className="w-full pl-10 pr-4 py-2 border border-gray-300 rounded-lg"
          />
          <button
            onClick={() => handleSearch(searchQuery)}
            className="absolute right-2 top-1/2 transform -translate-y-1/2 bg-blue-600 hover:bg-blue-700 text-white px-4 py-1 rounded text-sm font-medium transition-colors"
          >
            Search
          </button>
        </div>

        <div className="flex justify-center mt-4 space-x-2">
          <button
            onClick={() => setInstrumentTypeFilter("all")}
            className={`px-3 py-1 rounded text-sm ${
              instrumentTypeFilter === "all"
                ? "bg-blue-600 text-white"
                : "bg-gray-200"
            }`}
          >
            All
          </button>
          <button
            onClick={() => setInstrumentTypeFilter("stock")}
            className={`px-3 py-1 rounded text-sm ${
              instrumentTypeFilter === "stock"
                ? "bg-blue-600 text-white"
                : "bg-gray-200"
            }`}
          >
            Stocks
          </button>
          <button
            onClick={() => setInstrumentTypeFilter("mutualfund")}
            className={`px-3 py-1 rounded text-sm ${
              instrumentTypeFilter === "mutualfund"
                ? "bg-blue-600 text-white"
                : "bg-gray-200"
            }`}
          >
            Mutual Funds
          </button>
          <button
            onClick={() => setInstrumentTypeFilter("etf")}
            className={`px-3 py-1 rounded text-sm ${
              instrumentTypeFilter === "etf"
                ? "bg-blue-600 text-white"
                : "bg-gray-200"
            }`}
          >
            ETFs
          </button>
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-8">
        {loading ? (
          <p>Loading...</p>
        ) : (
          instrumentsToDisplay.map((instrument) => (
            <Card
              key={instrument.id}
              className={`cursor-pointer hover:shadow-md transition-shadow ${
                selectedInstrument.id === instrument.id
                  ? "ring-2 ring-blue-500"
                  : ""
              }`}
              onClick={() => handleInstrumentSelect(instrument.id)}
            >
              <CardContent className="p-4">
                <div className="flex justify-between items-center">
                  <div>
                    <p className="text-sm font-semibold">{instrument.symbol}</p>
                    <h3 className="text-lg font-bold">{instrument.name}</h3>
                    <span
                      className={`text-xs px-2 py-0.5 rounded-full ${
                        instrument.type === "stock"
                          ? "bg-blue-100 text-blue-800"
                          : instrument.type === "mutualfund"
                          ? "bg-purple-100 text-purple-800"
                          : "bg-amber-100 text-amber-800"
                      }`}
                    >
                      {instrument.type === "stock"
                        ? "Stock"
                        : instrument.type === "mutualfund"
                        ? "Mutual Fund"
                        : "ETF"}
                    </span>
                  </div>
                  <div className="text-right">
                    <p className="text-lg font-bold">
                      ₹{instrument.price.toFixed(2)}
                    </p>
                    <div className="flex items-center justify-end">
                      {instrument.changePercent >= 0 ? (
                        <ChevronUp className="h-4 w-4 text-green-600" />
                      ) : (
                        <ChevronDown className="h-4 w-4 text-red-600" />
                      )}
                      <span
                        className={
                          instrument.changePercent >= 0
                            ? "text-green-600"
                            : "text-red-600"
                        }
                      >
                        {instrument.changePercent >= 0 ? "+" : ""}
                        {instrument.changePercent.toFixed(2)}%
                      </span>
                    </div>
                  </div>
                </div>
              </CardContent>
            </Card>
          ))
        )}
      </div>

      <div className="grid grid-cols-1 xl:grid-cols-3 gap-6">
        <div className="xl:col-span-2 space-y-6">
          <Card>
            <CardHeader className="pb-2">
              <CardTitle className="text-lg font-semibold">
                {selectedInstrument.symbol} - {selectedInstrument.name}
                <span
                  className={`ml-2 text-xs px-2 py-0.5 rounded-full ${
                    selectedInstrument.type === "stock"
                      ? "bg-blue-100 text-blue-800"
                      : selectedInstrument.type === "mutualfund"
                      ? "bg-purple-100 text-purple-800"
                      : "bg-amber-100 text-amber-800"
                  }`}
                >
                  {selectedInstrument.type === "stock"
                    ? "Stock"
                    : selectedInstrument.type === "mutualfund"
                    ? "Mutual Fund"
                    : "ETF"}
                </span>
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="flex flex-col md:flex-row justify-between mb-4">
                <div>
                  <p className="text-sm text-gray-600">
                    {selectedInstrument.type === "stock"
                      ? "Current Price"
                      : "NAV"}
                  </p>
                  <p className="text-xl font-bold">
                    ₹{selectedInstrument.price.toFixed(2)}
                  </p>
                  <p
                    className={`text-sm ${
                      selectedInstrument.changePercent >= 0
                        ? "text-green-600"
                        : "text-red-600"
                    }`}
                  >
                    {selectedInstrument.changePercent >= 0 ? "+" : ""}
                    {selectedInstrument.change.toFixed(2)}(
                    {selectedInstrument.changePercent >= 0 ? "+" : ""}
                    {selectedInstrument.changePercent.toFixed(2)}%)
                  </p>
                </div>
                <div className="mt-4 md:mt-0">
                  <p className="text-sm text-gray-600">
                    {selectedInstrument.type === "stock" ? "Market Cap" : "AUM"}
                  </p>
                  <p className="text-md font-medium">
                    {selectedInstrument.type === "stock" &&
                    selectedInstrument.marketCap
                      ? `₹${(
                          selectedInstrument.marketCap / 10000000000
                        ).toFixed(2)} Bn`
                      : selectedInstrument.aum
                      ? `₹${(selectedInstrument.aum / 10000000000).toFixed(
                          2
                        )} Bn`
                      : "N/A"}
                  </p>
                  <p className="text-sm text-gray-600">
                    {selectedInstrument.type === "stock" &&
                    selectedInstrument.volume
                      ? `Volume: ${selectedInstrument.volume.toLocaleString()}`
                      : selectedInstrument.category
                      ? `Category: ${selectedInstrument.category}`
                      : ""}
                  </p>
                </div>
                <div className="mt-4 md:mt-0">
                  <p className="text-sm text-gray-600">
                    {selectedInstrument.type === "stock"
                      ? "Sector"
                      : "Category"}
                  </p>
                  <p className="text-md font-medium">
                    {selectedInstrument.type === "stock"
                      ? selectedInstrument.sector
                      : selectedInstrument.category}
                  </p>
                </div>
              </div>
              <FinancialChart
                data={selectedInstrument.historicalData}
                change={selectedInstrument.change}
                changePercent={selectedInstrument.changePercent}
                title={selectedInstrument.name}
              />
            </CardContent>
          </Card>

          <Tabs value={activeTab} onValueChange={setActiveTab}>
            <TabsList className="grid grid-cols-3 w-full mt-15 mb-5 border-b justify-center">
              <TabsTrigger
                value="relevant-news"
                className="py-3 px-2 font-medium transition-colors hover:bg-gray-50 data-[state=active]:border-b-2 data-[state=active]:border-blue-600 data-[state=active]:text-blue-600 rounded-none"
              >
                Relevant News
              </TabsTrigger>
              <TabsTrigger
                value="all-news"
                className="py-3 px-2 font-medium transition-colors hover:bg-gray-50 data-[state=active]:border-b-2 data-[state=active]:border-blue-600 data-[state=active]:text-blue-600 rounded-none"
              >
                All News
              </TabsTrigger>
              <TabsTrigger
                value="market-analysis"
                className="py-3 px-2 font-medium transition-colors hover:bg-gray-50 data-[state=active]:border-b-2 data-[state=active]:border-blue-600 data-[state=active]:text-blue-600 rounded-none"
              >
                Market Analysis
              </TabsTrigger>
            </TabsList>
            <TabsContent value="relevant-news" className="space-y-4">
              {loading ? (
                <div className="p-6 text-center">
                  <div className="inline-block animate-spin h-8 w-8 border-4 border-gray-300 border-t-blue-600 rounded-full"></div>
                  <p className="mt-2 text-gray-600">Loading news...</p>
                </div>
              ) : relevantNews && relevantNews.length > 0 ? (
                relevantNews.map((news, index) => (
                  <NewsCard key={news.id || index} news={news} />
                ))
              ) : (
                <div className="p-6 text-center border rounded-lg bg-gray-50">
                  <p className="text-gray-600">
                    No relevant news found for {selectedInstrument.name}.
                  </p>
                </div>
              )}
            </TabsContent>
            <TabsContent value="all-news" className="space-y-4">
              {loading ? (
                <div className="p-6 text-center">
                  <div className="inline-block animate-spin h-8 w-8 border-4 border-gray-300 border-t-blue-600 rounded-full"></div>
                  <p className="mt-2 text-gray-600">Loading news...</p>
                </div>
              ) : recentNews && recentNews.length > 0 ? (
                recentNews.map((news, index) => (
                  <NewsCard key={news.id || index} news={news} />
                ))
              ) : (
                <div className="p-6 text-center border rounded-lg bg-gray-50">
                  <p className="text-gray-600">No news available.</p>
                </div>
              )}
            </TabsContent>
            <TabsContent value="market-analysis">
              <Card className="p-6">
                <div className="flex items-center mb-4">
                  <h3 className="font-semibold">Market Analysis</h3>
                </div>
                <div className="space-y-4">
                  <p className="text-sm text-gray-700">
                    <span className="font-medium">
                      {selectedInstrument.symbol} ({selectedInstrument.name})
                    </span>{" "}
                    is currently{" "}
                    {selectedInstrument.type === "stock"
                      ? "trading at"
                      : "priced at"}{" "}
                    ₹{selectedInstrument.price.toFixed(2)}, showing a{" "}
                    {selectedInstrument.changePercent >= 0
                      ? "positive"
                      : "negative"}{" "}
                    change of{" "}
                    {Math.abs(selectedInstrument.changePercent).toFixed(2)}% (
                    {selectedInstrument.changePercent >= 0 ? "+" : ""}
                    {selectedInstrument.change.toFixed(2)}).
                  </p>

                  <div className="bg-gray-50 p-4 rounded-lg">
                    <h4 className="font-medium mb-2">Key Metrics</h4>
                    <div className="grid grid-cols-2 gap-4">
                      <div>
                        <p className="text-xs text-gray-500">
                          {selectedInstrument.type === "stock"
                            ? "Market Cap"
                            : "AUM"}
                        </p>
                        <p className="font-medium">
                          {selectedInstrument.type === "stock" &&
                          selectedInstrument.marketCap
                            ? `₹${(
                                selectedInstrument.marketCap / 10000000000
                              ).toFixed(2)} Billion`
                            : selectedInstrument.aum
                            ? `₹${(
                                selectedInstrument.aum / 10000000000
                              ).toFixed(2)} Billion`
                            : "N/A"}
                        </p>
                      </div>
                      <div>
                        <p className="text-xs text-gray-500">
                          {selectedInstrument.type === "stock"
                            ? "Trading Volume"
                            : "Category"}
                        </p>
                        <p className="font-medium">
                          {selectedInstrument.type === "stock" &&
                          selectedInstrument.volume
                            ? `${selectedInstrument.volume.toLocaleString()} shares`
                            : selectedInstrument.category}
                        </p>
                      </div>
                      <div>
                        <p className="text-xs text-gray-500">
                          {selectedInstrument.type === "stock"
                            ? "Sector"
                            : "Type"}
                        </p>
                        <p className="font-medium">
                          {selectedInstrument.type === "stock"
                            ? selectedInstrument.sector
                            : selectedInstrument.type === "mutualfund"
                            ? "Mutual Fund"
                            : "ETF"}
                        </p>
                      </div>
                      <div>
                        <p className="text-xs text-gray-500">
                          52-Week Performance
                        </p>
                        <p
                          className={`font-medium ${
                            selectedInstrument.changePercent >= 0
                              ? "text-green-600"
                              : "text-red-600"
                          }`}
                        >
                          {selectedInstrument.changePercent >= 0 ? "+" : ""}
                          {(selectedInstrument.changePercent * 2).toFixed(2)}%
                        </p>
                      </div>
                    </div>
                  </div>

                  {loading ? (
                    <p className="text-sm text-gray-600">
                      Loading market data...
                    </p>
                  ) : relevantNews && relevantNews.length > 0 ? (
                    <div>
                      <p className="text-sm text-gray-700 font-medium">
                        Recent news impact:
                      </p>
                      <p className="text-sm text-gray-700">
                        {relevantNews[0].summary ||
                          `Latest news from ${
                            relevantNews[0].source
                          } suggests market sentiment is ${
                            relevantNews[0].sentiment || "neutral"
                          }.`}
                      </p>
                      <p className="text-sm text-gray-500 mt-2">
                        {relevantNews[0].source} • {relevantNews[0].date}
                      </p>
                    </div>
                  ) : (
                    <p className="text-sm text-gray-700">
                      No recent news analysis available for this{" "}
                      {selectedInstrument.type === "stock"
                        ? "stock"
                        : selectedInstrument.type === "mutualfund"
                        ? "mutual fund"
                        : "ETF"}
                      .
                      {selectedInstrument.type === "stock" &&
                        selectedInstrument.volume &&
                        ` The trading volume is ${selectedInstrument.volume.toLocaleString()} shares.`}
                    </p>
                  )}
                </div>
              </Card>
            </TabsContent>
          </Tabs>
        </div>

        <div className="xl:col-span-1">
          <ChatInterface />
        </div>
      </div>
    </div>
  );
};

export default Dashboard;
