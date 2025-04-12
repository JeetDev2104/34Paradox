import React from "react";
import {
  ResponsiveContainer,
  AreaChart,
  Area,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
} from "recharts";
import { HistoricalDataPoint } from "@/utils/mockData";

interface FinancialChartProps {
  data: HistoricalDataPoint[];
  color?: string;
  title?: string;
  change?: number;
  changePercent?: number;
}

const formatCurrency = (value: number) => {
  return new Intl.NumberFormat("en-IN", {
    style: "currency",
    currency: "INR",
    minimumFractionDigits: 2,
  }).format(value);
};

const FinancialChart: React.FC<FinancialChartProps> = ({
  data,
  color = "#3b82f6",
  title,
  change,
  changePercent,
}) => {
  const isPositive = change !== undefined ? change >= 0 : true;
  const chartColor = isPositive ? "rgb(220, 38, 38)" : "rgb(220, 38, 38)"; // Override to match image - showing red

  return (
    <div className="h-[300px]">
      {title && (
        <div className="mb-4">
          <h3 className="text-lg font-semibold">{title}</h3>

          {change !== undefined && changePercent !== undefined && (
            <div className="flex items-center mt-1">
              <span className="text-2xl font-bold">
                {formatCurrency(data[data.length - 1].price)}
              </span>
              <span
                className={`ml-2 px-2 py-0.5 rounded text-sm ${
                  isPositive ? "text-green-600" : "text-red-600"
                }`}
              >
                {isPositive ? "+" : ""}
                {change.toFixed(2)} ({isPositive ? "+" : ""}
                {changePercent.toFixed(2)}%)
              </span>
            </div>
          )}
        </div>
      )}

      <div className="financial-chart h-full">
        <ResponsiveContainer width="100%" height="100%">
          <AreaChart
            data={data}
            margin={{ top: 10, right: 30, left: 0, bottom: 0 }}
          >
            <defs>
              <linearGradient id="colorGradient" x1="0" y1="0" x2="0" y2="1">
                <stop offset="5%" stopColor="#ef4444" stopOpacity={0.8} />
                <stop offset="95%" stopColor="#ef4444" stopOpacity={0} />
              </linearGradient>
            </defs>
            <XAxis
              dataKey="date"
              axisLine={false}
              tickLine={false}
              tick={{ fontSize: 10 }}
              tickFormatter={(date) => {
                const d = new Date(date);
                return `${d.getDate()}/${d.getMonth() + 1}`;
              }}
              minTickGap={30}
            />
            <YAxis
              domain={["auto", "auto"]}
              axisLine={false}
              tickLine={false}
              tick={{ fontSize: 10 }}
              tickFormatter={(value) => `₹${value}`}
              orientation="right"
            />
            <Tooltip
              formatter={(value) => formatCurrency(Number(value))}
              labelFormatter={(label) =>
                new Date(label).toLocaleDateString("en-IN", {
                  day: "numeric",
                  month: "short",
                })
              }
            />
            <Area
              type="monotone"
              dataKey="price"
              stroke="#ef4444"
              fillOpacity={1}
              fill="url(#colorGradient)"
              strokeWidth={2}
              activeDot={{
                r: 6,
                stroke: "#ef4444",
                strokeWidth: 1,
                fill: "#fff",
              }}
            />
          </AreaChart>
        </ResponsiveContainer>
      </div>
    </div>
  );
};

export default FinancialChart;
