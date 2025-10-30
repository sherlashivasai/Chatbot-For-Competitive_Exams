from langchain_google_genai import ChatGoogleGenerativeAI
from langgraph.graph import add_messages, StateGraph, END
from typing import TypedDict, Annotated, Optional
from dotenv import load_dotenv
from langgraph.checkpoint.memory import MemorySaver
from uuid import uuid4
import json
import os
from tools import search_tool
from langchain_google_genai import ChatGoogleGenerativeAI


load_dotenv()

tools = search_tool

llm = ChatGoogleGenerativeAI(
    api_key=os.getenv("GOOGLE_API_KEY"),
    model="gemini-1.5-pro",
    temperature=0,
    max_output_tokens=1024,
    tools=[tools],
)

graph = StateGraph()

