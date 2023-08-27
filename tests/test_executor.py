import logging
import os
import unittest
from typing import Optional

from fastapi.testclient import TestClient
from starlette.websockets import WebSocket

# os.environ['LOGGING_CONFIG_FILE'] = "../logging.conf"
from main import app

logger = logging.getLogger()


class ExecutorTests(unittest.IsolatedAsyncioTestCase):
    async def test_complete_program(self):
        client = TestClient(app)
        program: str
        with open("./programs/simple_2.xml") as f:
            program = f.read()
        with client.websocket_connect("/executor") as websocket:
            websocket.send_json({
                "type": "program",
                "value": program
            })
            websocket.send_json({
                "type": "start"
            })
            websocket.send_json({
                "type": "complete"
            })
            websocket.send_json({
                "type": "exit"
            })
            return True

    async def test_step_simple_2_program(self):
        client = TestClient(app)
        program: str
        with open("./programs/simple_2.xml") as f:
            program = f.read()
        with client.websocket_connect("/executor") as websocket:
            websocket.send_json({
                "type": "program",
                "value": program
            })
            websocket.send_json({
                "type": "start"
            })
            response: Optional[dict] = None
            while response is None or response["isRunning"] == True:
                websocket.send_json({
                    "type": "step"
                })
                response = None
                while response is None or response["type"] != "status":
                    response = websocket.receive_json()
                logger.debug("Variables: %s", response)
            websocket.send_json({
                "type": "exit"
            })
