from pathlib import Path

import pandas as pd

BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "data"

SUPERS = ["carrefour", "coope", "coto", "dia", "disco", "vea"]


class Datos:
    def __init__(self):
        precios = pd.read_csv(DATA_DIR / "precios_historico.csv", parse_dates=["fecha"])
        supermercados = pd.read_csv(DATA_DIR / "supermercados.csv")

        precios = precios.drop_duplicates(subset=["fecha", "producto", "marca"])
        precios["fecha_str"] = precios["fecha"].dt.strftime("%d-%m-%Y")

        largo = precios.melt(
            id_vars=["fecha", "fecha_str", "producto", "producto_representativo", "marca"],
            value_vars=SUPERS,
            var_name="codigo",
            value_name="precio",
        ).dropna(subset=["precio"])

        largo = largo.merge(supermercados, on="codigo", how="left")

        promedio_hist = (
            largo.groupby("producto")["precio"]
            .mean()
            .reset_index()
            .rename(columns={"precio": "precio_promedio_historico"})
        )
        largo = largo.merge(promedio_hist, on="producto", how="left")
        largo["variacion_pct"] = largo["precio"] / largo["precio_promedio_historico"] - 1
        largo = largo.sort_values("fecha")

        self.wide = precios
        self.long = largo
        self.supermercados = supermercados
        self.ultima_fecha = precios["fecha"].max()

        self.productos = sorted(largo["producto"].unique())
        self.marcas = sorted(largo["marca"].unique())
        self.codigos = supermercados["codigo"].tolist()
        self.nombres_super = supermercados["nombre_completo"].tolist()

    def ultimo_dia(self):
        return self.long[self.long["fecha"] == self.ultima_fecha]


_datos = None


def get_datos():
    global _datos
    if _datos is None:
        _datos = Datos()
    return _datos
