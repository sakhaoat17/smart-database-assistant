from flask import Flask, request, jsonify
from test_sql import create_sql_agent  # Use our new SQL agent module
from langchain_core.messages import HumanMessage
from flask_cors import CORS
import json
import traceback
import logging

app = Flask(__name__)
CORS(app)

# Enable logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

app.config["JSON_SORT_KEYS"] = False

# Initialize SQL agent
try:
    logger.info("Initializing SQL agent...")
    sql_agent = create_sql_agent()
    logger.info("SQL agent initialized successfully")
except Exception as e:
    logger.error(f"Failed to initialize SQL agent: {e}")
    logger.error(traceback.format_exc())
    sql_agent = None

@app.route("/query", methods=["POST"])
def run_query():
    data = request.get_json()
    query = data.get("query")
    
    if not query:
        return jsonify({"error": "Query not provided"}), 400
    
    if not sql_agent:
        return jsonify({"error": "SQL agent not initialized"}), 500
    
    logger.info(f"Processing query: {query}")
    
    try:
        # Invoke the SQL agent with the query
        messages = sql_agent.invoke(query)
        logger.info(f"Got {len(messages)} messages from agent")
        
        # Get the final message from the result
        if not messages:
            return jsonify({"error": "No response from agent"}), 500
            
        final_message = messages[-1]
        logger.info(f"Final message type: {type(final_message).__name__}")
        logger.info(f"Final message content: {final_message.content[:200] if hasattr(final_message, 'content') else 'N/A'}")
        
        response = {"final_answer": final_message.content if hasattr(final_message, "content") else str(final_message)}
        
        # Extract SQL query if available from tool calls
        if hasattr(final_message, "tool_calls") and final_message.tool_calls:
            for tc in final_message.tool_calls:
                if tc.get("name") == "sql_db_query":
                    response["sql_query"] = tc.get("args", {}).get("query", "")
                    break
        
        logger.info(f"Returning response: {response}")
        return jsonify(response)
    
    except Exception as e:
        logger.error(f"Error processing query: {e}")
        logger.error(traceback.format_exc())
        return jsonify({"error": str(e), "type": type(e).__name__}), 500

@app.route("/tables", methods=["GET"])
def get_tables():
    """Endpoint to get all tables in the database."""
    try:
        # Get tables directly from the database
        tables = sql_agent.db.get_usable_table_names()
        return jsonify({"tables": tables})
    except Exception as e:
        logger.error(f"Error getting tables: {e}")
        return jsonify({"error": str(e)}), 500

@app.route("/test", methods=["POST"])
def test_query():
    """Simple test endpoint that doesn't use the agent."""
    try:
        data = request.get_json()
        query = data.get("query", "SELECT COUNT(*) as count FROM actor")
        logger.info(f"Running test query: {query}")
        
        # Direct SQL query without agent
        result = sql_agent.db.run(query)
        logger.info(f"Query result: {result}")
        
        return jsonify({"final_answer": str(result), "sql_query": query})
    except Exception as e:
        logger.error(f"Error in test query: {e}")
        logger.error(traceback.format_exc())
        return jsonify({"error": str(e)}), 500

@app.route("/", methods=["GET"])
def index():
    return "SQL Data Agent API is running. POST to /query with {\"query\": \"...\"}"

if __name__ == "__main__":
    app.run(debug=True)