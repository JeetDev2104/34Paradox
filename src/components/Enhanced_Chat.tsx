import React, { useState } from "react";
import { api, ChatResponse } from "../services/api";

const Chat: React.FC = () => {
  const [query, setQuery] = useState("");
  const [response, setResponse] = useState<ChatResponse | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!query.trim()) return;

    setLoading(true);
    setError(null);

    try {
      const result = await api.chat.query(query);
      setResponse(result);
    } catch (err) {
      setError(err instanceof Error ? err.message : "An error occurred");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="max-w-4xl mx-auto p-4">
      <form onSubmit={handleSubmit} className="mb-6">
        <div className="flex gap-2">
          <input
            type="text"
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            placeholder="Ask about stocks, funds, or market news..."
            className="flex-1 p-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
            disabled={loading}
          />
          <button
            type="submit"
            disabled={loading}
            className="px-4 py-2 bg-blue-500 text-white rounded-lg hover:bg-blue-600 disabled:opacity-50"
          >
            {loading ? "Thinking..." : "Ask"}
          </button>
        </div>
      </form>

      {error && (
        <div className="p-4 mb-4 text-red-700 bg-red-100 rounded-lg">
          {error}
        </div>
      )}

      {response && (
        <div className="space-y-6">
          <div className="p-4 bg-white rounded-lg shadow">
            <h3 className="font-semibold mb-2">Answer</h3>
            <p className="whitespace-pre-wrap">{response.answer}</p>
            <div className="mt-2 text-sm text-gray-500">
              Confidence: {(response.confidence * 100).toFixed(1)}%
            </div>
          </div>

          {response.related_news.length > 0 && (
            <div className="p-4 bg-white rounded-lg shadow">
              <h3 className="font-semibold mb-4">Related News</h3>
              <div className="space-y-4">
                {response.related_news.map((news, index) => (
                  <div key={index} className="border-b last:border-b-0 pb-4">
                    <h4 className="font-medium">{news.title}</h4>
                    <p className="text-sm text-gray-600 mt-1">{news.summary}</p>
                    <div className="mt-2 flex gap-4 text-sm text-gray-500">
                      <span>Source: {news.source}</span>
                      <span>Sentiment: {news.sentiment}</span>
                      <span>
                        Date: {new Date(news.date).toLocaleDateString()}
                      </span>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}

          {(response.financial_data.stock || response.financial_data.fund) && (
            <div className="p-4 bg-white rounded-lg shadow">
              <h3 className="font-semibold mb-4">Financial Data</h3>
              {response.financial_data.stock && (
                <div className="mb-4">
                  <h4 className="font-medium">Stock Information</h4>
                  <p>Symbol: {response.financial_data.stock.symbol}</p>
                  <p>Price: ${response.financial_data.stock.price}</p>
                </div>
              )}
              {response.financial_data.fund && (
                <div>
                  <h4 className="font-medium">Fund Information</h4>
                  <p>Scheme: {response.financial_data.fund.scheme_name}</p>
                  <p>NAV: ₹{response.financial_data.fund.nav}</p>
                </div>
              )}
            </div>
          )}
        </div>
      )}
    </div>
  );
};

export default Chat;
