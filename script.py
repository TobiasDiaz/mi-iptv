import os
import re
import requests
from github import Github

token = os.environ.get('GH_TOKEN')
repo_name = os.environ.get('REPO_NAME')

headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8'
}

# La página exacta que muestra la captura de pantalla
URL_PAGINA = "https://spinoff.link/listas-iptv-actualizadas-2025/"

nuevo_codigo = None

print(f"=== CONSULTANDO PÁGINA ESPECÍFICA: {URL_PAGINA} ===")

try:
    res = requests.get(URL_PAGINA, headers=headers, timeout=15)
    
    if res.status_code == 200:
        html = res.text
        
        # 1. Buscar los 4 caracteres justo antes de /android1.m3u (como https://tecnotv.club/65cg/android1.m3u)
        m = re.search(r'tecnotv\.club\/([a-zA-Z0-9]{4})\/android1\.m3u', html, re.IGNORECASE)
        if m:
            nuevo_codigo = m.group(1)
            print(f"¡Código hallado directamente en la URL de Android 1!: [{nuevo_codigo}]")
            
        # 2. Si la estructura cambia ligeramente, buscar cualquier /XXXX/android*.m3u
        if not nuevo_codigo:
            m = re.search(r'\/([a-zA-Z0-9]{4})\/android[0-9]*\.m3u', html, re.IGNORECASE)
            if m:
                nuevo_codigo = m.group(1)
                print(f"¡Código hallado con patrón alternativo!: [{nuevo_codigo}]")

        # 3. Buscar la coincidencia en cualquier caja de texto del HTML
        if not nuevo_codigo:
            m = re.search(r'tecnotv\.club\/([a-zA-Z0-9]{4})\/', html, re.IGNORECASE)
            if m:
                nuevo_codigo = m.group(1)
                print(f"¡Código hallado en dominio tecnotv.club!: [{nuevo_codigo}]")

    else:
        print(f"Error al cargar la página. Código de respuesta: {res.status_code}")

except Exception as e:
    print(f"Error al conectar con {URL_PAGINA}: {e}")

if not nuevo_codigo:
    print("\n[!] CRÍTICO: No se pudo extraer el código de 4 caracteres de la página.")
    exit(1)

print(f"\n¡CÓDIGO FINAL DETECTADO!: [{nuevo_codigo}]")

# === ACTUALIZACIÓN EN GITHUB ===
print("\n=== ACTUALIZANDO ARCHIVO EN GITHUB ===")
g = Github(token)
repo = g.get_repo(repo_name)

file_content = repo.get_contents('lista.m3u')
contenido_viejo = file_content.decoded_content.decode('utf-8')

# Reemplaza ÚNICAMENTE los 4 caracteres guardados en la lista de tu repositorio
contenido_nuevo = re.sub(
    r'(tecnotv\.club\/)[a-zA-Z0-9]{4}(\/)',
    f'\\1{nuevo_codigo}\\2',
    contenido_viejo
)

if contenido_viejo != contenido_nuevo:
    print(f"Actualizando lista.m3u con el nuevo código: [{nuevo_codigo}]...")
    repo.update_file(
        path=file_content.path,
        message=f"Auto-update código: {nuevo_codigo}",
        content=contenido_nuevo,
        sha=file_content.sha
    )
    print("¡Tu archivo lista.m3u se actualizó con éxito en GitHub!")
else:
    print("El código detectado en la página es el mismo que ya está guardado.")
