"""
convert_to_webp.py - Convierte PNG/JPG pesados a WebP para reducir peso 90%+.
Crea archivos .webp al lado de los originales (no los borra).
Recorre static/images/ excluyendo iconos pequenos (<50KB).
"""
import os
import sys
from PIL import Image

# UTF-8 stdout para Windows
if sys.platform == "win32":
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
IMAGES_DIR = os.path.join(BASE_DIR, 'static', 'images')
MIN_SIZE_KB = 50          # solo convertir si pesa mas de 50KB
WEBP_QUALITY = 85         # calidad alta, peso bajo


def convertir(ruta_png: str) -> tuple[bool, int, int]:
    """Convierte un PNG a WebP. Devuelve (ok, peso_original_kb, peso_webp_kb)."""
    ruta_webp = ruta_png.rsplit('.', 1)[0] + '.webp'
    peso_orig = os.path.getsize(ruta_png) // 1024
    if peso_orig < MIN_SIZE_KB:
        return False, peso_orig, 0
    try:
        img = Image.open(ruta_png)
        # Mantener transparencia si la tiene
        if img.mode in ('RGBA', 'LA', 'P'):
            img.save(ruta_webp, 'WEBP', quality=WEBP_QUALITY, method=6)
        else:
            img.convert('RGB').save(ruta_webp, 'WEBP', quality=WEBP_QUALITY, method=6)
        peso_webp = os.path.getsize(ruta_webp) // 1024
        return True, peso_orig, peso_webp
    except Exception as exc:
        print(f"  ERROR convirtiendo {ruta_png}: {exc}")
        return False, peso_orig, 0


def main():
    if not os.path.isdir(IMAGES_DIR):
        print(f"No existe {IMAGES_DIR}")
        return
    total_orig = total_webp = 0
    convertidos = 0
    for root, _, files in os.walk(IMAGES_DIR):
        for f in files:
            if not f.lower().endswith(('.png', '.jpg', '.jpeg')):
                continue
            ruta = os.path.join(root, f)
            ok, peso_o, peso_w = convertir(ruta)
            if ok:
                ahorro = peso_o - peso_w
                pct = (ahorro / peso_o) * 100 if peso_o else 0
                rel = os.path.relpath(ruta, BASE_DIR)
                print(f"  OK  {rel}  {peso_o}KB -> {peso_w}KB  (-{pct:.0f}%)")
                total_orig += peso_o
                total_webp += peso_w
                convertidos += 1
    if convertidos:
        ahorro = total_orig - total_webp
        pct = (ahorro / total_orig) * 100
        print(f"\nTotal: {convertidos} imagenes  {total_orig}KB -> {total_webp}KB  (ahorro -{pct:.0f}%)")
    else:
        print("Nada para convertir.")


if __name__ == '__main__':
    main()
