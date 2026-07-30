import os
import re
from playwright.sync_api import sync_playwright
from github import Github

token = os.environ.get('GH_TOKEN')
repo_name = os.environ.get('REPO_NAME')

URL_PAGINA = "https://spinoff.link/listas-iptv-actualizadas-2025/"
nuevo_codigo = None

print(f"=== ABRIENDO NAVEGADOR Y NAVEGANDO A: {URL_PAGINA} ===")

try:
    with sync_playwright() as p:
        # Abrir un navegador Chromium invisible pero idéntico a un usuario real
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36"
        )
        page = context.new_page()
        
        # Cargar la página y esperar a que el JavaScript genere el contenido
        page.goto(URL_PAGINA, wait_until="networkidle", timeout=60000)
        
        # Obtener el contenido completo de la página ya renderizada por JavaScript
        content = page.content()
        
        # 1. Buscar coincidencia exacta tecnotv.club/XXXX/android
        m = re.search(r'tecnotv\.club\/([a-zA-Z0-9]{4})\/android', content, re.IGNORECASE)
        if m:
            nuevo_codigo = m.group(1)
            print(f"¡Código hallado en el render del navegador!: [{nuevo_codigo}]")
            
        # 2. Si no coincide exactamente, buscar en cualquier caja de texto que diga /android1.m3u
        if not nuevo_codigo:
            m = re.search(r'\/([a-zA-Z0-9]{4})\/android1\.m3u', content, re.IGNORECASE)
            if m:
                nuevo_codigo = m.group(1)
                print(f"¡Código hallado con patrón alternativo!: [{nuevo_codigo}]")

        browser.close()

except Exception as e:
    print(f"Error al ejecutar el navegador: {e}")

if not nuevo_codigo:
    print("\n[!] CRÍTICO: No se pudo extraer el código de 4 caracteres.")
    exit(1)

print(f"\n¡CÓDIGO FINAL DETECTADO!: [{nuevo_codigo}]")

# === ACTUALIZACIÓN EN GITHUB ===
print("\n=== ACTUALIZANDO ARCHIVO EN GITHUB ===")
g = Github(token)
repo = g.get_repo(repo_name)

file_content = repo.get_contents('lista.m3u')
contenido_viejo = file_content.decoded_content.decode('utf-8')

contenido_nuevo = re.sub(
    r'(tecnotv\.club\/)[a-zA-Z0-9]{4}(\/)',
    f'\\1{nuevo_codigo}\\2',
    contenido_viejo
)

if contenido_viejo != contenido_nuevo:
    print(f"Actualizando lista.m3u con el nuevo código: [{nuevo_codigo}]...")
    repo.update_file(
        path=file_content.path,
        message=f"Auto-update código: {nuevo_codigo}",
        content=contenido_nuevo,
        sha=file_content.sha
    )
    print("¡Tu archivo lista.m3u se actualizó con éxito en GitHub!")
else:
    print("El código detectado es idéntico al que ya está guardado en lista.m3u.")
