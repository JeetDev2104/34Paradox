import React from "react";
import { Card } from "@/components/ui/card";

interface NewsItem {
  id?: string;
  title: string;
  source: string;
  date: string;
  summary: string;
  url?: string;
  sentiment?: "positive" | "negative" | "neutral";
  sentiment_score?: number;
}

interface NewsCardProps {
  news: NewsItem;
}

// Function to convert URLs in text to hyperlinks
const formatTextWithLinks = (text: string) => {
  if (!text) return "";

  // URL regex pattern
  const urlPattern = /(https?:\/\/[^\s]+)/g;

  // Split text by URLs
  const parts = text.split(urlPattern);

  // Find all URLs
  const urls = text.match(urlPattern) || [];

  // If no URLs, return the original text
  if (urls.length === 0) return text;

  // Combine parts and URLs
  return parts.map((part, i) => {
    // If this part is a URL
    if (urls[i]) {
      return (
        <React.Fragment key={i}>
          {part}
          <a
            href={urls[i]}
            target="_blank"
            rel="noopener noreferrer"
            className="text-blue-600 underline break-all"
          >
            {urls[i]}
          </a>
        </React.Fragment>
      );
    }
    return part;
  });
};

const NewsCard: React.FC<NewsCardProps> = ({ news }) => {
  const { title, source, date, summary, sentiment = "neutral", url } = news;

  // Determine sentiment class
  const sentimentClass =
    sentiment === "positive"
      ? "bg-green-100 text-green-800"
      : sentiment === "negative"
      ? "bg-red-100 text-red-800"
      : "bg-gray-100 text-gray-800";

  return (
    <Card className="hover:shadow-md">
      <div className="p-6">
        <div className="flex justify-between items-start mb-2">
          <h3 className="text-lg font-semibold">{title}</h3>
          <span className={`text-xs px-2 py-1 rounded ${sentimentClass}`}>
            {sentiment}
          </span>
        </div>

        <div className="text-sm text-gray-600 mb-4 whitespace-pre-wrap break-words">
          {typeof summary === "string" ? formatTextWithLinks(summary) : summary}
        </div>

        <div className="text-sm text-gray-500 flex items-center">
          <span>
            {source} • {date}
          </span>
          <div className="ml-auto">
            {url && (
              <a
                href={url}
                target="_blank"
                rel="noopener noreferrer"
                className="text-xs text-blue-600 hover:text-blue-800"
              >
                Read full article →
              </a>
            )}
          </div>
        </div>
      </div>
    </Card>
  );
};

export default NewsCard;
