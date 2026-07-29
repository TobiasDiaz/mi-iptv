import os
import re
import requests
from github import Github

# Variables de entorno enviadas desde el Workflow
token = os.environ['GH_TOKEN']
repo_name = os.environ['REPO_NAME']
spinoff_url = 'https://spinoff.link/listas-iptv-actualizadas-2025/'

headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36'
}

print("Accediendo a spinoff.link...")
res = requests.get(spinoff_url, headers=headers)

if res.status_code != 200:
    print(f"Error al cargar la pagina. Status: {res.status_code}")
    exit(1)

# Buscar cualquier mención de 4 caracteres alfanuméricos seguidos de tecnotv o enlaces directos
match = re.search(r'tecnotv\.club\/([a-zA-Z0-9]{4})\/', res.text)

# Si la web oculta la URL base y solo deja rastros del patrón de 4 letras en scripts JS:
if not match:
    match = re.search(r'\/([a-zA-Z0-9]{4})\/android1\.m3u', res.text)

if not match:
    # Buscar patrones alternativos que contengan la estructura /xxxx/
    match = re.search(r'["\']/([a-zA-Z0-9]{4})\/["\']', res.text)

if not match:
    print("No se encontraron las 4 letras en el codigo fuente de spinoff.link")
    exit(1)

nuevo_codigo = match.group(1)
print(f"¡Codigo detectado con exito!: [{nuevo_codigo}]")

# Conectar a GitHub API
g = Github(token)
repo = g.get_repo(repo_name)

# Obtener el archivo M3U actual
file_content = repo.get_contents('lista.m3u')
contenido_viejo = file_content.decoded_content.decode('utf-8')

# Extraer las 4 letras viejas almacenadas actualmente en tu lista.m3u
match_actual = re.search(r'tecnotv\.club\/([a-zA-Z0-9]{4})\/', contenido_viejo)

if match_actual:
    codigo_viejo = match_actual.group(1)
    print(f"Codigo actual guardado en lista.m3u: [{codigo_viejo}]")
    
    if codigo_viejo != nuevo_codigo:
        print(f"Actualizando lista de [{codigo_viejo}] a [{nuevo_codigo}]...")
        contenido_nuevo = contenido_viejo.replace(f'tecnotv.club/{codigo_viejo}/', f'tecnotv.club/{nuevo_codigo}/')
        
        repo.update_file(
            path=file_content.path,
            message=f"Auto-update codigo: {nuevo_codigo}",
            content=contenido_nuevo,
            sha=file_content.sha
        )
        print("¡Lista M3U actualizada con exito en GitHub!")
    else:
        print("El codigo detectado es igual al que ya esta guardado. No requiere cambios.")
else:
    print("No se pudo detectar la estructura de 4 letras dentro de tu archivo lista.m3u.")import os
import re
import requests
from github import Github

# Variables de entorno enviadas desde el Workflow
token = os.environ['GH_TOKEN']
repo_name = os.environ['REPO_NAME']
spinoff_url = 'https://spinoff.link/listas-iptv-actualizadas-2025/'

headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36'
}

print("Accediendo a spinoff.link...")
res = requests.get(spinoff_url, headers=headers)

if res.status_code != 200:
    print(f"Error al cargar la pagina. Status: {res.status_code}")
    exit(1)

# Buscar cualquier mención de 4 caracteres alfanuméricos seguidos de tecnotv o enlaces directos
match = re.search(r'tecnotv\.club\/([a-zA-Z0-9]{4})\/', res.text)

# Si la web oculta la URL base y solo deja rastros del patrón de 4 letras en scripts JS:
if not match:
    match = re.search(r'\/([a-zA-Z0-9]{4})\/android1\.m3u', res.text)

if not match:
    # Buscar patrones alternativos que contengan la estructura /xxxx/
    match = re.search(r'["\']/([a-zA-Z0-9]{4})\/["\']', res.text)

if not match:
    print("No se encontraron las 4 letras en el codigo fuente de spinoff.link")
    exit(1)

nuevo_codigo = match.group(1)
print(f"¡Codigo detectado con exito!: [{nuevo_codigo}]")

# Conectar a GitHub API
g = Github(token)
repo = g.get_repo(repo_name)

# Obtener el archivo M3U actual
file_content = repo.get_contents('lista.m3u')
contenido_viejo = file_content.decoded_content.decode('utf-8')

# Extraer las 4 letras viejas almacenadas actualmente en tu lista.m3u
match_actual = re.search(r'tecnotv\.club\/([a-zA-Z0-9]{4})\/', contenido_viejo)

if match_actual:
    codigo_viejo = match_actual.group(1)
    print(f"Codigo actual guardado en lista.m3u: [{codigo_viejo}]")
    
    if codigo_viejo != nuevo_codigo:
        print(f"Actualizando lista de [{codigo_viejo}] a [{nuevo_codigo}]...")
        contenido_nuevo = contenido_viejo.replace(f'tecnotv.club/{codigo_viejo}/', f'tecnotv.club/{nuevo_codigo}/')
        
        repo.update_file(
            path=file_content.path,
            message=f"Auto-update codigo: {nuevo_codigo}",
            content=contenido_nuevo,
            sha=file_content.sha
        )
        print("¡Lista M3U actualizada con exito en GitHub!")
    else:
        print("El codigo detectado es igual al que ya esta guardado. No requiere cambios.")
else:
    print("No se pudo detectar la estructura de 4 letras dentro de tu archivo lista.m3u.")
