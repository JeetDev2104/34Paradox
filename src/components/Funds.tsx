import React, { useState, useEffect } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Search } from "lucide-react";
import api from "@/services/api";

interface Fund {
  name: string;
  type: "Mutual Fund" | "ETF";
  nav: number;
  aum: number;
  oneYearReturn: number;
  threeYearReturn: number;
  category: string;
  riskLevel: "Low" | "Moderate" | "High";
  schemeCode?: string;
  amcName?: string;
  isin?: string;
  topHoldings?: string[];
}

const Funds: React.FC = () => {
  const [funds, setFunds] = useState<Fund[]>([]);
  const [searchTerm, setSearchTerm] = useState("");
  const [loading, setLoading] = useState(true);
  const [filter, setFilter] = useState<"all" | "mf" | "etf">("all");
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const fetchFunds = async () => {
      try {
        setLoading(true);
        setError(null);

        // Fetch data from API
        const response = await api.getAllFunds();

        // API service now handles fallback data internally,
        // so we should always have data to display
        if (
          response &&
          response.status === "success" &&
          Array.isArray(response.data)
        ) {
          console.log(`Loaded ${response.data.length} funds from API`);

          if (response.data.length === 0) {
            // If we got an empty array, show a warning
            setError("No fund data available. Using default examples.");
            setFunds([
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
            ]);
          } else {
            // We got actual data
            setFunds(response.data);

            // Check if we're using fallback data from the server
            if (
              response.data.length === 5 &&
              response.data[0].name === "HDFC Top 100 Fund" &&
              response.data[1].name === "Nifty BeES"
            ) {
              setError("Failed to load fund data. Using fallback data.");
            }
          }
        } else {
          throw new Error("Invalid data format received from API");
        }
      } catch (error) {
        console.error("Error fetching funds:", error);
        setError("Failed to load fund data. Using fallback data.");

        // Fallback data is now handled by the API service,
        // but we include this as an absolute last resort
        setFunds([
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
        ]);
      } finally {
        setLoading(false);
      }
    };

    fetchFunds();
  }, []);

  const filteredFunds = funds.filter((fund) => {
    const matchesSearch = fund.name
      .toLowerCase()
      .includes(searchTerm.toLowerCase());
    const matchesFilter =
      filter === "all" ||
      (filter === "mf" && fund.type === "Mutual Fund") ||
      (filter === "etf" && fund.type === "ETF");
    return matchesSearch && matchesFilter;
  });

  const getRiskColor = (risk: Fund["riskLevel"]) => {
    switch (risk) {
      case "Low":
        return "text-green-500";
      case "Moderate":
        return "text-yellow-500";
      case "High":
        return "text-red-500";
      default:
        return "text-gray-500";
    }
  };

  return (
    <div className="container mx-auto p-4">
      <div className="mb-6 space-y-4">
        <div className="relative">
          <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400" />
          <Input
            type="text"
            placeholder="Search funds..."
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            className="pl-10 w-full"
          />
        </div>
        <div className="flex space-x-2">
          <button
            onClick={() => setFilter("all")}
            className={`px-4 py-2 rounded-md ${
              filter === "all" ? "bg-blue-500 text-white" : "bg-gray-100"
            }`}
          >
            All
          </button>
          <button
            onClick={() => setFilter("mf")}
            className={`px-4 py-2 rounded-md ${
              filter === "mf" ? "bg-blue-500 text-white" : "bg-gray-100"
            }`}
          >
            Mutual Funds
          </button>
          <button
            onClick={() => setFilter("etf")}
            className={`px-4 py-2 rounded-md ${
              filter === "etf" ? "bg-blue-500 text-white" : "bg-gray-100"
            }`}
          >
            ETFs
          </button>
        </div>
      </div>

      {error && (
        <div className="bg-yellow-50 border border-yellow-200 text-yellow-800 px-4 py-3 rounded mb-4">
          {error}
        </div>
      )}

      {loading ? (
        <div className="flex justify-center items-center py-20">
          <div className="animate-spin rounded-full h-12 w-12 border-t-2 border-b-2 border-blue-500"></div>
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {filteredFunds.length > 0 ? (
            filteredFunds.map((fund, index) => (
              <Card key={index} className="hover:shadow-lg transition-shadow">
                <CardHeader>
                  <CardTitle className="flex justify-between items-start">
                    <span className="text-lg font-semibold pr-2">
                      {fund.name}
                    </span>
                    <span className="text-sm bg-gray-100 px-2 py-1 rounded whitespace-nowrap">
                      {fund.type}
                    </span>
                  </CardTitle>
                  {fund.amcName && (
                    <p className="text-sm text-gray-500 mt-1">{fund.amcName}</p>
                  )}
                </CardHeader>
                <CardContent>
                  <div className="space-y-3">
                    <div className="grid grid-cols-2 gap-2 text-sm">
                      <div>
                        <p className="text-gray-500">NAV</p>
                        <p className="font-semibold">₹{fund.nav.toFixed(2)}</p>
                      </div>
                      <div>
                        <p className="text-gray-500">AUM (Cr)</p>
                        <p className="font-semibold">₹{fund.aum.toFixed(0)}</p>
                      </div>
                    </div>
                    <div className="grid grid-cols-2 gap-2 text-sm">
                      <div>
                        <p className="text-gray-500">1Y Return</p>
                        <p
                          className={`font-semibold ${
                            fund.oneYearReturn >= 0
                              ? "text-green-500"
                              : "text-red-500"
                          }`}
                        >
                          {fund.oneYearReturn >= 0 ? "+" : ""}
                          {fund.oneYearReturn.toFixed(2)}%
                        </p>
                      </div>
                      <div>
                        <p className="text-gray-500">3Y Return</p>
                        <p
                          className={`font-semibold ${
                            fund.threeYearReturn >= 0
                              ? "text-green-500"
                              : "text-red-500"
                          }`}
                        >
                          {fund.threeYearReturn >= 0 ? "+" : ""}
                          {fund.threeYearReturn.toFixed(2)}%
                        </p>
                      </div>
                    </div>
                    <div className="flex justify-between text-sm">
                      <span className="text-gray-500">{fund.category}</span>
                      <span className={getRiskColor(fund.riskLevel)}>
                        {fund.riskLevel} Risk
                      </span>
                    </div>
                  </div>
                </CardContent>
              </Card>
            ))
          ) : (
            <div className="col-span-full text-center py-10">
              <p className="text-gray-500">
                No funds found matching your search criteria.
              </p>
            </div>
          )}
        </div>
      )}
    </div>
  );
};

export default Funds;
