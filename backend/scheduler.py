import os
import json
import time
import datetime
import threading
import urllib.request
from typing import Optional

# Persistent JSON database for scheduled tasks
TASKS_FILE = os.path.join("db", "scheduled_tasks.json")
_tasks_lock = threading.Lock()
_last_update_id = 0

def load_tasks():
    """Loads all scheduled tasks from the local JSON file."""
    with _tasks_lock:
        if not os.path.exists(TASKS_FILE):
            return []
        try:
            with open(TASKS_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception as e:
            print(f"[Scheduler] Error cargando tareas: {e}")
            return []
            
def save_tasks(tasks):
    """Saves all scheduled tasks to the local JSON file."""
    with _tasks_lock:
        os.makedirs(os.path.dirname(TASKS_FILE), exist_ok=True)
        try:
            with open(TASKS_FILE, "w", encoding="utf-8") as f:
                json.dump(tasks, f, ensure_ascii=False, indent=4)
        except Exception as e:
            print(f"[Scheduler] Error guardando tareas: {e}")

def schedule_task(message: str, scheduled_time: str, platform: str, target_number: str = None):
    """
    Schedules a new reminder task.
    scheduled_time format: 'YYYY-MM-DD HH:MM:SS'
    """
    tasks = load_tasks()
    task_id = str(int(time.time() * 1000))
    new_task = {
        "id": task_id,
        "message": message,
        "scheduled_time": scheduled_time,
        "platform": platform.lower(),
        "target_number": target_number,
        "status": "pending",
        "created_at": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    }
    tasks.append(new_task)
    save_tasks(tasks)
    print(f"[Scheduler] Tarea programada con éxito: {new_task}")
    return new_task

def send_telegram_message(text: str) -> bool:
    """Sends a text message using the Telegram Bot API."""
    token = os.environ.get("TELEGRAM_BOT_TOKEN")
    chat_id = os.environ.get("TELEGRAM_CHAT_ID")
    if not token or not chat_id:
        print("[Scheduler] TELEGRAM_BOT_TOKEN o TELEGRAM_CHAT_ID no configurados en .env. Saltando envío real.")
        return False
        
    url = f"https://api.telegram.org/bot{token}/sendMessage"
    payload = {
        "chat_id": chat_id,
        "text": text
    }
    data = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(
        url,
        data=data,
        headers={"Content-Type": "application/json"},
        method="POST"
    )
    try:
        with urllib.request.urlopen(req, timeout=10) as response:
            return response.status == 200
    except Exception as e:
        print(f"[Scheduler] Error enviando mensaje a Telegram: {e}")
        return False

def send_whatsapp_message(text: str, target_number: str = None) -> bool:
    """Sends WhatsApp message via local Node.js microservice."""
    if not target_number:
        target_number = os.environ.get("WHATSAPP_TARGET_NUMBER")
    if not target_number:
        print("[Scheduler] No hay número de destino configurado para WhatsApp.")
        return False
        
    url = "http://localhost:3001/send"
    payload = {
        "to": target_number,
        "message": text
    }
    data = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(
        url,
        data=data,
        headers={"Content-Type": "application/json"},
        method="POST"
    )
    try:
        with urllib.request.urlopen(req, timeout=15) as response:
            return response.status == 200
    except Exception as e:
        print(f"[Scheduler] Error comunicándose con el puente local de WhatsApp: {e}")
        return False

def scheduler_loop():
    """Background worker daemon loop checking pending tasks every 10 seconds."""
    print("[Scheduler] Hilo del planificador de tareas iniciado.")
    while True:
        try:
            # Dynamically reload environment variables on every check tick
            from dotenv import load_dotenv
            load_dotenv(override=True)
            
            tasks = load_tasks()
            changed = False
            now = datetime.datetime.now()
            
            for task in tasks:
                if task["status"] == "pending":
                    try:
                        task_time = datetime.datetime.strptime(task["scheduled_time"], "%Y-%m-%d %H:%M:%S")
                    except ValueError:
                        print(f"[Scheduler] Formato de fecha inválido para tarea {task['id']}: {task['scheduled_time']}")
                        task["status"] = "failed"
                        changed = True
                        continue
                        
                    if now >= task_time:
                        print(f"[Scheduler] Ejecutando tarea programada {task['id']}...")
                        success = False
                        if task["platform"] == "telegram":
                            success = send_telegram_message(task["message"])
                        elif task["platform"] == "whatsapp":
                            success = send_whatsapp_message(task["message"], task.get("target_number"))
                        else:
                            print(f"[Scheduler] Plataforma desconocida: {task['platform']}")
                            
                        task["status"] = "sent" if success else "failed"
                        changed = True
                        
            if changed:
                save_tasks(tasks)
        except Exception as e:
            print(f"[Scheduler] Error en bucle del planificador: {e}")
            
        time.sleep(10)

WELCOME_MESSAGE = "Hola soy tu asistente que te ayuda a controlar la imaginacion"

# Persistent registry of Telegram users who have started the bot
USERS_FILE = os.path.join("db", "telegram_users.json")
_users_lock = threading.Lock()

def load_telegram_users() -> dict:
    with _users_lock:
        if not os.path.exists(USERS_FILE):
            return {}
        try:
            with open(USERS_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except:
            return {}

def save_telegram_user(chat_id: int, first_name: str, username: str):
    users = load_telegram_users()
    key = str(chat_id)
    users[key] = {
        "chat_id": chat_id,
        "first_name": first_name or "",
        "username": username or "",
    }
    with _users_lock:
        os.makedirs(os.path.dirname(USERS_FILE), exist_ok=True)
        with open(USERS_FILE, "w", encoding="utf-8") as f:
            json.dump(users, f, ensure_ascii=False, indent=4)
    print(f"[TelegramBot] Usuario registrado: {first_name} (@{username}) chat_id={chat_id}")

def find_telegram_user(name_or_username: str) -> Optional[dict]:
    """Find a registered user by first name or @username (case-insensitive)."""
    users = load_telegram_users()
    needle = name_or_username.lstrip("@").lower()
    for u in users.values():
        if u.get("username", "").lower() == needle:
            return u
        if u.get("first_name", "").lower() == needle:
            return u
    return None

def send_telegram_to_user(name_or_username: str, text: str) -> bool:
    """Send a message to a registered user by name or @username."""
    user = find_telegram_user(name_or_username)
    if not user:
        print(f"[TelegramBot] Usuario '{name_or_username}' no registrado.")
        return False
    return send_telegram_to_chat(user["chat_id"], text)

def send_telegram_to_chat(chat_id, text: str) -> bool:
    """Send a message to a specific chat_id."""
    token = os.environ.get("TELEGRAM_BOT_TOKEN")
    if not token:
        return False
    result = _tg_api("sendMessage", {"chat_id": chat_id, "text": text})
    return result.get("ok", False)


def _tg_api(method: str, payload: dict) -> dict:
    """Helper: call any Telegram Bot API method."""
    token = os.environ.get("TELEGRAM_BOT_TOKEN")
    if not token:
        return {}
    url = f"https://api.telegram.org/bot{token}/{method}"
    data = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(
        url, data=data,
        headers={"Content-Type": "application/json"},
        method="POST"
    )
    try:
        with urllib.request.urlopen(req, timeout=10) as r:
            return json.loads(r.read())
    except Exception as e:
        print(f"[TelegramBot] Error llamando {method}: {e}")
        return {}

def _tg_get(method: str, params: dict = {}) -> dict:
    """Helper: GET request to Telegram API."""
    token = os.environ.get("TELEGRAM_BOT_TOKEN")
    if not token:
        return {}
    query = "&".join(f"{k}={v}" for k, v in params.items())
    url = f"https://api.telegram.org/bot{token}/{method}?{query}"
    req = urllib.request.Request(url, method="GET")
    try:
        with urllib.request.urlopen(req, timeout=10) as r:
            return json.loads(r.read())
    except Exception as e:
        print(f"[TelegramBot] Error en GET {method}: {e}")
        return {}

def telegram_polling_loop():
    """Polls Telegram for incoming messages, registers users, and sends welcome to new chats."""
    global _last_update_id
    _welcomed_chats = set()
    print("[TelegramBot] Hilo de escucha de Telegram iniciado.")
    while True:
        try:
            from dotenv import load_dotenv
            load_dotenv(override=True)

            params = {"timeout": 20, "offset": _last_update_id + 1}
            result = _tg_get("getUpdates", params)

            if result.get("ok") and result.get("result"):
                for update in result["result"]:
                    _last_update_id = update["update_id"]
                    msg = update.get("message") or update.get("edited_message")
                    if not msg:
                        continue

                    chat = msg["chat"]
                    chat_id = chat["id"]
                    first_name = chat.get("first_name", "")
                    username = chat.get("username", "")
                    text = msg.get("text", "").strip()

                    # Always register/update this user in our database
                    save_telegram_user(chat_id, first_name, username)

                    # Send welcome on first contact or on /start
                    if chat_id not in _welcomed_chats:
                        _welcomed_chats.add(chat_id)
                        _tg_api("sendMessage", {
                            "chat_id": chat_id,
                            "text": WELCOME_MESSAGE,
                        })
                        print(f"[TelegramBot] Bienvenida enviada a {first_name} (chat_id={chat_id})")
                    elif text.lower() in ["/start", "start", "hola", "hi", "hello"]:
                        _tg_api("sendMessage", {
                            "chat_id": chat_id,
                            "text": WELCOME_MESSAGE,
                        })

        except Exception as e:
            print(f"[TelegramBot] Error en bucle de polling: {e}")

        time.sleep(3)

def start_scheduler():
    """Starts the background task scheduler and Telegram bot listener."""
    # Task scheduler
    thread = threading.Thread(target=scheduler_loop, name="BackgroundScheduler")
    thread.daemon = True
    thread.start()

    # Telegram incoming message listener
    tg_thread = threading.Thread(target=telegram_polling_loop, name="TelegramPoller")
    tg_thread.daemon = True
    tg_thread.start()

