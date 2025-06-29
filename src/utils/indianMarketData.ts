/**
 * Indian stock market-specific utilities and data
 */

// List of high-value Indian stocks with their NSE and BSE symbols
export const indianStocks = {
  MRF: {
    nseSymbol: "MRF.NS",
    bseSymbol: "MRF.BO",
    fullName: "MRF Limited",
    sector: "Automobiles & Auto Components",
    industry: "Tyres & Rubber Products",
  },
  PAGEIND: {
    nseSymbol: "PAGEIND.NS",
    bseSymbol: "PAGEIND.BO",
    fullName: "Page Industries Ltd.",
    sector: "Consumer Discretionary",
    industry: "Textiles & Apparel",
  },
  SHREECEM: {
    nseSymbol: "SHREECEM.NS",
    bseSymbol: "SHREECEM.BO",
    fullName: "Shree Cement Ltd.",
    sector: "Materials",
    industry: "Cement & Cement Products",
  },
  BOSCHLTD: {
    nseSymbol: "BOSCHLTD.NS",
    bseSymbol: "BOSCHLTD.BO",
    fullName: "Bosch Ltd.",
    sector: "Capital Goods",
    industry: "Auto Components",
  },
  NESTLEIND: {
    nseSymbol: "NESTLEIND.NS",
    bseSymbol: "NESTLEIND.BO",
    fullName: "Nestle India Ltd.",
    sector: "Fast Moving Consumer Goods",
    industry: "Food Products",
  },
};

// Major Indian indices
export const indianIndices = {
  NIFTY: {
    symbol: "^NSEI",
    fullName: "NIFTY 50",
    description:
      "Benchmark Indian stock market index representing the weighted average of 50 top Indian companies listed on NSE.",
  },
  SENSEX: {
    symbol: "^BSESN",
    fullName: "S&P BSE SENSEX",
    description:
      "Free-float market-weighted stock market index of 30 well-established and financially sound companies listed on BSE.",
  },
  BANKNIFTY: {
    symbol: "^NSEBANK",
    fullName: "NIFTY BANK",
    description:
      "Index comprising the most liquid Indian banking stocks traded on NSE.",
  },
};

// Formatting utilities for Indian market data
export const formatIndianMarketPrice = (price: number): string => {
  // Format in Indian currency style (with commas at different positions)
  if (!price) return "N/A";

  const priceString = price.toString();
  const decimalPart = priceString.includes(".")
    ? priceString.substring(priceString.indexOf("."))
    : "";

  let integerPart = priceString.includes(".")
    ? priceString.substring(0, priceString.indexOf("."))
    : priceString;

  // For numbers less than 1000, no formatting needed
  if (integerPart.length <= 3) {
    return `₹${price.toLocaleString("en-IN")}`;
  }

  // Indian number system: 1,00,000 instead of 100,000
  let formattedInteger = "";

  // First group of 3 from right
  const lastThree = integerPart.substring(integerPart.length - 3);
  const remaining = integerPart.substring(0, integerPart.length - 3);

  // Rest in groups of 2
  if (remaining) {
    formattedInteger =
      remaining.replace(/\B(?=(\d{2})+(?!\d))/g, ",") + "," + lastThree;
  } else {
    formattedInteger = lastThree;
  }

  return `₹${formattedInteger}${decimalPart}`;
};

export const formatIndianMarketCap = (marketCap: number): string => {
  if (!marketCap) return "N/A";

  // Format in crores and lakhs
  if (marketCap >= 10000000000) {
    // ≥ 1000 crore
    return `₹${(marketCap / 10000000).toFixed(2)} Cr`;
  } else if (marketCap >= 100000) {
    // ≥ 1 lakh
    return `₹${(marketCap / 100000).toFixed(2)} L`;
  } else {
    return `₹${marketCap.toLocaleString("en-IN")}`;
  }
};

export default {
  indianStocks,
  indianIndices,
  formatIndianMarketPrice,
  formatIndianMarketCap,
};
