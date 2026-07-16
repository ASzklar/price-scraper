import os
import glob
import numpy as np
import pandas as pd
import streamlit as st
from datetime import datetime, timedelta

# -------------------- Configuración de la página --------------------
st.set_page_config(
    page_title="Price Scraper Dashboard",
    layout="wide"
)
st.title("🛒 NotCo, Vegetalex y Felices las Vacas en los principales supermercados:")
st.logo("logo_V.png", size="large")

# -------------------- Constantes --------------------
SUPERS = ['carrefour', 'coope', 'coto', 'dia', 'disco', 'vea']
SUPER_RENAMES = {
    'carrefour': 'Carrefour',
    'coope': 'Cooperativa Obrera',
    'coto': 'Coto',
    'dia': 'Dia',
    'disco': 'Disco',
    'vea': 'Vea'
}

# -------------------- Carga y cache de datos --------------------
@st.cache_data
def load_data(filenames, mtimes=None):
    dfs = []
    for fp in filenames:
        df = pd.read_csv(fp, parse_dates=['fecha'])
        marca = os.path.basename(fp).split('_')[1]
        df['brand'] = marca.replace('felices', 'Felices las Vacas') \
                           .replace('vegetalex', 'Vegetalex') \
                           .replace('not', 'Not')
        dfs.append(df)
    df = pd.concat(dfs, ignore_index=True)
    df.rename(columns={'producto_unificado':'Producto'}, inplace=True)
    return df

file_list = sorted(glob.glob("Data/Cleaned/*.csv"))
# Incluir mtime en la clave de cache para invalidar cuando cambia el contenido
mtimes = tuple(os.path.getmtime(f) for f in file_list)
df = load_data(filenames=tuple(file_list), mtimes=mtimes)

# Obtener la fecha más reciente en el DataFrame
ultima_fecha = df['fecha'].max().strftime("%d-%m-%Y")

# Horario fijo
horario_fijo = "07:10AM"

st.markdown(
    f"<small>Última actualización: {ultima_fecha} {horario_fijo}</small>",
    unsafe_allow_html=True
)

# -------------------- Sidebar --------------------
st.sidebar.header("Filtros")
marcas = ["Todas"] + sorted(df['brand'].unique())
marca_sel = st.sidebar.selectbox("Marca", marcas)
if marca_sel != "Todas":
    df = df[df['brand'] == marca_sel]

# -------------------- Filtro de fecha (solo para la tabla) --------------------
fechas_disponibles = sorted(df['fecha'].unique(), reverse=True)
fecha_sel = st.sidebar.selectbox(
    "Fecha",
    fechas_disponibles,
    index=0,
    format_func=lambda x: x.strftime("%d-%m-%Y")
)
for _ in range(15):
    st.sidebar.write("")

st.sidebar.markdown("---")
st.sidebar.markdown(
    """
    <small>
    👤 Adrian Szklar<br>
    📧 <a href="mailto:szklaradriandatos@gmail.com">szklaradriandatos@gmail.com</a><br>
    🔗 <a href="https://linkedin.com/in/adrian-szklar" target="_blank">LinkedIn</a> · 
    <a href="https://github.com/ASzklar" target="_blank">GitHub</a><br>
    📂 <a href="https://github.com/ASzklar/price-scraper" target="_blank">Repo del proyecto</a>
    </small>
    """,
    unsafe_allow_html=True
)


df_latest = df[df['fecha'] == fecha_sel].copy()

# -------------------- Precio promedio histórico --------------------
df_long_all = df.melt(
    id_vars=['fecha', 'Producto'],
    value_vars=SUPERS,
    var_name='supermercado',
    value_name='precio'
).dropna(subset=['precio'])

avg_hist = (
    df_long_all
    .groupby('Producto')['precio']
    .mean()
    .reset_index(name='avg_precio')
)

# Unir promedio histórico a la tabla de última fecha
df_latest = df_latest.merge(avg_hist, on='Producto')

# -------------------- 1) Tabla dinámica de precios actuales --------------------
st.subheader(f"Precios del {fecha_sel.strftime('%d-%m-%Y')}")

pivot = df_latest.pivot_table(
    index='Producto',
    values=SUPERS,
    aggfunc='first'
)
pivot['Promedio histórico'] = df_latest.groupby('Producto')['avg_precio'].first()
pivot.index.name = "Producto"
pivot = pivot.rename(columns=SUPER_RENAMES)

# Columnas de supermercados únicamente (excluyendo promedio histórico)
cols_supers = list(SUPER_RENAMES.values())
cols_supers_presentes = [col for col in cols_supers if col in pivot.columns]

# st.dataframe no respeta na_rep de Styler.format para celdas nulas (siempre
# muestra "None"), asi que se formatea a texto antes y el resaltado se calcula
# aparte sobre los valores numéricos originales.
def resaltar_fila(fila):
    estilos = pd.Series('', index=fila.index)
    valores = pivot.loc[fila.name, cols_supers_presentes]
    no_nulos = valores.dropna()
    if no_nulos.empty:
        return estilos
    max_val, min_val = no_nulos.max(), no_nulos.min()
    for col in cols_supers_presentes:
        val = valores[col]
        if pd.isna(val):
            continue
        if val == max_val:
            estilos[col] = 'background-color: crimson'
        if val == min_val:
            estilos[col] = 'background-color: forestgreen'
    return estilos

pivot_texto = pivot.map(lambda x: '-' if pd.isna(x) else f'{x:,.2f}')
styled = pivot_texto.style.apply(resaltar_fila, axis=1)

st.dataframe(styled, use_container_width=True)

st.markdown(
    """
    <div style='text-align: right'>
        <span style='color:green; font-weight:bold'>precio más bajo</span> · 
        <span style='color:red; font-weight:bold'>precio más alto</span>
    </div>
    """,
    unsafe_allow_html=True
)

# -------------------- 2) Gráfico de evolución histórica (30 días) --------------------
st.subheader("Evolución en los últimos 30 días por producto")
producto_sel = st.selectbox(
    "Seleccioná un producto:",
    sorted(df['Producto'].unique())
)

ultimo_dia = df['fecha'].max()
df_ultimos_30 = df[df['fecha'] >= (ultimo_dia - timedelta(days=30))]
df_long_30 = df_ultimos_30.melt(
    id_vars=['fecha', 'Producto'],
    value_vars=SUPERS,
    var_name='supermercado',
    value_name='precio'
).dropna(subset=['precio'])

df_prod = df_long_30[df_long_30['Producto'] == producto_sel]

chart_df = df_prod.pivot_table(
    index='fecha',
    columns='supermercado',
    values='precio',
    aggfunc='mean'
)
st.line_chart(chart_df)

# -------------------- 3) Oportunidades de ahorro --------------------
st.subheader("Oportunidades de hoy (con respecto al promedio histórico)")

# Calcular precio mínimo actual y supermercado correspondiente
def min_precio_y_super(row):
    precios = row[SUPERS]
    if precios.isnull().all():
        return pd.Series([np.nan, None])
    min_precio = precios.min()
    super_min = precios.idxmin()
    return pd.Series([min_precio, SUPER_RENAMES[super_min]])

# Usar la última fecha real (independiente del filtro del sidebar)
df_ultimo = df[df['fecha'] == df['fecha'].max()].copy()

# Calcular promedio histórico nuevamente para asegurar consistencia
df_ultimo = df_ultimo.merge(avg_hist, on='Producto')

# Calcular precio mínimo actual y supermercado correspondiente
df_ultimo[['min_precio', 'super_min']] = df_ultimo.apply(min_precio_y_super, axis=1)
df_ultimo['ahorro_pct'] = 1 - (df_ultimo['min_precio'] / df_ultimo['avg_precio'])

# Top 10 productos con mayor porcentaje de ahorro
opp = df_ultimo.sort_values('ahorro_pct', ascending=False).head(5)

cols = st.columns(len(opp))
for i, (_, row) in enumerate(opp.iterrows()):
    with cols[i]:
        st.metric(
            label=row['Producto'],
            value=f"${row['min_precio']:,.0f}",
            delta=f"-{row['ahorro_pct']:.0%}")
        st.caption(row['super_min'])
