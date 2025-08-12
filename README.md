UDPcat-Go
Una herramienta tipo Netcat para UDP, escrita en Go, con menú interactivo, envío de archivos y banner personalizado.

📌 Descripción
UDPcat-Go es una utilidad ligera y versátil para establecer conexiones UDP entre cliente y servidor, enviar y recibir mensajes en tiempo real, y transferir archivos binarios o de texto.
Ideal para pruebas de red, comunicación en entornos controlados y uso educativo.

🚀 Características
Servidor y cliente UDP en un solo binario.

Menú interactivo con opciones claras.

Envío y recepción de mensajes en tiempo real.

Transferencia de archivos vía UDP.

Banner estético al inicio.

Código limpio y comentado para fácil modificación.

🛠️ Requisitos
Go 1.19 o superior

Acceso a terminal

📥 Instalación

# Clonar el repositorio
git clone https://github.com/tuusuario/UDPcat-Go.git
cd UDPcat-Go

# Compilar
go build -o udp-cat main.go
📌 Uso
Ejecuta el binario para acceder al menú:


./udp-cat

Menú principal:
Iniciar en modo Servidor UDP.

Iniciar en modo Cliente UDP.

Enviar archivo.

Salir.

Ejemplo de servidor:

./udp-cat
# Selecciona opción 1
# Ingresa el puerto, por ejemplo 5000
Ejemplo de cliente:

./udp-cat
# Selecciona opción 2
# Ingresa IP y puerto del servidor
# Escribe mensajes que quieras enviar

Ejemplo de envío de archivo:

./udp-cat
# Selecciona opción 3
# Ingresa IP y puerto del servidor receptor
# Proporciona la ruta del archivo

⚠️ Advertencia
Esta herramienta es para fines educativos y de pruebas en entornos autorizados.
No la uses en redes o sistemas sin permiso.

📄 Licencia
MIT License — libre para modificar y distribuir con atribución.
