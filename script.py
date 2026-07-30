import os
import re
import requests
from github import Github

token = os.environ.get('GH_TOKEN')
repo_name = os.environ.get('REPO_NAME')

headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36',
    'Accept': 'text/html,application/json,text/plain,*/*'
}

nuevo_codigo = None

def extraer_token_real(texto):
    if not texto or not isinstance(texto, str):
        return None

    # 1. Buscar la ruta exacta tipo: adkodi/65cg/ o /adkodi/65cg
    # Ignora la palabra 'adkodi' y extrae el grupo de 4 a 6 caracteres alfanuméricos
    m = re.search(r'adkodi\/([a-zA-Z0-9]{4,6})(?:\/|$)', texto, re.IGNORECASE)
    if m and m.group(1).lower() != 'adkodi':
        return m.group(1)

    # 2. Buscar si el token de 4 caracteres está antes de adkodi: /65cg/adkodi/
    m = re.search(r'\/([a-zA-Z0-9]{4,6})\/adkodi', texto, re.IGNORECASE)
    if m and m.group(1).lower() != 'adkodi':
        return m.group(1)

    # 3. Buscar patrones tipo tecnotv.club/65cg/ o similar
    m = re.search(r'tecnotv\.club\/([a-zA-Z0-9]{4,6})\/', texto, re.IGNORECASE)
    if m and m.group(1).lower() != 'adkodi':
        return m.group(1)

    return None

print("=== BUSCANDO EL TOKEN DINÁMICO (EJEMPLO: 65cg) ===")

try:
    # 1. Probar consultando la API de publicaciones
    res = requests.get("https://spinoff.link/wp-json/wp/v2/posts?per_page=10", headers=headers, timeout=15)
    if res.status_code == 200 and isinstance(res.json(), list):
        for post in res.json():
            contenido = post.get('content', {}).get('rendered', '')
            nuevo_codigo = extraer_token_real(contenido)
            if nuevo_codigo:
                print(f"¡Token hallado en post ID {post.get('id')}!: [{nuevo_codigo}]")
                break

    # 2. Si no se encuentra en la API, revisar la web pública
    if not nuevo_codigo:
        res_web = requests.get("https://spinoff.link/", headers=headers, timeout=15)
        if res_web.status_code == 200:
            nuevo_codigo = extraer_token_real(res_web.text)
            if nuevo_codigo:
                print(f"¡Token hallado en la web directa!: [{nuevo_codigo}]")

except Exception as e:
    print(f"Error durante la búsqueda: {e}")

if not nuevo_codigo:
    print("\n[!] ERROR CRÍTICO: No se pudo extraer el token dinámico de 4 caracteres.")
    exit(1)

print(f"\n¡CÓDIGO EXTRAÍDO CORRECTAMENTE!: [{nuevo_codigo}]")

# === ACTUALIZACIÓN EN GITHUB ===
print("\n=== ACTUALIZANDO ARCHIVO EN GITHUB ===")
g = Github(token)
repo = g.get_repo(repo_name)

file_content = repo.get_contents('lista.m3u')
contenido_viejo = file_content.decoded_content.decode('utf-8')

# Reemplazar tokens antiguos de 4 a 6 caracteres por el nuevo extraído
# Mantiene la estructura de URL requerida para la TV
contenido_nuevo = re.sub(
    r'(tecnotv\.club\/)[a-zA-Z0-9]{4,6}(\/)',
    f'\\1{nuevo_codigo}\\2',
    contenido_viejo
)

# Si la lista usa subdominio adkodi en lugar de tecnotv, ajustamos ambas posibilidades:
contenido_nuevo = re.sub(
    r'(adkodi\/)[a-zA-Z0-9]{4,6}(\/)',
    f'\\1{nuevo_codigo}\\2',
    contenido_nuevo
)

if contenido_viejo != contenido_nuevo:
    print(f"Aplicando cambios con el nuevo token: [{nuevo_codigo}]...")
    repo.update_file(
        path=file_content.path,
        message=f"Auto-update token: {nuevo_codigo}",
        content=contenido_nuevo,
        sha=file_content.sha
    )
    print("¡Tu lista.m3u fue actualizada exitosamente!")
else:
    print("El archivo ya tiene el token actualizado. No se requieren cambios.")
