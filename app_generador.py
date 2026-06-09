import streamlit as st
import replicate
import requests
from PIL import Image
import io
import os
import re

st.set_page_config(page_title="Generador de Imágenes SEO - Flux 2 Pro", page_icon="🎨", layout="wide")

st.title("🎨 Generador de Imágenes con Flux 2 Pro")
st.markdown("Crea imágenes de **calidad profesional** optimizadas para **SEO** y **AdSense**.")

# --- Sidebar: Configuración ---
with st.sidebar:
    st.header("⚙️ Configuración")
    
    # API Key desde secretos o manual
    try:
        replicate_api_key = st.secrets["REPLICATE_API_TOKEN"]
        st.success("✅ API Key cargada")
    except Exception:
        replicate_api_key = st.text_input("Replicate API Token", type="password")
    
    if replicate_api_key:
        os.environ["REPLICATE_API_TOKEN"] = replicate_api_key
    
    st.markdown("---")
    st.info("💡 **Flux 2 Pro** ofrece:\n- Mayor calidad fotorealista\n- Mejor comprensión de prompts\n- Detalles más precisos")

def crear_prompt_seo(titulo):
    """Crea un prompt optimizado para Flux 2 Pro"""
    prompt = (
        f"Professional editorial photography, blog header image about: {titulo}. "
        "Ultra high quality, photorealistic, cinematic lighting, 8k resolution, "
        "highly detailed, sharp focus, modern aesthetic, clean composition, "
        "professional photography, suitable for premium website"
    )
    
    negative_prompt = (
        "text, watermark, signature, logo, blurry, deformed, distorted, low quality, "
        "ugly, bad anatomy, oversaturated, cartoonish, messy background, extra limbs, "
        "disfigured, amateur, poorly lit, grainy"
    )
    
    return prompt, negative_prompt

def generar_imagen(prompt, negative_prompt):
    """Genera imagen con Flux 2 Pro"""
    try:
        output = replicate.run(
            "black-forest-labs/flux-2-pro",  # ✅ NUEVO MODELO
            input={
                "prompt": prompt,
                "negative_prompt": negative_prompt,
                "aspect_ratio": "3:2",  # Ideal para cabeceras de blog
                "output_format": "webp",
                "output_quality": 90,
                "num_outputs": 1,
                # Parámetros específicos de Flux 2 Pro (opcional):
                "guidance_scale": 3.5,  # Controla qué tan fiel es al prompt
                "num_inference_steps": 28  # Más pasos = mejor calidad (pero más lento)
            }
        )
        return output[0]
    except Exception as e:
        st.error(f"❌ Error al generar: {str(e)}")
        return None

def optimizar_imagen(image_url, titulo):
    """Descarga y optimiza la imagen para web"""
    try:
        response = requests.get(image_url)
        img = Image.open(io.BytesIO(response.content))
        
        # Redimensionar para web (máx 1200px de ancho)
        img.thumbnail((1200, 800), Image.Resampling.LANCZOS)
        
        # Guardar como WebP optimizado
        img_byte_arr = io.BytesIO()
        img.save(img_byte_arr, format='WEBP', quality=85, optimize=True)
        img_byte_arr.seek(0)
        
        # Generar metadatos SEO
        slug = re.sub(r'[^\w\s-]', '', titulo.lower())
        slug = re.sub(r'[\s_]+', '-', slug).strip('-')
        filename = f"{slug[:50]}.webp"
        alt_text = f"Imagen profesional sobre {titulo.lower()}"
        
        return img_byte_arr.getvalue(), filename, alt_text, len(img_byte_arr.getvalue()) / 1024
        
    except Exception as e:
        st.error(f"❌ Error al optimizar: {str(e)}")
        return None, None, None, 0

# --- Interfaz Principal ---
titulo_articulo = st.text_input(
    "📝 Título del artículo:", 
    placeholder="Ej: Las 10 mejores estrategias de marketing digital para 2024",
    help="Escribe un título descriptivo para generar la mejor imagen"
)

if st.button("🚀 Generar Imagen con Flux 2 Pro", type="primary", use_container_width=True):
    if not replicate_api_key:
        st.error("❌ Introduce tu API Key de Replicate en la barra lateral.")
    elif not titulo_articulo.strip():
        st.warning("⚠️ Escribe un título para el artículo.")
    else:
        with st.spinner("🎨 Generando imagen con Flux 2 Pro (calidad premium)..."):
            try:
                prompt, negative_prompt = crear_prompt_seo(titulo_articulo)
                image_url = generar_imagen(prompt, negative_prompt)
                
                if image_url is None:
                    st.error("❌ No se generó la imagen. Verifica:")
                    st.error("1. Tu API Key de Replicate")
                    st.error("2. Que tengas créditos disponibles")
                    st.error("3. Que hayas aceptado los términos de Flux 2 Pro")
                    st.stop()
                
                st.success("✅ ¡Imagen generada con calidad Flux 2 Pro!")
                
                img_bytes, filename, alt_text, size_kb = optimizar_imagen(image_url, titulo_articulo)
                
                if img_bytes is None:
                    st.error("❌ Error al optimizar la imagen.")
                    st.stop()
                
                # Mostrar resultados
                res_col1, res_col2 = st.columns([1, 1])
                
                with res_col1:
                    st.image(image_url, caption="🖼️ Vista previa (Flux 2 Pro)", use_container_width=True)
                    st.download_button(
                        label="📥 Descargar Imagen Optimizada (WebP)",
                        data=img_bytes,
                        file_name=filename,
                        mime="image/webp",
                        use_container_width=True
                    )
                
                with res_col2:
                    st.subheader("📊 Metadatos SEO")
                    st.code(f"📁 Nombre de archivo:\n{filename}", language="text")
                    st.code(f"🏷️  Alt Text:\n{alt_text}", language="text")
                    st.info(f"⚖️ Peso: **{size_kb:.2f} KB** (Optimizado para Core Web Vitals)")
                    
                    with st.expander("👀 Ver prompts utilizados"):
                        st.markdown("**Prompt:**")
                        st.text(prompt)
                        st.markdown("**Negative Prompt:**")
                        st.text(negative_prompt)
                        
            except Exception as e:
                st.error(f"❌ Error inesperado: {str(e)}")
                st.info("💡 Verifica que tienes créditos en Replicate y aceptaste los términos de Flux 2 Pro")
