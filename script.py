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

# ID de la publicación extraído del meta del HTML: 21202
url_api = "https://spinoff.link/wp-json/wp/v2/posts/21202"

try:
    res = requests.get(url_api, headers=headers, timeout=10)
    if res.status_code == 200:
        data = res.json()
        # El contenido completo de la publicación está en data['content']['rendered']
        contenido_html = data.get('content', {}).get('rendered', '')
        
        # 1. Buscar coincidencia tecnotv.club/XXXX/
        match = re.search(r'tecnotv\.club\/([a-zA-Z0-9]{4})\/', contenido_html)
        
        # 2. Si no, buscar la ruta /XXXX/android1.m3u
        if not match:
            match = re.search(r'\/([a-zA-Z0-9]{4})\/android[0-9]*\.m3u', contenido_html)
            
        # 3. Buscar cualquier atributo o enlace de 4 caracteres
        if not match:
            match = re.search(r'["\']/([a-zA-Z0-9]{4})\/["\']', contenido_html)

        if match:
            nuevo_codigo = match.group(1)
            print(f"¡Código detectado exitosamente mediante la API!: [{nuevo_codigo}]")
        else:
            print("No se encontró el patrón dentro del contenido de la API de la publicación 21202.")
            
            # Intento secundario: Buscar en las últimas publicaciones generales
            res_recientes = requests.get("https://spinoff.link/wp-json/wp/v2/posts?per_page=5", headers=headers, timeout=10)
            if res_recientes.status_code == 200:
                texto_global = res_recientes.text
                match_global = re.search(r'tecnotv\.club\/([a-zA-Z0-9]{4})\/', texto_global) or \
                               re.search(r'\/([a-zA-Z0-9]{4})\/android', texto_global)
                if match_global:
                    nuevo_codigo = match_global.group(1)
                    print(f"¡Código detectado en la API global!: [{nuevo_codigo}]")

except Exception as e:
    print(f"Error consultando la API: {e}")

if not nuevo_codigo:
    print("CRÍTICO: No se pudo extraer el código desde la API REST.")
    exit(1)

# --- ACTUALIZACIÓN EN GITHUB ---
g = Github(token)
repo = g.get_repo(repo_name)

file_content = repo.get_contents('lista.m3u')
contenido_viejo = file_content.decoded_content.decode('utf-8')

match_actual = re.search(r'tecnotv\.club\/([a-zA-Z0-9]{4})\/', contenido_viejo)

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
    print("No se encontró el patrón de 4 letras dentro de tu archivo lista.m3u.")
