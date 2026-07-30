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

def extraer_solo_codigo_4(texto):
    if not texto or not isinstance(texto, str):
        return None

    # 1. Buscar código de 4 caracteres exactos antes de /android*.m3u
    # Ejemplo: /65cg/android1.m3u
    m = re.search(r'\/([a-zA-Z0-9]{4})\/android[0-9]*\.m3u', texto, re.IGNORECASE)
    if m:
        cand = m.group(1)
        # Exigir que tenga al menos un número para evitar palabras como 'apps' o 'kodi'
        if re.search(r'\d', cand):
            return cand

    # 2. Buscar 4 caracteres exactos acompañados de tecnotv o adkodi
    # Ejemplo: tecnotv.club/65cg/ o adkodi/65cg/
    m = re.search(r'(?:tecnotv|adkodi)[^\/]*\/([a-zA-Z0-9]{4})\/', texto, re.IGNORECASE)
    if m:
        cand = m.group(1)
        if re.search(r'\d', cand):
            return cand

    # 3. Buscar cualquier coincidencia de 4 caracteres con al menos un número cerca de .m3u
    coincidencias = re.findall(r'\/([a-zA-Z0-9]{4})\/', texto)
    for cand in coincidencias:
        if re.search(r'\d', cand) and '.m3u' in texto:
            return cand

    return None

print("=== BUSCANDO EL CÓDIGO DE 4 CARACTERES EN SPINOFF ===")

# Consultar API de WordPress
try:
    res = requests.get("https://spinoff.link/wp-json/wp/v2/posts?per_page=20", headers=headers, timeout=15)
    if res.status_code == 200 and isinstance(res.json(), list):
        for post in res.json():
            contenido = post.get('content', {}).get('rendered', '')
            nuevo_codigo = extraer_solo_codigo_4(contenido)
            if nuevo_codigo:
                print(f"¡Código de 4 caracteres hallado en API!: [{nuevo_codigo}]")
                break
except Exception as e:
    print(f"Error consultando API: {e}")

# Consultar portada de la web si la API no lo entregó
if not nuevo_codigo:
    try:
        res_web = requests.get("https://spinoff.link/", headers=headers, timeout=15)
        if res_web.status_code == 200:
            nuevo_codigo = extraer_solo_codigo_4(res_web.text)
            if nuevo_codigo:
                print(f"¡Código de 4 caracteres hallado en la web!: [{nuevo_codigo}]")
    except Exception as e:
        print(f"Error consultando web: {e}")

if not nuevo_codigo:
    print("\n[!] CRÍTICO: No se encontró ningún código de 4 caracteres válido.")
    exit(1)

print(f"\n¡CÓDIGO EXTRAÍDO CORRECTAMENTE!: [{nuevo_codigo}]")

# === ACTUALIZACIÓN EN GITHUB ===
print("\n=== ACTUALIZANDO ARCHIVO EN GITHUB ===")
g = Github(token)
repo = g.get_repo(repo_name)

file_content = repo.get_contents('lista.m3u')
contenido_viejo = file_content.decoded_content.decode('utf-8')

# Reemplaza ÚNICAMENTE los 4 caracteres dentro de tu archivo lista.m3u
contenido_nuevo = re.sub(
    r'(tecnotv\.club\/)[a-zA-Z0-9]{4}(\/)',
    f'\\1{nuevo_codigo}\\2',
    contenido_viejo
)

if contenido_viejo != contenido_nuevo:
    print(f"Actualizando lista.m3u con el código: [{nuevo_codigo}]...")
    repo.update_file(
        path=file_content.path,
        message=f"Auto-update código: {nuevo_codigo}",
        content=contenido_nuevo,
        sha=file_content.sha
    )
    print("¡Tu archivo lista.m3u se actualizó con éxito en GitHub!")
else:
    print("El código de 4 caracteres en la web es exactamente el mismo que ya tienes guardado.")
