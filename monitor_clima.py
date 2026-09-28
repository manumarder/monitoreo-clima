"""Monitorea palabras meteorologicas en la pagina de Meteored Corrientes."""

from __future__ import annotations

import argparse
import re
import time
import unicodedata
from collections.abc import Sequence

# Estos valores se usan si no pasamos opciones por la terminal.
DEFAULT_URL = (
    "https://www.meteored.com.ar/tiempo-en_Corrientes-America+Sur-"
    "Argentina-Corrientes-SARC-1-16886.html"
)
DEFAULT_KEYWORDS = ("alerta", "tormenta", "lluvia intensa", "granizo")


def normalize_text(value: str) -> str:
    """Pasa el texto a minusculas y elimina acentos para compararlo."""
    # Por ejemplo, "Lluvia" y "lluvia", o "débil" y "debil", quedan comparables.
    decomposed = unicodedata.normalize("NFKD", value.casefold())
    return "".join(char for char in decomposed if not unicodedata.combining(char))


def find_matches(content: str, keywords: Sequence[str]) -> list[str]:
    """Devuelve las palabras clave que aparecen completas en el reporte."""
    normalized_content = normalize_text(content)
    matches = []
    for keyword in keywords:
        normalized_keyword = normalize_text(keyword.strip())
        if not normalized_keyword:
            continue
        # Escapamos caracteres especiales y permitimos varios espacios en una frase.
        phrase_pattern = re.escape(normalized_keyword).replace(r"\ ", r"\s+")
        # Los limites evitan, por ejemplo, que "lluvia" coincida con "lluvias".
        if re.search(rf"(?<!\w){phrase_pattern}(?!\w)", normalized_content):
            matches.append(keyword.strip())
    return matches


def extract_weather_report(content: str, city: str) -> str | None:
    """Extrae una version breve del estado actual y el pronostico de una ciudad."""
    # re.escape permite insertar el nombre de ciudad dentro de una expresion regular.
    city_pattern = re.escape(city.strip())

    # Busca el bloque superior y lo corta antes de la noticia o del detalle diario.
    current_section = re.search(
        rf"\bTiempo en {city_pattern}\b.*?"
        rf"(?=\bUltima hora\b|\bÚltima hora\b|\bClima en {city_pattern}\s+hoy\b)",
        content,
        flags=re.IGNORECASE | re.DOTALL,
    )

    # Busca el pronostico del dia y evita que se cuele el pronostico de otra ciudad.
    daily_section = re.search(
        rf"\bClima en {city_pattern}\s+hoy\b.*?"
        r"(?=\bClima en [^\r\n]{1,80}\bhoy\b|\bTiempo:\s*PDF\b|"
        r"\bFotoprotecci[oó]n\b|$)",
        content,
        flags=re.IGNORECASE | re.DOTALL,
    )

    sections = []
    if current_section:
        # Aplana saltos del HTML y elimina titulo, hora, dia y datos que se repiten.
        current_text = re.sub(r"\s+", " ", current_section.group(0)).strip()
        current_text = re.sub(
            rf"^Tiempo en {city_pattern}\s*", "", current_text, flags=re.IGNORECASE
        )
        current_text = re.sub(r"\b\d{1,2}:\d{2}\b\s*\|?\s*", "", current_text)
        current_text = re.sub(
            r"\b(lunes|martes|miércoles|miercoles|jueves|viernes|sábado|sabado|domingo)\b",
            "",
            current_text,
            flags=re.IGNORECASE,
        )
        current_text = re.split(r"\bPor horas\b", current_text, maxsplit=1)[0]
        current_text = re.sub(r"\bUV\s+\d+\b.*$", "", current_text).strip(" ,|-·")
        if current_text:
            sections.append(f"Ahora: {current_text}")

    if daily_section:
        daily_text = re.sub(r"\s+", " ", daily_section.group(0)).strip()
        # La primera parte narrativa resume manana, tarde y noche.
        description_match = re.search(
            rf"\bHoy en {city_pattern},.*?(?=\s+(?:[01]?\d|2[0-3]):[0-5]\d\b|$)",
            daily_text,
            flags=re.IGNORECASE,
        )
        if description_match:
            description = description_match.group(0).strip()
            description = re.sub(
                rf"^Hoy en {city_pattern},\s*",
                "",
                description,
                flags=re.IGNORECASE,
            )
            date_match = re.search(
                rf"\bClima en {city_pattern}\s+hoy,\s*(\d{{1,2}}\s+de\s+\w+)",
                daily_text,
                flags=re.IGNORECASE,
            )
            date_label = f" ({date_match.group(1).strip()})" if date_match else ""
            sections.append(f"Hoy{date_label}: {description}")

        hourly_pattern = re.compile(
            r"(?P<time>(?:[01]?\d|2[0-3]):[0-5]\d)\s+"
            r"(?:(?P<precip>\d{1,3}%\s+(?:\d+(?:[.,]\d+)?\s*mm\s+)?)?)?"
            r"(?P<temperature>\d{1,2}°)\s+(?P<details>.*?)"
            r"(?=\s+(?:[01]?\d|2[0-3]):[0-5]\d\s+|$)",
            flags=re.IGNORECASE,
        )
        hourly_rows = []
        # Cada coincidencia representa una hora. Los grupos con nombre separan
        # hora, lluvia, temperatura y resto de datos de esa fila.
        for match in hourly_pattern.finditer(daily_text):
            # Conservamos la condicion y descartamos sensacion, viento e indice UV.
            condition = re.split(
                r"\bSensaci[oó]n\b|\b(?:Norte|Noreste|Noroeste|Sur|Sudeste|"
                r"Sudoeste|Este|Oeste)\b|\bUV\b",
                match.group("details"),
                maxsplit=1,
                flags=re.IGNORECASE,
            )[0].strip(" ,.-")
            if condition:
                precipitation = (match.group("precip") or "").strip()
                row = (
                    f"{match.group('time')} | {match.group('temperature')} | "
                    f"{condition}"
                )
                if precipitation:
                    row += f" | {precipitation.replace('  ', ' ')}"
                hourly_rows.append(row)

        if hourly_rows:
            sections.append("Por hora:\n  " + "\n  ".join(hourly_rows))

    return "\n".join(sections) if sections else None


def parse_args() -> argparse.Namespace:
    # argparse convierte opciones como --interval 30 en atributos de args.interval.
    parser = argparse.ArgumentParser(
        description="Busca avisos meteorologicos en la pagina de Meteored Corrientes."
    )
    parser.add_argument("--url", default=DEFAULT_URL, help="URL que se va a consultar")
    parser.add_argument(
        "--city", default="Corrientes", help="Ciudad cuyo pronostico se monitoriza"
    )
    parser.add_argument(
        "--interval",
        type=int,
        default=20,
        help="Segundos entre consultas (por defecto: 20)",
    )
    parser.add_argument(
        "--keywords",
        nargs="+",
        default=list(DEFAULT_KEYWORDS),
        help="Palabras o frases para buscar",
    )
    parser.add_argument(
        "--headed", action="store_true", help="Muestra la ventana de Chromium"
    )
    parser.add_argument(
        "--once", action="store_true", help="Consulta una sola vez y termina"
    )
    parser.add_argument(
        "--timeout",
        type=int,
        default=30,
        help="Tiempo maximo de carga en segundos (por defecto: 30)",
    )
    args = parser.parse_args()
    if args.interval < 1:
        parser.error("--interval debe ser al menos 1 segundo")
    if args.timeout < 1:
        parser.error("--timeout debe ser al menos 1 segundo")
    return args


def run_monitor(
    url: str,
    city: str,
    interval: int,
    keywords: Sequence[str],
    headed: bool,
    once: bool,
    timeout: int,
) -> None:
    # Importamos Playwright aqui para que las pruebas del parser no necesiten abrir
    # Chromium ni iniciar Playwright.
    from playwright.sync_api import TimeoutError as PlaywrightTimeoutError
    from playwright.sync_api import sync_playwright

    # Guardamos la consulta anterior para informar solo cambios, no repetir alertas.
    previous_report: str | None = None
    previous_matches: frozenset[str] = frozenset()
    # Playwright recibe el timeout en milisegundos; la opcion de consola esta en segundos.
    timeout_ms = timeout * 1000

    # Este bloque administra el inicio y cierre de Playwright aunque ocurra un error.
    with sync_playwright() as playwright:
        # headless=True significa navegador invisible; --headed permite verlo.
        browser = playwright.chromium.launch(headless=not headed)
        page = browser.new_page(locale="es-AR")
        try:
            while True:
                checked_at = time.strftime("%Y-%m-%d %H:%M:%S")
                try:
                    # Primera vuelta: navegar a la URL. Siguientes vueltas: recargarla.
                    if page.url == "about:blank":
                        page.goto(url, wait_until="domcontentloaded", timeout=timeout_ms)
                    else:
                        page.reload(wait_until="domcontentloaded", timeout=timeout_ms)
                    content = page.locator("body").inner_text(timeout=timeout_ms)
                    report = extract_weather_report(content, city)
                    if report is None:
                        print(
                            f"[{checked_at}] No encontre los bloques del pronostico "
                            f"de {city}; se volvera a intentar.",
                            flush=True,
                        )
                    else:
                        matches = frozenset(find_matches(report, keywords))
                        # La diferencia de conjuntos deja solo palabras nuevas.
                        new_matches = matches - previous_matches

                        if previous_report is None:
                            print(f"\nPronostico inicial de {city} [{checked_at}]")
                            print(report, flush=True)
                            if matches:
                                print(
                                    "Terminos a vigilar presentes: "
                                    f"{', '.join(sorted(matches))}",
                                    flush=True,
                                )
                        elif report != previous_report:
                            if new_matches:
                                print(f"\n!!! CAMBIO METEOROLOGICO [{checked_at}] !!!")
                                print(
                                    "Nuevos terminos detectados: "
                                    f"{', '.join(sorted(new_matches))}"
                                )
                            else:
                                print(f"\nCambio en el pronostico de {city} [{checked_at}]")
                            print(report, flush=True)
                        else:
                            print(f"[{checked_at}] Sin cambios en el pronostico de {city}.")

                        previous_report = report
                        previous_matches = matches
                except PlaywrightTimeoutError:
                    print(
                        f"[{checked_at}] La pagina excedio el tiempo de espera; "
                        "se volvera a intentar.",
                        flush=True,
                    )
                except Exception as error:
                    print(
                        f"[{checked_at}] Error al consultar la pagina: {error}",
                        flush=True,
                    )

                if once:
                    break
                # Espera entre consultas; Ctrl+C interrumpe este bucle de forma segura.
                time.sleep(interval)
        except KeyboardInterrupt:
            print("\nMonitor detenido por el usuario.", flush=True)
        finally:
            browser.close()


def main() -> None:
    # Punto de entrada: leer opciones y pasarlas al monitor.
    args = parse_args()
    print(
        f"Monitorizando el pronostico de {args.city} cada {args.interval} segundos. "
        "Ctrl+C para salir."
    )
    run_monitor(
        url=args.url,
        city=args.city,
        interval=args.interval,
        keywords=args.keywords,
        headed=args.headed,
        once=args.once,
        timeout=args.timeout,
    )


# Este chequeo permite importar las funciones desde las pruebas sin arrancar el bot.
if __name__ == "__main__":
    main()