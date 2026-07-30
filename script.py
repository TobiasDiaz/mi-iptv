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

def extraer_codigo_4_caracteres(texto):
    if not texto or not isinstance(texto, str):
        return None

    # Exclusiones conocidas que NO son códigos
    ignorar = {'kodi', 'html', 'json', 'page', 'post', 'main', 'm3u8', 'home'}

    # 1. Buscar código de 4 caracteres antes de .m3u (ejemplo: /65cg/android1.m3u o /65cg.m3u)
    coincidencias = re.findall(r'\/([a-zA-Z0-9]{4})\/(?:android|lista|[a-zA-Z0-9_-]+\.m3u)', texto, re.IGNORECASE)
    for c in coincidencias:
        if c.lower() not in ignorar:
            return c

    # 2. Buscar 4 caracteres acompañados de tecnotv o adkodi (ejemplo: tecnotv.club/65cg/ o adkodi/65cg/)
    coincidencias = re.findall(r'(?:tecnotv|adkodi)[^\/]*\/([a-zA-Z0-9]{4})\/', texto, re.IGNORECASE)
    for c in coincidencias:
        if c.lower() not in ignorar:
            return c

    # 3. Buscar estructura tipo /65cg/ en cualquier enlace que contenga .m3u
    coincidencias = re.findall(r'\/([a-zA-Z0-9]{4})\/', texto)
    for c in coincidencias:
        if c.lower() not in ignorar and '.m3u' in texto:
            return c

    return None

print("=== 1. BUSCANDO EN POSTS Y PÁGINAS RECIENTES DE LA API ===")
urls_api = [
    "https://spinoff.link/wp-json/wp/v2/posts?per_page=20",
    "https://spinoff.link/wp-json/wp/v2/pages?per_page=20",
    "https://spinoff.link/wp-json/wp/v2/posts?search=iptv",
    "https://spinoff.link/wp-json/wp/v2/posts?search=tecnotv"
]

for url in urls_api:
    try:
        res = requests.get(url, headers=headers, timeout=10)
        if res.status_code == 200:
            datos = res.json()
            if isinstance(datos, list):
                for item in datos:
                    # Buscar en el contenido renderizado
                    contenido = item.get('content', {}).get('rendered', '')
                    nuevo_codigo = extraer_codigo_4_caracteres(contenido)
                    if nuevo_codigo:
                        print(f"¡Código de 4 caracteres hallado en API ({url})!: [{nuevo_codigo}]")
                        break
                    
                    # Buscar en el extracto (excerpt)
                    excerpt = item.get('excerpt', {}).get('rendered', '')
                    nuevo_codigo = extraer_codigo_4_caracteres(excerpt)
                    if nuevo_codigo:
                        print(f"¡Código hallado en Excerpt!: [{nuevo_codigo}]")
                        break
        if nuevo_codigo:
            break
    except Exception as e:
        print(f"Aviso en API ({url}): {e}")

if not nuevo_codigo:
    print("\n=== 2. SCRAPING DIRECTO EN PÁGINAS PRINCIPALES ===")
    rutas_web = [
        "https://spinoff.link/",
        "https://spinoff.link/category/iptv/",
        "https://spinoff.link/lista-iptv/"
    ]
    
    for ruta in rutas_web:
        try:
            res_web = requests.get(ruta, headers=headers, timeout=12)
            if res_web.status_code == 200:
                nuevo_codigo = extraer_codigo_4_caracteres(res_web.text)
                if nuevo_codigo:
                    print(f"¡Código de 4 caracteres hallado en ({ruta})!: [{nuevo_codigo}]")
                    break
        except Exception as e:
            print(f"Error visitando {ruta}: {e}")

if not nuevo_codigo:
    print("\n[!] CRÍTICO: No se pudo extraer el código de 4 caracteres.")
    exit(1)

print(f"\n¡CÓDIGO EXTRAÍDO CON ÉXITO!: [{nuevo_codigo}]")

# === ACTUALIZACIÓN EN GITHUB ===
print("\n=== ACTUALIZANDO ARCHIVO EN GITHUB ===")
g = Github(token)
repo = g.get_repo(repo_name)

file_content = repo.get_contents('lista.m3u')
contenido_viejo = file_content.decoded_content.decode('utf-8')

# Reemplaza ÚNICAMENTE los 4 caracteres dentro de tecnotv.club/XXXX/
contenido_nuevo = re.sub(
    r'(tecnotv\.club\/)[a-zA-Z0-9]{4}(\/)',
    f'\\1{nuevo_codigo}\\2',
    contenido_viejo
)

if contenido_viejo != contenido_nuevo:
    print(f"Actualizando tu lista.m3u con el código: [{nuevo_codigo}]...")
    repo.update_file(
        path=file_content.path,
        message=f"Auto-update código: {nuevo_codigo}",
        content=contenido_nuevo,
        sha=file_content.sha
    )
    print("¡Tu archivo lista.m3u se actualizó correctamente en GitHub!")
else:
    print("El código de 4 caracteres en la web es igual al que ya tienes guardado.")
