# Menú de terminal para la API

Este menú consulta la API desplegada y muestra los enlaces funcionales:

- API: <https://aprendices-api.onrender.com>
- Estado y conexión a MongoDB: <https://aprendices-api.onrender.com/health>
- Documentación interactiva: <https://aprendices-api.onrender.com/docs>
- Lista de aprendices: <https://aprendices-api.onrender.com/api/aprendices>

Desde la carpeta raíz del proyecto, abre PowerShell y ejecuta:

```powershell
py views\api_menu.py
```

El menú permite comprobar la conexión, listar aprendices, buscar por ID,
registrar un aprendiz y consultar los enlaces. La opción de registro guarda
los datos en la base de datos de producción.

Para usar una API local en lugar de Render:

```powershell
$env:APRENDICES_API_URL = "http://127.0.0.1:8000"
py views\api_menu.py
```

Al cerrar PowerShell, la variable de entorno temporal deja de estar definida.
