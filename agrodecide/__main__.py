"""Arranque local y aprovisionamiento de cuentas administradoras."""
import argparse
from getpass import getpass
import os
from urllib.parse import urlsplit
from wsgiref.simple_server import make_server

from .aplicacion import Identidad, Monitoreo
from .dominio import ErrorAPI
from .http import ControladorHTTP
from .repositorio import RepositorioSQLite
from .seguridad import Tokens, crear_hash_argon2


def crear_app():
    tokens = Tokens(os.environ.get("AGRODECIDE_JWT_SECRET", ""))
    ruta = os.environ.get("AGRODECIDE_DB_PATH", "agrodecide.sqlite3")
    origenes = {
        origen.strip() for origen in os.environ.get("AGRODECIDE_CORS_ORIGINS", "").split(",")
        if origen.strip()
    }
    for origen in origenes:
        partes = urlsplit(origen)
        if (partes.scheme not in {"http", "https"} or not partes.hostname
                or partes.username or partes.path or partes.query or partes.fragment):
            raise ValueError("AGRODECIDE_CORS_ORIGINS requiere orígenes HTTP(S) exactos.")
    repositorio = RepositorioSQLite(ruta)
    identidad = Identidad(repositorio, crear_hash_argon2(), tokens)
    return ControladorHTTP(identidad, Monitoreo(repositorio), origenes)


def main():
    os.umask(0o077)
    analizador = argparse.ArgumentParser(description="API local de AgroDecide")
    comandos = analizador.add_subparsers(dest="comando", required=True)
    servir = comandos.add_parser("servir", help="Arrancar la API local")
    servir.add_argument("--puerto", type=int, default=8000)
    registro = comandos.add_parser("crear-admin", help="Crear administrador de forma local")
    registro.add_argument("correo")
    args = analizador.parse_args()
    try:
        app = crear_app()
        if args.comando == "crear-admin":
            contrasena = getpass("Contraseña del administrador: ")
            if contrasena != getpass("Repetir contraseña: "):
                analizador.error("Las contraseñas no coinciden.")
            app.identidad.registrar({"correo": args.correo, "contrasena": contrasena}, "administrador")
            print("Administrador creado.")
            return
        with make_server("127.0.0.1", args.puerto, app) as servidor:
            print(f"API local disponible en http://127.0.0.1:{servidor.server_port}", flush=True)
            servidor.serve_forever()
    except (ErrorAPI, ValueError, RuntimeError) as error:
        analizador.error(str(error))


if __name__ == "__main__":
    main()
