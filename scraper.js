const puppeteer = require('puppeteer');
const fs = require('fs').promises;
const createCsvWriter = require('csv-writer').createObjectCsvWriter;

async function scrapeElectionData() {
  const browser = await puppeteer.launch({
    headless: true,
    args: ['--no-sandbox', '--disable-setuid-sandbox']
  });
  
  try {
    const page = await browser.newPage();
    await page.setUserAgent('Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36');
    
    console.log('Navegando a la página...');
    await page.goto('https://eleccionesdepartamentales2025.corteelectoral.gub.uy/ResultadosDepartamentales.htm#', {
      waitUntil: 'networkidle2',
      timeout: 30000
    });
    
    // Esperar a que la página cargue
    await page.waitForSelector('#resultadosDepartamental', { timeout: 10000 });
    
    console.log('Seleccionando Lavalleja...');
    // Ejecutar selectDepto para Lavalleja
    await page.evaluate(() => {
      selectDepto('LAVALLEJA', 'Lavalleja');
    });
    
    // Esperar a que se actualicen los datos
    await page.waitForTimeout(3000);
    
    // Extraer datos de la tabla
    console.log('Extrayendo datos...');
    const data = await page.evaluate(() => {
      const table = document.querySelector('#resultadosDepartamental');
      if (!table) return null;
      
      const result = {
        timestamp: new Date().toISOString()
      };
      
      const rows = table.querySelectorAll('tr');
      
      for (const row of rows) {
        const cols = row.querySelectorAll('div');
        if (cols.length >= 2) {
          const label = cols[0].textContent.trim();
          const valueSpan = cols[1].querySelector('span');
          
          if (valueSpan) {
            const value = valueSpan.textContent.trim();
            
            if (label.includes('Resultados al:')) {
              result.ultimaActualizacion = value;
            } else if (label.includes('Circuitos escrutados:')) {
              result.circuitosEscrutados = value;
            } else if (label.includes('Total de circuitos:')) {
              result.totalCircuitos = parseInt(value);
            } else if (label.includes('Circuitos con observaciones:')) {
              result.circuitosConObservaciones = parseInt(value);
            } else if (label.includes('Total de habilitados:')) {
              result.totalHabilitados = parseInt(value.replace(/[^\d]/g, ''));
            }
          }
        }
      }
      
      return result;
    });
    
    // Extraer datos de partidos
    const partidos = await page.evaluate(() => {
      const partidosData = {};
      const partidoElements = document.querySelectorAll('.row.row-xsm.manito');
      
      for (const elemento of partidoElements) {
        const nombreElement = elemento.querySelector('.lema, .lema-sm');
        const votosElement = elemento.querySelector('.subtotal, .subtotal-sm');
        
        if (nombreElement && votosElement) {
          const nombre = nombreElement.textContent.trim();
          const votos = parseInt(votosElement.textContent.trim().replace(/[^\d]/g, ''));
          // Limpiar nombre del partido para usar como clave
          const nombreLimpio = nombre.replace(/\s+/g, '_').replace(/[^\w]/g, '');
          partidosData[`votos_${nombreLimpio}`] = votos;
        }
      }
      
      return partidosData;
    });
    
    // Combinar todos los datos
    const resultado = {
      ...data,
      ...partidos
    };
    
    return resultado;
    
  } catch (error) {
    console.error('Error durante el scraping:', error);
    throw error;
  } finally {
    await browser.close();
  }
}

async function saveToCSV(data) {
  const filename = 'elecciones_lavalleja.csv';
  
  // Verificar si el archivo existe
  let fileExists = false;
  try {
    await fs.access(filename);
    fileExists = true;
  } catch (error) {
    // Archivo no existe
  }
  
  // Crear headers dinámicamente basado en los datos
  const headers = Object.keys(data).map(key => ({
    id: key,
    title: key
  }));
  
  const csvWriter = createCsvWriter({
    path: filename,
    header: headers,
    append: fileExists
  });
  
  await csvWriter.writeRecords([data]);
  console.log(`Datos guardados en ${filename}`);
}

async function main() {
  console.log('🗳️  Iniciando scraping para Lavalleja...');
  console.log(`⏰ ${new Date().toLocaleString()}`);
  
  try {
    const resultado = await scrapeElectionData();
    await saveToCSV(resultado);
    
    console.log('✅ Scraping completado exitosamente');
    console.log('📊 Datos extraídos:', resultado);
    
    process.exit(0);
  } catch (error) {
    console.error('❌ Error:', error);
    process.exit(1);
  }
}

main();