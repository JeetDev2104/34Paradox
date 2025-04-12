import React from "react";
import { TrendingUp, TrendingDown } from "lucide-react";

interface StockCardProps {
  symbol: string;
  name: string;
  price: number;
  change: number;
  onClick?: () => void;
}

const StockCard: React.FC<StockCardProps> = ({
  symbol,
  name,
  price,
  change,
  onClick,
}) => {
  const isPositive = change >= 0;
  const changePercent = Math.abs(change).toFixed(2);

  return (
    <div
      className="bg-white rounded-lg border border-gray-200 p-4 hover:shadow-md transition-shadow cursor-pointer"
      onClick={onClick}
    >
      <div className="flex justify-between items-start">
        <div>
          <h3 className="text-sm font-bold text-gray-700">{symbol}</h3>
          <p className="text-xs text-gray-500 mb-2">{name}</p>
        </div>
        <div
          className={`flex items-center text-xs ${
            isPositive ? "text-green-600" : "text-red-600"
          }`}
        >
          {isPositive ? (
            <TrendingUp className="h-3 w-3 mr-1" />
          ) : (
            <TrendingDown className="h-3 w-3 mr-1" />
          )}
          {isPositive ? "+" : "-"}
          {changePercent}%
        </div>
      </div>
      <div className="mt-2">
        <span className="text-xl font-bold">₹{price.toLocaleString()}</span>
      </div>
    </div>
  );
};

export default StockCard;
