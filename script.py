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

# Parser nativo de HTML para extraer texto y enlaces sin librerías externas
class SimpleHTMLParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.text = []
        self.links = []

    def handle_data(self, data):
        self.text.append(data)

    def handle_starttag(self, tag, attrs):
        if tag == 'a':
            for attr, val in attrs:
                if attr == 'href' and val:
                    self.links.append(val)

nuevo_codigo = None

print("=== 1. CONSULTANDO PUBLICACIÓN BASE EN API REST ===")
url_api = "https://spinoff.link/wp-json/wp/v2/posts/21202"

try:
    res = requests.get(url_api, headers=headers, timeout=15)
    if res.status_code == 200:
        data = res.json()
        html_content = data.get('content', {}).get('rendered', '')
        
        # Extraer texto y enlaces con parser nativo
        parser = SimpleHTMLParser()
        parser.feed(html_content)
        texto_limpio = " ".join(parser.text)
        
        print("\n--- Texto extraído de la entrada 21202 ---")
        print(texto_limpio[:1000])
        print("-------------------------------------------\n")

        print("Enlaces encontrados en la publicación:")
        for href in parser.links:
            print(f" - {href}")
            match = re.search(r'(?:tecnotv|m3u|lista|play|get|file|stream)[^/]*\/([a-zA-Z0-9]{4,8})', href, re.IGNORECASE)
            if match and not nuevo_codigo:
                nuevo_codigo = match.group(1)

        # Si no hay código en enlaces, buscar patrones en el contenido HTML crudo
        if not nuevo_codigo:
            match = re.search(r'tecnotv\.club\/([a-zA-Z0-9]{4,8})\/', html_content, re.IGNORECASE) or \
                    re.search(r'\/([a-zA-Z0-9]{4,8})\/android', html_content, re.IGNORECASE) or \
                    re.search(r'\/([a-zA-Z0-9]{4,8})\/', html_content, re.IGNORECASE)
            if match:
                nuevo_codigo = match.group(1)

except Exception as e:
    print(f"Error durante la consulta a la API: {e}")

# === 2. BÚSQUEDA EN ÚLTIMOS POSTS SI EL POST 21202 FALLÓ ===
if not nuevo_codigo:
    print("\n=== 2. REVISANDO ÚLTIMAS PUBLICACIONES PUBLICADAS ===")
    try:
        res_recientes = requests.get("https://spinoff.link/wp-json/wp/v2/posts?per_page=5", headers=headers, timeout=15)
        if res_recientes.status_code == 200:
            posts = res_recientes.json()
            for p in posts:
                print(f"Analizando Post ID {p.get('id')} - Título: {p.get('title', {}).get('rendered')}")
                contenido = p.get('content', {}).get('rendered', '')
                
                match = re.search(r'tecnotv\.club\/([a-zA-Z0-9]{4,8})\/', contenido, re.IGNORECASE) or \
                        re.search(r'\/([a-zA-Z0-9]{4,8})\/android', contenido, re.IGNORECASE)
                if match:
                    nuevo_codigo = match.group(1)
                    print(f"¡Código hallado en post {p.get('id')}!: [{nuevo_codigo}]")
                    break
    except Exception as e:
        print(f"Error al revisar publicaciones recientes: {e}")

# === 3. RESULTADO DE EXTRACCIÓN ===
if not nuevo_codigo:
    print("\n[!] CRÍTICO: No se detectó ningún código automático.")
    print("Por favor revisa el bloque 'Texto extraído de la entrada 21202' o los 'Enlaces encontrados' impresos arriba.")
    exit(1)

print(f"\n¡CÓDIGO FINAL DETECTADO!: [{nuevo_codigo}]")

# === 4. ACTUALIZACIÓN EN GITHUB ===
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
        print("¡Archivo lista.m3u actualizado exitosamente en GitHub!")
    else:
        print("El código no ha cambiado. No se requieren cambios en GitHub.")
else:
    print("Aviso: No se encontró la estructura tecnotv.club/XXXX/ en tu archivo lista.m3u local.")
