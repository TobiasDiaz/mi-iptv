import os
import re
from playwright.sync_api import sync_playwright
from github import Github, Auth

token = os.environ.get('GH_TOKEN')
repo_name = os.environ.get('REPO_NAME')

URL_PAGINA = "https://spinoff.link/listas-iptv-actualizadas-2025/"
nuevo_codigo = None

print(f"=== NAVEGANDO A: {URL_PAGINA} ===")

try:
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36"
        )
        page = context.new_page()
        
        # Cargar página con timeout amplio de red
        page.goto(URL_PAGINA, wait_until="domcontentloaded", timeout=60000)
        
        # Hacer scroll para activar lazy loading o scripts de la web
        page.evaluate("window.scrollTo(0, document.body.scrollHeight / 2);")
        page.wait_for_timeout(3000)
        
        selector_input = 'input[data-iptv="android1.m3u"]'
        
        print("Esperando a que el campo cargue el código real (Timeout ampliado a 45s)...")
        
        try:
            # Ampliado a 60.000 ms (60 segundos)
            page.wait_for_function(
                f'''() => {{
                    const el = document.querySelector('{selector_input}');
                    return el && el.value && el.value !== "Cargando..." && el.value.includes("tecnotv.club");
                }}''',
                timeout=60000
            )
        except Exception as err_wait:
            print(f"Aviso: La espera directa dio tiempo agotado, intentando lectura alternativa... ({err_wait})")

        # Intentar leer el valor final cargado
        try:
            valor_final = page.locator(selector_input).input_value()
            print(f"Valor obtenido del cuadro ANDROID 1: [{valor_final}]")
            
            m = re.search(r'tecnotv\.club\/([a-zA-Z0-9]{4})\/android1\.m3u', valor_final, re.IGNORECASE)
            if m:
                nuevo_codigo = m.group(1)
                print(f"¡Código extraído del input!: [{nuevo_codigo}]")
        except:
            pass

        # Respaldo 1: Buscar en todo el HTML del navegador si el input no se leyó bien
        if not nuevo_codigo:
            content = page.content()
            m = re.search(r'tecnotv\.club\/([a-zA-Z0-9]{4})\/android1\.m3u', content, re.IGNORECASE)
            if m:
                nuevo_codigo = m.group(1)
                print(f"¡Código extraído del HTML del navegador (Respaldo 1)!: [{nuevo_codigo}]")

        # Respaldo 2: Buscar cualquier coincidencia con tecnotv.club/XXXX/
        if not nuevo_codigo:
            content = page.content()
            m = re.search(r'tecnotv\.club\/([a-zA-Z0-9]{4})\/', content, re.IGNORECASE)
            if m:
                nuevo_codigo = m.group(1)
                print(f"¡Código extraído por patrón general (Respaldo 2)!: [{nuevo_codigo}]")

        browser.close()

except Exception as e:
    print(f"Error general durante el raspado: {e}")

if not nuevo_codigo:
    print("\n[!] CRÍTICO: No se pudo extraer el código de 4 caracteres.")
    exit(1)

print(f"\n¡CÓDIGO EXTRAÍDO Y LISTO!: [{nuevo_codigo}]")

# === ACTUALIZACIÓN EN GITHUB ===
print("\n=== ACTUALIZANDO ARCHIVO EN GITHUB ===")

if not token:
    print("[!] ERROR CRÍTICO: El token GH_TOKEN está vacío. Revisa tus Secrets en GitHub.")
    exit(1)

auth = Auth.Token(token)
g = Github(auth=auth)
repo = g.get_repo(repo_name)

file_content = repo.get_contents('lista.m3u')
contenido_viejo = file_content.decoded_content.decode('utf-8')

# Reemplazo seguro mediante Lookbehind
patron_reemplazo = r'(?<=tecnotv\.club\/)[^\/]+'

contenido_nuevo = re.sub(
    patron_reemplazo,
    nuevo_codigo,
    contenido_viejo
)

if contenido_viejo != contenido_nuevo:
    print(f"Actualizando lista.m3u aplicando el nuevo código: [{nuevo_codigo}]...")
    repo.update_file(
        path=file_content.path,
        message=f"Auto-update código: {nuevo_codigo}",
        content=contenido_nuevo,
        sha=file_content.sha
    )
    print("¡Tu archivo lista.m3u se actualizó con éxito en GitHub!")
else:
    print("El código detectado es idéntico al guardado. No se requieren cambios.")
