import React, { useState, useEffect } from "react";
import { api, ChatResponse } from "../services/api";

// Generate unique session ID
const generateSessionId = () => {
  return `session_${Date.now()}_${Math.random().toString(36).substring(2, 9)}`;
};

const ComparisonTable = ({ tableData }: { tableData: any }) => {
  if (!tableData || !tableData.rows || tableData.rows.length === 0) {
    return null;
  }

  return (
    <div className="overflow-x-auto mt-4">
      <table className="min-w-full divide-y divide-gray-200 border">
        <thead className="bg-gray-50">
          <tr>
            {tableData.headers.map((header: string, index: number) => (
              <th
                key={index}
                className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider"
              >
                {header}
              </th>
            ))}
          </tr>
        </thead>
        <tbody className="bg-white divide-y divide-gray-200">
          {tableData.rows.map((row: any, rowIndex: number) => (
            <tr
              key={rowIndex}
              className={rowIndex % 2 === 0 ? "bg-white" : "bg-gray-50"}
            >
              <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900">
                {row.metric}
              </td>
              <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                {row.value1}
              </td>
              <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                {row.value2}
              </td>
              <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                {row.difference}
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
};

const Chat: React.FC = () => {
  const [query, setQuery] = useState("");
  const [sessionId, setSessionId] = useState("");
  const [response, setResponse] = useState<ChatResponse | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [conversations, setConversations] = useState<
    Array<{ query: string; response: ChatResponse | null }>
  >([]);

  // Initialize session ID on component mount
  useEffect(() => {
    setSessionId(generateSessionId());
  }, []);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!query.trim()) return;

    setLoading(true);
    setError(null);

    try {
      // Add query to conversation history
      setConversations((prev) => [...prev, { query, response: null }]);

      // Make API request with session ID for conversation state
      const result = await api.chat.query(query, sessionId);

      setResponse(result);

      // Update conversation history with response
      setConversations((prev) => {
        const updated = [...prev];
        updated[updated.length - 1].response = result;
        return updated;
      });

      // Clear input field
      setQuery("");
    } catch (err) {
      setError(err instanceof Error ? err.message : "An error occurred");
    } finally {
      setLoading(false);
    }
  };

  // Handle quick responses for prompts
  const handleQuickResponse = (responseText: string) => {
    setQuery(responseText);
    // Submit automatically
    setTimeout(() => {
      const formEvent = { preventDefault: () => {} } as React.FormEvent;
      handleSubmit(formEvent);
    }, 100);
  };

  return (
    <div className="max-w-4xl mx-auto p-4">
      {/* Conversation history */}
      {conversations.length > 0 && (
        <div className="mb-6 space-y-6">
          {conversations.map((conv, index) => (
            <div key={index}>
              {/* User query */}
              <div className="bg-blue-50 p-4 rounded-lg mb-2">
                <p className="text-blue-800 font-medium">You:</p>
                <p>{conv.query}</p>
              </div>

              {/* Assistant response */}
              {conv.response && (
                <div className="bg-white p-4 rounded-lg shadow">
                  <p className="text-gray-800 whitespace-pre-wrap">
                    {conv.response.answer}
                  </p>

                  {/* Quick response buttons for prompts */}
                  {conv.response.is_prompt && (
                    <div className="mt-4 space-x-2">
                      <button
                        onClick={() => handleQuickResponse("stock")}
                        className="px-3 py-1 bg-blue-100 text-blue-800 rounded-full hover:bg-blue-200"
                      >
                        Stock
                      </button>
                      <button
                        onClick={() => handleQuickResponse("mutual fund")}
                        className="px-3 py-1 bg-blue-100 text-blue-800 rounded-full hover:bg-blue-200"
                      >
                        Mutual Fund
                      </button>
                      <button
                        onClick={() => handleQuickResponse("ETF")}
                        className="px-3 py-1 bg-blue-100 text-blue-800 rounded-full hover:bg-blue-200"
                      >
                        ETF
                      </button>
                    </div>
                  )}

                  {/* Comparison table */}
                  {conv.response.table_data && (
                    <ComparisonTable tableData={conv.response.table_data} />
                  )}

                  {/* Related news */}
                  {conv.response.related_news &&
                    conv.response.related_news.length > 0 && (
                      <div className="mt-4">
                        <h4 className="text-sm font-medium text-gray-700 mb-2">
                          Related News:
                        </h4>
                        <ul className="space-y-1 text-sm">
                          {conv.response.related_news
                            .slice(0, 3)
                            .map((news, newsIndex) => (
                              <li key={newsIndex} className="text-gray-600">
                                •{" "}
                                {news.url ? (
                                  <a
                                    href={news.url}
                                    target="_blank"
                                    rel="noopener noreferrer"
                                    className="text-blue-600 hover:underline"
                                  >
                                    {news.title}
                                  </a>
                                ) : (
                                  <span>{news.title}</span>
                                )}
                                <span className="text-gray-500 text-xs ml-1">
                                  ({news.source},{" "}
                                  {new Date(news.date).toLocaleDateString()})
                                </span>
                              </li>
                            ))}
                        </ul>
                        {conv.response.related_news.length > 3 && (
                          <p className="text-xs text-gray-500 mt-1">
                            {conv.response.related_news.length - 3} more news
                            items available.
                          </p>
                        )}
                      </div>
                    )}

                  {/* Financial data */}
                  {conv.response.financial_data &&
                    Object.keys(conv.response.financial_data).length > 0 && (
                      <div className="mt-4">
                        <h4 className="text-sm font-medium text-gray-700">
                          Financial Data:
                        </h4>
                        {conv.response.financial_data.stock && (
                          <div className="mt-1 text-sm text-gray-600">
                            <p>
                              <span className="font-medium">
                                {conv.response.financial_data.stock.name ||
                                  conv.response.financial_data.stock.symbol}
                              </span>{" "}
                              ₹{conv.response.financial_data.stock.price}
                              {conv.response.financial_data.stock
                                .changePercent && (
                                <span
                                  className={`ml-2 ${
                                    Number(
                                      conv.response.financial_data.stock
                                        .changePercent
                                    ) >= 0
                                      ? "text-green-600"
                                      : "text-red-600"
                                  }`}
                                >
                                  {Number(
                                    conv.response.financial_data.stock
                                      .changePercent
                                  ) >= 0
                                    ? "+"
                                    : ""}
                                  {
                                    conv.response.financial_data.stock
                                      .changePercent
                                  }
                                  %
                                </span>
                              )}
                            </p>
                          </div>
                        )}

                        {conv.response.financial_data.fund && (
                          <div className="mt-1 text-sm text-gray-600">
                            <p>
                              <span className="font-medium">
                                {conv.response.financial_data.fund.scheme_name}
                              </span>{" "}
                              NAV: ₹{conv.response.financial_data.fund.nav}
                            </p>
                            {conv.response.financial_data.fund.category && (
                              <p className="text-xs text-gray-500">
                                {conv.response.financial_data.fund.category}
                              </p>
                            )}
                          </div>
                        )}

                        {conv.response.financial_data.etf && (
                          <div className="mt-1 text-sm text-gray-600">
                            <p>
                              <span className="font-medium">
                                {conv.response.financial_data.etf.name}
                              </span>{" "}
                              ₹{conv.response.financial_data.etf.price}
                            </p>
                          </div>
                        )}
                      </div>
                    )}
                </div>
              )}
            </div>
          ))}
        </div>
      )}

      {/* Query input form */}
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

      {/* Error display */}
      {error && (
        <div className="p-4 mb-4 text-red-700 bg-red-100 rounded-lg">
          {error}
        </div>
      )}
    </div>
  );
};

export default Chat;
