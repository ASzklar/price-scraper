import pandas as pd
from fuzzywuzzy import fuzz
import numpy as np
import re
import os
from datetime import datetime

pd.set_option('display.max_colwidth', 200)

def parse_price(price):
    if pd.isna(price):
        return np.nan
    
    price_str = str(price)
    price_str = price_str.replace('$', '').replace('.', '').strip()
    price_str = price_str.replace(',', '.')
    
    try:
        return float(price_str)
    except ValueError:
        return np.nan

def unify_products(input_filepath, output_directory, product_column, supermarket_columns, unification_map):
    # Extract brand and date from the input filename
    filename = os.path.basename(input_filepath)
    match = re.match(r'precios_async_(\d{4}-\d{2}-\d{2})_(\w+)\.csv', filename)
    
    if not match:
        print(f"Error: El nombre del archivo de entrada '{filename}' no sigue el formato esperado (precios_async_AAAA-MM-DD_marca.csv).")
        return

    date_str = match.group(1)
    brand = match.group(2)

    if not os.path.exists(input_filepath):
        print(f"Error: El archivo '{input_filepath}' no se encontró en la ruta especificada.")
        return

    df = pd.read_csv(input_filepath)

    # Add 'fecha' column
    df['fecha'] = date_str 

    reverse_unification_map = {}
    for canonical_name, variants in unification_map.items():
        for variant in variants:
            reverse_unification_map[variant] = canonical_name

    df['producto_unificado'] = df[product_column].map(reverse_unification_map).fillna(df[product_column])

    existing_supermarket_cols = [col for col in supermarket_columns if col in df.columns]

    if not existing_supermarket_cols:
        print("Advertencia: No se encontraron columnas de supermercados para procesar precios.")
        print("Asegúrate de que los nombres de las columnas en el CSV ('carrefour', 'coope', etc.)")
        print("coincidan con los definidos en SUPERMARKET_COLUMNS en el script.")
        print("\nNo se realizó la unificación de precios ni el guardado de CSV porque no se encontraron columnas de supermercados.")
        print("Aquí tienes una vista del DataFrame con 'producto_unificado':")
        print(df[[product_column, 'producto_unificado']].head(20).to_string())
    else:
        for col in existing_supermarket_cols:
            df[col] = df[col].apply(parse_price)

        agg_funcs = {
            col: (col, lambda x: x.dropna().iloc[0] if not x.dropna().empty else np.nan)
            for col in existing_supermarket_cols
        }
        
        agg_funcs['fecha'] = ('fecha', lambda x: x.iloc[0]) 
        agg_funcs['producto_representativo'] = (product_column, lambda x: x.iloc[0])

        unified_df = df.groupby('producto_unificado', as_index=False).agg(**agg_funcs)
        unified_df = unified_df[['fecha', 'producto_unificado', 'producto_representativo'] + existing_supermarket_cols]
        
        print("\n--- Vista Previa de Productos Unificados (Primeras 20 Filas) ---")
        print(unified_df.head(20).to_string())

        print(f"\nNúmero total de productos únicos antes de unificar: {df[product_column].nunique()}")
        print(f"Número total de productos unificados: {unified_df['producto_unificado'].nunique()}")
        
        # Create output directory if it doesn't exist
        os.makedirs(output_directory, exist_ok=True)
        
        output_filename = f'productos_{brand}_unificados_{date_str}.csv'
        output_filepath = os.path.join(output_directory, output_filename)
        
        unified_df.to_csv(output_filepath, index=False)
        print(f"\nProceso de unificación completado. Resultados guardados en '{output_filepath}'.")

# --- Unification Maps ---
unification_map_not = {
    'Not Cream Cheese 210g': [
        'Aderezo Not cream cheese 210 g.',
        'Queso Crema Not Cream 210 Gr.',
        'Notcreamcheese 210 Gr',
        'Notcreamcheese The Not Co 210 Gr'
    ],
    'Not Cheese Bastoncitos 300g': [
        'Alimento A Base De Plantas Bastoncitos Not Cheese 300g',
        'Bastoncitos Not Cheese 300 Gr',
        'Bastoncitos Not cheese en bolsa 300 g.'
    ],
    'Not Chicken Mila 220g': [
        'Alimento A Base De Plantas Not Chicken Mila 220g',
        'Milanesas Notco Not Chicken Mila X2 220grs',
        'NotChickenMila 2.0 220 g.',
        'Milanesa Not Chicken Mila 110 Gr X 2 U',
        'Milanesa Notchicken 2.0 Not Mila 110 Gr.'
    ],
    'Not Chicken Nuggets 300g': [
        'Alimento A Base De Plantas Nuggets Not Chiken 300g',
        'Nuggets 300 Gr Not Chicken',
        'Nuggets Not Chicken 300 Gr.',
        'Nuggets Not chicken en bolsa 300 g.',
        'Nuggets Notchicken Notco 0.3kgs'
    ],
    'Not Chicken Relleno Espinaca 240g': [
        'Alimento A Base De Plantas Relleno De Espinaca Not Chiken 240g',
        'Medallon Notchicken Relleno Espinaca Notco 240 Gr.',
        'Medallones Notco Not Chicken Crispy Rellenos Espinaca X2 0.24kgs',
        'Not Chicken Crispy The Not Co Rellena Espinaca 240 Gr',
        'Medallón relleno espinaca Not chicken 240 g.'
    ],
    'Not Chicken Relleno Napolitana 240g': [
        'Alimento A Base De Plantas Relleno Napolitana Not Chiken 240g',
        'Medallones Notco Not Chicken Crispy Rellenas Napolitanas X2 0.24kgs',
        'Not Chicken Crispy The Not Co Rellena Napolitana 240 Gr'
    ],
    'Not Chicken Spicy 250g': [
        'Alimento A Base De Plantas Spicy Not Chicken 250g',
        'Bocadito plant based spicy bites Not Chicken 250 g.',
        'Bocaditos De Pollo Spicy Bites 250 Gr Not Chicken',
        'Formados Notchicken Spicy Bit Con Salsa Tabasco 250grs'
    ],
    'Not Cheese Dambo 140g': [
        'Alimento plant based dambo Not Cheese 140 g.',
        'Notcheese Dambo Notco 140 Gr.',
        'Producto A Base De Aceite Vegetal Notco Not Cheese Sabor Danbo 140grs',
        'Queso Vegano Danbo Not Cheese 140g'
    ],
    'Not Cheese Cheddar 140g': [
        'Cheddar 140 Gr Not Cheese',
        'Notcheese Cheddar Notco 140 Gr.',
        'Queso Cheddar Not Cheese 140 Grm',
        'Queso Cheddar Not Cheese Not Cheese 140 Grm'
    ],
    'Not Chicken Relleno Champis 240g': [
        'Chicken Crispy Rellena Champis X 240 Gr Not Chicken',
        'Medallón relleno champis NotChicken 240 grs',
        'Alimento A Base De Plantas Relleno Champis Not Chicken 240g'
    ],
    'Not Chorixo 240g': [
        'Chorizo Vegano X 240 Gr Not Chorixo',
        'Chorizo a base de planta NotChorixo 240 grs',
        'Notco Not Chorixo X4 240grs',
        'Not Chorixo 240g',
        'Alimento A Base De Plantas Not Chorixo 240g'
    ],
    'Not Ice Cream Chocolate Chip 330g': [
        'Helado Chocolate Chip NOT ICE CREAM 330 Grm',
        'Helado Chocolate Chips 330 Gr Not Icecream',
        'Helado de chocolate chips NotIceCream® 330 g.'
    ],
    'Not Ice Cream Chocolate Chip 100g': [
        'Helado Chocolate Chips 100 Gr Not Icecream',
        'Helado Not ice cream chocolate chips pote 100 g.'
    ],
    'Not Ice Cream Cookies & Cream 330g': [
        'Helado Cookies And Cream 330 Gr Not Icecream',
        'Helado Not ice cookes cream 330 g.',
        'Helado Vegetal Cookies Y Cream Not Ice 330g'
    ],
    'Not Ice Cream Frutillas Crema 330g': [
        'Helado Frutillas Con Crema 330 Gr Not Icecream',
        'Helado de frutillas con crema NotIceCream® 330 g.'
    ],
    'Not Ice Cream Dulce de Leche 330g': [
        'Helado Super Dulce De Leche 330 Gr Not Icecream',
        'Helado Vegetal Super Dulce De Leche Not Ice Cream 330g',
        'NotIce Cream super dulce de leche en pote 330 g.'
    ],
    'Medallon Not chicken burger flow pack x2 80 g.': [
        'Medallon Not chicken burger flow pack x2 80 g.',
        'Not Chicken Burger 2 Un X 80 Gr Not Chicken',
        'Notchicken Burger X2 160grs',
        'Medallón A Base De Vegetales Not Chiken 160g'
    ],
    'Not Chicken Burger Crispy 2x100g': [
        'Burger Crispy 2 Un X 100 Gr Not Chicken',
        'Medallón crispy Not chicken burger flowpack x2 100 g.',
        'Medallón A Base De Plantas Sabor Pollo Not Chiken 200g',
        'Notchicken Burger Crispy X2 200grs'
    ],
    'Medallones Notco Not Burger X2 160grs': [
        'Medallon A Base De Vegetal X2 Not Burger 160g',
        'Medallones Notco Not Burger X2 160grs',
        'Medallón The Not Co Premium Not Burger 160 Gr X 2 U',
        'Medallon Vegetal Not Burger Notco 80 Gr.',
        'Medallón Not burger premium flow pack 2 uni'
    ],
    'Medallon A Base De Vegetal X4 Not Burger 320g': [
        'Medallon A Base De Vegetal X4 Not Burger 320g',
        'Medallones Notco Not Burger Premium X4 320grs',
        'Medallón Not burger premium flow pack 4 uni',
        'Medallón Not Burger Premium 320 Gr X 4 Un Not Co'
    ],
    'Not Burger XL 2x120g (240g)': [
        'Medallon A Base De Vegetal Xl X2 Not Burger 240g',
        'Medallón The Not Co Premium Not Burger 240 Gr X 2 U',
        'Medallón Not burger premium XL flow pack 2 uni',
        'Medallones Notco Not Burger Xl Premium X2 240grs'
    ],
    'Not Burger Parrillera 220g': [
        'Medallones Estilo Parrillera Not Burger 220 Grm',
        'Medallón Not burger parrillera 2 uni',
        'Not Burger Parrillera 220 Gr.',
        'Notburger The Not Co Parrillera 110 Gr',
        'Medallones Notco Burger Estilo Parrillera Congelados X2 110grs'
    ],
    'Not Burguer Quick 2 U De 65 Gr': [
        'Not Burguer Quick 2 U De 65 Gr',
        'Not Burguer Quick Notco 140 Gr.',
        'Medallón Not burger quick flow pack 2 uni',
        'Medallon A Base De Vegetales Not Burger 130g',
        'Medallones Notco Notburger Quick Sabor Carne X2 130grs'
    ],
    'Not Chicken Mila con Semillas 220g': [
        'Notchicken Mila Notco Con Semillas 220grs',
        'Mila con semillas NotChicken 110 grs'
    ],
    'Not Mila con Semillas 220g': [
        'Notmila Notco Con Semillas 220grs',
        'Mila con semillas NotMila 110 grs'
    ],
    'Not Cheese Mozzarella 250g': [
        'Mozzarella 250 Gr Not Cheese',
        'Mozzarella Notcheese 250 g.',
        'NotCheese Mozzarella 250 Gr.',
        'Producto A Base De Plantas Notcheese Sabor Mozzarella 250grs',
        'Queso Vegano Mozzarella Not Cheese 250g'
    ],
    'Not Salxicha 250g': [
        'Salchicha de planta Not Salxicha 5 uni',
        'Salchichas A Base De Plantas Not Salxicha 250g',
        'Notco Not Salxicha X5 250grs',
        'Salchicha de planta Not Salxicha 5 uni'
    ],
    'Not Ice Cream Paleta Chocolate Blanco 4x240g': [
        'Paletas Heladas Chocolate Blanco 4 Un X 240 Gr Not Icecream',
        'Paletas Heladas De Chocolate Blanco Not Icecream 4 X 240 Gr',
        'Paletas heladas de chocolate blanco NotIceCream® 4 x 240 g.'
    ],
    'Not Ice Cream Paleta Crema Americana 4x240g': [
        'Paletas Heladas Crema Americana 4 Un X 240 Gr Not Icecream®',
        'Paletas Heladas De Crema Americana Not Icecream 4 X 240 Gr',
        'Paletas heladas de crema americana NotIceCream® 4 x 240 g.'
    ],
    'Not Ice Cream Paleta Chocolate Crocante 4x240g': [
        'Paletas Heladas De Chocolate Crocante Not Icecream 4 X 240 Gr',
        'Paletas heladas de chocolate crocante NotIceCream® 4 x 240 g.'
    ],
    'Not Ice Cream Tableta Menta 6x300g': [
        'Tabletas Heladas Menta 300 Gr Not Icecream',
        'Tabletas heladas de menta NotIceCream® 6 x 300 g.'
    ],
    'Not Mila 220g': [
        'Alimento A Base De Plantas Not Mila 220g',
        'Milanesa 2.0 Notmila 110 Gr.',
        'NotMila meat 2.0 220 g.',
        'Not Mila 220g',
        'Milanesas Notco Not Mila X2 220grs',
        'Alimento A Base De Plantas Not Mila 220g'
    ],
    'Not Chicken Sticks 300g': [
        'Nuggets Not chicken sticks 300 g.',
        'Nuggets Notco Not Chicken Sticks Con Hierbas Congelados 300grs',
        'Sticks 300 Gr Not Chicken',
        'Crocantes Con Hierbas Not Chiken 300 Grm'
    ]
}

unification_map_vegetalex = {
    'Hot Dogs 100% Vegetal Vegetalex 225g': [
        'Alimento a base de vegetales Vegetalex hot dog x6.',
        'Formados De Vegetales Vegetalex Tipo Hot Dogs X6 225grs',
        'Hot Dogs 100 Vegetal 225 Gr Vegetalex',
        'Hot Dogs De Origen Vegetal Vegetalex 225g',
        'Hot Dogs Vegetalex 100% Vegetal 225 Gr.'
    ],
    'Hamburguesa Vegetal Tradicional Vegetalex 226g': [
        'Burger 100 Vegetal 226 Gr Vegetalex',
        'Burger De Origen Vegetal Vegetalex 226g',
        'Hamburguesa De Soja Vegetalex Tradicional 226 Gr.',
        'Medallones De Vegetales Vegetalex Burger X2 226grs',
        'Medallón de vegetal burguer Vegetalex 2 uni'
    ],
    'Hamburguesa Vegetal Soja Vegetalex 300g': [
        'Hamburguesa Vegetalex Soja 300 Gr',
        'Hamburguesas De Soja Vegetalex X4 300grs',
        'Hamburguesa de soja Vegetalex 4 u.'
    ],
    'Medallones Vegetales Calabaza, Avena y Chía Vegetalex 300g': [
        'Medallones De Calabaza Avena Y Chia Vegetalex 300g',
        'Medallones De Calabaza Vegetalex Con Avena Y Chía X4 300grs',
        'Medallón Calabaza 300 Gr Vegetalex',
        'Medallón Vegetalex Calabaza, Avena y Chía 300 Gr.',
        'Medallón de calabaza avena y chia Vegetalex en caja 4 uni'
    ],
    'Medallones Vegetales Espinaca Vegetalex 300g': [
        'Medallones De Espinaca Vegetalex 300g',
        'Medallones De Espinaca Vegetalex X4 300grs',
        'Medallón Espinaca 300 Gr Vegetalex',
        'Medallón Vegetalex Espinaca 300 Gr.',
        'Medallón de espinaca Vegetalex en caja 4 uni'
    ],
    'Medallones Vegetales Legumbres y Quinoa Vegetalex 300g': [
        'Medallones De Legumbres Y Quinoa Vegetalex 300g',
        'Medallones De Legumbres Y Quinoa Vegetalex X4 300grs',
        'Medallón Legumbres 300 Gr Vegetalex',
        'Medallón de legumbres y quinoa Vegetalex en caja 4 uni'
    ],
    'Medallones Vegetales Verduras Vegetalex 300g': [
        'Medallones De Verduras Vegetalex 300g',
        'Medallones De Verduras Vegetalex X4 300grs',
        'Medallón Verduras 300 Gr Vegetalex',
        'Medallón de verduras Vegetalex en caja 4 uni',
        'Medallones Vegetales VEGETALÉX 4 Uni X 75 Gr Soja'
    ],
    'Milanesa de Soja Vegetalex Tradicional 340g': [
        'Milanesa Vegetalex Tradicional 340 Gr Vegetalex',
        'Milanesa de Soja Vegetalex Tradicional 340 Gr.',
        'Milanesa de soja Vegetalex 4 uni',
        'Milanesas De Soja Tradicional Vegetalex 340g',
        'Milanesas De Soja Vegetalex Tradicionales X4 340grs'
    ],
    'Milanesa de Soja Calabaza Vegetalex 340g': [
        'Milanesa Vegetalex Calabaza 340 Gr Vegetalex',
        'Milanesa de calabaza Vegetalex 4 uni',
        'Milanesas De Soja Con Calabaza Vegetalex 340g',
        'Milanesas De Soja Vegetalex Con Calabaza X4 340grs'
    ],
    'Milanesa de Soja Cebolla Vegetalex 340g': [
        'Milanesa Vegetalex Cebolla 340 Gr Vegetalex',
        'Milanesa de soja y cebolla Vegetalex 4 uni',
        'Milanesas De Soja Con Cebolla Vegetalex 340g',
        'Milanesas De Soja Vegetalex Con Cebolla X4 340grs'
    ],
    'Milanesa de Soja Espinaca Vegetalex 340g': [
        'Milanesa Vegetalex Espinaca 340 Gr Vegetalex',
        'Milanesa de soja y espinaca congelada Vegetalex 4 uni',
        'Milanesas De Soja Con Espinaca Vegetalex 340g',
        'Milanesas De Soja Vegetalex Con Espinaca X4 340grs'
    ],
    'Nuggets 100% Vegetal Vegetalex 300g': [
        'Nuggets 100 Vegetal 300 Gr Vegetalex',
        'Nuggets De Origen Vegetal Vegetalex 300g',
        'Nuggets Vegetalex Origen Vegetal 300grs',
        'Nuggets vegetal Vegetalex 300 g.'
    ],
    'Snack de Arroz con Chocolate Vegetalex 60g': [
        'Snack De Arroz Con Chocolate Vegetalex 60g'
    ],
    'Snack de Arroz Sabor Queso Vegetalex 40g': [
        'Snack De Arroz Sabor Queso Vegetalex 40g'
    ],
    'Snack de Arroz y Quinoa Vegetalex 40g': [
        'Snack De Arroz Y Quinoa Vegetalex 40g'
    ],
}

unification_map_felices_las_vacas = {
    'Alfajor Maicena Felices Las Vacas 60g': [
        'Alfajor Felices Las Vacas de maicena 60 g.',
    ],
    'Alfajor Maní Felices Las Vacas 60g': [
        'Alfajor Felices Las Vacas de maní 60 g.',
    ],
    'Alfajor Chocolate Blanco Felices Las Vacas 60g': [
        'Alfajor de chocolate blancp Felices las Vacas 60 grs',
    ],
    'Alfajor Membrillo Felices Las Vacas 60g': [
        'Alfajor de membrillo Felices las Vacas 60 grs',
    ],
    'Untable Almendras Tipo Cheddar Felices Las Vacas 200g': [
        'Alim Base Alm Unt Felices Las Vacas Cheddar 200g',
        'Alimento A Base De Almendra Untable Cheddar 200 Gr Felices Las Vacas',
    ],
    'Untable Almendras Finas Hierbas Felices Las Vacas 200g': [
        'Alim Base Alm Unt Felices Las Vacas F.hierbas 200g',
        'Untable fantastique finas hierbas Felices las vacas 200 g.',
    ],
    'Untable Almendras Clásico Felices Las Vacas 200g': [
        'Alimento A Base De Almendra Untable Tradicional 200 Gr Felices Las Vacas',
        'Untabla clásico cremoso Felices las vacas 200 g.',
    ],
    'Cremoso Vegano Felices Las Vacas 500g': [
        'Cremoso vegano Felices Las Vacas 500 g.',
        'Producto Vegetal Cremoso Felices Las Vacas Cilindro 500grs',
        'Queso Vegano FELICES LAS VACAS Cremoso Felices 500 Gr',
    ],
    'Dulce de Almendras Colonial Felices Las Vacas 250g': [
        'Dulce de almendras colonial Felices las vacas 250 g.',
        'Untable A Base De Almendras Felices Las Vacas Sabor Dulce De Leche 250grs',
    ],
    'Fetas Veganas Sabor Danbo Felices Las Vacas 200g': [
        'Fetas veganas Felices Las Vacas sabor danbo 200 g.',
        'Queso Vegano Danbo En Fetas Felices Las Vacas 150g',
    ],
    'Hummus Garbanzo Felices Las Vacas 220-230g': [
        'Hummus De Garbanzo Vegano Felices Las Vacas 220grs',
        'Hummus vegano Felices Las Vacas 230 g.'
    ],
    'Hummus Garbanzo Felices Las Vacas con Palta 220g': [
        'Hummus de garbanzo Felices las vacas con palta 220 g.'
    ],
    'Yogur Almendras Neutro Felices Las Vacas 170g': [
        'Jogurtti neutro base de almendras 170 g.',
    ],
    'Yogur Almendras Vainilla Felices Las Vacas 170g': [
        'Jogurtti vainilla base de almendras Felices las vacas 170 g.',
    ],
    'Medallón Arveja Chickenvil Party Felices Las Vacas 2uni': [
        'Medallón de arveja Felices las Vacas chickenvil party 2 uni',
    ],
    'Medallón Arveja Chickenvil Party Felices Las Vacas 4uni': [
        'Medallón de arveja Felices las Vacas chickenvil party 4 uni',
    ],
    'Medallón Arveja Karnevil Party Felices Las Vacas 2uni': [
        'Medallón de arveja Felices las Vacas karnevil party 2 uni',
    ],
    'Medallón Arveja Karnevil Party Felices Las Vacas 4uni': [
        'Medallón de arveja Felices las Vacas karnevil party 4 uni',
    ],
    'Medallón Soja Big Classic Felices Las Vacas 2uni': [
        'Medallón de soja Felices las Vacas big classic 2 uni',
    ],
    'Milanesa Arveja Sabor Carne Felices Las Vacas 2uni': [
        'Milanesa a base de arveja Felices las Vacas sabor carne 2 uni',
    ],
    'Muzzalmendra Vegana Felices Las Vacas 500g': [
        'Muzzalmendra 500 Gr Felices Las Vacas',
        'Muzzalmendra vegana Felices Las Vacas 500 g.',
        'Producto Vegetal A Base De Almendras Felices Las Vacas Sabor Mozzarella 500grs',
        'Queso Vegano FELICES LAS VACAS Mozzarella 500 Gr',
    ],
    'Pasta Vegana Sabor Provolone Felices Las Vacas 250g': [
        'Pasta vegana Felices Las Vacas sabor provolone 250 g.',
        'Producto Vegetal Felices Las Vacas Sabor Provolone 250grs',
        'Queso Vegano FELICES LAS VACAS Provolone 250 Gr',
    ],
    'Postre Plant Based Chocolate Felices Las Vacas 125g': [
        'Postre plant ba de chocolate Felices las Vacas 125 g.',
        'Postrecito Felices Las Vacas Sabor Chocolate 125grs',
    ],
    'Postre Plant Based Dulce de Leche Felices Las Vacas 125g': [
        'Postre plant bas de dulce de leche Felices las Vacas 125 g.',
        'Postrecito Felices Las Vacas Sabor Dulce De Leche 125grs',
    ],
    'Queso Vegano Cheddar Fetas Felices Las Vacas 150g': [
        'Queso Vegano Cheddar En Fetas Felices Las Vacas 150g',
        'Queso cheddar en fetas Felices las Vacas 150 g.',
    ],
    'Queso Vegano Hebras Mix de Quesos Felices Las Vacas 150g': [
        'Queso Vegano En Hebras Mix De Quesos Felices Las Vacas 150g',
    ],
    'Queso Vegano Hebras Reggianito Felices Las Vacas 150g': [
        'Queso Vegano En Hebras Reggianito Felices Las Vacas 150g',
    ],
    'Queso Almendra Oliva Muzzoliva Felices Las Vacas 500g': [
        'Queso Vegano Muzzoliva Felices Las Vacas 500g',
        'Queso de almendra con oliva muzzoliva Felices las Vacas 500 grs',
    ],
    'Yogur Plant Based Frutos Rojos Felices Las Vacas 125g': [
        'Yogur plant bas colchón de frutos rojos Felices las Vacas 125 g.',
    ],
    'Yogur Plant Based Mango Maracuyá Felices Las Vacas 125g': [
        'Yogur plant bas colchón mango y maracuya Felices las Vacas 125 g.',
    ],
}

# --- Main execution ---
import os

PRODUCT_COLUMN = 'producto'
SUPERMARKET_COLUMNS = ['carrefour', 'coope', 'coto', 'dia', 'disco', 'vea']

# Definir rutas multiplataforma
RAW_DATA_PATH     = os.path.join("Data", "Raw")
CLEANED_DATA_PATH = os.path.join("Data", "Cleaned")
USED_DATA_PATH    = os.path.join("Data", "Used")

# Crear directorios si no existen
os.makedirs(RAW_DATA_PATH,     exist_ok=True)
os.makedirs(CLEANED_DATA_PATH, exist_ok=True)
os.makedirs(USED_DATA_PATH,    exist_ok=True)

# Recorrer todos los CSVs en la carpeta Raw
for filename in os.listdir(RAW_DATA_PATH):
    if not (filename.endswith(".csv") and filename.startswith("precios_async_")):
        continue

    input_path = os.path.join(RAW_DATA_PATH, filename)

    # Seleccionar el mapa de unificación según el nombre del archivo
    if "_not.csv" in filename:
        unification_map = unification_map_not
    elif "_felices_las_vacas.csv" in filename:
        unification_map = unification_map_felices_las_vacas
    elif "_vegetalex.csv" in filename:
        unification_map = unification_map_vegetalex
    else:
        print(f"⚠️ No se encontró un 'unification_map' para el archivo: {filename}")
        continue

    try:
        # Ejecutar la función de unificación y guardar en Cleaned
        unify_products(
            input_path,
            CLEANED_DATA_PATH,
            PRODUCT_COLUMN,
            SUPERMARKET_COLUMNS,
            unification_map
        )
        print(f"✅ Unificado: {filename}")

        # Mover el CSV procesado a Used
        dest_path = os.path.join(USED_DATA_PATH, filename)
        os.rename(input_path, dest_path)
        print(f"📦 Archivo movido a Used: {dest_path}")

    except Exception as e:
        print(f"❌ Error procesando {filename}: {e}")
