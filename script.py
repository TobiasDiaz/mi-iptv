import os
import re
import requests
from html.parser import HTMLParser
from github import Github

token = os.environ.get('GH_TOKEN')
repo_name = os.environ.get('REPO_NAME')

headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8'
}

URL_PAGINA = "https://spinoff.link/listas-iptv-actualizadas-2025/"
nuevo_codigo = None

class JSExtractorParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.js_sources = []

    def handle_starttag(self, tag, attrs):
        if tag == 'script':
            for attr, val in attrs:
                if attr == 'src' and val:
                    self.js_sources.append(val)

def buscar_codigo_en_texto(texto):
    if not texto or not isinstance(texto, str):
        return None
    
    # 1. Buscar coincidencia exacta tecnotv.club/XXXX/android
    m = re.search(r'tecnotv\.club\/([a-zA-Z0-9]{4})\/android', texto, re.IGNORECASE)
    if m: return m.group(1)

    # 2. Buscar patrón general /XXXX/android1.m3u
    m = re.search(r'\/([a-zA-Z0-9]{4})\/android1\.m3u', texto, re.IGNORECASE)
    if m: return m.group(1)

    # 3. Buscar cualquier coincidencia de tecnotv.club/XXXX/
    m = re.search(r'tecnotv\.club\/([a-zA-Z0-9]{4})\/', texto, re.IGNORECASE)
    if m: return m.group(1)

    return None

print(f"=== 1. ANALIZANDO HTML DIRECTO DE {URL_PAGINA} ===")

try:
    res = requests.get(URL_PAGINA, headers=headers, timeout=15)
    if res.status_code == 200:
        html = res.text
        nuevo_codigo = buscar_codigo_en_texto(html)
        
        if nuevo_codigo:
            print(f"¡Código hallado en HTML directo!: [{nuevo_codigo}]")
        else:
            print("No se halló en el HTML estático. Analizando archivos JavaScript de la página...")
            parser = JSExtractorParser()
            parser.feed(html)
            
            # Recorrer todos los JS que carga esa página
            for script_src in parser.js_sources:
                if not script_src.startswith('http'):
                    if script_src.startswith('//'):
                        script_src = "https:" + script_src
                    else:
                        script_src = "https://spinoff.link" + script_src
                
                # Ignorar librerías genéricas para acelerar
                if any(x in script_src for x in ['jquery', 'bootstrap', 'gtag', 'analytics']):
                    continue
                
                try:
                    res_js = requests.get(script_src, headers=headers, timeout=5)
                    if res_js.status_code == 200:
                        nuevo_codigo = buscar_codigo_en_texto(res_js.text)
                        if nuevo_codigo:
                            print(f"¡Código hallado dentro de archivo JS ({script_src})!: [{nuevo_codigo}]")
                            break
                except:
                    pass

except Exception as e:
    print(f"Error consultando la página: {e}")

# Fallback: consultar el endpoint API de la página específica
if not nuevo_codigo:
    print("\n=== 2. CONSULTANDO SLUG ESPECÍFICO EN API DE WORDPRESS ===")
    try:
        url_api = "https://spinoff.link/wp-json/wp/v2/pages?slug=listas-iptv-actualizadas-2025"
        res_api = requests.get(url_api, headers=headers, timeout=10)
        if res_api.status_code == 200 and isinstance(res_api.json(), list) and len(res_api.json()) > 0:
            content = res_api.json()[0].get('content', {}).get('rendered', '')
            nuevo_codigo = buscar_codigo_en_texto(content)
            if nuevo_codigo:
                print(f"¡Código hallado en API por Slug!: [{nuevo_codigo}]")
    except Exception as e:
        print(f"Error en API por slug: {e}")

if not nuevo_codigo:
    print("\n[!] CRÍTICO: No se pudo extraer el código de 4 caracteres.")
    exit(1)

print(f"\n¡CÓDIGO EXTRAÍDO CORRECTAMENTE!: [{nuevo_codigo}]")

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
    print(f"Actualizando lista.m3u con el código: [{nuevo_codigo}]...")
    repo.update_file(
        path=file_content.path,
        message=f"Auto-update código: {nuevo_codigo}",
        content=contenido_nuevo,
        sha=file_content.sha
    )
    print("¡Tu archivo lista.m3u se actualizó con éxito en GitHub!")
else:
    print("El código detectado es idéntico al actual en lista.m3u. Sin cambios.")
