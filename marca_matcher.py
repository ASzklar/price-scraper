import re

NOTCO_RE = re.compile(
    r'\bnot(?:co|milk|burger|burguer|mila|chicken|chorixo|protein|cream|cheese|salxicha|creamcheese)\b'
    r'|\bnot\s+(?:milk|burger|mila|chicken|chorixo|protein|cream|cheese|co\b)',
    re.IGNORECASE
)


def es_producto_de_marca(nombre: str, marca: str) -> bool:
    """Determina si un nombre de producto pertenece a `marca`.

    "Not" usa un regex dedicado porque como substring es demasiado
    genérico. Felices Las Vacas también vende bajo la sub-marca
    "Jogurtti", que no siempre menciona el nombre de la marca.
    """
    marca_lower = marca.lower()
    if marca_lower == "not":
        return bool(NOTCO_RE.search(nombre))

    patron = re.compile(r'\b' + re.escape(marca), re.IGNORECASE)
    if patron.search(nombre):
        return True

    if marca_lower == "felices las vacas":
        return "jogurtti" in nombre.lower()

    return False
