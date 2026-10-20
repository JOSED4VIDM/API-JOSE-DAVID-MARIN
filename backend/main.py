import os
from contextlib import asynccontextmanager
from datetime import datetime, timezone
from pathlib import Path
from typing import Annotated

from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException, Request, status
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, EmailStr, Field, field_validator
from pymongo import ASCENDING, DESCENDING, MongoClient, ReturnDocument
from pymongo.collection import Collection
from pymongo.errors import DuplicateKeyError, PyMongoError


load_dotenv(Path(__file__).with_name(".env"))
MONGODB_URI = os.getenv("MONGODB_URI")
MONGODB_DATABASE = os.getenv("MONGODB_DATABASE", "aprendices_db")
DEFAULT_ALLOWED_ORIGINS = (
    "http://localhost:5173",
    "http://127.0.0.1:5173",
    "http://localhost:5174",
    "http://127.0.0.1:5174",
)


def get_allowed_origins() -> list[str]:
    configured_origins = os.getenv("ALLOWED_ORIGINS")
    if not configured_origins:
        return list(DEFAULT_ALLOWED_ORIGINS)

    origins = []
    for origin in configured_origins.split(","):
        normalized_origin = origin.strip().rstrip("/")
        if normalized_origin:
            if "://" not in normalized_origin:
                normalized_origin = f"https://{normalized_origin}"
            origins.append(normalized_origin)
    return origins


class AprendizCreate(BaseModel):
    nombre: Annotated[str, Field(min_length=1, max_length=100)]
    correo: EmailStr
    programa: Annotated[str, Field(min_length=1, max_length=120)]

    @field_validator("nombre", "programa")
    @classmethod
    def trim_text(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("Este campo no puede estar vacío.")
        return value

    @field_validator("correo")
    @classmethod
    def normalize_email(cls, value: EmailStr) -> str:
        return str(value).lower()


class Aprendiz(AprendizCreate):
    id: int
    creado_en: str


@asynccontextmanager
async def lifespan(app: FastAPI):
    if not MONGODB_URI:
        raise RuntimeError(
            "Falta configurar MONGODB_URI. Define la variable en backend/.env "
            "o en el panel de variables de entorno de Render antes de iniciar la API."
        )

    client = MongoClient(MONGODB_URI, serverSelectionTimeoutMS=5000)
    try:
        client.admin.command("ping")
        database = client[MONGODB_DATABASE]
        learners: Collection = database["aprendices"]
        counters: Collection = database["contadores"]
        learners.create_index([("id", ASCENDING)], unique=True)
        learners.create_index([("correo", ASCENDING)], unique=True)
        last_learner = learners.find_one(sort=[("id", DESCENDING)])
        counters.update_one(
            {"_id": "aprendices"},
            {"$max": {"secuencia": last_learner["id"] if last_learner else 0}},
            upsert=True,
        )
        app.state.mongo_client = client
        app.state.aprendices = learners
        app.state.contadores = counters
    except PyMongoError as error:
        client.close()
        raise RuntimeError(
            "No se pudo conectar con MongoDB Atlas. Revisa MONGODB_URI, "
            "el usuario y la contraseña de base de datos, y el acceso de red "
            "configurado en Atlas."
        ) from error

    try:
        yield
    finally:
        client.close()


app = FastAPI(
    title="API de aprendices",
    description="Registro y consulta de aprendices almacenados en MongoDB Atlas.",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=get_allowed_origins(),
    allow_credentials=False,
    allow_methods=["GET", "POST", "PUT"],
    allow_headers=["Content-Type"],
)


def get_collections(request: Request) -> tuple[Collection, Collection]:
    learners = getattr(request.app.state, "aprendices", None)
    counters = getattr(request.app.state, "contadores", None)
    if learners is None or counters is None:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="La conexión con MongoDB todavía no está disponible.",
        )
    return learners, counters


@app.get("/")
def root() -> dict[str, str]:
    return {
        "mensaje": "API de aprendices activa",
        "documentacion": "/docs",
        "base_datos": MONGODB_DATABASE,
        "almacenamiento": "MongoDB Atlas",
    }


@app.get("/health")
def health(request: Request) -> dict[str, str]:
    client = getattr(request.app.state, "mongo_client", None)
    if client is None:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="La conexión con MongoDB todavía no está disponible.",
        )
    try:
        client.admin.command("ping")
    except PyMongoError as error:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="No fue posible conectar con MongoDB.",
        ) from error
    return {"status": "ok", "database": MONGODB_DATABASE}


@app.post(
    "/api/aprendices",
    response_model=Aprendiz,
    status_code=status.HTTP_201_CREATED,
)
def create_aprendiz(
    aprendiz: AprendizCreate,
    request: Request,
) -> Aprendiz:
    learners, counters = get_collections(request)
    try:
        counter = counters.find_one_and_update(
            {"_id": "aprendices"},
            {"$inc": {"secuencia": 1}},
            upsert=True,
            return_document=ReturnDocument.AFTER,
        )
        document = {
            "id": counter["secuencia"],
            **aprendiz.model_dump(),
            "correo": str(aprendiz.correo),
            "creado_en": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        }
        learners.insert_one(document)
    except DuplicateKeyError as error:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Ya existe un aprendiz registrado con ese correo.",
        ) from error
    except PyMongoError as error:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="No fue posible guardar el aprendiz en MongoDB.",
        ) from error

    return Aprendiz(**document)


@app.get("/api/aprendices", response_model=list[Aprendiz])
def list_aprendices(request: Request) -> list[Aprendiz]:
    learners, _ = get_collections(request)
    try:
        return [
            Aprendiz(**document)
            for document in learners.find({}, {"_id": 0}).sort("id", DESCENDING)
        ]
    except PyMongoError as error:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="No fue posible consultar los aprendices en MongoDB.",
        ) from error


@app.get("/api/aprendices/{aprendiz_id}", response_model=Aprendiz)
def get_aprendiz(aprendiz_id: int, request: Request) -> Aprendiz:
    learners, _ = get_collections(request)
    try:
        document = learners.find_one({"id": aprendiz_id}, {"_id": 0})
    except PyMongoError as error:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="No fue posible consultar el aprendiz en MongoDB.",
        ) from error

    if document is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No se encontró el aprendiz.",
        )
    return Aprendiz(**document)


@app.put("/api/aprendices/{aprendiz_id}", response_model=Aprendiz)
def update_aprendiz(
    aprendiz_id: int,
    aprendiz: AprendizCreate,
    request: Request,
) -> Aprendiz:
    learners, _ = get_collections(request)
    try:
        document = learners.find_one_and_update(
            {"id": aprendiz_id},
            {"$set": aprendiz.model_dump()},
            projection={"_id": 0},
            return_document=ReturnDocument.AFTER,
        )
    except DuplicateKeyError as error:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Ya existe otro aprendiz registrado con ese correo.",
        ) from error
    except PyMongoError as error:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="No fue posible actualizar el aprendiz en MongoDB.",
        ) from error

    if document is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No se encontró el aprendiz.",
        )
    return Aprendiz(**document)
