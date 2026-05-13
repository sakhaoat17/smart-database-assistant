// src/App.js
import React from "react";
import { BrowserRouter as Router, Routes, Route } from "react-router-dom";
import SQLAgentPage from  "./pages/sql_frontend";

function App() {
  return (
    <Router>
      <Routes>
        <Route path="/" element={<SQLAgentPage />} />
      </Routes>
    </Router>
  );
}

export default App;
