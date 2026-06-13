from asyncio import sleep
from pathlib import Path
from telethon import TelegramClient, events, Button
import os, shutil
import asyncio
import subprocess
import re
from collections import deque


# Ponemos los identificadores de Telegram
claves = {}
with open("claves.txt", "r") as f:
    for linea in f:
        linea = linea.strip()
        if linea and "=" in linea:
            key, value = linea.split("=", 1)
            claves[key.strip()] = value.strip()

# Asignar variables a partir del diccionario
api_id = int(claves.get("API_ID", 0))
api_hash = claves.get("API_HASH", "")
bot_token = claves.get("BOT_TOKEN", "")
chat_personal = int(claves.get("CHAT_PERSONAL", 0))

# Comenzamos la sesión de telegram
client = TelegramClient("bot_awakener_session", api_id, api_hash, request_retries=10, timeout=60).start(bot_token=bot_token)

async def enviarMensaje(msj):
    await client.send_message(chat_personal, msj)

def isMessageText(event, text):
    return event.text and event.text == text
# Comenzamos a escuchar desde el cliente recien creado todos los mensajes entrantes
@client.on(events.NewMessage)
async def handler(event):
    if isMessageText(event, "sesiones"):
            cmd = "ps aux | grep beta.py | grep -v 'grep' | grep -v '/bin/sh -c'"
            result = subprocess.run(
                cmd,
                shell=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )

            if (result.stdout):
                await enviarMensaje("Los procesos beta son: \n" + result.stdout)
            else:
                await enviarMensaje("No hay procesos beta")

    elif isMessageText(event, "Awake beta"):
        cmd = "nohup /mnt/Mirror/TelegramBot/TelegramMediaDownloader/venvTelegram/bin/python beta.py > /dev/null 2>&1 &"
        await asyncio.create_subprocess_shell(
            cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )

        await enviarMensaje("Un proceso de beta.py ha sido arrancado")

print("Bot escuchando mensajes nuevos...")
client.run_until_disconnected()
