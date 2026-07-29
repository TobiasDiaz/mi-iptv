import os
import re
import requests
from github import Github

# Variables de entorno desde GitHub Actions
token = os.environ.get('GH_TOKEN')
repo_name = os.environ.get('REPO_NAME')
spinoff_url = 'https://spinoff.link/listas-iptv-actualizadas-2025/'

headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36'
}

print("Accediendo a spinoff.link...")
res = requests.get(spinoff_url, headers=headers)

if res.status_code != 200:
    print(f"Error al cargar la página. Status: {res.status_code}")
    exit(1)

# 1. Buscar coincidencia directa tecnotv.club/XXXX/
match = re.search(r'tecnotv\.club\/([a-zA-Z0-9]{4})\/', res.text)

# 2. Si la web lo oculta, buscar el atributo data-iptv o enlaces dinámicos
if not match:
    match = re.search(r'\/([a-zA-Z0-9]{4})\/android1\.m3u', res.text)

# 3. Buscar cualquier código de 4 letras alfanumérico asociado a m3u
if not match:
    match = re.search(r'["\']/([a-zA-Z0-9]{4})\/["\']', res.text)

if not match:
    print("No se encontraron las 4 letras en el código fuente de spinoff.link")
    exit(1)

nuevo_codigo = match.group(1)
print(f"¡Código detectado con éxito!: [{nuevo_codigo}]")

# Conectar a GitHub API
g = Github(token)
repo = g.get_repo(repo_name)

# Obtener el archivo M3U actual
file_content = repo.get_contents('lista.m3u')
contenido_viejo = file_content.decoded_content.decode('utf-8')

# Extraer las 4 letras guardadas actualmente en lista.m3u
match_actual = re.search(r'tecnotv\.club\/([a-zA-Z0-9]{4})\/', contenido_viejo)

if match_actual:
    codigo_viejo = match_actual.group(1)
    print(f"Código actual guardado en lista.m3u: [{codigo_viejo}]")
    
    if codigo_viejo != nuevo_codigo:
        print(f"Actualizando lista de [{codigo_viejo}] a [{nuevo_codigo}]...")
        contenido_nuevo = contenido_viejo.replace(f'tecnotv.club/{codigo_viejo}/', f'tecnotv.club/{nuevo_codigo}/')
        
        repo.update_file(
            path=file_content.path,
            message=f"Auto-update código: {nuevo_codigo}",
            content=contenido_nuevo,
            sha=file_content.sha
        )
        print("¡Lista M3U actualizada con éxito en GitHub!")
    else:
        print("El código detectado es igual al guardado. No requiere cambios.")
else:
    print("No se pudo detectar la estructura de 4 letras dentro de tu archivo lista.m3u.")
