import React, { useState, useEffect } from "react";
import { api } from "@/services/api";
import FinancialChart from "./FinancialChart";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Alert, AlertDescription, AlertTitle } from "@/components/ui/alert";
import { InfoIcon, AlertCircle, TrendingUp, TrendingDown } from "lucide-react";
import { Skeleton } from "@/components/ui/skeleton";
import NewsCard from "./NewsCard";
import {
  formatIndianMarketPrice,
  formatIndianMarketCap,
  indianStocks,
} from "@/utils/indianMarketData";

interface StockDetailProps {
  symbol: string;
}

const StockDetail: React.FC<StockDetailProps> = ({ symbol }) => {
  const [stockData, setStockData] = useState<any>(null);
  const [relatedNews, setRelatedNews] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [newsLoading, setNewsLoading] = useState(true);
  const [newsError, setNewsError] = useState<string | null>(null);

  useEffect(() => {
    const fetchStockData = async () => {
      setLoading(true);
      setError(null);
      try {
        const response = await api.getStockInfo(symbol);
        if (response && response.data) {
          setStockData(response.data.data || response.data);
        } else {
          setError("No data available for this stock");
        }
      } catch (err) {
        console.error("Error fetching stock data:", err);
        setError("Failed to fetch stock information");
      } finally {
        setLoading(false);
      }
    };

    const fetchRelatedNews = async () => {
      setNewsLoading(true);
      setNewsError(null);
      try {
        const news = await api.news.getByEntity(symbol);
        if (news && Array.isArray(news)) {
          setRelatedNews(news.slice(0, 5));
        } else {
          // If the API returns an empty array or non-array response
          setRelatedNews([]);
        }
      } catch (err) {
        console.error("Error fetching related news:", err);
        setNewsError("Failed to fetch news");
        setRelatedNews([]);
      } finally {
        setNewsLoading(false);
      }
    };

    if (symbol) {
      fetchStockData();
      fetchRelatedNews();
    }
  }, [symbol]);

  if (loading) {
    return <StockDetailSkeleton />;
  }

  if (error) {
    return (
      <Alert variant="destructive" className="mb-4">
        <AlertCircle className="h-4 w-4" />
        <AlertTitle>Error</AlertTitle>
        <AlertDescription>{error}</AlertDescription>
      </Alert>
    );
  }

  if (!stockData) {
    return (
      <Alert className="mb-4">
        <InfoIcon className="h-4 w-4" />
        <AlertTitle>No Data</AlertTitle>
        <AlertDescription>
          No information available for this stock symbol.
        </AlertDescription>
      </Alert>
    );
  }

  // Check if this is a non-listed entity
  const isNonListed = stockData.status === "non-listed";

  return (
    <div className="space-y-4">
      {isNonListed ? (
        <NonListedEntityCard data={stockData} />
      ) : (
        <StockDetailCard stockData={stockData} />
      )}

      {stockData.historical &&
        stockData.historical.length > 0 &&
        !isNonListed && (
          <Card>
            <CardHeader>
              <CardTitle>Price History</CardTitle>
            </CardHeader>
            <CardContent>
              <FinancialChart
                data={stockData.historical}
                change={stockData.change || 0}
                changePercent={stockData.changePercent || 0}
                title={stockData.name}
                dataSource={stockData.dataSource}
              />
            </CardContent>
          </Card>
        )}

      <Tabs defaultValue="news">
        <TabsList className="w-full mb-4">
          <TabsTrigger value="news" className="flex-1">
            Related News
          </TabsTrigger>
          <TabsTrigger value="info" className="flex-1">
            Information
          </TabsTrigger>
        </TabsList>

        <TabsContent value="news">
          <Card>
            <CardHeader>
              <CardTitle>Latest News about {stockData.name}</CardTitle>
            </CardHeader>
            <CardContent>
              {newsLoading ? (
                <div className="space-y-4">
                  <Skeleton className="h-24 w-full" />
                  <Skeleton className="h-24 w-full" />
                  <Skeleton className="h-24 w-full" />
                </div>
              ) : newsError ? (
                <Alert variant="destructive" className="mb-4">
                  <AlertCircle className="h-4 w-4" />
                  <AlertTitle>Error</AlertTitle>
                  <AlertDescription>{newsError}</AlertDescription>
                </Alert>
              ) : relatedNews.length > 0 ? (
                <div className="space-y-4">
                  {relatedNews.map((news, index) => (
                    <NewsCard key={index} news={news} />
                  ))}
                </div>
              ) : (
                <div className="text-center py-6 text-gray-500">
                  <p>No recent news found for {stockData.name}</p>
                  <p className="text-sm mt-2">
                    News data is refreshed periodically. Check back later for
                    updates.
                  </p>
                </div>
              )}
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="info">
          <Card>
            <CardHeader>
              <CardTitle>Company Information</CardTitle>
            </CardHeader>
            <CardContent>
              {isNonListed ? (
                <NonListedCompanyInfo data={stockData} />
              ) : (
                <ListedCompanyInfo data={stockData} />
              )}
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>
    </div>
  );
};

const StockDetailCard = ({ stockData }: { stockData: any }) => {
  const isPositive = (stockData.change || 0) >= 0;
  const isIndianStock = Object.keys(indianStocks).includes(
    stockData.symbol?.toUpperCase()
  );

  // Format price based on whether it's an Indian stock
  const formattedPrice = isIndianStock
    ? formatIndianMarketPrice(stockData.price)
    : stockData.price !== undefined &&
      stockData.price !== null &&
      stockData.price !== 0
    ? `₹${parseFloat(stockData.price).toLocaleString()}`
    : "N/A";

  // Format market cap based on whether it's an Indian stock
  const formattedMarketCap = isIndianStock
    ? formatIndianMarketCap(stockData.marketCap)
    : stockData.marketCap && stockData.marketCap > 0
    ? `₹${(stockData.marketCap / 10000000000).toFixed(2)} Bn`
    : "N/A";

  return (
    <Card>
      <CardHeader className="pb-2">
        <div className="flex justify-between items-start">
          <div>
            <CardTitle className="text-2xl">{stockData.name}</CardTitle>
            <p className="text-sm text-gray-500">{stockData.symbol}</p>
            {stockData.exchange && (
              <p className="text-xs text-gray-400">{stockData.exchange}</p>
            )}
          </div>
          <div className="text-right">
            <p className="text-sm text-gray-500">Last Updated</p>
            <p className="text-xs text-gray-400">
              {new Date(stockData.lastUpdated).toLocaleString()}
            </p>
            {stockData.dataSource && (
              <p className="text-xs text-blue-500 mt-1">
                {stockData.dataSource}
              </p>
            )}
          </div>
        </div>
      </CardHeader>
      <CardContent>
        <div className="grid grid-cols-1 sm:grid-cols-3 gap-4 mt-2">
          <div className="p-4 bg-gray-50 rounded-lg">
            <p className="text-sm text-gray-600">Current Price</p>
            <p className="text-2xl font-bold">{formattedPrice}</p>
            <p
              className={`text-sm flex items-center ${
                isPositive ? "text-green-600" : "text-red-600"
              }`}
            >
              {isPositive ? (
                <TrendingUp className="h-4 w-4 mr-1" />
              ) : (
                <TrendingDown className="h-4 w-4 mr-1" />
              )}
              {isPositive ? "+" : ""}
              {stockData.change?.toFixed(2) || "0.00"}({isPositive ? "+" : ""}
              {stockData.changePercent?.toFixed(2) || "0.00"}%)
            </p>
          </div>

          <div className="p-4 bg-gray-50 rounded-lg">
            <p className="text-sm text-gray-600">Market Cap</p>
            <p className="text-xl font-bold">{formattedMarketCap}</p>
            <p className="text-sm text-gray-500">
              {stockData.volume && stockData.volume > 0
                ? `Volume: ${stockData.volume.toLocaleString()}`
                : ""}
            </p>
          </div>

          <div className="p-4 bg-gray-50 rounded-lg">
            <p className="text-sm text-gray-600">Sector</p>
            <p className="text-xl font-bold">{stockData.sector || "Unknown"}</p>
            {stockData.industry && (
              <p className="text-sm text-gray-500">{stockData.industry}</p>
            )}
          </div>
        </div>
      </CardContent>
    </Card>
  );
};

const NonListedEntityCard = ({ data }: { data: any }) => {
  return (
    <Card>
      <CardHeader className="pb-2">
        <div className="flex justify-between items-start">
          <div>
            <CardTitle className="text-2xl">{data.name}</CardTitle>
            <p className="text-sm text-gray-500">{data.symbol}</p>
          </div>
          <Alert className="max-w-xs p-2">
            <AlertCircle className="h-4 w-4" />
            <AlertTitle className="text-sm">Private Company</AlertTitle>
            <AlertDescription className="text-xs">
              Not publicly traded on stock exchanges
            </AlertDescription>
          </Alert>
        </div>
      </CardHeader>
      <CardContent>
        <p className="mb-4 text-sm">{data.description}</p>

        <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
          {data.valuation && (
            <div className="p-4 bg-gray-50 rounded-lg">
              <p className="text-sm text-gray-600">Estimated Valuation</p>
              <p className="text-xl font-bold">{data.valuation}</p>
            </div>
          )}

          {data.lastFundingRound && (
            <div className="p-4 bg-gray-50 rounded-lg">
              <p className="text-sm text-gray-600">Last Funding Round</p>
              <p className="text-xl font-bold">{data.lastFundingRound}</p>
            </div>
          )}

          {data.sector && (
            <div className="p-4 bg-gray-50 rounded-lg">
              <p className="text-sm text-gray-600">Industry</p>
              <p className="text-xl font-bold">{data.sector}</p>
            </div>
          )}

          {data.founded && (
            <div className="p-4 bg-gray-50 rounded-lg">
              <p className="text-sm text-gray-600">Founded</p>
              <p className="text-xl font-bold">{data.founded}</p>
              {data.headquarters && (
                <p className="text-sm text-gray-500">{data.headquarters}</p>
              )}
            </div>
          )}
        </div>
      </CardContent>
    </Card>
  );
};

const ListedCompanyInfo = ({ data }: { data: any }) => {
  return (
    <div className="space-y-4">
      {data.description && (
        <div>
          <h3 className="text-lg font-semibold mb-2">About</h3>
          <p className="text-sm">{data.description}</p>
        </div>
      )}

      <div className="grid grid-cols-2 gap-4">
        {data.pe && (
          <div>
            <h4 className="text-sm font-medium text-gray-500">P/E Ratio</h4>
            <p className="text-md">{data.pe.toFixed(2)}</p>
          </div>
        )}

        {data.eps && (
          <div>
            <h4 className="text-sm font-medium text-gray-500">EPS</h4>
            <p className="text-md">₹{data.eps.toFixed(2)}</p>
          </div>
        )}

        {data.high52Week && (
          <div>
            <h4 className="text-sm font-medium text-gray-500">52-Week High</h4>
            <p className="text-md">₹{data.high52Week.toLocaleString()}</p>
          </div>
        )}

        {data.low52Week && (
          <div>
            <h4 className="text-sm font-medium text-gray-500">52-Week Low</h4>
            <p className="text-md">₹{data.low52Week.toLocaleString()}</p>
          </div>
        )}

        {data.dividend && (
          <div>
            <h4 className="text-sm font-medium text-gray-500">Dividend</h4>
            <p className="text-md">₹{data.dividend.toFixed(2)}</p>
          </div>
        )}

        {data.dividendYield && (
          <div>
            <h4 className="text-sm font-medium text-gray-500">
              Dividend Yield
            </h4>
            <p className="text-md">{data.dividendYield.toFixed(2)}%</p>
          </div>
        )}
      </div>
    </div>
  );
};

const NonListedCompanyInfo = ({ data }: { data: any }) => {
  return (
    <div className="space-y-4">
      {data.description && (
        <div>
          <h3 className="text-lg font-semibold mb-2">About</h3>
          <p className="text-sm">{data.description}</p>
        </div>
      )}

      <div className="grid grid-cols-2 gap-4">
        {data.ceo && (
          <div>
            <h4 className="text-sm font-medium text-gray-500">CEO</h4>
            <p className="text-md">{data.ceo}</p>
          </div>
        )}

        {data.founded && (
          <div>
            <h4 className="text-sm font-medium text-gray-500">Founded</h4>
            <p className="text-md">{data.founded}</p>
          </div>
        )}

        {data.headquarters && (
          <div>
            <h4 className="text-sm font-medium text-gray-500">Headquarters</h4>
            <p className="text-md">{data.headquarters}</p>
          </div>
        )}

        {data.valuation && (
          <div>
            <h4 className="text-sm font-medium text-gray-500">
              Estimated Valuation
            </h4>
            <p className="text-md">{data.valuation}</p>
          </div>
        )}
      </div>

      <Alert>
        <InfoIcon className="h-4 w-4" />
        <AlertTitle>Non-Listed Entity</AlertTitle>
        <AlertDescription>
          This company is not publicly traded on stock exchanges. Information is
          based on reported private funding rounds and valuations.
        </AlertDescription>
      </Alert>
    </div>
  );
};

const StockDetailSkeleton = () => {
  return (
    <div className="space-y-4">
      <Card>
        <CardHeader className="pb-2">
          <Skeleton className="h-8 w-2/3" />
          <Skeleton className="h-4 w-1/3 mt-2" />
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-1 sm:grid-cols-3 gap-4 mt-2">
            <div className="p-4 bg-gray-50 rounded-lg">
              <Skeleton className="h-4 w-20 mb-2" />
              <Skeleton className="h-8 w-24" />
              <Skeleton className="h-4 w-20 mt-2" />
            </div>
            <div className="p-4 bg-gray-50 rounded-lg">
              <Skeleton className="h-4 w-20 mb-2" />
              <Skeleton className="h-8 w-24" />
            </div>
            <div className="p-4 bg-gray-50 rounded-lg">
              <Skeleton className="h-4 w-20 mb-2" />
              <Skeleton className="h-8 w-24" />
            </div>
          </div>
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <Skeleton className="h-6 w-40" />
        </CardHeader>
        <CardContent>
          <Skeleton className="h-64 w-full" />
        </CardContent>
      </Card>
    </div>
  );
};

export default StockDetail;
