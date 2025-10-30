from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from sse_starlette.sse import EventSourceResponse
import uvicorn
import asyncio
from langchain_core.messages import HumanMessage
import json
import logging

# Import your graph-building function
from chatbot.agent import build_graph

# --- 1. Setup Logging ---
logging.basicConfig(
    level=logging.INFO, 
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# --- 2. Initialize FastAPI App & CORS ---
app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"], # Your React app's origin
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- 3. Compile LangGraph Agent ---
try:
    langgraph_app = build_graph()
except Exception as e:
    logger.critical(f"Failed to build and compile LangGraph: {e}", exc_info=True)
    # Exit or raise if the app can't be built
    raise

# --- 4. Define API Models ---
class ChatRequest(BaseModel):
    query: str
    thread_id: str  # To keep track of conversation history

# --- 5. Define Streaming Endpoint ---
@app.post("/chat/stream")
async def chat_stream(request: ChatRequest):
    
    config = {"configurable": {"thread_id": request.thread_id}}
    input_message = {"messages": [HumanMessage(content=request.query)]}
    
    logger.info(f"Received new stream request for thread_id: {request.thread_id}")
    
    async def event_stream():
        """
        Async generator to stream LangGraph events to the frontend.
        """
        try:
            async for event in langgraph_app.astream_events(
                input_message, config, version="v1"
            ):
                event_type = event["event"]
                
                # Stream LLM tokens
                if event_type == "on_chat_model_stream":
                    chunk = event["data"]["chunk"]
                    if chunk.content:
                        yield json.dumps({"type": "token", "data": chunk.content})
                
                # Stream the final quiz JSON
                if event_type == "on_chain_end" and event["name"] == "quiz_specialist":
                    quiz_json = event["data"]["output"]["messages"][-1].content
                    logger.info("Sending special 'quiz_json' event")
                    yield json.dumps({"type": "quiz_json", "data": quiz_json})
                
                # Optional: Log tool usage
                if event_type == "on_tool_start":
                    logger.info(f"Tool started: {event['name']} with input {event['data']['input']}")
                if event_type == "on_tool_end":
                    logger.info(f"Tool ended: {event['name']}")

            # Signal the end of the stream
            logger.info(f"Stream ended for thread_id: {request.thread_id}")
            yield json.dumps({"type": "stream_end"})

        except Exception as e:
            logger.error(f"Error in stream for thread_id {request.thread_id}: {e}", exc_info=True)
            yield json.dumps({"type": "error", "data": str(e)})

    return EventSourceResponse(event_stream())

@app.get("/")
def root():
    return {"status": "Chatbot API is running"}

# --- 6. Run the Server ---
if __name__ == "__main__":
    logger.info("Starting Uvicorn server on http://0.0.0.0:8000")
    uvicorn.run(app, host="0.0.0.0", port=8000)