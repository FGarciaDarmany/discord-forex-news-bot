# save_state.py
from playwright.sync_api import sync_playwright

with sync_playwright() as p:
    browser = p.chromium.launch(headless=False)  # Para que VEAS el navegador
    context = browser.new_context()
    page = context.new_page()

    page.goto("https://forecaster.biz")  # Cambia si tu login es otra URL

    input("🔑 Inicia sesión con Google COMPLETO y cuando veas tu panel premium, vuelve aquí y presiona ENTER...")

    context.storage_state(path="forecaster_state.json")
    print("✅ Estado de sesión guardado como forecaster_state.json")

    browser.close()
