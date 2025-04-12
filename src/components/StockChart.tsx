import React from "react";

interface StockChartProps {
  stockName: string;
  data?: { date: string; price: number }[];
}

const StockChart: React.FC<StockChartProps> = ({ stockName, data }) => {
  // Use provided data or fallback to mock data
  const chartData = data || [
    { date: "10/23", price: 1520 },
    { date: "11/23", price: 1580 },
    { date: "12/23", price: 1660 },
    { date: "01/24", price: 1640 },
    { date: "02/24", price: 1710 },
    { date: "03/24", price: 1790 },
    { date: "04/24", price: 1745 },
    { date: "05/24", price: 1825 },
    { date: "06/24", price: 1780 },
    { date: "07/24", price: 1850 },
    { date: "08/24", price: 1915 },
    { date: "09/24", price: 1850 },
  ];

  // Calculate highest and lowest prices for labels
  const highestPrice = Math.max(...chartData.map((item) => item.price));
  const lowestPrice = Math.min(...chartData.map((item) => item.price));

  // Calculate if trend is positive (for styling)
  const isPositiveTrend =
    chartData[chartData.length - 1].price >= chartData[0].price;

  return (
    <div className="bg-white border border-gray-200 rounded-lg p-4">
      <div className="relative h-64 mb-6">
        {/* This is a styled div for demonstration - replace with actual chart */}
        <div className="absolute inset-0 bg-gradient-to-b from-red-50 to-white overflow-hidden rounded">
          <div
            className="absolute inset-0"
            style={{
              backgroundImage:
                "url(\"data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 1440 320' preserveAspectRatio='none'%3E%3Cpath fill='rgba(239, 68, 68, 0.2)' d='M0,224L60,213.3C120,203,240,181,360,181.3C480,181,600,203,720,213.3C840,224,960,224,1080,213.3C1200,203,1320,181,1380,170.7L1440,160L1440,0L1380,0C1320,0,1200,0,1080,0C960,0,840,0,720,0C600,0,480,0,360,0C240,0,120,0,60,0L0,0Z'%3E%3C/path%3E%3C/svg%3E\")",
              backgroundSize: "cover",
              backgroundPosition: "center",
              opacity: 0.8,
            }}
          />
          <div className="absolute bottom-0 left-0 right-0 h-1/2 bg-gradient-to-t from-white to-transparent" />
        </div>

        {/* Y-axis labels */}
        <div className="absolute top-0 right-0 h-full flex flex-col justify-between text-xs text-gray-500 py-2">
          <span>
            ₹
            {highestPrice.toLocaleString(undefined, {
              maximumFractionDigits: 2,
            })}
          </span>
          <span>
            ₹
            {Math.round((highestPrice + lowestPrice) / 2).toLocaleString(
              undefined,
              { maximumFractionDigits: 2 }
            )}
          </span>
          <span>
            ₹
            {lowestPrice.toLocaleString(undefined, {
              maximumFractionDigits: 2,
            })}
          </span>
        </div>
      </div>

      {/* X-axis labels - dates */}
      <div className="flex justify-between text-xs text-gray-500">
        {chartData
          .filter((_, i) => i % 3 === 0)
          .map((item, index) => (
            <span key={index}>{item.date}</span>
          ))}
      </div>
    </div>
  );
};

export default StockChart;
