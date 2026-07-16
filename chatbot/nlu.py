import unicodedata

from fuzzywuzzy import fuzz

INTENTS = {
    "precio_actual_producto": [
        "cuanto sale",
        "que precio tiene",
        "cuanto cuesta",
        "precio actual de",
        "a cuanto esta",
    ],
    "super_mas_barato_producto": [
        "donde es mas barato",
        "que super tiene el menor precio",
        "en que supermercado conviene comprar este producto",
        "donde conviene comprarlo",
        "cual es el super mas barato para este producto",
    ],
    "super_mas_barato_general": [
        "que supermercado es el mas barato en general",
        "cual tiene los mejores precios en general",
        "que cadena es mas economica",
        "donde conviene comprar en general",
        "cual es el supermercado mas barato",
    ],
    "producto_mas_caro": [
        "cual es el producto mas caro",
        "que producto es el mas caro hoy",
        "cual es el precio mas alto",
    ],
    "producto_mas_barato": [
        "cual es el producto mas barato",
        "que producto es el mas barato hoy",
        "cual es el precio mas bajo",
    ],
    "promedio_historico_producto": [
        "cual es el precio promedio de",
        "cual es el promedio historico de",
        "cuanto sale en promedio",
    ],
    "evolucion_producto": [
        "como varia el precio de",
        "subio o bajo el precio de",
        "como evoluciono el precio de",
        "aumento el precio de",
        "que tendencia tiene el precio de",
    ],
    "oportunidades_ahorro": [
        "que conviene comprar hoy",
        "donde hay descuentos",
        "que oportunidades de ahorro hay",
        "que esta mas barato que el promedio",
        "que me recomendas comprar hoy",
    ],
    "no_vende_producto": [
        "que supermercados no tienen",
        "donde no se consigue",
        "en que super no venden",
    ],
    "comparar_dos_supers": [
        "es mas caro en un supermercado que en otro",
        "que conviene mas comprar en uno u otro supermercado",
        "comparar precio entre dos supermercados",
    ],
    "conteo_productos": [
        "cuantos productos hay",
        "cuantos productos se siguen",
        "cuantos productos distintos hay",
    ],
    "mayor_aumento_reciente": [
        "que producto aumento mas esta semana",
        "que producto subio mas de precio",
        "cual tuvo la mayor suba de precio",
        "que producto aumento mas en los ultimos dias",
    ],
    "mayor_baja_reciente": [
        "que producto bajo mas de precio",
        "que producto tuvo la mayor baja",
        "cual bajo mas de precio en los ultimos dias",
    ],
}

UMBRAL_INTENT = 45
UMBRAL_INTENT_ALTA_CONFIANZA = 85  # matchea casi textual a un ejemplo: alcanza solo
UMBRAL_PRODUCTO = 62

# Palabras que indican que la pregunta es sobre precios/supermercados. Frases
# genéricas ("cual es", "que") pueden matchear una intención por casualidad
# aunque no tengan nada que ver con el proyecto (ej. "cual es la distancia a
# la luna") — exigir alguna de estas palabras evita responder fuera de tema.
VOCABULARIO_DOMINIO = {
    "precio", "precios", "barato", "barata", "baratos", "baratas",
    "caro", "cara", "caros", "caras", "super", "supermercado", "supermercados",
    "producto", "productos", "marca", "marcas", "comprar", "compra", "conviene",
    "ahorro", "ahorrar", "promedio", "aumento", "aumento", "subio", "bajo",
    "bajó", "vale", "valen", "cuesta", "cuestan", "oferta", "ofertas",
    "descuento", "descuentos", "historico", "historia", "evolucion",
    "evoluciono", "variacion", "vario", "tienda", "gondola", "vende", "venden",
    "sale", "cuanto",
}


def menciona_vocabulario_dominio(pregunta_norm):
    palabras = set(pregunta_norm.split())
    return bool(palabras & VOCABULARIO_DOMINIO)


def normalizar(texto):
    texto = texto.lower().strip()
    texto = unicodedata.normalize("NFKD", texto)
    return "".join(c for c in texto if not unicodedata.combining(c))


def detectar_intent_en_texto(pregunta_norm):
    """Espera texto ya normalizado (ver normalizar()). Devuelve (intent, score).
    Si dos intents empatan en score, gana el que matcheó con el ejemplo más
    largo/específico — evita que una frase corta y genérica (ej. "que precio
    tiene") le gane por accidente a una más específica (ej. "que super tiene
    el menor precio") solo por ser subconjunto."""
    mejor_intent, mejor_score, mejor_longitud = None, 0, 0
    for intent, ejemplos in INTENTS.items():
        for ejemplo in ejemplos:
            score = fuzz.token_set_ratio(pregunta_norm, normalizar(ejemplo))
            longitud = len(ejemplo.split())
            if (score, longitud) > (mejor_score, mejor_longitud):
                mejor_intent, mejor_score, mejor_longitud = intent, score, longitud
    if mejor_score < UMBRAL_INTENT:
        return None, mejor_score
    return mejor_intent, mejor_score


def detectar_intent(pregunta):
    intent, _ = detectar_intent_en_texto(normalizar(pregunta))
    return intent


def quitar_palabras(pregunta_norm, texto_a_quitar):
    palabras_a_quitar = set(normalizar(texto_a_quitar).split())
    return " ".join(w for w in pregunta_norm.split() if w not in palabras_a_quitar)


def extraer_producto(pregunta, productos):
    pregunta_norm = normalizar(pregunta)
    mejor, mejor_score = None, 0
    for producto in productos:
        score = fuzz.token_set_ratio(pregunta_norm, normalizar(producto))
        if score > mejor_score:
            mejor, mejor_score = producto, score
    if mejor_score >= UMBRAL_PRODUCTO:
        return mejor
    return None


def extraer_supermercados(pregunta, supermercados_df):
    pregunta_norm = normalizar(pregunta)
    encontrados = []
    for _, fila in supermercados_df.iterrows():
        if normalizar(fila["codigo"]) in pregunta_norm or normalizar(fila["nombre_completo"]) in pregunta_norm:
            encontrados.append(fila["codigo"])
    return encontrados


def extraer_marca(pregunta, marcas):
    pregunta_norm = normalizar(pregunta)
    for marca in marcas:
        primera_palabra = marca.split()[0]
        if normalizar(marca) in pregunta_norm or normalizar(primera_palabra) in pregunta_norm:
            return marca
    return None
