"""Casos de uso de identidad y del catálogo de monitoreo."""
from .dominio import ErrorAPI, Medicion, Sensor, validar_credenciales


class Identidad:
    def __init__(self, repositorio, contrasenas, tokens):
        self.repositorio = repositorio
        self.contrasenas = contrasenas
        self.tokens = tokens
        self.hash_ficticio = contrasenas.generar("valor sin cuenta asociada")

    def registrar(self, datos, rol="agricultor"):
        correo, contrasena = validar_credenciales(datos)
        return self.repositorio.crear_usuario(correo, self.contrasenas.generar(contrasena), rol)

    def iniciar_sesion(self, datos):
        correo, contrasena = validar_credenciales(datos)
        usuario = self.repositorio.usuario_por_correo(correo)
        hash_guardado = usuario["hash"] if usuario else self.hash_ficticio
        if not self.contrasenas.verificar(contrasena, hash_guardado) or usuario is None:
            raise ErrorAPI(401, "credenciales_invalidas", "El correo o la contraseña es incorrecto.")
        return self.tokens.emitir(usuario["id"])

    def autenticar(self, autorizacion):
        usuario_id = self.tokens.validar(autorizacion)
        usuario = self.repositorio.usuario_por_id(usuario_id)
        if usuario is None:
            raise ErrorAPI(401, "token_invalido", "Se requiere un token de acceso válido.")
        return usuario

    @staticmethod
    def autorizar(usuario, rol):
        if usuario["rol"] != rol:
            raise ErrorAPI(403, "permiso_insuficiente", "El rol no tiene permiso para esta operación.")


class Monitoreo:
    modelos = {"sensores": Sensor, "mediciones": Medicion}

    def __init__(self, repositorio):
        self.repositorio = repositorio

    def guardar(self, tabla, datos, identificador=None):
        recurso = self.modelos[tabla].desde_json(datos)
        return self.repositorio.guardar(tabla, recurso, identificador)

    def obtener(self, tabla, identificador):
        return self.repositorio.obtener(tabla, identificador)

    def listar(self, tabla, limite, desplazamiento, sensor_id=None):
        return self.repositorio.listar(tabla, limite, desplazamiento, sensor_id)

    def eliminar(self, tabla, identificador):
        self.repositorio.eliminar(tabla, identificador)
