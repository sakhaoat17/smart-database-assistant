from typing import Literal, Dict, Any, List
from langchain_core.messages import AIMessage, HumanMessage, ToolMessage
from langchain_core.runnables import RunnableConfig
from langgraph.graph import END, START, MessagesState, StateGraph
from langgraph.prebuilt import ToolNode
from langchain_community.agent_toolkits import SQLDatabaseToolkit
import os
import json
from langchain_groq import ChatGroq
from langchain_community.utilities import SQLDatabase
from dotenv import load_dotenv
class SQLAgentBuilder:
    def __init__(self, model_name=None, db_path=None):
        """Initialize the SQL Agent Builder with model and database configuration.
        
        Args:
            model_name: The name of the LLM model to use (defaults to environment variable)
            db_path: The database connection string (defaults to environment variable)
        """
        load_dotenv()
        
        # Configuration - use parameters if provided, otherwise fall back to environment variables
        self.model_name = model_name or os.getenv("LLM_MODEL", "gemini-2.0-flash-lite")
        self.db_path = db_path or os.getenv("DB_PATH", "sqlite:///sakila.db")
        

        # Initialize components
        self._init_components()
        
        # Build the graph
        self.agent = self._build_graph()
    
    def _init_components(self):
        """Initialize LLM, database, and tools."""
        try:
            # Use Groq with Llama 3.3
            self.llm = ChatGroq(model="llama-3.3-70b-versatile", temperature=0)
            self.db = SQLDatabase.from_uri(self.db_path)
            print(f"Successfully connected to database. Tables: {self.db.get_usable_table_names()}")
        except Exception as e:
            print(f"Initialization error: {e}")
            raise
        
        # Create toolkit and get tools
        self.toolkit = SQLDatabaseToolkit(db=self.db, llm=self.llm)
        self.tools = self.toolkit.get_tools()
        
        # Get specific tools
        self.get_schema_tool = next(tool for tool in self.tools if tool.name == "sql_db_schema")
        self.get_schema_node = ToolNode([self.get_schema_tool], name="get_schema")
        
        self.run_query_tool = next(tool for tool in self.tools if tool.name == "sql_db_query")
        self.run_query_node = ToolNode([self.run_query_tool], name="run_query")
    
    def list_tables(self, state: MessagesState):
        """Create a tool call to list all tables in the database."""
        tool_call = {
            "name": "sql_db_list_tables",
            "args": {},
            "id": "abc123",
            "type": "tool_call",
        }
        tool_call_message = AIMessage(content="", tool_calls=[tool_call])
        
        list_tables_tool = next(tool for tool in self.tools if tool.name == "sql_db_list_tables")
        tool_message = list_tables_tool.invoke(tool_call)
        response = AIMessage(content=f"Available tables: {tool_message.content}")
        
        return {"messages": [tool_call_message, tool_message, response]}
    
    def call_get_schema(self, state: MessagesState):
        """Force the model to create a tool call to get the database schema."""
        llm_with_tools = self.llm.bind_tools([self.get_schema_tool], tool_choice="any")
        response = llm_with_tools.invoke(state["messages"])
        
        return {"messages": [response]}
    
    def generate_query(self, state: MessagesState):
        """Generate a SQL query based on the user question."""
        system_message = {
            "role": "system",
            "content": self._get_generate_query_prompt(),
        }
        
        llm_with_tools = self.llm.bind_tools([self.run_query_tool])
        response = llm_with_tools.invoke([system_message] + state["messages"])
        
        return {"messages": [response]}
    
    def check_query(self, state: MessagesState):
        """Check the generated SQL query for common mistakes."""
        system_message = {
            "role": "system",
            "content": self._get_check_query_prompt(),
        }
        
        # Generate an artificial user message to check
        tool_call = state["messages"][-1].tool_calls[0]
        user_message = {"role": "user", "content": tool_call["args"]["query"]}
        llm_with_tools = self.llm.bind_tools([self.run_query_tool], tool_choice="any")
        response = llm_with_tools.invoke([system_message, user_message])
        response.id = state["messages"][-1].id
        
        return {"messages": [response]}
    
    def should_continue(self, state: MessagesState) -> Literal[END, "check_query"]:
        """Determine if we should continue with checking the query or end."""
        messages = state["messages"]
        last_message = messages[-1]
        if not last_message.tool_calls:
            return END
        else:
            return "check_query"
    
    def _get_generate_query_prompt(self):
        """Get the system prompt for generating a SQL query."""
        return f"""
        You are an agent designed to interact with a SQL database.
        Given an input question, create a syntactically correct {self.db.dialect} query to run,
        then look at the results of the query and return the answer. Unless the user
        specifies a specific number of examples they wish to obtain, always limit your
        query to at most 5 results.
        
        You can order the results by a relevant column to return the most interesting
        examples in the database. Never query for all the columns from a specific table,
        only ask for the relevant columns given the question.
        
        DO NOT make any DML statements (INSERT, UPDATE, DELETE, DROP etc.) to the database.
        """
    
    def _get_check_query_prompt(self):
        """Get the system prompt for checking a SQL query."""
        return f"""
        You are a SQL expert with a strong attention to detail.
        Double check the {self.db.dialect} query for common mistakes, including:
        - Using NOT IN with NULL values
        - Using UNION when UNION ALL should have been used
        - Using BETWEEN for exclusive ranges
        - Data type mismatch in predicates
        - Properly quoting identifiers
        - Using the correct number of arguments for functions
        - Casting to the correct data type
        - Using the proper columns for joins
        
        If there are any of the above mistakes, rewrite the query. If there are no mistakes,
        just reproduce the original query.
        
        You will call the appropriate tool to execute the query after running this check.
        """
    
    def _build_graph(self):
        """Build the graph with all nodes and edges."""
        builder = StateGraph(MessagesState)
        
        # Add nodes
        builder.add_node(self.list_tables)
        builder.add_node(self.call_get_schema)
        builder.add_node(self.get_schema_node, "get_schema")
        builder.add_node(self.generate_query)
        builder.add_node(self.check_query)
        builder.add_node(self.run_query_node, "run_query")
        
        # Add edges
        builder.add_edge(START, "list_tables")
        builder.add_edge("list_tables", "call_get_schema")
        builder.add_edge("call_get_schema", "get_schema")
        builder.add_edge("get_schema", "generate_query")
        builder.add_conditional_edges(
            "generate_query",
            self.should_continue,
        )
        builder.add_edge("check_query", "run_query")
        builder.add_edge("run_query", "generate_query")
        
        # Compile and return agent
        return builder.compile()
    
    def invoke(self, question: str) -> List[Any]:
        """Run the agent with a user question.
        
        Args:
            question: The user's natural language question about the database
            
        Returns:
            A list of messages representing the conversation history
        """
        # Initialize with the user's question
        messages = [HumanMessage(content=question)]
        
        # Run the agent
        result = self.agent.invoke({"messages": messages})
        
        # Return the final messages
        return result["messages"]
    
    def astream_events(self, question: str):
        """Stream events from the agent as they occur.
        
        Args:
            question: The user's natural language question about the database
            
        Returns:
            A generator that yields events as they occur
        """
        # Initialize with the user's question
        messages = [HumanMessage(content=question)]
        
        # Stream events from the agent
        return self.agent.stream({"messages": messages})


# Create a convenience function to build and run the agent
def create_sql_agent(model_name=None, db_path=None):
    """Create a SQL agent that can be used to answer questions about a database.
    
    Args:
        model_name: The name of the LLM model to use
        db_path: The database connection string
        
    Returns:
        A SQLAgentBuilder instance
    """
    return SQLAgentBuilder(model_name=model_name, db_path=db_path)