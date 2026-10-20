# Aprende — gestión de aprendices

Aplicación web en React/Vite, API FastAPI y almacenamiento en MongoDB Atlas.
El frontend permite registrar aprendices, listar registros y buscar por ID.

## Configurar MongoDB Atlas

1. Crea un clúster y un usuario de base de datos en [MongoDB Atlas](https://www.mongodb.com/atlas).
2. En **Network Access**, permite la IP de tu equipo para desarrollo local.
3. Copia la cadena de conexión del clúster. No la publiques ni la compartas.

## Ejecutar localmente

Desde la carpeta del proyecto:

```powershell
py -m venv backend\.venv
backend\.venv\Scripts\python.exe -m pip install -r backend\requirements.txt
Copy-Item backend\.env.example backend\.env
```

Edita `backend/.env` y reemplaza `MONGODB_URI` con la cadena de Atlas. Si la
contraseña contiene caracteres especiales, codifícala para URL. El `.env`
local está excluido de Git.

En la primera terminal, inicia la API:

```powershell
cd backend
.\.venv\Scripts\python.exe -m uvicorn main:app --reload
```

La API estará en `http://127.0.0.1:8000`; Swagger en
`http://127.0.0.1:8000/docs`. La API crea la colección `aprendices` y sus
índices únicos para ID y correo. `/health` comprueba la conexión a MongoDB.

En otra terminal, inicia el frontend desde la raíz del proyecto:

```powershell
npm ci
npm run dev
```

Abre `http://127.0.0.1:5173`. En producción, `VITE_API_URL` configura el host
de la API; localmente, el frontend usa `http://127.0.0.1:8000` por defecto.

## Migrar los datos SQLite existentes (opcional)

Si ya tienes datos en `backend/aprendices.db`, copia `backend/.env.example` a
`backend/.env`, configura la URI de Atlas y ejecuta una vez:

```powershell
cd backend
.\.venv\Scripts\python.exe migrate_sqlite_to_mongodb.py
```

La migración conserva los IDs, se puede repetir sin duplicar esos IDs y no
borra la base SQLite original. Si el correo de un registro ya está asociado a
otro ID en MongoDB, la migración informa el conflicto y no lo oculta.

## Endpoints de la API

| Método | Ruta | Descripción |
| --- | --- | --- |
| `GET` | `/` | Estado de la API. |
| `GET` | `/health` | Estado de conexión con MongoDB. |
| `POST` | `/api/aprendices` | Registra un aprendiz. |
| `GET` | `/api/aprendices` | Consulta todos los aprendices. |
| `GET` | `/api/aprendices/{aprendiz_id}` | Consulta un aprendiz por ID. |
| `PUT` | `/api/aprendices/{aprendiz_id}` | Actualiza el nombre, correo y programa de un aprendiz. |

## Menú de la API en la terminal

La carpeta `views` contiene un menú interactivo para consultar la API de
producción desde PowerShell. Desde la raíz del proyecto, ejecútalo con:

```powershell
py views\api_menu.py
```

El menú permite comprobar la conexión con MongoDB, listar, buscar, registrar y
actualizar aprendices, además de mostrar los enlaces de la API. Las opciones
de registro y actualización modifican datos en producción. Para apuntar a la API local, define
`$env:APRENDICES_API_URL = "http://127.0.0.1:8000"` antes de ejecutarlo.
Los enlaces y las instrucciones están también en [views/README.md](views/README.md).

## Preparar GitHub

El `.gitignore` excluye dependencias, builds, entornos virtuales, la base de
datos local y `backend/.env`. Antes de subir, comprueba que no estás agregando
ninguna credencial.

1. Crea un repositorio vacío en GitHub, sin README ni archivos iniciales.
2. Desde la raíz del proyecto, agrega, confirma y sube los archivos:

```powershell
git add .
git status
git commit -m "Prepare learners app for deployment"
git branch -M main
git remote add origin https://github.com/USUARIO/REPOSITORIO.git
git push -u origin main
```

Reemplaza la URL por la de tu repositorio. Antes del `commit`, revisa `git
status` y confirma que `backend/.env` no aparezca.

## Desplegar en Render

El archivo `render.yaml` declara una API Python y un sitio estático. Después
de subir el repositorio:

1. En Render, selecciona **New → Blueprint** y conecta el repositorio.
2. Render te pedirá `MONGODB_URI`: pega la cadena privada de Atlas como secreto.
   No la pongas en `render.yaml`, `.env.example` ni en el repositorio.
3. En MongoDB Atlas, permite las direcciones de salida que Render muestra para
   el servicio de API en **Network Access**. Evita abrir la base a todas las IP.
4. Despliega los dos servicios. Render enlaza la API con el frontend y usa
   `/health` para las comprobaciones de salud.

La configuración inicial usa los nombres `aprendices-api` y `aprendices-web`;
si cambias el nombre del sitio, actualiza también `ALLOWED_ORIGINS` en
`render.yaml` para que coincida con su dominio HTTPS. Si cambias el nombre de
la API, la referencia de `VITE_API_URL` en ese archivo debe seguir apuntando
al nombre nuevo.

La API está configurada con el plan gratuito de Render. Render puede suspender
el servicio tras un periodo sin tráfico; la primera petición posterior puede
tardar mientras vuelve a iniciar. El sistema de archivos local del servicio
no es persistente, por lo que MongoDB Atlas es el almacenamiento de los datos.

Cuando el despliegue termine, abre el dominio del sitio estático. La
documentación Swagger estará en el dominio de la API seguido de `/docs`.
