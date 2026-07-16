import pandas as pd

from nlu import (
    UMBRAL_INTENT_ALTA_CONFIANZA,
    detectar_intent_en_texto,
    extraer_marca,
    extraer_producto,
    extraer_supermercados,
    menciona_vocabulario_dominio,
    normalizar,
    quitar_palabras,
)

SIN_ENTENDER = (
    "No entendí bien la pregunta. Podés preguntarme por el precio de un producto, "
    "el supermercado más barato, oportunidades de ahorro, o cómo varió un precio en el tiempo."
)

PEDIR_PRODUCTO_PRECIO = "No entendí a qué producto te referís. ¿Podés ser más específico?"
PEDIR_PRODUCTO_SUPER_BARATO = "Decime de qué producto querés saber el supermercado más barato."
PEDIR_PRODUCTO_PROMEDIO = "Decime de qué producto querés el promedio histórico."
PEDIR_PRODUCTO_EVOLUCION = "Decime de qué producto querés ver la evolución."
PEDIR_PRODUCTO_NO_VENDE = "Decime de qué producto querés saber dónde no se consigue."
PEDIR_PRODUCTO_Y_SUPERS = "Decime el producto y los dos supermercados que querés comparar."

# Respuestas sin ningún dato real todavía (piden que el usuario aclare algo) —
# no tiene sentido mandarlas al LLM a "reformular": no hay nada que mejorar y
# un modelo chico puede inventar un producto o supermercado de la nada para
# sonar más natural (nos pasó con "La Anónima" y "Jumbo", que ni siquiera
# seguimos). Ver main.py.
RESPUESTAS_SIN_DATOS = {
    SIN_ENTENDER,
    PEDIR_PRODUCTO_PRECIO,
    PEDIR_PRODUCTO_SUPER_BARATO,
    PEDIR_PRODUCTO_PROMEDIO,
    PEDIR_PRODUCTO_EVOLUCION,
    PEDIR_PRODUCTO_NO_VENDE,
    PEDIR_PRODUCTO_Y_SUPERS,
}


def _precio_actual_producto(datos, producto):
    if producto is None:
        return PEDIR_PRODUCTO_PRECIO
    hoy = datos.ultimo_dia()
    filas = hoy[hoy["producto"] == producto]
    if filas.empty:
        return f"No tengo precios recientes de '{producto}'."
    partes = [f"{fila.nombre_completo}: ${fila.precio:,.0f}" for fila in filas.itertuples()]
    return f"Precios de '{producto}' al {filas['fecha_str'].iloc[0]}: " + " · ".join(partes) + "."


def _super_mas_barato_producto(datos, producto):
    if producto is None:
        return PEDIR_PRODUCTO_SUPER_BARATO
    hoy = datos.ultimo_dia()
    filas = hoy[hoy["producto"] == producto]
    if filas.empty:
        return f"No encontré precios recientes de '{producto}'."
    fila = filas.loc[filas["precio"].idxmin()]
    return (
        f"El más barato para '{producto}' es {fila['nombre_completo']}, a ${fila['precio']:,.0f} "
        f"(al {fila['fecha_str']})."
    )


def _super_mas_barato_general(datos):
    hoy = datos.ultimo_dia()
    promedio_por_super = hoy.groupby("nombre_completo")["variacion_pct"].mean().sort_values()
    mejor = promedio_por_super.index[0]
    return (
        f"En promedio, {mejor} es el supermercado con los precios más bajos respecto al "
        "histórico de cada producto."
    )


def _producto_extremo(datos, cual):
    hoy = datos.ultimo_dia()
    fila = hoy.loc[hoy["precio"].idxmax() if cual == "caro" else hoy["precio"].idxmin()]
    return (
        f"El producto más {cual} hoy es '{fila['producto']}' en {fila['nombre_completo']}, "
        f"a ${fila['precio']:,.0f}."
    )


def _promedio_historico_producto(datos, producto):
    if producto is None:
        return PEDIR_PRODUCTO_PROMEDIO
    filas = datos.long[datos.long["producto"] == producto]
    if filas.empty:
        return f"No tengo datos históricos de '{producto}'."
    promedio = filas["precio_promedio_historico"].iloc[0]
    return f"El precio promedio histórico de '{producto}' es ${promedio:,.0f}."


def _evolucion_producto(datos, producto):
    if producto is None:
        return PEDIR_PRODUCTO_EVOLUCION
    filas = datos.long[datos.long["producto"] == producto]
    if filas.empty:
        return f"No tengo datos históricos de '{producto}'."
    por_fecha = filas.groupby("fecha")["precio"].mean().sort_index()
    primero_fecha, primero_precio = por_fecha.index[0], por_fecha.iloc[0]
    ultimo_fecha, ultimo_precio = por_fecha.index[-1], por_fecha.iloc[-1]
    variacion = (ultimo_precio / primero_precio - 1) * 100
    if variacion > 0.5:
        direccion = "subió"
    elif variacion < -0.5:
        direccion = "bajó"
    else:
        direccion = "se mantuvo estable"
    return (
        f"'{producto}' {direccion} un {abs(variacion):.1f}% entre el {primero_fecha:%d-%m-%Y} "
        f"(promedio ${primero_precio:,.0f}) y el {ultimo_fecha:%d-%m-%Y} (promedio ${ultimo_precio:,.0f})."
    )


def _mayor_variacion_reciente(datos, direccion, marca=None, dias=30):
    ultima_fecha = datos.ultima_fecha
    referencia = ultima_fecha - pd.Timedelta(days=dias)

    datos_marca = datos.long if marca is None else datos.long[datos.long["marca"] == marca]
    por_producto_fecha = datos_marca.groupby(["producto", "fecha"])["precio"].mean().reset_index()

    hoy = por_producto_fecha[por_producto_fecha["fecha"] == ultima_fecha][["producto", "precio"]]
    hoy = hoy.rename(columns={"precio": "precio_hoy"})

    pasado = por_producto_fecha[por_producto_fecha["fecha"] <= referencia].sort_values("fecha")
    pasado = pasado.groupby("producto").last().reset_index()[["producto", "precio"]]
    pasado = pasado.rename(columns={"precio": "precio_pasado"})

    comparacion = hoy.merge(pasado, on="producto")
    if comparacion.empty:
        acotado = f" de la marca {marca}" if marca else ""
        return f"Todavía no tengo suficiente historial{acotado} de {dias} días para calcular esto."

    comparacion["variacion_pct"] = (comparacion["precio_hoy"] / comparacion["precio_pasado"] - 1) * 100
    idx = comparacion["variacion_pct"].idxmax() if direccion == "aumento" else comparacion["variacion_pct"].idxmin()
    fila = comparacion.loc[idx]

    verbo = "aumentó" if direccion == "aumento" else "bajó"
    acotado = f" de {marca}" if marca else ""
    return (
        f"El producto{acotado} que más {verbo} en los últimos {dias} días es '{fila['producto']}': "
        f"{abs(fila['variacion_pct']):.1f}% (de ${fila['precio_pasado']:,.0f} a ${fila['precio_hoy']:,.0f})."
    )


def _oportunidades_ahorro(datos, top=5):
    hoy = datos.ultimo_dia()
    mejores = hoy.sort_values("variacion_pct").head(top)
    partes = [
        f"'{fila.producto}' en {fila.nombre_completo} a ${fila.precio:,.0f} "
        f"({fila.variacion_pct:.0%} vs. su promedio histórico)"
        for fila in mejores.itertuples()
    ]
    return "Las mejores oportunidades de hoy son: " + "; ".join(partes) + "."


def _no_vende_producto(datos, producto):
    if producto is None:
        return PEDIR_PRODUCTO_NO_VENDE
    hoy = datos.ultimo_dia()
    vende = set(hoy[hoy["producto"] == producto]["codigo"])
    no_vende = [
        datos.supermercados.loc[datos.supermercados["codigo"] == codigo, "nombre_completo"].iloc[0]
        for codigo in datos.codigos
        if codigo not in vende
    ]
    if not no_vende:
        return f"'{producto}' se consigue hoy en todos los supermercados que sigo."
    return f"'{producto}' no se encontró hoy en: {', '.join(no_vende)}."


def _comparar_dos_supers(datos, producto, codigos_supers):
    if producto is None or len(codigos_supers) < 2:
        return PEDIR_PRODUCTO_Y_SUPERS
    hoy = datos.ultimo_dia()
    filas = hoy[(hoy["producto"] == producto) & (hoy["codigo"].isin(codigos_supers))]
    if len(filas) < 2:
        return f"No tengo precios de '{producto}' en ambos supermercados para compararlos hoy."
    filas = filas.sort_values("precio")
    barato, caro = filas.iloc[0], filas.iloc[-1]
    diferencia = caro["precio"] - barato["precio"]
    return (
        f"'{producto}' es más barato en {barato['nombre_completo']} (${barato['precio']:,.0f}) que en "
        f"{caro['nombre_completo']} (${caro['precio']:,.0f}) — una diferencia de ${diferencia:,.0f}."
    )


def _conteo_productos(datos, marca):
    if marca:
        cantidad = datos.long[datos.long["marca"] == marca]["producto"].nunique()
        return f"Sigo {cantidad} productos distintos de la marca {marca}."
    return f"En total sigo {len(datos.productos)} productos distintos entre las 3 marcas."


def responder(datos, pregunta):
    producto = extraer_producto(pregunta, datos.productos)
    supers_mencionados = extraer_supermercados(pregunta, datos.supermercados)
    marca = extraer_marca(pregunta, datos.marcas)

    pregunta_norm = normalizar(pregunta)
    if producto:
        pregunta_norm = quitar_palabras(pregunta_norm, producto)
    intent, score = detectar_intent_en_texto(pregunta_norm)

    # Aunque el matching difuso encuentre una intención, si la pregunta no
    # menciona nada del dominio (ni vocabulario de precios/super, ni un
    # producto/marca conocido) la tratamos como fuera de tema — salvo que el
    # match sea casi textual a un ejemplo (score muy alto), donde ya alcanza.
    en_dominio = (
        score >= UMBRAL_INTENT_ALTA_CONFIANZA
        or menciona_vocabulario_dominio(pregunta_norm)
        or producto or marca or supers_mencionados
    )
    if intent is None or not en_dominio:
        return SIN_ENTENDER

    if intent == "precio_actual_producto":
        return _precio_actual_producto(datos, producto)
    if intent == "super_mas_barato_producto":
        return _super_mas_barato_producto(datos, producto)
    if intent == "super_mas_barato_general":
        return _super_mas_barato_general(datos)
    if intent == "producto_mas_caro":
        return _producto_extremo(datos, "caro")
    if intent == "producto_mas_barato":
        return _producto_extremo(datos, "barato")
    if intent == "promedio_historico_producto":
        return _promedio_historico_producto(datos, producto)
    if intent == "evolucion_producto":
        return _evolucion_producto(datos, producto)
    if intent == "oportunidades_ahorro":
        return _oportunidades_ahorro(datos)
    if intent == "no_vende_producto":
        return _no_vende_producto(datos, producto)
    if intent == "comparar_dos_supers":
        return _comparar_dos_supers(datos, producto, supers_mencionados)
    if intent == "conteo_productos":
        return _conteo_productos(datos, marca)
    if intent == "mayor_aumento_reciente":
        return _mayor_variacion_reciente(datos, "aumento", marca)
    if intent == "mayor_baja_reciente":
        return _mayor_variacion_reciente(datos, "baja", marca)
    return SIN_ENTENDER
