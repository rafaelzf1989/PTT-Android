[app]
# Título de tu aplicación
title = PTT Client

# Nombre del paquete (sin espacios)
package.name = pttclient

# Dominio del paquete (puede ser genérico)
package.domain = org.test

# Directorio donde está tu main.py (la raíz)
source.dir = .

# Tipos de archivos que se incluirán
source.include_exts = py,png,jpg,kv,atlas

# Versión de la aplicación
version = 0.1

# ¡AQUÍ ESTÁ LA CLAVE! Forzamos la misma versión para python3 y hostpython3
requirements = python3==3.10.12,hostpython3==3.10.12,kivy==2.3.0

# Orientación de la pantalla
orientation = portrait

# Permiso de Internet, esencial para que funcionen los sockets
android.permissions = INTERNET, ACCESS_NETWORK_STATE

# Versiones de Android (API 33 es una versión moderna y compatible)
android.api = 33
android.minapi = 21

# Arquitecturas de los teléfonos (cubre la gran mayoría)
android.archs = arm64-v8a, armeabi-v7a

# Permite copias de seguridad
android.allow_backup = True

# Opciones de compilación
[buildozer]
log_level = 2
