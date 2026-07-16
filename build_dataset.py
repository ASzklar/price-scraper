"""Consolida Data/Cleaned/*.csv en los dos CSVs chicos que usa el chatbot del TP.

Uso: python build_dataset.py
"""
import glob
import os

import pandas as pd

CLEANED_DIR = os.path.join("Data", "Cleaned")
OUTPUT_DIR = os.path.join("chatbot", "data")

SUPERS = ["carrefour", "coope", "coto", "dia", "disco", "vea"]
SUPER_RENAMES = {
    "carrefour": "Carrefour",
    "coope": "Cooperativa Obrera",
    "coto": "Coto",
    "dia": "Dia",
    "disco": "Disco",
    "vea": "Vea",
}


def cargar_precios_historico():
    filas = sorted(glob.glob(os.path.join(CLEANED_DIR, "*.csv")))
    dfs = []
    for fp in filas:
        df = pd.read_csv(fp, parse_dates=["fecha"])
        marca = os.path.basename(fp).split("_")[1]
        df["marca"] = (
            marca.replace("felices", "Felices las Vacas")
            .replace("vegetalex", "Vegetalex")
            .replace("not", "Not")
        )
        dfs.append(df)
    historico = pd.concat(dfs, ignore_index=True)
    historico.rename(columns={"producto_unificado": "producto"}, inplace=True)
    return historico


def main():
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    historico = cargar_precios_historico()
    historico.to_csv(os.path.join(OUTPUT_DIR, "precios_historico.csv"), index=False)
    print(f"[OK] precios_historico.csv: {len(historico)} filas")

    supermercados = pd.DataFrame(
        {"codigo": SUPERS, "nombre_completo": [SUPER_RENAMES[s] for s in SUPERS]}
    )
    supermercados.to_csv(os.path.join(OUTPUT_DIR, "supermercados.csv"), index=False)
    print(f"[OK] supermercados.csv: {len(supermercados)} filas")


if __name__ == "__main__":
    main()
