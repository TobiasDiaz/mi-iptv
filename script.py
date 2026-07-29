import os
import re
import requests
from github import Github

token = os.environ.get('GH_TOKEN')
repo_name = os.environ.get('REPO_NAME')

headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36',
    'Accept': 'application/json, text/plain, */*'
}

nuevo_codigo = None

print("Consultando la API REST de WordPress en spinoff.link...")

# ID de la publicación base
url_api = "https://spinoff.link/wp-json/wp/v2/posts/21202"

# Expresiones regulares más flexibilizadas para atrapar el token
patrones_regex = [
    r'tecnotv\.club\/([a-zA-Z0-9]{4,6})\/',                      # tecnotv.club/XXXX/
    r'\/([a-zA-Z0-9]{4,6})\/android[0-9]*\.m3u',                # /XXXX/android1.m3u
    r'https?:\/\/[^\/]+\/([a-zA-Z0-9]{4})\/(?:android|lista)',  # http.../XXXX/android
    r'["\']/([a-zA-Z0-9]{4})\/["\']',                           # "/XXXX/"
    r'code\s*[:=]\s*["\']?([a-zA-Z0-9]{4})["\']?'               # code = "XXXX"
]

def buscar_codigo(texto):
    for patron in patrones_regex:
        match = re.search(patron, texto, re.IGNORECASE)
        if match:
            return match.group(1)
    return None

try:
    # Intento 1: Post principal 21202
    res = requests.get(url_api, headers=headers, timeout=10)
    if res.status_code == 200:
        data = res.json()
        contenido_html = data.get('content', {}).get('rendered', '')
        nuevo_codigo = buscar_codigo(contenido_html)
        
        if nuevo_codigo:
            print(f"¡Código detectado exitosamente en post 21202!: [{nuevo_codigo}]")

    # Intento 2: Buscar en los 10 posts más recientes si el post fijo falla
    if not nuevo_codigo:
        print("Buscando en las publicaciones recientes...")
        res_recientes = requests.get("https://spinoff.link/wp-json/wp/v2/posts?per_page=10", headers=headers, timeout=10)
        if res_recientes.status_code == 200:
            posts = res_recientes.json()
            for p in posts:
                html = p.get('content', {}).get('rendered', '')
                nuevo_codigo = buscar_codigo(html)
                if nuevo_codigo:
                    print(f"¡Código detectado en publicación reciente ID {p.get('id')}!: [{nuevo_codigo}]")
                    break

except Exception as e:
    print(f"Error consultando la API: {e}")

# Mensaje de respaldo/diagnóstico si falla completamente
if not nuevo_codigo:
    print("CRÍTICO: No se pudo extraer el código desde la API REST.")
    print("Revisar si la API devolvió contenido o si la web cambió la ruta de la lista.")
    exit(1)

# --- ACTUALIZACIÓN EN GITHUB ---
g = Github(token)
repo = g.get_repo(repo_name)

file_content = repo.get_contents('lista.m3u')
contenido_viejo = file_content.decoded_content.decode('utf-8')

# Buscar código actual en el archivo m3u
match_actual = re.search(r'tecnotv\.club\/([a-zA-Z0-9]{4,6})\/', contenido_viejo)

if match_actual:
    codigo_viejo = match_actual.group(1)
    print(f"Código guardado actualmente en lista.m3u: [{codigo_viejo}]")
    
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
        print("El código detectado es igual al guardado. No requiere cambios.")
else:
    print("No se encontró el patrón anterior dentro de tu archivo lista.m3u.")
