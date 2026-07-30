import os
import re
from playwright.sync_api import sync_playwright
from github import Github

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
        
        # Cargar página
        page.goto(URL_PAGINA, wait_until="networkidle", timeout=60000)
        
        # Seleccionar específicamente el input de ANDROID 1 usando su atributo data-iptv
        selector_input = 'input[data-iptv="android1.m3u"]'
        
        print("Esperando a que el campo deje de decir 'Cargando...'...")
        
        # Esperar hasta 15 segundos a que el valor del input NO sea "Cargando..." ni esté vacío
        page.wait_for_function(
            f'''() => {{
                const el = document.querySelector('{selector_input}');
                return el && el.value && el.value !== "Cargando..." && el.value.includes("tecnotv.club");
            }}''',
            timeout=15000
        )
        
        # Leer el valor final ya cargado por JavaScript
        valor_final = page.locator(selector_input).input_value()
        print(f"Valor obtenido del cuadro ANDROID 1: [{valor_final}]")
        
        # Extraer los 4 caracteres justo antes de /android1.m3u (ejemplo: 65cg)
        m = re.search(r'tecnotv\.club\/([a-zA-Z0-9]{4})\/android1\.m3u', valor_final, re.IGNORECASE)
        if m:
            nuevo_codigo = m.group(1)
            print(f"¡Código extraído con éxito!: [{nuevo_codigo}]")
        else:
            # Respaldo si la URL varía ligeramente
            m_alt = re.search(r'\/([a-zA-Z0-9]{4})\/', valor_final)
            if m_alt:
                nuevo_codigo = m_alt.group(1)
                print(f"¡Código extraído (patrón alternativo)!: [{nuevo_codigo}]")

        browser.close()

except Exception as e:
    print(f"Error al capturar el enlace dinámico: {e}")

if not nuevo_codigo:
    print("\n[!] CRÍTICO: No se pudo extraer el código de 4 caracteres.")
    exit(1)

print(f"\n¡CÓDIGO EXTRAÍDO Y LISTO!: [{nuevo_codigo}]")

# === ACTUALIZACIÓN EN GITHUB ===
print("\n=== ACTUALIZANDO ARCHIVO EN GITHUB ===")
g = Github(token)
repo = g.get_repo(repo_name)

file_content = repo.get_contents('lista.m3u')
contenido_viejo = file_content.decoded_content.decode('utf-8')

# Reemplaza ÚNICAMENTE los 4 caracteres dentro de tu archivo lista.m3u
contenido_nuevo = re.sub(
    r'(tecnotv\.club\/)[a-zA-Z0-9]{4}(\/)',
    f'\\1{nuevo_codigo}\\2',
    contenido_viejo
)

if contenido_viejo != contenido_nuevo:
    print(f"Actualizando lista.m3u con el código: [{nuevo_codigo}]...")
    repo.update_file(
        path=file_content.path,
        message=f"Auto-update código: {nuevo_codigo}",
        content=contenido_nuevo,
        sha=file_content.sha
    )
    print("¡Tu archivo lista.m3u se actualizó con éxito en GitHub!")
else:
    print("El código detectado es idéntico al guardado. No se requieren cambios.")
