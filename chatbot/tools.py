from langchain_community.tools.tavily_search.tool import TavilySearchResults
from dotenv import load_dotenv
import os

load_dotenv()
tavily_api_key = os.getenv("TAVILY_API_KEY")
search_tool = TavilySearchResults(api_key=tavily_api_key, num_results=3)
 

