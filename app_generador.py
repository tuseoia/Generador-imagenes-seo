import streamlit as st
import replicate
import requests
from PIL import Image
import io
import os
import re

st.set_page_config(page_title="Generador de Imágenes SEO", page_icon="🎨", layout="wide")

st.title("🎨 Generador de Imágenes para Artículos (Flux.1 + SEO)")
st.markdown("Crea imágenes de alta calidad, optimizadas para **Google SEO** y **AdSense**.")

# --- Sidebar: API Key desde secretos o manual ---
with st.sidebar:
    st.header("⚙️ Configuración")
    
    # Intenta leer de secretos (cuando está en la nube) o pide manual
    try:
        replicate_api_key = st.secrets["REPLICATE_API_TOKEN"]
        st.success("✅ API Key cargada desde configuración segura")
    except Exception:
        replicate_api_key = st.text_input("Replicate API Token", type="password")
    
    if replicate_api_key:
        os.environ["REPLICATE_API_TOKEN"] = replicate_api_key

def crear_prompt_seo(titulo):
    prompt = (
        f"Professional, high-quality blog header image about: {titulo}. "
        "Photorealistic, excellent lighting, 8k resolution, clean composition, highly detailed, "
        "modern aesthetic, suitable for a professional website."
    )
    negative_prompt = (
        "text, watermark, signature, logo, blurry, deformed, distorted, low resolution, "
        "ugly, bad anatomy, oversaturated, cartoonish, messy background, extra limbs"
    )
    return prompt, negative_prompt

def generar_imagen(prompt, negative_prompt):
    try:
        output = replicate.run(
            "black-forest-labs/flux-dev",
            input={
                "prompt": prompt,
                "negative_prompt": negative_prompt,
                "aspect_ratio": "3:2",
                "output_format": "webp",
                "output_quality": 90,
                "num_outputs": 1
            }
        )
        return output[0]
    except Exception as e:
        st.error(f"❌ Error al generar la imagen: {e}")
        return None

def optimizar_imagen(image_url, titulo):
    try:
        response = requests.get(image_url)
        img = Image.open(io.BytesIO(response.content))
        img.thumbnail((1200, 800), Image.Resampling.LANCZOS)
        
        img_byte_arr = io.BytesIO()
        img.save(img_byte_arr, format='WEBP', quality=85, optimize=True)
        img_byte_arr.seek(0)
        
        slug = re.sub(r'[^\w\s-]', '', titulo.lower())
        slug = re.sub(r'[\s_]+', '-', slug).strip('-')
        filename = f"{slug[:50]}.webp"
        alt_text = f"Imagen ilustrativa profesional sobre {titulo.lower()}"
        
        return img_byte_arr.getvalue(), filename, alt_text, len(img_byte_arr.getvalue()) / 1024
    except Exception as e:
        st.error(f"❌ Error al optimizar: {e}")
        return None, None, None, 0

# --- Interfaz ---
titulo_articulo = st.text_input("📝 Título del artículo:", placeholder="Ej: Guía definitiva para optimizar WordPress")

if st.button("🚀 Generar Imagen", type="primary", use_container_width=True):
    if not replicate_api_key:
        st.error("Introduce tu API Key de Replicate.")
    elif not titulo_articulo.strip():
        st.warning("Escribe un título para el artículo.")
    else:
        with st.spinner("🎨 Generando imagen con Flux.1 (~15 segundos)..."):
            prompt, negative_prompt = crear_prompt_seo(titulo_articulo)
            image_url = generar_imagen(prompt, negative_prompt)
            
            if image_url:
                img_bytes, filename, alt_text, size_kb = optimizar_imagen(image_url, titulo_articulo)
                if img_bytes:
                    res_col1, res_col2 = st.columns([1, 1])
                    with res_col1:
                        st.image(image_url, caption="Vista previa", use_container_width=True)
                        st.download_button("📥 Descargar Imagen (WebP)", img_bytes, filename, "image/webp", use_container_width=True)
                    with res_col2:
                        st.subheader("📊 Metadatos SEO")
                        st.code(f"Nombre: {filename}", language="text")
                        st.code(f"Alt Text: {alt_text}", language="text")
                        st.info(f"⚖️ Peso: **{size_kb:.2f} KB**")
