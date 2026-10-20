import os
import sqlite3
import sys
from pathlib import Path

from dotenv import load_dotenv
from pymongo import ASCENDING, DESCENDING, MongoClient
from pymongo.collection import Collection
from pymongo.errors import PyMongoError


load_dotenv(Path(__file__).with_name(".env"))
DATABASE_PATH = Path(
    os.getenv("APP_DATABASE_PATH", str(Path(__file__).with_name("aprendices.db")))
)
MONGODB_URI = os.getenv("MONGODB_URI")
MONGODB_DATABASE = os.getenv("MONGODB_DATABASE", "aprendices_db")


def main() -> None:
    if not MONGODB_URI:
        raise SystemExit(
            "Falta MONGODB_URI. Configura la cadena de conexión de Atlas "
            "en la variable de entorno antes de ejecutar la migración."
        )
    if not DATABASE_PATH.is_file():
        raise SystemExit(f"No se encontró la base SQLite: {DATABASE_PATH}")

    client = MongoClient(MONGODB_URI, serverSelectionTimeoutMS=5000)
    try:
        client.admin.command("ping")
        learners: Collection = client[MONGODB_DATABASE]["aprendices"]
        counters: Collection = client[MONGODB_DATABASE]["contadores"]
        learners.create_index([("id", ASCENDING)], unique=True)
        learners.create_index([("correo", ASCENDING)], unique=True)

        with sqlite3.connect(DATABASE_PATH) as connection:
            connection.row_factory = sqlite3.Row
            rows = connection.execute(
                """
                SELECT id, nombre, correo, programa, creado_en
                FROM aprendices
                ORDER BY id
                """
            ).fetchall()

        for row in rows:
            document = dict(row)
            learners.update_one(
                {"id": document["id"]},
                {"$setOnInsert": document},
                upsert=True,
            )

        last_learner = learners.find_one(sort=[("id", DESCENDING)])
        counters.update_one(
            {"_id": "aprendices"},
            {"$max": {"secuencia": last_learner["id"] if last_learner else 0}},
            upsert=True,
        )
    except PyMongoError as error:
        raise SystemExit(
            "La migración falló. Revisa la conexión, permisos de Atlas y "
            f"posibles conflictos de correo único. Detalle: {error}"
        ) from error
    finally:
        client.close()

    print(
        f"Migración completada: {len(rows)} registros revisados en "
        f"MongoDB '{MONGODB_DATABASE}'."
    )


if __name__ == "__main__":
    try:
        main()
    except sqlite3.Error as error:
        print(f"Error al leer SQLite: {error}", file=sys.stderr)
        raise
