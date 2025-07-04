# scraper.py
import asyncio
from playwright.async_api import async_playwright
import json
from io import BytesIO

# === CARGA TUS COOKIES ===
def cargar_cookies():
    with open("forecaster_cookies.json", "r", encoding="utf-8") as f:
        cookies = json.load(f)
    return cookies

# === FUNCION: OBTENER PRONOSTICO ===
async def obtener_pronostico(asset: str) -> str:
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context()
        cookies = cargar_cookies()
        await context.add_cookies(cookies)

        page = await context.new_page()
        await page.goto(f"https://forecaster.biz/")  # Asegúrate de ajustar URL base

        # 🟢 Navega al activo
        await page.goto(f"https://forecaster.biz/assets/{asset.lower()}")
        await page.wait_for_timeout(3000)  # Ajusta según tu conexión

        # Extrae texto de la sección clave
        contenido = await page.locator("div:has-text('¿Lo que está sucediendo?')").text_content()

        await browser.close()
        return contenido.strip()

# === FUNCION: OBTENER ESTACIONALIDAD ===
async def obtener_estacionalidad(asset: str) -> BytesIO:
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context()
        cookies = cargar_cookies()
        await context.add_cookies(cookies)

        page = await context.new_page()
        await page.goto(f"https://forecaster.biz/assets/{asset.lower()}/seasonality")
        await page.wait_for_timeout(3000)

        # Encuentra el gráfico y saca captura en memoria
        element = page.locator("div:has-text('Estacionalidad')")
        buffer = BytesIO()
        await element.screenshot(path=buffer)
        buffer.seek(0)

        await browser.close()
        return buffer

# === FUNCION: OBTENER OVERBOUGHT/OVERSOLD ===
async def obtener_obos(asset: str) -> BytesIO:
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context()
        cookies = cargar_cookies()
        await context.add_cookies(cookies)

        page = await context.new_page()
        await page.goto(f"https://forecaster.biz/assets/{asset.lower()}/overbought-oversold")
        await page.wait_for_timeout(3000)

        # Encuentra el gráfico OBOS
        element = page.locator("div:has-text('Overbought/Oversold')")
        buffer = BytesIO()
        await element.screenshot(path=buffer)
        buffer.seek(0)

        await browser.close()
        return buffer
