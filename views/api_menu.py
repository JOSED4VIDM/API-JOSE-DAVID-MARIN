import json
import os
import sys
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen


DEFAULT_API_URL = "https://aprendices-api.onrender.com"
API_URL = os.getenv("APRENDICES_API_URL", DEFAULT_API_URL).strip().rstrip("/")
sys.stdout.reconfigure(encoding="utf-8")


def request_api(path: str, method: str = "GET", body: dict | None = None) -> object:
    data = json.dumps(body).encode("utf-8") if body is not None else None
    request = Request(
        f"{API_URL}{path}",
        data=data,
        headers={"Content-Type": "application/json"},
        method=method,
    )

    try:
        with urlopen(request, timeout=30) as response:
            return json.loads(response.read().decode("utf-8"))
    except HTTPError as error:
        response_body = error.read().decode("utf-8", errors="replace")
        try:
            detail = json.loads(response_body).get("detail", response_body)
        except (json.JSONDecodeError, AttributeError):
            detail = response_body or error.reason
        raise RuntimeError(f"Error HTTP {error.code}: {detail}") from error
    except (URLError, TimeoutError) as error:
        raise RuntimeError(
            f"No se pudo conectar con {API_URL}. "
            "Comprueba la URL y que el servicio de Render esté disponible."
        ) from error
    except json.JSONDecodeError as error:
        raise RuntimeError("La API respondió con un formato JSON no válido.") from error


def print_json(data: object) -> None:
    print(json.dumps(data, ensure_ascii=False, indent=2))


def show_links() -> None:
    print(f"\nAPI:           {API_URL}")
    print(f"Estado:        {API_URL}/health")
    print(f"Documentación: {API_URL}/docs")
    print(f"Aprendices:    {API_URL}/api/aprendices")


def read_positive_id() -> int:
    value = input("ID del aprendiz: ").strip()
    if not value.isdecimal() or int(value) < 1:
        raise ValueError("El ID debe ser un número entero positivo.")
    return int(value)


def register_learner() -> None:
    learner = {
        "nombre": input("Nombre completo: ").strip(),
        "correo": input("Correo electrónico: ").strip(),
        "programa": input("Programa de formación: ").strip(),
    }
    print("\nRespuesta de la API:")
    print_json(request_api("/api/aprendices", method="POST", body=learner))


def main() -> None:
    print("=== MENÚ DE LA API DE APRENDICES ===")
    print(f"API configurada: {API_URL}")

    while True:
        print(
            "\n1. Comprobar conexión y MongoDB"
            "\n2. Listar aprendices"
            "\n3. Buscar aprendiz por ID"
            "\n4. Registrar aprendiz"
            "\n5. Mostrar enlaces de la API"
            "\n0. Salir"
        )
        option = input("\nElige una opción: ").strip()

        if option == "0":
            print("Menú cerrado.")
            return
        if option == "1":
            path = "/health"
            action = "Estado de la API y MongoDB"
        elif option == "2":
            path = "/api/aprendices"
            action = "Aprendices registrados"
        elif option == "3":
            try:
                path = f"/api/aprendices/{read_positive_id()}"
            except ValueError as error:
                print(f"\nDato no válido: {error}")
                continue
            action = "Aprendiz encontrado"
        elif option == "4":
            try:
                register_learner()
            except RuntimeError as error:
                print(f"\nNo se pudo completar la solicitud: {error}")
            continue
        elif option == "5":
            show_links()
            continue
        else:
            print("Opción no válida. Elige un número del menú.")
            continue

        try:
            print(f"\n{action}:")
            print_json(request_api(path))
        except RuntimeError as error:
            print(f"\nNo se pudo completar la solicitud: {error}")


if __name__ == "__main__":
    try:
        main()
    except (EOFError, KeyboardInterrupt):
        print("\nMenú cerrado.")
