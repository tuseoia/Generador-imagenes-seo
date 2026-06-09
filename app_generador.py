import streamlit as st
import replicate
import requests
from PIL import Image
import io
import os
import re

st.set_page_config(
    page_title="Generador de Imágenes SEO - Flux 2 Pro", 
    page_icon="🎨", 
    layout="wide"
)

st.title("🎨 Generador de Imágenes con Flux 2 Pro")
st.markdown("""
Crea imágenes de **calidad profesional** optimizadas para **Google SEO** y **AdSense**.
""")

# --- Sidebar ---
with st.sidebar:
    st.header("⚙️ Configuración")
    
    try:
        replicate_api_key = st.secrets["REPLICATE_API_TOKEN"]
        st.success("✅ API Key cargada")
    except Exception:
        replicate_api_key = st.text_input("Replicate API Token", type="password")
    
    if replicate_api_key:
        os.environ["REPLICATE_API_TOKEN"] = replicate_api_key
    
    st.markdown("---")
    st.header("🎛️ Parámetros")
    
    aspect_ratio = st.selectbox(
        "📐 Proporción:",
        options=["3:2", "16:9", "1:1", "4:3", "2:3", "9:16"],
        index=0
    )
    
    guidance_scale = st.slider("🎯 Fidelidad:", 2.0, 7.0, 3.5, 0.5)
    num_steps = st.slider("⚡ Pasos:", 14, 50, 28, 2)
    output_quality = st.slider("🖼️ Calidad:", 70, 100, 90, 5)
    
    output_format = st.selectbox(
        "🎨 Formato:",
        options=["webp", "jpg", "png"],
        index=0
    )

def crear_prompt_seo(titulo):
    prompt = (
        f"Professional editorial photography, blog header about: {titulo}. "
        "Ultra high quality, photorealistic, cinematic lighting, 8k resolution, "
        "highly detailed, sharp focus, modern aesthetic, clean composition"
    )
    negative_prompt = (
        "text, watermark, signature, logo, blurry, deformed, distorted, "
        "low quality, ugly, bad anatomy, oversaturated, cartoonish"
    )
    return prompt, negative_prompt

def generar_imagen(prompt, negative_prompt, aspect_ratio, guidance_scale, 
                   num_steps, output_quality, output_format):
    """Genera imagen con Flux 2 Pro - CORREGIDO PARA FILEOUTPUT"""
    try:
        output = replicate.run(
            "black-forest-labs/flux-2-pro",
            input={
                "prompt": prompt,
                "negative_prompt": negative_prompt,
                "aspect_ratio": aspect_ratio,
                "guidance_scale": guidance_scale,
                "num_inference_steps": num_steps,
                "output_quality": output_quality,
                "output_format": output_format
            }
        )
        
        # ✅ CORRECCIÓN: Obtener URL del objeto FileOutput
        if hasattr(output, 'url'):
            # Si es un objeto FileOutput único
            return output.url
        elif isinstance(output, list) and len(output) > 0:
            # Si es una lista (versión antigua)
            return output[0].url if hasattr(output[0], 'url') else output[0]
        else:
            # Si es directamente una URL string
            return str(output)
            
    except Exception as e:
        st.error(f"❌ Error: {str(e)}")
        return None

def optimizar_imagen(image_url, titulo, output_format):
    try:
        response = requests.get(image_url, timeout=30)
        response.raise_for_status()
        img = Image.open(io.BytesIO(response.content))
        img.thumbnail((1200, 800), Image.Resampling.LANCZOS)
        
        format_map = {"webp": "WEBP", "jpg": "JPEG", "png": "PNG"}
        mime_map = {"webp": "image/webp", "jpg": "image/jpeg", "png": "image/png"}
        
        img_byte_arr = io.BytesIO()
        save_kwargs = {"format": format_map[output_format], "optimize": True}
        if output_format != "png":
            save_kwargs["quality"] = 85
        
        img.save(img_byte_arr, **save_kwargs)
        img_byte_arr.seek(0)
        
        slug = re.sub(r'[^\w\s-]', '', titulo.lower())
        slug = re.sub(r'[\s_]+', '-', slug).strip('-')
        filename = f"{slug[:50]}.{output_format}"
        alt_text = f"Imagen profesional sobre {titulo.lower()}"
        size_kb = len(img_byte_arr.getvalue()) / 1024
        
        return img_byte_arr.getvalue(), filename, alt_text, mime_map[output_format], size_kb
        
    except Exception as e:
        st.error(f"❌ Error al optimizar: {str(e)}")
        return None, None, None, None, 0

# --- Interfaz Principal ---
titulo_articulo = st.text_input(
    "📝 Título del artículo:", 
    placeholder="Ej: Las 10 mejores estrategias de marketing digital para 2024"
)

if st.button("🚀 Generar Imagen", type="primary", use_container_width=True):
    if not replicate_api_key:
        st.error("❌ Introduce tu API Key")
        st.stop()
    
    if not titulo_articulo.strip():
        st.warning("⚠️ Escribe un título")
        st.stop()
    
    with st.spinner(f"🎨 Generando (~15-25s)..."):
        prompt, negative_prompt = crear_prompt_seo(titulo_articulo)
        
        image_url = generar_imagen(
            prompt, negative_prompt, aspect_ratio, guidance_scale,
            num_steps, output_quality, output_format
        )
        
        if image_url is None:
            st.error("❌ No se generó la imagen")
            st.error("Verifica: 1) API Key correcta, 2) Créditos disponibles")
            st.stop()
        
        st.success("✅ ¡Imagen generada!")
        
        img_bytes, filename, alt_text, mime_type, size_kb = optimizar_imagen(
            image_url, titulo_articulo, output_format
        )
        
        if img_bytes:
            col1, col2 = st.columns([1, 1])
            with col1:
                st.image(image_url, caption="🖼️ Vista previa", use_container_width=True)
                st.download_button(
                    label=f"📥 Descargar ({output_format.upper()})",
                    data=img_bytes,
                    file_name=filename,
                    mime=mime_type,
                    use_container_width=True
                )
            with col2:
                st.subheader("📊 Metadatos SEO")
                st.code(f"Archivo: {filename}", language="text")
                st.code(f"Alt Text: {alt_text}", language="text")
                st.info(f"⚖️ Peso: **{size_kb:.2f} KB**")
