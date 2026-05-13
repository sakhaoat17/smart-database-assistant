// src/pages/SQLAgentPage.jsx
import React, { useState } from "react";
import DataChart from "../components/DataChart";
import DataTable from "../components/DataTable";
import "./sql_frontend.css";

const SQLAgentPage = () => {
  const [query, setQuery] = useState("");
  const [response, setResponse] = useState(null);
  const [loading, setLoading] = useState(false);
  const [viewMode, setViewMode] = useState("text"); // "text", "table", "chart"
  const [chartType, setChartType] = useState("bar");
  const [parsedData, setParsedData] = useState(null);

  const handleSubmit = async (e, useTest = false) => {
    e.preventDefault();
    setLoading(true);
    setResponse(null);
    setParsedData(null);

    try {
      const endpoint = useTest ? "/test" : "/query";
      console.log(`Sending query to ${endpoint}:`, query);
      
      const res = await fetch(`http://127.0.0.1:5000${endpoint}`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({ query }),
      });
      
      console.log(`Response status: ${res.status}`);
      
      if (!res.ok) {
        const errorData = await res.json().catch(() => ({}));
        throw new Error(`HTTP error! status: ${res.status}. Message: ${errorData.error || 'Unknown error'}`);
      }
      
      const data = await res.json();
      console.log("Response data:", data);
      
      const responseText = data.final_answer || data.error || "No answer found";
      setResponse(responseText);
      
      const parsed = data.table_data && Array.isArray(data.table_data) ? data.table_data : [];
      setParsedData(parsed);
      
      if (parsed && parsed.length > 0) {
        setViewMode("table");
      }
    } catch (error) {
      console.error("Error:", error);
      setResponse(`Error: ${error.message}. Make sure the backend is running on http://127.0.0.1:5000`);
    }
    setLoading(false);
  };

  return (
    <div className="container">
      <h1>SQL Agent Interface</h1>
      <form onSubmit={handleSubmit}>
        <input
          type="text"
          value={query}
          placeholder="Enter your query (e.g., 'How many actors are in the database?')"
          onChange={(e) => setQuery(e.target.value)}
          required
        />
        <button type="submit" disabled={loading}>
          {loading ? "Processing..." : "Submit Query"}
        </button>
        <button 
          type="button" 
          disabled={loading}
          onClick={(e) => {
            setQuery("SELECT COUNT(*) as count FROM actor");
            handleSubmit(e, true);
          }}
          style={{marginLeft: "10px"}}
        >
          {loading ? "Testing..." : "Test API"}
        </button>
      </form>
      {response && (
        <div className="response">
          <div className="view-controls">
            <button
              className={viewMode === "text" ? "active" : ""}
              onClick={() => setViewMode("text")}
            >
              Text
            </button>
            {parsedData && parsedData.length > 0 && (
              <>
                <button
                  className={viewMode === "table" ? "active" : ""}
                  onClick={() => setViewMode("table")}
                >
                  Table
                </button>
                <button
                  className={viewMode === "chart" ? "active" : ""}
                  onClick={() => setViewMode("chart")}
                >
                  Chart
                </button>
              </>
            )}
          </div>
          {viewMode === "chart" && parsedData && parsedData.length > 0 && (
            <div className="chart-controls">
              <label>Chart Type: </label>
              <select
                value={chartType}
                onChange={(e) => setChartType(e.target.value)}
              >
                <option value="bar">Bar Chart</option>
                <option value="line">Line Chart</option>
                <option value="pie">Pie Chart</option>
              </select>
            </div>
          )}
          <div className="response-content">
            {viewMode === "text" && (
              <>
                <h3>Response:</h3>
                <p>{response}</p>
              </>
            )}
            {viewMode === "table" && parsedData && parsedData.length > 0 && (
              <>
                <h3>Data Table:</h3>
                <DataTable data={parsedData} />
              </>
            )}
            {viewMode === "chart" && parsedData && parsedData.length > 0 && (
              <>
                <h3>Data Visualization:</h3>
                <DataChart data={parsedData} chartType={chartType} />
              </>
            )}
            {((viewMode === "table" || viewMode === "chart") && (!parsedData || parsedData.length === 0)) && (
              <p>No data available for visualization.</p>
            )}
          </div>
        </div>
      )}
    </div>
  );
};

export default SQLAgentPage;
