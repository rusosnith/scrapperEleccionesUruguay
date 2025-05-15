import time
import pandas as pd
from datetime import datetime
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.chrome.service import Service
import os

def setup_driver():
    """Configurar Chrome driver para el scraping"""
    chrome_options = Options()
    chrome_options.add_argument('--headless')
    chrome_options.add_argument('--no-sandbox')
    chrome_options.add_argument('--disable-dev-shm-usage')
    chrome_options.add_argument('--disable-gpu')
    chrome_options.add_argument('--remote-debugging-port=9222')
    
    service = Service(ChromeDriverManager().install())
    return webdriver.Chrome(service=service, options=chrome_options)

def scrape_election_data():
    """Hacer scraping de los datos de elecciones"""
    driver = setup_driver()
    
    try:
        print("🗳️  Navegando a la página...")
        driver.get("https://eleccionesdepartamentales2025.corteelectoral.gub.uy/ResultadosDepartamentales.htm#")
        
        # Esperar a que la página cargue
        wait = WebDriverWait(driver, 10)
        wait.until(EC.presence_of_element_located((By.ID, "resultadosDepartamental")))
        
        print("📍 Seleccionando Lavalleja...")
        # Ejecutar JavaScript para seleccionar Lavalleja
        driver.execute_script("selectDepto('LAVALLEJA', 'Lavalleja');")
        
        # Esperar a que se actualicen los datos
        time.sleep(3)
        
        print("📊 Extrayendo datos...")
        
        # Crear diccionario para los datos
        data = {
            'timestamp': datetime.now().isoformat()
        }
        
        # Extraer datos de la tabla
        table = driver.find_element(By.ID, "resultadosDepartamental")
        rows = table.find_elements(By.TAG_NAME, "tr")
        
        for row in rows:
            divs = row.find_elements(By.TAG_NAME, "div")
            if len(divs) >= 2:
                label = divs[0].text.strip()
                
                # Buscar el span dentro del segundo div
                spans = divs[1].find_elements(By.TAG_NAME, "span")
                if spans:
                    value = spans[0].text.strip()
                    
                    if "Resultados al:" in label:
                        data['ultimaActualizacion'] = value
                    elif "Circuitos escrutados:" in label:
                        data['circuitosEscrutados'] = value
                    elif "Total de circuitos:" in label:
                        data['totalCircuitos'] = int(value) if value.isdigit() else value
                    elif "Circuitos con observaciones:" in label:
                        data['circuitosConObservaciones'] = int(value) if value.isdigit() else value
                    elif "Total de habilitados:" in label:
                        # Limpiar número (quitar puntos, comas)
                        clean_value = ''.join(filter(str.isdigit, value))
                        data['totalHabilitados'] = int(clean_value) if clean_value else 0
        
        # Extraer datos de partidos
        print("🎯 Extrayendo votos por partido...")
        partidos = driver.find_elements(By.CSS_SELECTOR, ".row.row-xsm.manito")
        
        for partido in partidos:
            # Buscar el nombre del partido
            nombre_elements = partido.find_elements(By.CSS_SELECTOR, ".lema, .lema-sm")
            votos_elements = partido.find_elements(By.CSS_SELECTOR, ".subtotal, .subtotal-sm")
            
            if nombre_elements and votos_elements:
                nombre = nombre_elements[0].text.strip()
                votos_text = votos_elements[0].text.strip()
                
                # Limpiar los votos (quitar puntos, comas)
                clean_votos = ''.join(filter(str.isdigit, votos_text))
                votos = int(clean_votos) if clean_votos else 0
                
                # Limpiar nombre para usar como clave
                nombre_limpio = nombre.replace(' ', '_').replace('ñ', 'n')
                # Quitar caracteres especiales pero mantener letras acentuadas básicas
                nombre_limpio = ''.join(c for c in nombre_limpio if c.isalnum() or c == '_')
                
                data[f'votos_{nombre_limpio}'] = votos
        
        return data
        
    except Exception as e:
        print(f"❌ Error durante el scraping: {e}")
        raise
        
    finally:
        driver.quit()

def save_to_csv(data):
    """Guardar los datos en CSV"""
    filename = 'elecciones_lavalleja.csv'
    
    # Convertir a DataFrame
    df_new = pd.DataFrame([data])
    
    # Verificar si el archivo existe
    if os.path.exists(filename):
        # Leer datos existentes y concatenar
        df_existing = pd.read_csv(filename)
        df_combined = pd.concat([df_existing, df_new], ignore_index=True)
    else:
        df_combined = df_new
    
    # Guardar CSV
    df_combined.to_csv(filename, index=False)
    print(f"✅ Datos guardados en {filename}")
    
    # Mostrar últimos datos guardados
    print("📋 Último registro:")
    print(df_new.to_string(index=False))

def main():
    print("🗳️  Iniciando scraping para Lavalleja...")
    print(f"⏰ {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    try:
        resultado = scrape_election_data()
        save_to_csv(resultado)
        print("✅ Scraping completado exitosamente")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        exit(1)

if __name__ == "__main__":
    main()