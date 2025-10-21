from telethon import TelegramClient, events
import os

# Ponemos los identificadores de Telegram
api_id = placeholder
api_hash = "placeholder"
bot_token = "placeholder"
chat_personal = placeholder

# Llamamos a la carpeta de descarga
folder = "descargas"

# Comprobamos que nuestra carpeta exista. Si no es el caso, la crea
os.makedirs(folder, exist_ok=True)

# Comenzamos la sesión de telegram
client = TelegramClient("bot_session", api_id, api_hash).start(bot_token=bot_token)

# Comenzamos a escuchar desde el cliente recien creado todos los mensajes entrantes
@client.on(events.NewMessage)
async def handler(event):
# Solo en el caso de que el mensaje nuevo sea media, se intenta descargar
    if event.message.media:
        file_name = event.message.file.name

        if (file_name == None):
            file_name = event.message.message

        try:
            await client.send_message(chat_personal, f"{file_name} ha sido iniciado como descarga")
            path = os.path.join(folder, file_name)
            await event.message.download_media(file=path)
            await client.send_message(chat_personal, f"{file_name} se ha descargado con exito")
            print(f"{file_name} descargado")

        except Exception as e:
          print(f"No se pudo descargar {file_name}")
          await client.send_message(chat_personal, f"No se pudo descargar {file_name}")

# Si no estamos seguros de si el bot está ahora mismo activo, le podemos preguntar mandando "alive?"
    if event.message.text and event.text=="alive?":
        await client.send_message(chat_personal, "Aqui estoy bb")

# TODO: Mostrar por mensaje una barra de progreso con todos los archivos en proceso de descargar
#    if event.message.text and event.text=="progreso":
#       await client.send_message(chat_personal, "placeholder de progreso")

# Si lo estamos ejecutando desde terminal, nos muestra que todo va bien y que está esperando los mensajes
print("Bot escuchando mensajes nuevos...")
client.run_until_disconnected()
