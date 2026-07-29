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

    def handle_starttag(self, tag, attrs):
        if tag == 'a':
            for attr, val in attrs:
                if attr == 'href' and val:
                    self.links.append(val)

nuevo_codigo = None

def buscar_en_texto(texto):
    if not texto or not isinstance(texto, str):
        return None
    # 1. Buscar patrón tecnotv.club/XXXX/
    m = re.search(r'tecnotv\.club\/([a-zA-Z0-9]{4,8})\/', texto, re.IGNORECASE)
    if m: return m.group(1)
    
    # 2. Buscar patrón /XXXX/android
    m = re.search(r'\/([a-zA-Z0-9]{4,8})\/android', texto, re.IGNORECASE)
    if m: return m.group(1)
    
    # 3. Buscar cualquier enlace o atributo con 4 letras/números
    m = re.search(r'["\']/([a-zA-Z0-9]{4})\/["\']', texto, re.IGNORECASE)
    if m: return m.group(1)

    return None

print("=== 1. CONSULTANDO PUBLICACIONES RECIENTES EN LA API ===")
try:
    # Solicitamos directamente los posts recientes en lugar del ID 21202 estático
    res = requests.get("https://spinoff.link/wp-json/wp/v2/posts?per_page=10", headers=headers, timeout=15)
    print(f"Estado HTTP API: {res.status_code}")
    
    if res.status_code == 200:
        data = res.json()
        if isinstance(data, list):
            for post in data:
                print(f"-> Analizando post ID {post.get('id')}: {post.get('title', {}).get('rendered', '')}")
                html_content = post.get('content', {}).get('rendered', '')
                
                # Probar extracción sobre el contenido del post
                nuevo_codigo = buscar_en_texto(html_content)
                if nuevo_codigo:
                    print(f"¡Código hallado en post ID {post.get('id')}!: [{nuevo_codigo}]")
                    break
        else:
            print(f"La API no devolvió una lista válida. Respuesta: {str(data)[:200]}")
    else:
        print(f"Respuesta inesperada de la API: {res.text[:200]}")

except Exception as e:
    print(f"Error consultando la API: {e}")

# Intento 2: Scraping directo a la portada HTML si la API falla o está vacía
if not nuevo_codigo:
    print("\n=== 2. INTENTANDO SCRAPING DIRECTO DE LA PORTADA HTML ===")
    try:
        res_web = requests.get("https://spinoff.link/", headers=headers, timeout=15)
        print(f"Estado HTTP Web Directa: {res_web.status_code}")
        if res_web.status_code == 200:
            nuevo_codigo = buscar_en_texto(res_web.text)
            
            # Buscar también dentro de los enlaces <a> de la página
            if not nuevo_codigo:
                parser = SimpleHTMLParser()
                parser.feed(res_web.text)
                for link in parser.links:
                    nuevo_codigo = buscar_en_texto(link)
                    if nuevo_codigo:
                        print(f"¡Código hallado en enlace directo!: [{nuevo_codigo}]")
                        break
    except Exception as e:
        print(f"Error realizando scraping directo: {e}")

# Comprobación final
if not nuevo_codigo:
    print("\n[!] CRÍTICO: No se pudo extraer el código por ningún medio.")
    print("Es posible que la web requiera acceso especial o haya cambiado totalmente el formato.")
    exit(1)

print(f"\n¡CÓDIGO DETECTADO CON ÉXITO!: [{nuevo_codigo}]")

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
        print("El código detectado es idéntico al actual. No se requieren cambios.")
else:
    print("Aviso: No se encontró la estructura tecnotv.club/XXXX/ en tu archivo lista.m3u local.")
