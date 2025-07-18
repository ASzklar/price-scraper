# 🛒 Capturador automático de precios

Se trata de una aplicación que automatiza la extracción, procesamiento y visualización de precios de productos veganos de 3 marcas líderes (NotCo, Vegetalex y Felices las Vacas) en 6 de los principales supermercados de Argentina.  
Su objetivo es brindar **transparencia frente a la dispersión de precios**, detectar **oportunidades de ahorro** y permitir un análisis **rápido e interactivo**.

---

## 📊 Características principales

- 🧾 **Scraping automatizado** de sitios de supermercados  
- 🧹 **Unificación y limpieza de datos históricos**  
- 📈 **Dashboard interactivo** desarrollado con Streamlit  
- 🔎 **Gráficos de evolución** y **tabla dinámica** con resaltado de precios mínimos y máximos  
- 🎯 **Filtros por marca y fecha** para análisis específicos  
- 💸 **Tarjetas de oportunidades** que muestran el supermercado con el precio más bajo disponible

---

## 🏗 Arquitectura y stack tecnológico

### 🕸 Scraping
- **Python 3.9+**
- `Playwright` para navegación y extracción automatizada
- `GitHub Actions` para ejecución periódica con `cron`

### 🧪 Procesamiento de datos
- `pandas` para limpieza, transformación y consolidación de datos
- `FuzzyWuzzy` para normalización de nombres de productos
- `glob` y `os` para manejo de archivos

### 📊 Visualización
- `Streamlit` para la interfaz web interactiva
- `DataFrame Styler` para formato de tablas con resaltado de precios
- Gráficos generados con pandas y componentes nativos de Streamlit

### ⚙️ CI/CD y despliegue
- `GitHub Actions` para orquestar scraping, procesamiento y actualización
- Hosting en `Streamlit Cloud` (o alternativamente en `Heroku`) con despliegue automático

---

## 📂 Estructura del repositorio

Data/
├── Raw/ # Archivos brutos descargados del scraping
└── Cleaned/ # CSVs listos para usar en el dashboard

scrape_all_async_v2.py # Script principal de scraping
unify_product_names.py # Normalización de nombres con FuzzyWuzzy
dashboard.py # App principal en Streamlit
requirements.txt # Dependencias
.github/workflows/ # Jobs de CI/CD para scraping y despliegue

yaml
Copiar
Editar

---

## 🚀 Guía rápida de instalación y uso

### 1. Clonar el repositorio
```bash
git clone https://github.com/ASzklar/price-scraper.git
cd price-scraper
2. Crear entorno virtual e instalar dependencias
bash
Copiar
Editar
python -m venv .venv
source .venv/bin/activate        # macOS/Linux
# .venv\Scripts\activate         # Windows

pip install --upgrade pip
pip install -r requirements.txt
python -m playwright install --with-deps
3. Ejecutar scraping y procesamiento
bash
Copiar
Editar
python scrape_all_async_v2.py
python unify_product_names.py
4. Iniciar el dashboard localmente
bash
Copiar
Editar
streamlit run dashboard.py
👉 Luego abrí tu navegador en: http://localhost:8501

📈 Contexto: Dispersión de precios en Argentina
En el mercado argentino, los precios de alimentos pueden variar hasta un 30–40 % entre supermercados para un mismo producto. Factores como ubicación, stock o promociones hacen difícil saber cuál es realmente la mejor oferta.

Este proyecto permite visualizar cómo cambian los precios a lo largo del tiempo y entre cadenas, facilitando la comparación y ayudando a los consumidores a tomar mejores decisiones.

🤝 Cómo contribuir
Hacé fork del repositorio

Creá una rama: git checkout -b feature/nueva-caracteristica

Commit de tus cambios: git commit -m "Agrega X"

Push a tu fork: git push origin feature/nueva-caracteristica

Abrí un Pull Request describiendo tu aporte

📄 Licencia
Este proyecto está bajo licencia MIT. Para más detalles, consultá el archivo LICENSE.
