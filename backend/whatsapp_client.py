"""
Cliente Python para el servicio WhatsApp (whatsapp-web.js en Node).
Llama a http://localhost:3001 para enviar mensajes.
"""

import httpx
import logging

logger = logging.getLogger(__name__)

WA_SERVICE_URL = "http://localhost:3001"


def get_whatsapp_status() -> dict:
    """Devuelve el estado de la conexión WhatsApp y el QR si no está conectado."""
    try:
        r = httpx.get(f"{WA_SERVICE_URL}/status", timeout=5)
        return r.json()
    except Exception as e:
        logger.warning(f"[WhatsApp] Servicio no disponible: {e}")
        return {"ready": False, "has_qr": False, "qr": None, "error": str(e)}


def send_whatsapp_message(to: str, message: str) -> dict:
    """
    Envía un mensaje de WhatsApp.
    :param to: Número con código de país sin +, ej: "5491112345678"
    :param message: Texto a enviar
    """
    try:
        status = get_whatsapp_status()
        if not status.get("ready"):
            return {
                "ok": False,
                "error": "WhatsApp no está conectado. Iniciá el servicio y escaneá el QR."
            }

        r = httpx.post(
            f"{WA_SERVICE_URL}/send",
            json={"to": to, "message": message},
            timeout=15
        )
        return r.json()
    except httpx.ConnectError:
        return {
            "ok": False,
            "error": "El servicio de WhatsApp no está corriendo. Ejecutá: cd whatsapp && npm start"
        }
    except Exception as e:
        logger.error(f"[WhatsApp] Error al enviar: {e}")
        return {"ok": False, "error": str(e)}


def send_whatsapp_bulk(contacts: list[dict]) -> dict:
    """
    Envía mensajes a múltiples contactos.
    :param contacts: Lista de {"to": "549...", "message": "..."}
    """
    try:
        r = httpx.post(
            f"{WA_SERVICE_URL}/send-bulk",
            json={"contacts": contacts},
            timeout=60
        )
        return r.json()
    except Exception as e:
        logger.error(f"[WhatsApp] Error bulk: {e}")
        return {"ok": False, "error": str(e)}
