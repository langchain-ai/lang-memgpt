"""Discord bot that integrates with LangGraph for AI-assisted conversations.

This module sets up a Discord bot that can interact with users in Discord channels
and threads. It uses LangGraph to process messages and generate responses.
"""

import asyncio
import logging
import os
import uuid

import discord
from aiohttp import web
from discord.ext import commands
from discord.message import Message
from dotenv import load_dotenv
from langchain_core.messages import HumanMessage
from langgraph_sdk import get_client
from langgraph_sdk.schema import Thread

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("discord")

# Load environment variables
load_dotenv()


TOKEN = os.getenv("DISCORD_TOKEN")
if not TOKEN:
    raise ValueError(
        "No Discord token found. Make sure DISCORD_TOKEN is set in your environment."
    )

INTENTS = discord.Intents.default()
INTENTS.message_content = True
BOT = commands.Bot(command_prefix="!", intents=INTENTS)
_LANGGRAPH_CLIENT = get_client(url=os.environ["ASSISTANT_URL"])
_ASSISTANT_ID = os.environ.get("ASSISTANT_ID")
_GRAPH_ID = os.environ.get("GRAPH_ID", "memory")
_LOCK = asyncio.Lock()


@BOT.event
async def on_ready():
    """Log a message when the bot has successfully connected to Discord."""
    logger.info(f"{BOT.user} has connected to Discord!")


async def _get_assistant_id() -> str:
    """Retrieve or set the assistant ID for the bot.

    This function checks if an assistant ID is already set. If not, it fetches
    the first available assistant from the LangGraph client and sets it as the
    current assistant ID.

    Returns:
        str: The assistant ID to be used for processing messages.

    Raises:
        ValueError: If no assistant is found in the graph.
    """
    global _ASSISTANT_ID
    if _ASSISTANT_ID is None:
        async with _LOCK:
            if _ASSISTANT_ID is None:
                assistants = await _LANGGRAPH_CLIENT.assistants.search(
                    graph_id=_GRAPH_ID
                )
                if not assistants:
                    raise ValueError("No assistant found in the graph.")
                _ASSISTANT_ID = assistants[0]["assistant_id"]
                logger.warning(f"Using assistant ID: {_ASSISTANT_ID}")
    return _ASSISTANT_ID


async def _get_thread(message: Message) -> discord.Thread:
    """Get or create a Discord thread for the given message.

    If the message is already in a thread, return that thread.
    Otherwise, create a new thread in the channel where the message was sent.

    Args:
        message (Message): The Discord message to get or create a thread for.

    Returns:
        discord.Thread: The thread associated with the message.
    """
    channel = message.channel
    if isinstance(channel, discord.Thread):
        return channel
    else:
        return await channel.create_thread(name="Response", message=message)


async def _create_or_fetch_lg_thread(thread_id: uuid.UUID) -> Thread:
    """Create or fetch a LangGraph thread for the given thread ID.

    This function attempts to fetch an existing LangGraph thread. If it doesn't
    exist, a new thread is created.

    Args:
        thread_id (uuid.UUID): The unique identifier for the thread.

    Returns:
        Thread: The LangGraph thread object.
    """
    try:
        return await _LANGGRAPH_CLIENT.threads.get(thread_id)
    except Exception:
        pass
    return await _LANGGRAPH_CLIENT.threads.create(thread_id=thread_id)


def _format_inbound_message(message: Message) -> HumanMessage:
    """Format a Discord message into a HumanMessage for LangGraph processing.

    This function takes a Discord message and formats it into a structured
    HumanMessage object that includes context about the message's origin.

    Args:
        message (Message): The Discord message to format.

    Returns:
        HumanMessage: A formatted message ready for LangGraph processing.
    """
    guild_str = "" if message.guild is None else f"guild={message.guild}"
    content = f"""<discord {guild_str} channel={message.channel} author={repr(message.author)}>
    {message.content}
    </discord>"""
    return HumanMessage(
        content=content, name=str(message.author.global_name), id=str(message.id)
    )


@BOT.event
async def on_message(message: Message):
    """Event handler for incoming Discord messages.

    This function processes incoming messages, ignoring those sent by the bot itself.
    When the bot is mentioned, it creates or fetches the appropriate threads,
    processes the message through LangGraph, and sends the response.

    Args:
        message (Message): The incoming Discord message.
    """
    if message.author == BOT.user:
        return
    if BOT.user.mentioned_in(message):
        aid = await _get_assistant_id()
        thread = await _get_thread(message)
        lg_thread = await _create_or_fetch_lg_thread(
            uuid.uuid5(uuid.NAMESPACE_DNS, f"DISCORD:{thread.id}")
        )
        thread_id = lg_thread["thread_id"]
        user_id = message.author.id  # TODO: is this unique?
        run_result = await _LANGGRAPH_CLIENT.runs.wait(
            thread_id,
            assistant_id=aid,
            input={"messages": [_format_inbound_message(message)]},
            config={
                "configurable": {
                    "user_id": user_id,
                    # "model": "accounts/fireworks/models/firefunction-v2"
                }
            },
        )
        bot_message = run_result["messages"][-1]
        response = bot_message["content"]
        if isinstance(response, list):
            response = "".join([r["text"] for r in response])
        await thread.send(response)


async def health_check(request):
    """Health check endpoint for the web server.

    This function responds to GET requests on the /health endpoint with an "OK" message.

    Args:
        request: The incoming web request.

    Returns:
        web.Response: A response indicating the service is healthy.
    """
    return web.Response(text="OK")


async def run_bot():
    """Run the Discord bot.

    This function starts the Discord bot and handles any exceptions that occur during its operation.
    """
    try:
        await BOT.start(TOKEN)
    except Exception as e:
        print(f"Error starting BOT: {e}")


async def run_web_server():
    """Run the web server for health checks.

    This function sets up and starts a simple web server that includes a health check endpoint.
    """
    app = web.Application()
    app.router.add_get("/health", health_check)
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, "0.0.0.0", 8080)
    await site.start()


async def main():
    """Main function to run both the Discord bot and the web server concurrently.

    This function uses asyncio.gather to run both the bot and the web server in parallel.
    """
    await asyncio.gather(run_bot(), run_web_server())


if __name__ == "__main__":
    asyncio.run(main())
