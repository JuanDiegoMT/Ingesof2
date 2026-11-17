"""Persistencia relacional SQLite con escrituras transaccionales."""
from contextlib import closing, contextmanager
import sqlite3

from .dominio import ErrorAPI


class RepositorioSQLite:
    columnas = {
        "sensores": ("nombre", "ubicacion", "profundidad_cm"),
        "mediciones": ("sensor_id", "instante", "humedad_pct"),
    }

    def __init__(self, ruta):
        self.ruta = ruta
        with self.conexion() as db:
            db.executescript("""
                CREATE TABLE IF NOT EXISTS usuarios(
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    correo TEXT NOT NULL UNIQUE, hash TEXT NOT NULL,
                    rol TEXT NOT NULL CHECK(rol IN ('agricultor', 'administrador'))
                );
                CREATE TABLE IF NOT EXISTS sensores(
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    nombre TEXT NOT NULL, ubicacion TEXT NOT NULL,
                    profundidad_cm REAL NOT NULL CHECK(profundidad_cm BETWEEN 0.1 AND 1000)
                );
                CREATE TABLE IF NOT EXISTS mediciones(
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    sensor_id INTEGER NOT NULL REFERENCES sensores(id) ON DELETE RESTRICT,
                    instante TEXT NOT NULL,
                    humedad_pct REAL NOT NULL CHECK(humedad_pct BETWEEN 0 AND 100),
                    UNIQUE(sensor_id, instante)
                );
            """)

    @contextmanager
    def conexion(self):
        with closing(sqlite3.connect(self.ruta)) as db:
            db.row_factory = sqlite3.Row
            db.execute("PRAGMA foreign_keys = ON")
            with db:
                yield db

    def crear_usuario(self, correo, hash_guardado, rol):
        try:
            with self.conexion() as db:
                cursor = db.execute(
                    "INSERT INTO usuarios(correo,hash,rol) VALUES(?,?,?)",
                    (correo, hash_guardado, rol)
                )
                return {"id": cursor.lastrowid, "correo": correo, "rol": rol}
        except sqlite3.IntegrityError:
            raise ErrorAPI(409, "correo_duplicado", "El correo ya está registrado.") from None

    def usuario_por_correo(self, correo):
        with self.conexion() as db:
            return db.execute("SELECT * FROM usuarios WHERE correo = ?", (correo,)).fetchone()

    def usuario_por_id(self, id_usuario):
        with self.conexion() as db:
            resultado = db.execute(
                "SELECT id,correo,rol FROM usuarios WHERE id = ?", (id_usuario,)
            ).fetchone()
            return dict(resultado) if resultado else None

    def obtener(self, tabla, identificador):
        with self.conexion() as db:
            fila = db.execute(
                f"SELECT * FROM {tabla} WHERE id = ?", (identificador,)
            ).fetchone()
            if fila is None:
                raise ErrorAPI(404, "no_encontrado", "El recurso solicitado no existe.")
            return dict(fila)

    def listar(self, tabla, limite, desplazamiento, sensor_id=None):
        with self.conexion() as db:
            filtro = "WHERE sensor_id = ?" if sensor_id is not None else ""
            valores = (sensor_id, limite, desplazamiento) if filtro else (limite, desplazamiento)
            filas = db.execute(
                f"SELECT * FROM {tabla} {filtro} ORDER BY id LIMIT ? OFFSET ?", valores
            )
            return [dict(fila) for fila in filas]

    def guardar(self, tabla, recurso, identificador=None):
        columnas = self.columnas[tabla]
        valores = tuple(getattr(recurso, columna) for columna in columnas)
        try:
            with self.conexion() as db:
                if identificador is None:
                    nombres = ",".join(columnas)
                    parametros = ",".join("?" for _ in columnas)
                    cursor = db.execute(f"INSERT INTO {tabla}({nombres}) VALUES({parametros})", valores)
                    identificador = cursor.lastrowid
                else:
                    asignaciones = ",".join(f"{columna} = ?" for columna in columnas)
                    cursor = db.execute(
                        f"UPDATE {tabla} SET {asignaciones} WHERE id = ?",
                        (*valores, identificador)
                    )
                    if not cursor.rowcount:
                        raise ErrorAPI(404, "no_encontrado", "El recurso solicitado no existe.")
                return {"id": identificador, **dict(zip(columnas, valores))}
        except sqlite3.IntegrityError as error:
            if error.sqlite_errorcode == sqlite3.SQLITE_CONSTRAINT_FOREIGNKEY:
                raise ErrorAPI(404, "sensor_inexistente", "El sensor referenciado no existe.") from None
            if error.sqlite_errorcode == sqlite3.SQLITE_CONSTRAINT_UNIQUE:
                raise ErrorAPI(409, "instante_duplicado", "Ya existe una medición del sensor en ese instante.") from None
            raise

    def eliminar(self, tabla, identificador):
        try:
            with self.conexion() as db:
                cursor = db.execute(f"DELETE FROM {tabla} WHERE id = ?", (identificador,))
                if not cursor.rowcount:
                    raise ErrorAPI(404, "no_encontrado", "El recurso solicitado no existe.")
        except sqlite3.IntegrityError:
            raise ErrorAPI(409, "sensor_con_mediciones", "El sensor conserva mediciones asociadas.") from None
