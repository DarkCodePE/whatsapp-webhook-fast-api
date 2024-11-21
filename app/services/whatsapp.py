from fastapi import FastAPI, HTTPException, Request
from langchain.chat_models import ChatOpenAI
from langchain.schema import SystemMessage, HumanMessage
from typing import Dict, Optional
from pydantic import BaseModel
import aioredis
import httpx
from enum import Enum

class WhatsAppService:
    def __init__(self, api_token: str, phone_id: str):
        self.api_token = api_token
        self.phone_id = phone_id
        self.base_url = "https://graph.facebook.com/v17.0"

    async def send_message(self, to: str, text: str):
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.base_url}/{self.phone_id}/messages",
                headers={"Authorization": f"Bearer {self.api_token}"},
                json={
                    "messaging_product": "whatsapp",
                    "to": to,
                    "text": {"body": text}
                }
            )
            return response.json()

    async def send_interactive(self, to: str, body: str, buttons: list):
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.base_url}/{self.phone_id}/messages",
                headers={"Authorization": f"Bearer {self.api_token}"},
                json={
                    "messaging_product": "whatsapp",
                    "to": to,
                    "type": "interactive",
                    "interactive": {
                        "type": "button",
                        "body": {"text": body},
                        "action": {"buttons": buttons}
                    }
                }
            )
            return response.json()