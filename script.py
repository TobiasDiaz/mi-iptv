import os
import re
import requests
from github import Github

# Variables desde GitHub Actions
token = os.environ.get('GH_TOKEN')
repo_name = os.environ.get('REPO_NAME')

headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36'
}

nuevo_codigo = None

print("Consultando la redirección directa del servidor de TecnoTV...")

# Intentamos obtener la dirección directa a la que redirige TecnoTV
urls_prueba = [
    "https://tecnotv.club/android1.m3u",
    "http://tecnotv.club/android1.m3u"
]

for url in urls_prueba:
    try:
        # Hacemos una petición ligera HEAD permitiendo redirecciones
        response = requests.head(url, headers=headers, allow_redirects=True, timeout=10)
        url_final = response.url
        print(f"URL obtenida del servidor: {url_final}")
        
        # Buscamos el patrón de las 4 letras en la URL final (ej: tecnotv.club/65cg/android1.m3u)
        match = re.search(r'tecnotv\.club\/([a-zA-Z0-9]{4})\/', url_final)
        if match:
            nuevo_codigo = match.group(1)
            print(f"¡Código capturado exitosamente!: [{nuevo_codigo}]")
            break
    except Exception as e:
        print(f"Error consultando {url}: {e}")

# Si no devolvió por HEAD, probamos con una petición GET ligera
if not nuevo_codigo:
    try:
        response = requests.get("https://tecnotv.club/android1.m3u", headers=headers, stream=True, timeout=10)
        url_final = response.url
        match = re.search(r'tecnotv\.club\/([a-zA-Z0-9]{4})\/', url_final)
        if match:
            nuevo_codigo = match.group(1)
            print(f"¡Código capturado por GET!: [{nuevo_codigo}]")
    except Exception as e:
        print(f"Error en respaldo GET: {e}")

if not nuevo_codigo:
    print("CRÍTICO: No se pudo obtener el código del servidor.")
    exit(1)

# --- ACTUALIZACIÓN EN GITHUB ---
g = Github(token)
repo = g.get_repo(repo_name)

file_content = repo.get_contents('lista.m3u')
contenido_viejo = file_content.decoded_content.decode('utf-8')

# Extraer el código que tienes actualmente guardado en lista.m3u
match_actual = re.search(r'tecnotv\.club\/([a-zA-Z0-9]{4})\/', contenido_viejo)

if match_actual:
    codigo_viejo = match_actual.group(1)
    print(f"Código guardado actualmente en tu lista.m3u: [{codigo_viejo}]")
    
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
        print("El código obtenido es idéntico al actual. Tu lista ya está al día.")
else:
    print("No se encontró el patrón de 4 letras dentro de tu archivo lista.m3u.")
