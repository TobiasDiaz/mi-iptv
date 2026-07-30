import os
import re
import requests
from html.parser import HTMLParser
from github import Github

token = os.environ.get('GH_TOKEN')
repo_name = os.environ.get('REPO_NAME')

headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36',
    'Accept': 'text/html,application/json,text/plain,*/*'
}

class SimpleHTMLParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.links = []
        self.scripts = []

    def handle_starttag(self, tag, attrs):
        if tag == 'a':
            for attr, val in attrs:
                if attr == 'href' and val:
                    self.links.append(val)
        elif tag == 'script':
            for attr, val in attrs:
                if attr == 'src' and val:
                    self.scripts.append(val)

nuevo_codigo = None

def extraer_codigo_exacto(texto):
    if not texto or not isinstance(texto, str):
        return None
    
    # 1. Buscar el código de 4 caracteres exactos dentro de cualquier URL con android1.m3u o similar
    # Ejemplo: tecnotv.club/65cg/android1.m3u o /adkodi/65cg/android1.m3u
    m = re.search(r'\/([a-zA-Z0-9]{4})\/android[0-9]*\.m3u', texto, re.IGNORECASE)
    if m and m.group(1).lower() != 'kodi':
        return m.group(1)

    # 2. Buscar 4 caracteres exactos justo después de tecnotv.club/ o adkodi/
    m = re.search(r'(?:tecnotv\.club|adkodi)\/([a-zA-Z0-9]{4})\/', texto, re.IGNORECASE)
    if m and m.group(1).lower() != 'kodi':
        return m.group(1)

    # 3. Buscar 4 caracteres exactos antes de la extensión .m3u
    m = re.search(r'\/([a-zA-Z0-9]{4})\/(?:lista|m3u)', texto, re.IGNORECASE)
    if m and m.group(1).lower() != 'kodi':
        return m.group(1)

    return None

print("=== 1. BUSCANDO EN LA API DE SPINOFF ===")
try:
    res_search = requests.get("https://spinoff.link/wp-json/wp/v2/posts?per_page=10", headers=headers, timeout=15)
    if res_search.status_code == 200 and isinstance(res_search.json(), list):
        for post in res_search.json():
            nuevo_codigo = extraer_codigo_exacto(post.get('content', {}).get('rendered', ''))
            if nuevo_codigo:
                print(f"¡Código de 4 caracteres hallado!: [{nuevo_codigo}]")
                break
except Exception as e:
    print(f"Error en API: {e}")

if not nuevo_codigo:
    print("\n=== 2. ESCANEANDO LA WEB DIRECTA ===")
    try:
        res_web = requests.get("https://spinoff.link/", headers=headers, timeout=15)
        if res_web.status_code == 200:
            parser = SimpleHTMLParser()
            parser.feed(res_web.text)
            
            # Buscar en enlaces HTML de la página
            for link in parser.links:
                nuevo_codigo = extraer_codigo_exacto(link)
                if nuevo_codigo:
                    print(f"¡Código hallado en enlace!: [{nuevo_codigo}]")
                    break

            # Si no está en enlaces, buscar en scripts JS
            if not nuevo_codigo:
                for script_url in parser.scripts[:10]:
                    if not script_url.startswith('http'):
                        script_url = "https://spinoff.link" + script_url
                    try:
                        res_js = requests.get(script_url, headers=headers, timeout=5)
                        if res_js.status_code == 200:
                            nuevo_codigo = extraer_codigo_exacto(res_js.text)
                            if nuevo_codigo:
                                print(f"¡Código hallado en script JS!: [{nuevo_codigo}]")
                                break
                    except:
                        pass
    except Exception as e:
        print(f"Error en web pública: {e}")

if not nuevo_codigo:
    print("\n[!] CRÍTICO: No se pudo extraer el código de 4 caracteres.")
    exit(1)

print(f"\n¡CÓDIGO EXTRAÍDO (4 CARACTERES): [{nuevo_codigo}]")

# === ACTUALIZACIÓN EN GITHUB ===
print("\n=== ACTUALIZANDO ARCHIVO EN GITHUB ===")
g = Github(token)
repo = g.get_repo(repo_name)

file_content = repo.get_contents('lista.m3u')
contenido_viejo = file_content.decoded_content.decode('utf-8')

# Reemplaza ÚNICAMENTE el código de 4 caracteres dentro de tu estructura tecnotv.club/XXXX/
contenido_nuevo = re.sub(
    r'(tecnotv\.club\/)[a-zA-Z0-9]{4}(\/)',
    f'\\1{nuevo_codigo}\\2',
    contenido_viejo
)

if contenido_viejo != contenido_nuevo:
    print(f"Actualizando tu lista.m3u con el código exacto: [{nuevo_codigo}]...")
    repo.update_file(
        path=file_content.path,
        message=f"Auto-update código: {nuevo_codigo}",
        content=contenido_nuevo,
        sha=file_content.sha
    )
    print("¡Tu archivo lista.m3u se actualizó correctamente con los 4 caracteres!")
else:
    print("El código de 4 caracteres en la web es igual al que ya tienes guardado.")
