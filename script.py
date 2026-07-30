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

def buscar_en_texto(texto):
    if not texto or not isinstance(texto, str):
        return None
    # 1. Patrón tecnotv.club/XXXX/
    m = re.search(r'tecnotv\.club\/([a-zA-Z0-9]{4,8})\/', texto, re.IGNORECASE)
    if m: return m.group(1)
    
    # 2. Patrón /XXXX/android
    m = re.search(r'\/([a-zA-Z0-9]{4,8})\/android[0-9]*\.m3u', texto, re.IGNORECASE)
    if m: return m.group(1)
    
    # 3. Patrón directo android1.m3u o similar
    m = re.search(r'\/([a-zA-Z0-9]{4,6})\/(?:android|lista|m3u)', texto, re.IGNORECASE)
    if m: return m.group(1)

    return None

print("=== 1. BUSCANDO EN POSTS CON PALABRAS CLAVE (IPTV / LISTA / TECNOTV) ===")
try:
    # Buscar publicaciones que contengan palabras relacionadas con la lista
    res_search = requests.get("https://spinoff.link/wp-json/wp/v2/posts?search=iptv&per_page=10", headers=headers, timeout=15)
    if res_search.status_code == 200 and isinstance(res_search.json(), list):
        for post in res_search.json():
            print(f"-> Encontrado post de búsqueda: {post.get('title', {}).get('rendered')}")
            nuevo_codigo = buscar_en_texto(post.get('content', {}).get('rendered', ''))
            if nuevo_codigo:
                print(f"¡Código hallado por búsqueda!: [{nuevo_codigo}]")
                break
except Exception as e:
    print(f"Error en búsqueda API: {e}")

if not nuevo_codigo:
    print("\n=== 2. ESCANEANDO TODAS LAS PÁGINAS Y CATEGORÍAS DE LA API ===")
    try:
        # Intentar obtener las páginas de WordPress (pages en vez de posts)
        res_pages = requests.get("https://spinoff.link/wp-json/wp/v2/pages?per_page=20", headers=headers, timeout=15)
        if res_pages.status_code == 200 and isinstance(res_pages.json(), list):
            for page in res_pages.json():
                print(f"-> Analizando Página ID {page.get('id')}: {page.get('title', {}).get('rendered')}")
                nuevo_codigo = buscar_en_texto(page.get('content', {}).get('rendered', ''))
                if nuevo_codigo:
                    print(f"¡Código hallado en Página {page.get('id')}!: [{nuevo_codigo}]")
                    break
    except Exception as e:
        print(f"Error al revisar páginas: {e}")

if not nuevo_codigo:
    print("\n=== 3. SCRAPING AVANZADO EN LA WEB PÚBLICA ===")
    try:
        res_web = requests.get("https://spinoff.link/", headers=headers, timeout=15)
        if res_web.status_code == 200:
            parser = SimpleHTMLParser()
            parser.feed(res_web.text)
            
            # Buscar en todos los enlaces encontrados en la web
            for link in parser.links:
                nuevo_codigo = buscar_en_texto(link)
                if nuevo_codigo:
                    print(f"¡Código hallado en enlace público!: [{nuevo_codigo}]")
                    break

            # Buscar dentro de los scripts JS cargados en el sitio
            if not nuevo_codigo:
                print("Escaneando archivos JavaScript de la portada...")
                for script_url in parser.scripts[:10]:
                    if not script_url.startswith('http'):
                        script_url = "https://spinoff.link" + script_url
                    try:
                        res_js = requests.get(script_url, headers=headers, timeout=5)
                        if res_js.status_code == 200:
                            nuevo_codigo = buscar_en_texto(res_js.text)
                            if nuevo_codigo:
                                print(f"¡Código hallado dentro de JS ({script_url})!: [{nuevo_codigo}]")
                                break
                    except:
                        pass
    except Exception as e:
        print(f"Error en scraping avanzado: {e}")

if not nuevo_codigo:
    print("\n[!] CRÍTICO: No se encontró ningún código de la lista.")
    print("Revisa si el sitio spinoff.link cambió la URL o eliminó la sección de la lista.")
    exit(1)

print(f"\n¡CÓDIGO FINAL DETECTADO!: [{nuevo_codigo}]")

# === ACTUALIZACIÓN EN GITHUB ===
print("\n=== ACTUALIZANDO ARCHIVO EN GITHUB ===")
g = Github(token)
repo = g.get_repo(repo_name)

file_content = repo.get_contents('lista.m3u')
contenido_viejo = file_content.decoded_content.decode('utf-8')

match_actual = re.search(r'tecnotv\.club\/([a-zA-Z0-9]{4,8})\/', contenido_viejo)

if match_actual:
    codigo_viejo = match_actual.group(1)
    print(f"Código guardado en lista.m3u: [{codigo_viejo}]")
    
    if codigo_viejo != nuevo_codigo:
        print(f"Actualizando lista de [{codigo_viejo}] a [{nuevo_codigo}]...")
        contenido_nuevo = contenido_viejo.replace(f'tecnotv.club/{codigo_viejo}/', f'tecnotv.club/{nuevo_codigo}/')
        
        repo.update_file(
            path=file_content.path,
            message=f"Auto-update código: {nuevo_codigo}",
            content=contenido_nuevo,
            sha=file_content.sha
        )
        print("¡Tu archivo lista.m3u se actualizó con éxito en GitHub!")
    else:
        print("El código detectado es idéntico al actual. Sin cambios.")
else:
    print("Aviso: No se encontró la estructura tecnotv.club/XXXX/ en tu archivo lista.m3u local.")
