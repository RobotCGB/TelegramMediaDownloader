from asyncio import sleep
from pathlib import Path
from telethon import TelegramClient, events
import os, shutil
import asyncio
import subprocess
from telethon import Button
 


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
# Llamamos a la carpeta de descarga
incomplete_folder = "descargas/incomplete"
complete_folder = "descargas/complete"

# Comprobamos que nuestra carpeta exista. Si no es el caso, la crea
os.makedirs(incomplete_folder, exist_ok=True)
os.makedirs(complete_folder, exist_ok=True)

# Comenzamos la sesión de telegram
client = TelegramClient("bot_session", api_id, api_hash, request_retries=10, timeout=60).start(bot_token=bot_token)

# Coso copiado de https://stackoverflow.com/questions/1094841/get-a-human-readable-version-of-a-file-size
# Obtener el tamaño de archivo en versión humana
def sizeof_fmt(num, suffix="B"):
    for unit in ("", "Ki", "Mi", "Gi", "Ti", "Pi", "Ei", "Zi"):
        if abs(num) < 1024.0:
            return f"{num:3.1f}{unit}{suffix}"
        num /= 1024.0
    return f"{num:.1f}Yi{suffix}"

downloaded = []
downloads = {}
errored = []

tamanoMAXTelegram = 1900 * 1024 * 1024 # 1900MB

sem = asyncio.Semaphore(13)

async def descargarArchivos(client, event, file_name):
# TODO: añadir opción de mover descargas a carpeta concreta

    async with sem:

        try:
            # Mandamos un mensaje una vez ha entrado en el try antes de comenzar a descargar
            await enviarMensaje(f"{file_name} ha sido iniciado como descarga")

            # Creamos una variable path que va a contener la ruta a la carpeta destino + el nombre del archivo
            path_incomplete = os.path.join(incomplete_folder, file_name)

            # Hacemos la descarga per se
            path_real = await event.message.download_media(file=path_incomplete, progress_callback=progreso(event.message.id, file_name))

            # Una vez termina, enviamos lo descargado a la carpeta de completados
            file_real_name = os.path.basename(path_real)

            path_complete = os.path.join(complete_folder, file_real_name)

            shutil.move(path_real, path_complete)

            # Mandamos un mensaje una vez ha terminado la descarga y la quitamos de la cola de progreso
            await enviarMensaje(f"{file_name} se ha descargado con exito")
            completed = downloads.pop(event.message.id, None)
            if completed:
                downloaded.append(completed)
        
        # En el caso de que haya ocurrido un error, nos manda un mensaje indicandolo
        except Exception as e:
            await client.send_message(chat_personal, f"No se pudo descargar {file_name} por culpa de {e}")
            errored.append((event, file_name))

# Para que telegram permita la previsualización de los videos subidos, voy a cambiar la extensión de todos los archivos en formatos de video a mp4
# Parece que está obsoleto por el momento. Se consigue lo mismo añadiendo el parámetro supports_streaming=True en client.send_file para conseguir lo mismo
# sin tocar el tipo de archivo
"""
async def preProcesadoVideos(real_path):

    base, ext = os.path.splitext(real_path)
    extension = ext.lstrip('.').lower()

    actual_path = real_path

    if extension == "mkv":
        nuevo_path = base + ".mp4"
        if os.path.exists(nuevo_path):
            os.remove(nuevo_path)
        shutil.move(real_path, nuevo_path)
        actual_path = nuevo_path
        await enviarMensaje("El archivo original era mkv, se renombrará la extensión a mp4")

    elif extension == "avi":
        nuevo_path = base + ".mp4"
        # si ya existe el destino, lo eliminamos para evitar errores de ffmpeg
        if os.path.exists(nuevo_path):
            os.remove(nuevo_path)
        
        await enviarMensaje("El archivo original era avi, se convertirá a mp4")

        cmd = [
            "ffmpeg", "-y",
            "-i", real_path,
            "-c:v", "copy",
            "-c:a", "copy",
            nuevo_path
        ]

        # Llamamos a ffmpeg 
        completed = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=True)    
        actual_path = nuevo_path

    return actual_path
"""

# subirCarpeta itera sobre la carpeta "uploads", que se puede cambiar si cambiamos la variable folder_path.
# Por cada entrada de directorio que contega se comprueba si esta es un archivo o un directorio. En el caso de
# ser un directorio, repite lo mismo con el folder_path como la carpeta contenedora, subiendo todo lo que haya dentro de las carpetas.
# Si la entrada es un archivo, lo sube, no sin antes comprobar que el tamaño del archivo está dentro de los límites
# de telegram. Si no lo está lo divide en tantas partes de 2GB (o el limite que tenga telegram en el momento) como
# sean necesarias para subir el contenido. Lo hace, y luego si ha dividido, borra las partes para dejar espacio en el disco.

async def subirCarpeta(folder_path):
        
        await enviarMensaje("CARPETA " + folder_path)

        for file_name in os.listdir(folder_path):

            file_path = os.path.join(folder_path, file_name)
            real_path = os.path.realpath(file_path)

            if os.path.isfile(real_path):
                base, ext = os.path.splitext(real_path)
                if ext != ".nfo":
                    size = os.path.getsize(real_path)
                    if size == 0:
                        continue

                    if size > tamanoMAXTelegram:
                        size = os.path.getsize(real_path)
                        await enviarMensaje(real_path + " : " + sizeof_fmt(size))
                        partes = partirArchivoGrande(real_path)
                        await enviarMensaje(f"Partes creadas: {len(partes)}")
                        for parte in partes:
                            parte_name = os.path.basename(parte)
                            size = os.path.getsize(parte)
                            await enviarMensaje(parte_name + " : " + sizeof_fmt(size))
                            await client.send_file(chat_personal, parte, caption=parte_name)
                            os.remove(parte)
                    else:
                        size = os.path.getsize(real_path)
                        await enviarMensaje(real_path + " : " + sizeof_fmt(size))
                        await client.send_file(chat_personal, real_path, caption=file_name, supports_streaming=True) #supports_streming=True te deja previsualizar videos en la app. Creo que no se puede de otra manera desde cliente ;)
            elif os.path.isdir(real_path):
                    await subirCarpeta(real_path)
                

        await enviarMensaje("SALIENDO DE CARPETA " + folder_path)

def partirArchivoGrande(path, tamano_parte_mb=1900):
    tamano_parte = f"-v{tamano_parte_mb}m"
    base_name = os.path.basename(path)
    dir_name = os.path.dirname(path)
    out_7z = os.path.join(dir_name, base_name + ".7z")

    cmd = [ "7z", "a", tamano_parte, out_7z, path ]

    result = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)

    if result.returncode != 0:
        raise RuntimeError(f"Error ejecutando 7z:\n{result.stderr}")
    
    partes = []
    i = 1
    while True:
        parte_path = f"{out_7z}.{i:03d}"
        if os.path.exists(parte_path):
            partes.append(parte_path)
            i+=1
        else:
            break

    return partes

def progreso(message_id, file_name):
    
    def callback(current, total):
        downloads[message_id] = (current, total, file_name)
    return callback

async def enviarMensaje(msj):
    await client.send_message(chat_personal, msj)

def isMessageText(event, text):
    return event.text and event.text == text


# Gestion del menu


MENU_PRINCIPAL = [
    [Button.text("Menu descargas")],
    [Button.text("Menu uploads")],
    [Button.text("Limpieza")],
    [Button.text("Tools")],
    [Button.text("Salir")]
]

MENU_DESCARGAS = [
    [Button.text("progreso")],
    [Button.text("completados")],
    [Button.text("errores")],
    [Button.text("reintentarErrores")],
    [Button.text("Ordenar")],
    [Button.text("Volver al menu principal")]
]

MENU_ORDENAR = [
    [Button.text("ordenarDescargas")],
    [Button.text("ordenarCompletados")],
    [Button.text("Volver al menu descargas")]
]

MENU_TOOLS = [
    [Button.text("alive?")],
    [Button.text("help")],
    [Button.text("kill")],
    [Button.text("Volver al menu principal")]
]

@client.on(events.NewMessage(pattern='/start'))
async def start(event):
    await event.respond(
        "Menu Principal:",
        buttons=[
            [Button.text("Menu descargas")],
            [Button.text("Menu uploads")],
            [Button.text("Limpieza")],
            [Button.text("Tools")],
            [Button.text("Salir")]
        ]
    )
    

@client.on(events.NewMessage)
async def menu_handler(event):


    if isMessageText(event, "Menu descargas"):
        await event.respond(
            "Elige opción de descargas:",
            buttons=MENU_DESCARGAS
        )

    if isMessageText(event, "Ordenar"):
        await event.respond(
            "Elige opción de ordenacion:",
            buttons=MENU_ORDENAR
        )

    if isMessageText(event, "Menu uploads"):
        await event.respond(
            "Elige opción de uploads:",
            buttons=[
                [Button.text("uploadFolder")],
                [Button.text("Volver al menu principal")]
            ]
        )

    if isMessageText(event, "Limpieza"):
        await event.respond(
            "Elige opción de limpieza:",
            buttons=[
                [Button.text("limpiezaCompletados")],
                [Button.text("limpiezaErrores")],
                [Button.text("Volver al menu principal")]
            ]
        )

    if isMessageText(event, "Tools"):
        await event.respond(
            "Elige la herramineta:",
            buttons=MENU_TOOLS
        )

    if isMessageText(event, "Volver al menu principal"):
        await event.respond(
            "Elige una opción", 
            buttons=MENU_PRINCIPAL
        )

    if isMessageText(event, "Volver al menu descargas"):
        await event.respond(
            "Elige opción de descargas:",
            buttons=MENU_DESCARGAS
        )

    if isMessageText(event, "Salir"):

        await event.respond(
            "¿Seguro/a?",
            buttons=[
                [Button.text("Si")],
                [Button.text("Volver al menu principal")]
            ]
        )

    if isMessageText(event, "Si"):
        exit()


@client.on(events.NewMessage(pattern='/limpiar'))
async def limpiar_chat(event):
    chat = await event.get_chat()
    # Borrar últimos 100 mensajes (puede variar)
    msgs = await client.get_messages(chat, limit=100)
    ids = [msg.id for msg in msgs]
    
    await client.delete_messages(chat, ids)
    await event.respond("Chat limpiado!")

# Comenzamos a escuchar desde el cliente recien creado todos los mensajes entrantes
@client.on(events.NewMessage)
async def handler(event):

    global downloads



    # Solo en el caso de que el mensaje nuevo sea media, se intenta descargar
    if event.message.media:

        file_name = event.message.file.name

        if (file_name == None):
            file_name = event.message.message

        await descargarArchivos(client, event, file_name)

    elif isMessageText(event, "progreso"):
        if downloads:
            msg = "Descargas en proceso:\n\n"
            # Como errored son {"event", file_name}, vamos a extraer los nombres de los errados
            errored_files = {f for _, f in errored}

            for msg_id, (current, total, name) in downloads.items():
                # Metemos en msg los nombres de únicamente las descargas que no estén en errored
                if name not in errored:
                    porcentaje = (current / total) * 100 if total else 0
                    msg += f"* {name}: {porcentaje:.2f}%\n"
                    msg += f"{sizeof_fmt(current)} / {sizeof_fmt(total)}\n\n"
            await enviarMensaje(msg)
        else:
            await enviarMensaje("No hay descargas en curso.")
    
    elif isMessageText(event, "completados"):
        if downloaded:
            msj = "Han sido completadas:\n\n"
            for _, _, name in downloaded:
                msj += f"{name}\n\n"
            await enviarMensaje(msj)
        else:
            await enviarMensaje("No hay descargas recientemente completadas")
    
    elif event.text and event.text == "limpiezaCompletados":
        await enviarMensaje("Se ha limpiado los completados con exito")
        downloaded.clear()
    
    elif isMessageText(event, "ordenarCompletados"):
        if downloaded:
            downloaded.sort(key=lambda x: x[1])
            await enviarMensaje("Completados ha sido ordenado")
        else:
            await enviarMensaje("No hay nada en completados")

    elif isMessageText(event, "ordenarDescargas"):
        if downloads:
            downloads = dict(sorted(downloads.items(), key=lambda item: item[1]["file_name"].lower()))
            await enviarMensaje("Descargas ha sido ordenado")
        else:
            await enviarMensaje("No hay nada en descargas")

    elif isMessageText(event, "ordenarErrores"):
        if errored:
            errored.sort(key=lambda x: x[1])
            await enviarMensaje("Errores ha sido ordenado")
        else:
            await enviarMensaje("No hay nada en errores")

    elif isMessageText(event, "errores"):
        if errored:
            msj = "Han fallado:\n\n"
            for _, name in errored:
                msj += f"{name}\n\n"
            await enviarMensaje(msj)
        else:
            await enviarMensaje("No hay descargas recientemente falladas")
    
    elif event.text and event.text == "limpiezaErrores":
        if errored:
            await enviarMensaje("Limpiando todas las descargas erradas")
            errored.clear()
        else:
            await enviarMensaje("No hay descargas recientemente falladas")
            
    elif isMessageText(event, "reintentarErrores"):
        if errored:
            await enviarMensaje("Se van a reintentar todos los errores")
            copy_errored = errored.copy()
            msj = "Se ha añadido a descargas de la lista de errores:\n\n"
            errored.clear()
            for event, file_name in copy_errored:
                msj += file_name
                msj += "\n\n"
            await enviarMensaje(msj)
            for event, file_name in copy_errored:
                await descargarArchivos(client, event, file_name)
        else:
            await enviarMensaje("No hay descargas recientemente falladas")

    elif isMessageText(event, "uploadFolder"):

        upload_folder = "./uploads"

        await subirCarpeta(upload_folder)
            
            
        
    
    elif isMessageText(event, "help"):
        msj = "Puedes escribirme los siguientes mensajes para que haga cosas:\n\n"
        msj += "* progreso : Muestra el progreso de las descargas actualmente en proceso\n\n"
        msj += "* completados : Muestra una lista con todas las descargas que han alcanzado el 100%\n\n"
        msj += "* errores : Muestra una lista con todas las descargas que han fallado\n\n"
        #TODO: msj += "* cancelar [id] : Cancela la descargar indicada por id\n\n"
        #TODO: msj += "* cancelados : Muestra un listado de las descargas canceladas\n\n"
        #TODO: msj += "* descancelar [id] : Reinicia la descarga cancelada indicada por id"
        #TODO: msj += "* pausa [id] : Pausa la descarga indicada por id"
        #TODO: msj += "* reanuda [id] : Reanuda la descarga pausada indicada por id"
        #TODO: msj += "* reiniciaScript: Para el bot y vuelve a conectar la ultima beta. Util para probar nuevas funcionalidades"
        #TODO: msj += "* "
        #TODO: msj += "* "
        msj += "* limpiezaCompletados : Borra la lista que tengas de completados\n\n"
        msj += "* limpiezaErrores : Borra la lista que tengas de errores\n\n"
        msj += "* ordenarDescargas : Ordena la lista de descargas\n\n"
        msj += "* ordenarCompletados : Ordena la lista de completados\n\n"
        msj += "* ordenarErrores : Ordena la lista de errores\n\n"
        msj += "* limpiezaErrores : Borra la lista que tengas en errores\n\n"
        msj += "* reintentarErrores : Reintenta aquellas descargas que forman parte de la lista de errores\n\n"
        msj += "* uploadFolder : Sube al chat de telegram todo lo contenido en la carpeta \"upload\"\n\n"
        msj += "* alive? : Te responde si sigue en funcionamiento\n\n"
        msj += "* help : EJEM EJEM\n\n"
        msj += "* kill : termina el proceso remoto"
        await enviarMensaje(msj)
    
    elif isMessageText(event, "kill"):
        exit()

    # Si no estamos seguros de si el bot está ahora mismo activo, le podemos preguntar mandando "alive?"
    elif isMessageText(event, "alive?"):
        await enviarMensaje("Aqui estoy bb")

# Si lo estamos ejecutando desde terminal, nos muestra que todo va bien y que está esperando los mensajes
print("Bot escuchando mensajes nuevos...")
client.run_until_disconnected()
