import json
import logging.config
import os
import sys
from typing import Callable, ContextManager

import uvicorn
from fastapi import FastAPI, WebSocket
from starlette.middleware.cors import CORSMiddleware
from starlette.responses import HTMLResponse
from starlette.staticfiles import StaticFiles

from engine.blocks.block import get_block_definition
from engine.blocks.core_plugin import CorePluginContext
from engine.blocks.default import default_blocks
from engine.executor.executor import Executor
from engine.plugins.gui import gui_blocks, GuiPluginContext
from engine.plugins.io import io_blocks
from engine.plugins.keyboard import keyboard_blocks, KeyboardPluginContext
from engine.plugins.numbers import numbers_blocks
from engine.plugins.strings import strings_blocks

logging_config_file = os.environ['LOGGING_CONFIG_FILE'] if 'LOGGING_CONFIG_FILE' in os.environ else 'logging.conf'
print(os.path.abspath(logging_config_file or "logging.conf"))
logging.config.fileConfig(fname=logging_config_file, disable_existing_loggers=False)
logger = logging.getLogger()

sys.setrecursionlimit(2**16)

loaded_blocks = [
    *default_blocks,
    *keyboard_blocks,
    # *gui_blocks,
    *strings_blocks,
    *numbers_blocks,
    *io_blocks
]

loaded_plugin_contexts: list[Callable[['Executor'], ContextManager]] = [
    # GuiPluginContext,
    CorePluginContext,
    KeyboardPluginContext
]

app = FastAPI()
origins = [
    "http://localhost",
    "http://localhost:3000",
]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
if os.path.exists("static/editor"):
    app.mount("/static/editor", StaticFiles(directory="static/editor"), name="editor")
    app.mount("/static/media", StaticFiles(directory="static/editor/media"), name="editor-media")


@app.get('/')
def get_app():
    if not os.path.exists("static/editor/index.html"):
        return HTMLResponse("Editor has not been compiled. Please see the Readme for more information.", 200)
    with open('static/editor/index.html', 'r') as file_index:
        html_content = file_index.read()
    return HTMLResponse(html_content, status_code=200)


@app.get("/config")
async def config():
    return {"message": f"Hello"}


@app.get("/blocks")
async def blocks():
    converted = {block["type"]: get_block_definition(block) for block in loaded_blocks}
    return {key: value for key, value in converted.items() if value is not None}


@app.websocket("/executor")
async def ws(websocket: WebSocket):
    await websocket.accept()
    executor = Executor()
    executor.load_blocks(loaded_blocks)
    for plugin_context in loaded_plugin_contexts:
        executor.add_plugin_context(plugin_context)

    broadcast_list = []

    def broadcast_listener(topic, message):
        broadcast_list.append([topic, message])

    executor.add_global_broadcast_listener(broadcast_listener)

    def get_status():
        nonlocal broadcast_list
        obj = {
            "type": "status",
            "variables": executor.get_variables(),
            "isRunning": not executor.is_complete(),
            "taskCount": executor.get_task_count(),
            "highlights": list(executor.get_highlights()),
            "broadcasts": broadcast_list
        }
        broadcast_list = []
        return obj

    try:
        async for data_json in websocket.iter_json():
            message_type = data_json["type"]
            try:
                if message_type == "program":
                    executor.load_program(data_json["value"])
                if message_type == "start":
                    if "isEager" in data_json:
                        executor.start(data_json["isEager"])
                    else:
                        executor.start()
                    await websocket.send_json(get_status())
                if message_type == "complete":
                    executor.complete()
                    await websocket.send_json(get_status())
                if message_type == "stop":
                    executor.stop()
                    await websocket.send_json(get_status())
                if message_type == "step":
                    executor.step()
                    await websocket.send_json(get_status())
                if message_type == "status":
                    await websocket.send_json(get_status())
                if message_type == "exit":
                    logger.debug("Closing executor socket...")
                    executor.stop()
                    break
                await websocket.send_text(json.dumps({
                    "type": "log",
                    "value": f"Message text was: {data_json}"
                }))
            except Exception as e:
                logger.error("Executor encountered an error", exc_info=e)
                await websocket.send_text(json.dumps({
                    "type": "error",
                    "value": f"{type(e).__name__}: {str(e)}"
                }))
        await websocket.close()
    except Exception as e:
        logger.error("Websocket closed unexpectedly", exc_info=e)
    finally:
        executor.stop()


if __name__ == "__main__":
    uvicorn.run("main:app", port=3001)
