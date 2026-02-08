# Telegram Media Downloader (TMD)

## ¿Como configurar las claves?

1º Renombra el archivo claves_plantilla.txt

2º Añade las variables correspondientes siguiendo las instrucciones:

API_ID= #ID de la API de telegram https://my.telegram.org/auth?to=apps

API_HASH= # HASH de la API de telegram https://my.telegram.org/auth?to=apps

BOT_TOKEN= # Token del bot de telegram creado por el botFather https://core.telegram.org/bots abajo del todo

CHAT_PERSONAL= # ID de tu chat en telegram. Hay varias formas, por ejemplo el uso del https://t.me/RawDataBot

## ¿Como ejecutar?

```
source venvTelegram/bin/activate
```

```
python3 script.py
```
Si quieres que el comando se ejecute de fonde pudiendo desconectar la terminal, siempre que el ordenador siga encendido:
```
nohup python3 script.py &
```

## ¿Como descargo archivos?

1º Reenvia o sube los archivos que quieras descargar al bot.

2º Los archivos parciales se irán guardando en "./downloads/incomplete"

3º Una vez se haya terminado la descarga se pasará a la carpeta "./downloads/complete"

## ¿Como subir archivos?

1º Añade los archivos que quieras que se suban a telegram a la carpeta "./uploads"

2º Escribele al bot "uploadFolder" utilizando la opción en el menú de subidas.

3º Se subirán todos los archivos al chat con el bot uno a uno.

*Si el archivo pesa más de 2GB, que es el límite para un mismo archivo en telegram, lo comprimirá por partes .7z de 1,9GB.

Para descomprimir estos archivos, simplemente tendrás que ejecutar:
```
7z x NOMBRE_DEL_ARCHIVO.7z.001
```
### Consejo para uploads 
Si quieres descargar archivos que ya tengas organizados en tu ordenador sin moverlos, puedes crear un soft link a la carpeta uploads. 

Por ejemplo, si quiero subir la carpeta
"/home/myUser/Series/" puedo hacer:

`ln -s /home/myUser/Series/MiSerie ./uploads/MiSerie`

y usando uploadFolder se descargarán los archivos como si estuviesen ahí. Luego puedes borrar
el enlace y los archivos se mantendrán donde estaban ya que solo es un enlace.
