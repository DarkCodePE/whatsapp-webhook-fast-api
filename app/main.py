from fastapi import FastAPI, HTTPException, Request, Query
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import Response, PlainTextResponse
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
import httpx
from enum import Enum
import os
from dotenv import load_dotenv
import json
# Load environment variables
load_dotenv()

app = FastAPI(title="WhatsApp API Service")

app.add_middleware(
    TrustedHostMiddleware,
    allowed_hosts=["*"]  # Ajusta esto según tus necesidades de seguridad
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Configuración desde variables de entorno
class Config:
    WEBHOOK_VERIFY_TOKEN = os.getenv("WEBHOOK_VERIFY_TOKEN")
    API_TOKEN = os.getenv("API_TOKEN")
    BUSINESS_PHONE = os.getenv("BUSINESS_PHONE")
    API_VERSION = os.getenv("API_VERSION", "v21.0")
    BASE_URL = f"https://graph.facebook.com/{API_VERSION}"


async def send_whatsapp_request(data: dict) -> dict:
    """
    Función auxiliar para enviar solicitudes a la API de WhatsApp
    """
    url = f"{Config.BASE_URL}/{Config.BUSINESS_PHONE}/messages"
    headers = {
        "Authorization": f"Bearer {Config.API_TOKEN}",
        "Content-Type": "application/json"
    }

    async with httpx.AsyncClient() as client:
        try:
            response = await client.post(url, json=data, headers=headers)
            response.raise_for_status()
            return response.json()
        except httpx.HTTPError as e:
            print(f"Error en la solicitud a WhatsApp: {e}")
            raise HTTPException(status_code=500, detail=str(e))


@app.get("/")
async def root():
    """
    Ruta raíz para verificar que el servicio está funcionando
    """
    return {"message": "WhatsApp Webhook Service. Consulta la documentación para comenzar."}



@app.get("/webhook")
async def verify_webhook(request: Request):
    """
    Endpoint GET para la verificación inicial del webhook con inspección detallada.
    """
    # Imprimir toda la información de la solicitud
    print("Encabezados de la solicitud:", request.headers)
    print("Query Params:", request.query_params)
    print("URL completa:", request.url)

    # Captura de parámetros
    hub_mode = request.query_params.get("hub.mode")
    hub_verify_token = request.query_params.get("hub.verify_token")
    hub_challenge = request.query_params.get("hub.challenge")

    # Depuración de los valores capturados
    print(f"Recibido: hub_mode={hub_mode}, hub_verify_token={hub_verify_token}, hub_challenge={hub_challenge}")

    # Lógica de verificación
    if hub_mode == "subscribe" and hub_verify_token == Config.WEBHOOK_VERIFY_TOKEN:
        print("¡Webhook verificado exitosamente!")
        return PlainTextResponse(content=hub_challenge)
    else:
        print("Verificación fallida.")
        raise HTTPException(status_code=403, detail="Verificación fallida")


@app.post("/webhook")
async def webhook_handler(request: Request):
    """
    Endpoint POST para manejar mensajes entrantes de WhatsApp
    Documentación: https://developers.facebook.com/docs/whatsapp/cloud-api/webhooks/payload-examples#text-messages
    """
    try:
        body = await request.json()
        # Registrar mensaje entrante para debugging
        print("Mensaje webhook entrante:", json.dumps(body, indent=2))

        # Extraer el mensaje usando la misma estructura que en el ejemplo
        message = (
            body.get("entry", [{}])[0]
            .get("changes", [{}])[0]
            .get("value", {})
            .get("messages", [{}])[0]
        )

        # Verificar si es un mensaje de texto
        if message and message.get("type") == "text":
            # Enviar mensaje de respuesta
            await send_whatsapp_request({
                "messaging_product": "whatsapp",
                "to": message["from"],
                "text": {"body": "Echo: " + message["text"]["body"]},
                "context": {
                    "message_id": message["id"]  # Mostrar como respuesta al mensaje original
                }
            })

            # Marcar el mensaje como leído
            await send_whatsapp_request({
                "messaging_product": "whatsapp",
                "status": "read",
                "message_id": message["id"]
            })

        return {"status": "success"}

    except Exception as e:
        print(f"Error procesando webhook: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/status")
async def check_status():
    """
    Endpoint para verificar el estado del servicio
    """
    return {
        "status": "active",
        "config": {
            "webhook_token_configured": bool(Config.WEBHOOK_VERIFY_TOKEN),
            "api_token_configured": bool(Config.API_TOKEN),
            "business_phone_configured": bool(Config.BUSINESS_PHONE),
            "api_version": Config.API_VERSION
        }
    }


if __name__ == "__main__":
    import uvicorn

    port = int(os.getenv("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
