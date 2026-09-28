# Bot de Monitoreo Climático con Playwright 🌦️

Proyecto desarrollado para la materia **Tópicos Avanzados de Ingeniería de Software** (UNNE).

## 🎯 Objetivo
Automatizar el monitoreo de páginas meteorológicas (Meteored) utilizando **Python** y **Playwright** para detectar cambios o alertas climáticas de forma periódica en segundo plano.

## 🛠️ Stack Tecnológico
* Python
* Playwright
* Git / GitHub

## Instalación y uso

Requiere Python 3.10 o superior.

1. Crear y activar un entorno virtual:

	```powershell
	py -m venv .venv
	.\.venv\Scripts\Activate.ps1
	```

	Si PowerShell bloquea la activación, se puede ejecutar el Python del entorno directamente con `.\.venv\Scripts\python.exe`.

2. Instalar Playwright y Chromium:

	```powershell
	python -m pip install -r requirements.txt
	python -m playwright install chromium
	```

3. Iniciar el monitor:

	```powershell
	python monitor_clima.py
	```

Por defecto, consulta la página de Corrientes cada 20 segundos en modo headless. `Ctrl+C` lo detiene. Toma como referencia el resumen de condiciones actuales y el apartado **“Clima en Corrientes hoy”**, incluida la descripción y el pronóstico por horas. La consola muestra un resumen, la descripción del día y filas horarias compactas con condición y temperatura (más precipitación cuando está disponible), omitiendo datos repetidos de viento, sensación térmica y UV en cada hora. Guarda la primera consulta como referencia y avisa cuando cambia el pronóstico; así no confunde una noticia o un anuncio de otra ciudad con el pronóstico local.

### Opciones

```powershell
python monitor_clima.py --interval 30
python monitor_clima.py --headed
python monitor_clima.py --once
python monitor_clima.py --keywords alerta tormenta lluvia granizo
python monitor_clima.py --city "Buenos Aires" --url "URL_DEL_PRONOSTICO"
python monitor_clima.py --url "https://www.meteored.com.ar/"
```

`--headed` muestra la ventana del navegador y `--once` hace una sola consulta, útil para probarlo en clase. Las palabras clave se buscan solo dentro del reporte de la ciudad. El monitor no pulsa el enlace de alertas: ese enlace abre un mapa/noticia y puede referirse a otra zona. Si Meteored cambia los títulos de sus secciones, habrá que actualizar los marcadores de extracción.

> Este prototipo detecta palabras en el texto de la página; no confirma por sí solo que exista una alerta oficial ni reemplaza los avisos del Servicio Meteorológico Nacional.

## Estructura

* `monitor_clima.py`: monitor periódico con Playwright.
* `test_monitor_clima.py`: pruebas unitarias de detección.
* `requirements.txt`: dependencias del proyecto.

Ejecutar las pruebas con `python -m unittest`.