# Chatbot for Competitive Exams

This chatbot is designed for aspirants preparing for competitive exams like UPSC, SSC, and other state service exams. It features a persistent memory using Redis and a multi-conversation user interface.

## Features

-   **Specialized Agents**: Can generate study notes, create quizzes, and search for current affairs.
-   **Persistent Memory**: Uses Redis to save conversation history, allowing users to continue past conversations.
-   **Multi-Conversation UI**: A sidebar lists all past conversations for a user.
-   **Streaming Responses**: The user interface feels fast and responsive thanks to Server-Sent Events.

## Project Structure

```
.
├── chatbot/          # Contains the core LangGraph agent logic
├── frontend/         # The React frontend application
├── .env.example      # Example environment variables
├── main.py           # The FastAPI backend server
└── pyproject.toml    # Python dependencies
```

## Setup and Installation

### 1. Prerequisites

-   Python 3.10+
-   Node.js 18+
-   Docker (for running Redis)

### 2. Backend Setup

**a. Create a Virtual Environment and Install Dependencies:**

```bash
python -m venv venv
source venv/bin/activate  # On Windows, use `venv\Scripts\activate`
pip install -e .
```

**b. Set Up Environment Variables:**

Copy the `.env.example` file to a new file named `.env`:

```bash
cp .env.example .env
```

Now, open the `.env` file and add your API keys:

```
GOOGLE_API_KEY="YOUR_GOOGLE_API_KEY"
TAVILY_API_KEY="YOUR_TAVILY_API_KEY"
REDIS_URL="redis://localhost:6379"
```

**c. Start Redis with Docker:**

The easiest way to run Redis locally is with Docker. Run the following command in your terminal:

```bash
docker run -d -p 6379:6379 redis
```

This will start a Redis container and map the port to your local machine.

### 3. Frontend Setup

**a. Navigate to the Frontend Directory and Install Dependencies:**

```bash
cd frontend
npm install
```

### 4. Running the Application

You will need to run the backend and frontend servers in two separate terminals.

**a. Start the Backend Server:**

In the root directory of the project, run:

```bash
uvicorn main:app --reload
```

The backend server will be running at `http://localhost:8000`.

**b. Start the Frontend Development Server:**

In the `frontend` directory, run:

```bash
npm start
```

The frontend application will open automatically in your browser at `http://localhost:3000`.

You can now log in with a username and start chatting!
