¿Como usar el script? Haciendo esto te conectas a un entorno virtual con todas las dependencias necesarias para ejecutarlo
1º source venvTelegram/bin/activate
2º python3 script.py

¿Como usar la plantilla claves_plantilla.txt?
1º Renombrala a claves.txt
2º Añade las variables correspondientes


¿Como descargar?

1º Reenvia o sube los archivos que quieras descargar al bot
2º Los archivos parciales se irán guardando en "./downloads/incomplete"
3º Una vez se haya terminado la descarga se pasará a la carpeta "./downloads/complete"

¿Como subir archivos?

1º Añade los archivos que quieras que se suban a telegram a la carpeta "./uploads"
2º Escribele al bot "uploadFolder"
3º Se subirán todos los archivos al chat con el bot

Consejo: Si quieres descargar archivos que ya tengas organizados en servidor,
puedes crear un soft link a la carpeta uploads. Por ejemplo, si quiero subir la carpeta
"/home/myUser/Downloads/" puedo hacer " ln -s /home/myUser/Downloads/" "./uploads/Downloads" "
y usando uploadFolder se descargarán los archivos como si estuviesen ahí. Luego puedes borrar
el enlace y los archivos se mantendrán donde estaban ya que solo es un enlace.