"""Parcial 1: Sistema de Registro de Presupuesto en Línea de Comandos."""

import json
from decimal import Decimal, InvalidOperation
from pathlib import Path

ARCHIVO = Path(__file__).resolve().with_name("articulos_presupuesto.json")


def cargar_articulos():
    """Lee los registros existentes o comienza con una lista vacía."""
    if not ARCHIVO.exists():
        return []
    try:
        with ARCHIVO.open("r", encoding="utf-8") as archivo:
            datos = json.load(archivo)
        if not isinstance(datos, list):
            raise ValueError("El contenido debe ser una lista de artículos.")
        for articulo in datos:
            if not isinstance(articulo, dict) or not all(
                campo in articulo
                for campo in ("id", "nombre", "categoria", "cantidad", "precio_unitario", "descripcion")
            ):
                raise ValueError("Se encontró un artículo con datos incompletos.")
        return datos
    except (OSError, json.JSONDecodeError, ValueError) as error:
        print(f"\nNo fue posible leer el archivo de datos: {error}")
        print("Se conservará el archivo original y se cancelará la ejecución para evitar pérdidas.")
        raise SystemExit(1) from error


def guardar_articulos(articulos):
    """Guarda los datos en JSON, usando un archivo temporal antes de reemplazar."""
    temporal = ARCHIVO.with_suffix(".tmp")
    try:
        with temporal.open("w", encoding="utf-8") as archivo:
            json.dump(articulos, archivo, ensure_ascii=False, indent=4)
        temporal.replace(ARCHIVO)
        return True
    except OSError as error:
        print(f"Error al guardar: {error}")
        return False


def pedir_texto(etiqueta, actual=None, obligatorio=True):
    """Solicita texto; en edición, Enter conserva el dato actual."""
    while True:
        indicacion = f"{etiqueta} [{actual}]: " if actual is not None else f"{etiqueta}: "
        texto = input(indicacion).strip()
        if actual is not None and not obligatorio and texto == "-":
            return ""
        if not texto and actual is not None:
            return actual
        if texto or not obligatorio:
            return texto
        print("Este campo no puede quedar vacío.")


def pedir_entero(etiqueta, actual=None):
    """Solicita una cantidad entera positiva."""
    while True:
        valor = input(f"{etiqueta}{f' [{actual}]' if actual is not None else ''}: ").strip()
        if not valor and actual is not None:
            return actual
        try:
            numero = int(valor)
            if numero <= 0:
                raise ValueError
            return numero
        except ValueError:
            print("Ingrese una cantidad entera mayor que cero.")


def pedir_precio(etiqueta, actual=None):
    """Solicita un precio no negativo, con hasta dos decimales."""
    while True:
        valor = input(f"{etiqueta}{f' [{actual}]' if actual is not None else ''}: ").strip()
        if not valor and actual is not None:
            return str(actual)
        try:
            numero = Decimal(valor)
            if not numero.is_finite() or numero < 0 or numero.as_tuple().exponent < -2:
                raise ValueError
            return str(numero.quantize(Decimal("0.01")))
        except (InvalidOperation, ValueError):
            print("Ingrese un precio válido, no negativo y con máximo dos decimales (ej. 12.50).")


def siguiente_id(articulos):
    return max((articulo["id"] for articulo in articulos), default=0) + 1


def dinero(valor):
    return f"B/. {Decimal(str(valor)):,.2f}"


def mostrar_articulos(articulos):
    """Muestra el inventario presupuestario y su suma total."""
    if not articulos:
        print("\nNo hay artículos para mostrar.")
        return

    cabecera = (
        f"{'ID':<5} {'NOMBRE':<20} {'CATEGORÍA':<17} "
        f"{'CANT.':>6} {'PRECIO':>13} {'TOTAL':>13}"
    )
    print("\n" + cabecera)
    print("-" * len(cabecera))
    presupuesto = Decimal("0.00")
    for articulo in sorted(articulos, key=lambda dato: dato["id"]):
        total = Decimal(str(articulo["precio_unitario"])) * articulo["cantidad"]
        presupuesto += total
        print(
            f"{articulo['id']:<5} "
            f"{articulo['nombre'][:20]:<20} "
            f"{articulo['categoria'][:17]:<17} "
            f"{articulo['cantidad']:>6} "
            f"{dinero(articulo['precio_unitario']):>13} "
            f"{dinero(total):>13}"
        )
        print(f"      Descripción: {articulo['descripcion']}")
    print("-" * len(cabecera))
    print(f"Artículos registrados: {len(articulos)}")
    print(f"PRESUPUESTO TOTAL: {dinero(presupuesto)}")


def registrar_articulo(articulos):
    print("\n=== REGISTRAR ARTÍCULO ===")
    nuevo = {
        "id": siguiente_id(articulos),
        "nombre": pedir_texto("Nombre"),
        "categoria": pedir_texto("Categoría"),
        "cantidad": pedir_entero("Cantidad"),
        "precio_unitario": pedir_precio("Precio unitario"),
        "descripcion": pedir_texto("Descripción", obligatorio=False),
    }
    articulos.append(nuevo)
    if guardar_articulos(articulos):
        print(f"Artículo registrado correctamente con ID {nuevo['id']}.")
    else:
        articulos.pop()


def buscar_articulos(articulos):
    print("\n=== BUSCAR ARTÍCULOS ===")
    termino = pedir_texto("Nombre o categoría a buscar").casefold()
    encontrados = [
        articulo for articulo in articulos
        if termino in articulo["nombre"].casefold()
        or termino in articulo["categoria"].casefold()
    ]
    mostrar_articulos(encontrados)


def seleccionar_articulo(articulos):
    """Identifica un artículo por ID o nombre; pide ID si hay nombres repetidos."""
    if not articulos:
        print("No hay artículos registrados.")
        return None
    criterio = pedir_texto("Escriba el ID o el nombre exacto del artículo")
    if criterio.isdigit():
        encontrados = [a for a in articulos if a["id"] == int(criterio)]
    else:
        encontrados = [a for a in articulos if a["nombre"].casefold() == criterio.casefold()]
    if len(encontrados) == 1:
        return encontrados[0]
    if not encontrados:
        print("No se encontró ningún artículo con ese ID o nombre.")
    else:
        print("Hay varios artículos con ese nombre. Seleccione uno mediante su ID:")
        mostrar_articulos(encontrados)
    return None


def editar_articulo(articulos):
    print("\n=== EDITAR ARTÍCULO ===")
    articulo = seleccionar_articulo(articulos)
    if articulo is None:
        return
    print("Presione Enter para mantener el valor actual.")
    print("En descripción, escriba - para borrarla.")
    cambios = articulo.copy()
    cambios["nombre"] = pedir_texto("Nombre", articulo["nombre"])
    cambios["categoria"] = pedir_texto("Categoría", articulo["categoria"])
    cambios["cantidad"] = pedir_entero("Cantidad", articulo["cantidad"])
    cambios["precio_unitario"] = pedir_precio("Precio unitario", articulo["precio_unitario"])
    cambios["descripcion"] = pedir_texto("Descripción", articulo["descripcion"], obligatorio=False)
    posicion = articulos.index(articulo)
    articulos[posicion] = cambios
    if guardar_articulos(articulos):
        print("Artículo actualizado correctamente.")
    else:
        articulos[posicion] = articulo


def eliminar_articulo(articulos):
    print("\n=== ELIMINAR ARTÍCULO ===")
    articulo = seleccionar_articulo(articulos)
    if articulo is None:
        return
    respuesta = input(f"¿Eliminar '{articulo['nombre']}' (ID {articulo['id']})? (s/n): ").strip().casefold()
    if respuesta not in ("s", "si", "sí"):
        print("Eliminación cancelada.")
        return
    articulos.remove(articulo)
    if guardar_articulos(articulos):
        print("Artículo eliminado correctamente.")
    else:
        articulos.append(articulo)


def menu():
    print("\n" + "=" * 47)
    print(" SISTEMA DE REGISTRO DE PRESUPUESTO ")
    print("=" * 47)
    print("1. Registrar artículo")
    print("2. Buscar artículo por nombre o categoría")
    print("3. Editar artículo")
    print("4. Eliminar artículo")
    print("5. Mostrar todos los artículos")
    print("6. Salir")


def main():
    articulos = cargar_articulos()
    acciones = {
        "1": registrar_articulo,
        "2": buscar_articulos,
        "3": editar_articulo,
        "4": eliminar_articulo,
        "5": mostrar_articulos,
    }
    try:
        while True:
            menu()
            opcion = input("Seleccione una opción (1-6): ").strip()
            if opcion == "6":
                print("Gracias por utilizar el sistema. ¡Hasta pronto!")
                return
            accion = acciones.get(opcion)
            if accion is None:
                print("Opción inválida. Ingrese un número del 1 al 6.")
                continue
            accion(articulos)
    except (KeyboardInterrupt, EOFError):
        print("\nPrograma finalizado. Los cambios guardados permanecen en el archivo JSON.")


if __name__ == "__main__":
    main()
