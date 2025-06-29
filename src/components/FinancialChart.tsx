import React from "react";
import {
  AreaChart,
  Area,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
} from "recharts";
import { TrendingUp, TrendingDown } from "lucide-react";

interface HistoricalDataPoint {
  date: string;
  price: number;
}

interface FinancialChartProps {
  data?: HistoricalDataPoint[];
  change: number;
  changePercent: number;
  title: string;
  dataSource?: string;
}

const FinancialChart: React.FC<FinancialChartProps> = ({
  data,
  change,
  changePercent,
  title,
  dataSource,
}) => {
  const isPositive = change >= 0;

  // Create mock data if no data is provided
  const chartData = data || [
    { date: "2024-05-01", price: 1520 },
    { date: "2024-05-02", price: 1580 },
    { date: "2024-05-03", price: 1660 },
    { date: "2024-05-04", price: 1640 },
    { date: "2024-05-05", price: 1710 },
    { date: "2024-05-06", price: 1790 },
    { date: "2024-05-07", price: 1745 },
  ];

  // Format dates for better display
  const formattedData = chartData.map((point) => ({
    ...point,
    formattedDate: new Date(point.date).toLocaleDateString("en-US", {
      month: "short",
      day: "numeric",
    }),
  }));

  // Determine min and max for Y axis (with a small buffer)
  const prices = chartData.map((item) => item.price);
  const minPrice = Math.min(...prices) * 0.995;
  const maxPrice = Math.max(...prices) * 1.005;

  // Custom tooltip
  const CustomTooltip = ({ active, payload, label }: any) => {
    if (active && payload && payload.length) {
      return (
        <div className="bg-white p-2 border border-gray-200 shadow-md rounded text-xs">
          <p className="font-semibold">{payload[0].payload.formattedDate}</p>
          <p className="font-bold">
            ₹
            {payload[0].value.toLocaleString(undefined, {
              maximumFractionDigits: 2,
            })}
          </p>
        </div>
      );
    }
    return null;
  };

  return (
    <div className="bg-white rounded-lg border border-gray-200 p-4">
      <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center mb-4">
        <div>
          <h3 className="text-lg font-bold">{title}</h3>
          {dataSource && (
            <p className="text-xs text-gray-500">Data Source: {dataSource}</p>
          )}
        </div>
        <div className="mt-2 sm:mt-0 flex items-center">
          <div
            className={`flex items-center text-sm font-medium ${
              isPositive ? "text-green-600" : "text-red-600"
            }`}
          >
            {isPositive ? (
              <TrendingUp className="h-4 w-4 mr-1" />
            ) : (
              <TrendingDown className="h-4 w-4 mr-1" />
            )}
            <span>
              {isPositive ? "+" : ""}
              {change.toFixed(2)} ({isPositive ? "+" : ""}
              {changePercent.toFixed(2)}%)
            </span>
          </div>
        </div>
      </div>

      <div className="h-64 w-full">
        <ResponsiveContainer width="100%" height="100%">
          <AreaChart
            data={formattedData}
            margin={{ top: 10, right: 0, left: 0, bottom: 5 }}
          >
            <defs>
              <linearGradient id="colorPrice" x1="0" y1="0" x2="0" y2="1">
                <stop
                  offset="5%"
                  stopColor={isPositive ? "#10B981" : "#EF4444"}
                  stopOpacity={0.8}
                />
                <stop
                  offset="95%"
                  stopColor={isPositive ? "#10B981" : "#EF4444"}
                  stopOpacity={0}
                />
              </linearGradient>
            </defs>
            <CartesianGrid
              vertical={false}
              strokeDasharray="3 3"
              opacity={0.2}
            />
            <XAxis
              dataKey="formattedDate"
              tick={{ fontSize: 10 }}
              tickMargin={5}
              axisLine={false}
              tickLine={false}
            />
            <YAxis
              domain={[minPrice, maxPrice]}
              tick={{ fontSize: 10 }}
              tickFormatter={(value) =>
                `₹${value.toLocaleString(undefined, {
                  maximumFractionDigits: 0,
                })}`
              }
              width={60}
              axisLine={false}
              tickLine={false}
            />
            <Tooltip content={<CustomTooltip />} />
            <Area
              type="monotone"
              dataKey="price"
              stroke={isPositive ? "#10B981" : "#EF4444"}
              fillOpacity={1}
              fill="url(#colorPrice)"
              strokeWidth={2}
            />
          </AreaChart>
        </ResponsiveContainer>
      </div>

      <div className="mt-4 text-xs text-gray-400 text-center">
        Last {chartData.length} days of price history
      </div>
    </div>
  );
};

export default FinancialChart;
