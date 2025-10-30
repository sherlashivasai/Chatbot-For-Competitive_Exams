import os
import logging
from dotenv import load_dotenv
from typing import TypedDict, Annotated, Literal
import operator

from langchain_core.messages import BaseMessage, HumanMessage
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_community.tools.tavily_search import TavilySearchResults
from langgraph.prebuilt import ToolNode
from langgraph.graph import StateGraph, END
from langgraph.checkpoint.memory import MemorySaver # For production, use RedisSaver

# --- 1. Setup Logging ---
# Configures logging to output to console with a clear format.
# In production, you might want to log to a file.
logging.basicConfig(
    level=logging.INFO, 
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# --- 2. Load Environment & Define Model ---
load_dotenv()
google_key = os.getenv("GOOGLE_API_KEY")
tavily_key = os.getenv("TAVILY_API_KEY")

class Model:
    """
    Encapsulates the LLM configuration, now defined directly in agent.py.
    """
    def __init__(self):
        self.key = google_key
        self.model = "gemini-1.5-pro"
        
        # Production-ready check: Ensure API key is present
        if not self.key:
            logger.error("GOOGLE_API_KEY not found in environment variables.")
            raise ValueError("GOOGLE_API_KEY not set. Please add it to your .env file.")
            
        logger.info(f"Initializing ChatGoogleGenerativeAI with model: {self.model}")
        self.llm = ChatGoogleGenerativeAI(
            api_key=self.key, 
            model=self.model, 
            temperature=0, 
            max_output_tokens=1024
        )

    def get_llm(self):
        return self.llm

# --- 3. Initialize Model & Tools ---
model_provider = Model()
llm = model_provider.get_llm()

# Production-ready check for the search tool
if not tavily_key:
    logger.warning("TAVILY_API_KEY not found. The 'current_affairs_search' tool will fail.")
    # We can create a dummy tool or raise an error.
    # For this example, we'll let it fail if called.
    tavily_tool = None
else:
    tavily_tool = TavilySearchResults(max_results=4, name="current_affairs_search")
    tavily_tool.description = "Searches the web for recent news, events, and current affairs. Use this for any questions about recent topics."

# We only include tools that are properly configured
tools = [t for t in [tavily_tool] if t]
llm_with_tools = llm.bind_tools(tools)

# --- 4. Define Agent State ---
class AgentState(TypedDict):
    messages: Annotated[list, operator.add]
    intent: Literal["notes", "quiz", "current_affairs", "general"]

# --- 5. Define Graph Nodes ---

def call_model_node(state):
    """The primary node that calls the LLM with tools."""
    logger.info("--- Calling Model ---")
    messages = state["messages"]
    response = llm_with_tools.invoke(messages)
    return {"messages": [response]}

def classify_intent_node(state):
    """Classifies the user's intent to route to the correct specialist."""
    logger.info("--- Classifying Intent ---")
    last_message = state["messages"][-1]
    
    if last_message.tool_calls:
        # If the LLM already decided to use a tool, route to it
        logger.info("Intent classified as 'current_affairs' (tool call detected)")
        return {"intent": "current_affairs"}

    query = last_message.content.lower()
    if "quiz" in query:
        logger.info("Intent classified as 'quiz'")
        return {"intent": "quiz"}
    if "notes" in query or "explain" in query or "summarize" in query:
        logger.info("Intent classified as 'notes'")
        return {"intent": "notes"}
    if "current affairs" in query or "latest news" in query:
        logger.info("Intent classified as 'current_affairs' (keywords)")
        return {"intent": "current_affairs"}
        
    logger.info("Intent classified as 'general'")
    return {"intent": "general"}

def notes_node(state):
    logger.info("--- Generating Notes ---")
    original_query = state["messages"][0].content
    prompt = f"""
    You are a specialist in generating study notes for UPSC and SSC exams.
    A student has asked for notes on: "{original_query}"
    Provide detailed, well-structured notes. Use headings and bullet points.
    """
    response = llm.invoke(prompt)
    return {"messages": [response]}

def quiz_node(state):
    logger.info("--- Generating Quiz ---")
    original_query = state["messages"][0].content
    prompt = f"""
    You are a Quiz Generator for competitive exams.
    A student has requested a quiz on: "{original_query}"
    Generate a 5-question multiple-choice quiz.
    Respond ONLY with a valid JSON object in the format:
    {{
      "topic": "Topic of the quiz",
      "questions": [
        {{"question": "...", "options": ["A", "B", "C", "D"], "correct_answer": "..."}}
      ]
    }}
    """
    response = llm.invoke(prompt)
    return {"messages": [response]}

tool_node = ToolNode(tools)

def synthesize_search_results_node(state):
    logger.info("--- Synthesizing Search Results ---")
    original_query = state["messages"][0].content
    tool_results = state["messages"][-1].content
    
    prompt = f"""
    You are a current affairs analyst for competitive exams.
    A student asked: "{original_query}"
    The latest web search results are:
    {tool_results}
    Synthesize these results into a concise summary.
    """
    response = llm.invoke(prompt)
    return {"messages": [response]}
    
# --- 6. Build the Graph ---
def build_graph():
    workflow = StateGraph(AgentState)
    
    workflow.set_entry_point("classify_intent")
    
    workflow.add_node("classify_intent", classify_intent_node)
    workflow.add_node("call_agent_model", call_model_node)
    workflow.add_node("notes_specialist", notes_node)
    workflow.add_node("quiz_specialist", quiz_node)
    workflow.add_node("synthesize_results", synthesize_search_results_node)

    # Only add the tool node if tools are available
    if tools:
        workflow.add_node("call_tool", tool_node)
    
    # Conditional router
    workflow.add_conditional_edges(
        "classify_intent",
        lambda x: x["intent"],
        {
            "current_affairs": "call_agent_model",
            "quiz": "quiz_specialist",
            "notes": "notes_specialist",
            "general": END 
        }
    )
    
    workflow.add_edge("quiz_specialist", END)
    workflow.add_edge("notes_specialist", END)
    
    # Conditional logic for the tool-using branch
    def check_for_tools(state):
        last_message = state["messages"][-1]
        if last_message.tool_calls:
            return "call_tool"
        return END

    # Only add tool-related edges if tools are available
    if tools:
        workflow.add_conditional_edges(
            "call_agent_model",
            check_for_tools,
            {
                "call_tool": "call_tool",
                END: END
            }
        )
        workflow.add_edge("call_tool", "synthesize_results")
        workflow.add_edge("synthesize_results", END)
    else:
        # If no tools, just end after the model call
        workflow.add_edge("call_agent_model", END)

    # --- 7. Compile the Graph ---
    checkpointer = MemorySaver()
    app = workflow.compile(checkpointer=checkpointer)
    logger.info("LangGraph agent compiled successfully.")
    return app

if __name__ == "__main__":
    # Test execution
    logger.info("Running agent.py directly for testing...")
    app = build_graph()
    config = {"configurable": {"thread_id": "test-thread-cli"}}
    
    # query = "Give me a quiz on the Indian National Congress"
    query = "What is the latest news on the new education policy?"
    
    for event in app.stream({"messages": [HumanMessage(content=query)]}, config):
        logger.info(event)