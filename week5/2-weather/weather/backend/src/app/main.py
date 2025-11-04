from fastapi import FastAPI, Request, Response
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from strands import Agent
from strands.session.s3_session_manager import S3SessionManager
import boto3
import json
import logging
import os
import uuid
import uvicorn

from strands import tool
import requests

model_id = os.environ.get("MODEL_ID", "global.anthropic.claude-haiku-4-5-20251001-v1:0")
state_bucket = os.environ.get("STATE_BUCKET", "")
state_prefix = os.environ.get("STATE_PREFIX", "sessions/")
logging.getLogger("strands").setLevel(logging.WARNING)
logging.basicConfig(
    format="%(levelname)s | %(name)s | %(message)s", handlers=[logging.StreamHandler()]
)
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
logger.info("Logger initialized")

if not state_bucket:
    raise RuntimeError("STATE_BUCKET environment variable must be set")

if state_prefix and not state_prefix.endswith("/"):
    state_prefix = f"{state_prefix}/"

boto_session = boto3.Session()


class ChatRequest(BaseModel):
    prompt: str


@tool(name="get_weather", description="Fetch the current weather for a city")
def get_weather(city: str = "Chicago") -> str:
    """Fetch current weather/temperature info using wttr.in for the given city.

    Args:
        city: The name of the city to check the weather for.
    """
    url = f"https://wttr.in/{city}?format=3&u"

    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        return response.text.strip()
    except requests.RequestException as e:
        return f"Error fetching weather {e}"


def create_agent(session_id: str) -> Agent:
    session_manager_kwargs = {
        "session_id": session_id,
        "bucket": state_bucket,
        "boto_session": boto_session,
    }
    if state_prefix:
        session_manager_kwargs["prefix"] = state_prefix

    session_manager = S3SessionManager(**session_manager_kwargs)
    # 🧩 Include the weather tool here
    agent = Agent(
        model=model_id, session_manager=session_manager, tools=[get_weather]
    )  # 👈 Register the tool
    logger.info("Agent initialized for session %s", session_id)
    return agent


app = FastAPI()


# Called by the Lambda Adapter to check liveness
@app.get("/")
async def root():
    return {"message": "OK"}


@app.get("/chat")
def chat_history(request: Request):
    session_id = request.cookies.get("session_id", str(uuid.uuid4()))
    agent = create_agent(session_id)

    # Filter messages to only include first text content
    filtered_messages = []
    for message in agent.messages:
        if (
            message.get("content")
            and len(message["content"]) > 0
            and "text" in message["content"][0]
        ):
            filtered_messages.append(
                {
                    "role": message["role"],
                    "content": [{"text": message["content"][0]["text"]}],
                }
            )

    response = Response(
        content=json.dumps(
            {
                "messages": filtered_messages,
            }
        ),
        media_type="application/json",
    )
    response.set_cookie(key="session_id", value=session_id)
    return response


@app.post("/chat")
async def chat(chat_request: ChatRequest, request: Request):
    session_id = request.cookies.get("session_id", str(uuid.uuid4()))
    agent = create_agent(session_id)
    response = StreamingResponse(
        generate(agent, session_id, chat_request.prompt, request),
        media_type="text/event-stream",
    )
    response.set_cookie(key="session_id", value=session_id)
    return response


async def generate(agent: Agent, session_id: str, prompt: str, request: Request):
    try:
        async for event in agent.stream_async(prompt):
            if await request.is_disconnected():
                logger.info(
                    "Client disconnected before completion for session %s", session_id
                )
                break
            if "complete" in event:
                logger.info("Response generation complete")
            if "data" in event:
                yield f"data: {json.dumps(event['data'])}\n\n"

    except Exception as e:
        error_message = json.dumps({"error": str(e)})
        yield f"event: error\ndata: {error_message}\n\n"


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=int(os.environ.get("PORT", "8080")))
