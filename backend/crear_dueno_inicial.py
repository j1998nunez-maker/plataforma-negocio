# crear_dueno_inicial.py = un script de arranque, se corre UNA SOLA VEZ.
#
# Problema que resuelve: para crear un usuario nuevo hay que ser "dueño" y
# estar logueado (POST /usuarios exige ese rol) — pero al principio no
# existe ningún usuario todavía. Este script crea el primer usuario "dueño"
# directo en la base de datos, sin pasar por la API, para poder arrancar.
#
# Cómo correrlo (desde la carpeta backend/, con el entorno virtual activado):
#   python crear_dueno_inicial.py

from getpass import getpass

from app.core.security import hashear_contrasena
from app.db.session import SessionLocal
from app.usuarios.models import Usuario


def main() -> None:
    print("== Crear el primer usuario (dueño) ==")
    nombre = input("Nombre completo: ").strip()
    correo = input("Correo: ").strip().lower()
    contrasena = getpass("Contraseña (mínimo 6 caracteres): ").strip()

    if len(contrasena) < 6:
        print("La contraseña debe tener al menos 6 caracteres. Cancelado.")
        return

    db = SessionLocal()
    try:
        if db.query(Usuario).filter(Usuario.correo == correo).first():
            print(f"Ya existe un usuario con el correo {correo}. Cancelado.")
            return

        usuario = Usuario(
            nombre_completo=nombre,
            correo=correo,
            contrasena_hash=hashear_contrasena(contrasena),
            rol="dueno",
        )
        db.add(usuario)
        db.commit()
        print(f"Usuario dueño '{nombre}' creado correctamente. Ya puedes iniciar sesión.")
    finally:
        db.close()


if __name__ == "__main__":
    main()
