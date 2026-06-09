import streamlit as st
import replicate
import requests
from PIL import Image
import io
import os
import re

# Configuración de la página
st.set_page_config(
    page_title="Generador de Imágenes SEO - Flux 2 Pro", 
    page_icon="🎨", 
    layout="wide"
)

st.title("🎨 Generador de Imágenes con Flux 2 Pro")
st.markdown("""
Crea imágenes de **calidad profesional** optimizadas para **Google SEO** y **AdSense**.
Usa el modelo más avanzado de Black Forest Labs con parámetros personalizables.
""")

# --- Sidebar: Configuración y Parámetros ---
with st.sidebar:
    st.header("⚙️ Configuración")
    
    # API Key de Replicate
    try:
        replicate_api_key = st.secrets["REPLICATE_API_TOKEN"]
        st.success("✅ API Key cargada desde secretos")
    except Exception:
        replicate_api_key = st.text_input(
            "Replicate API Token", 
            type="password",
            help="Obtén tu token en https://replicate.com/account/api-tokens"
        )
    
    if replicate_api_key:
        os.environ["REPLICATE_API_TOKEN"] = replicate_api_key
    
    st.markdown("---")
    st.header("🎛️ Parámetros del Modelo")
    
    # 📐 Aspect Ratio
    aspect_ratio = st.selectbox(
        "📐 Proporción de imagen:",
        options=["3:2", "16:9", "1:1", "4:3", "2:3", "9:16"],
        index=0,
        help="3:2 = Ideal para cabeceras de blog (1024x680px)"
    )
    
    #  Guidance Scale
    guidance_scale = st.slider(
        "🎯 Fidelidad al prompt:",
        min_value=2.0,
        max_value=7.0,
        value=3.5,
        step=0.5,
        help="Más alto = más fiel al prompt pero menos creativo"
    )
    
    # ⚡ Num Inference Steps
    num_steps = st.slider(
        "⚡ Calidad (pasos de inferencia):",
        min_value=14,
        max_value=50,
        value=28,
        step=2,
        help="Más pasos = mejor calidad pero más lento (14-50)"
    )
    
    # 🖼️ Output Quality
    output_quality = st.slider(
        "🖼️ Calidad de compresión WebP:",
        min_value=70,
        max_value=100,
        value=90,
        step=5,
        help="WebP quality (0-100). 90 = excelente balance calidad/peso"
    )
    
    # 🎨 Formato de salida
    output_format = st.selectbox(
        "🎨 Formato de salida:",
        options=["webp", "jpg", "png"],
        index=0,
        help="WebP = Mejor compresión para web (recomendado para SEO)"
    )
    
    # Resumen de configuración
    st.markdown("---")
    st.info(f"""
    **Configuración actual:**
    -  Proporción: {aspect_ratio}
    - 🎯 Fidelidad: {guidance_scale}
    - ⚡ Pasos: {num_steps}
    - 🖼️ Calidad: {output_quality}%
    - 🎨 Formato: {output_format.upper()}
    """)

# --- Funciones ---

def crear_prompt_seo(titulo):
    """Crea un prompt optimizado para Flux 2 Pro y SEO"""
    prompt = (
        f"Professional editorial photography, blog header image about: {titulo}. "
        "Ultra high quality, photorealistic, cinematic lighting, 8k resolution, "
        "highly detailed, sharp focus, modern aesthetic, clean composition, "
        "professional photography, suitable for premium website"
    )
    
    negative_prompt = (
        "text, watermark, signature, logo, blurry, deformed, distorted, low quality, "
        "ugly, bad anatomy, oversaturated, cartoonish, messy background, extra limbs, "
        "disfigured, amateur, poorly lit, grainy, noisy"
    )
    
    return prompt, negative_prompt

def generar_imagen(prompt, negative_prompt, aspect_ratio, guidance_scale, 
                   num_steps, output_quality, output_format):
    """Genera imagen con Flux 2 Pro y parámetros personalizados"""
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
                "output_format": output_format,
                "num_outputs": 1
            }
        )
        return output[0] if output else None
    except Exception as e:
        st.error(f"❌ Error al generar la imagen: {str(e)}")
        return None

def optimizar_imagen(image_url, titulo, output_format):
    """Descarga, redimensiona y optimiza la imagen para web"""
    try:
        response = requests.get(image_url, timeout=30)
        response.raise_for_status()
        img = Image.open(io.BytesIO(response.content))
        
        # Redimensionar para web (máx 1200px de ancho para buen LCP)
        img.thumbnail((1200, 800), Image.Resampling.LANCZOS)
        
        # Mapeo de formatos
        format_map = {"webp": "WEBP", "jpg": "JPEG", "png": "PNG"}
        mime_map = {"webp": "image/webp", "jpg": "image/jpeg", "png": "image/png"}
        
        # Guardar como formato optimizado
        img_byte_arr = io.BytesIO()
        save_kwargs = {
            "format": format_map[output_format],
            "optimize": True
        }
        if output_format != "png":
            save_kwargs["quality"] = 85
        
        img.save(img_byte_arr, **save_kwargs)
        img_byte_arr.seek(0)
        
        # Generar metadatos SEO
        slug = re.sub(r'[^\w\s-]', '', titulo.lower())
        slug = re.sub(r'[\s_]+', '-', slug).strip('-')
        filename = f"{slug[:50]}.{output_format}"
        alt_text = f"Imagen profesional sobre {titulo.lower()}"
        
        size_kb = len(img_byte_arr.getvalue()) / 1024
        
        return img_byte_arr.getvalue(), filename, alt_text, mime_map[output_format], size_kb
        
    except Exception as e:
        st.error(f"❌ Error al optimizar la imagen: {str(e)}")
        return None, None, None, None, 0

# --- Interfaz Principal ---

titulo_articulo = st.text_input(
    " Título del artículo:", 
    placeholder="Ej: Las 10 mejores estrategias de marketing digital para 2024",
    help="Escribe un título descriptivo para generar la mejor imagen posible"
)

if st.button(" Generar Imagen con Flux 2 Pro", type="primary", use_container_width=True):
    # Validaciones
    if not replicate_api_key:
        st.error("❌ Introduce tu API Key de Replicate en la barra lateral.")
        st.stop()
    
    if not titulo_articulo.strip():
        st.warning("⚠️ Escribe un título para el artículo.")
        st.stop()
    
    # Generación
    with st.spinner(f" Generando imagen con Flux 2 Pro ({num_steps} pasos, ~15-25s)..."):
        prompt, negative_prompt = crear_prompt_seo(titulo_articulo)
        
        image_url = generar_imagen(
            prompt=prompt,
            negative_prompt=negative_prompt,
            aspect_ratio=aspect_ratio,
            guidance_scale=guidance_scale,
            num_steps=num_steps,
            output_quality=output_quality,
            output_format=output_format
        )
        
        if image_url is None:
            st.error("❌ No se generó la imagen. Verifica:")
            st.error("1. Tu API Key de Replicate es correcta")
            st.error("2. Tienes créditos disponibles en Replicate")
            st.error("3. Aceptaste los términos de Flux 2 Pro en replicate.com/black-forest-labs/flux-2-pro")
            st.stop()
        
        st.success("✅ ¡Imagen generada con calidad Flux 2 Pro!")
        
        # Optimización
        img_bytes, filename, alt_text, mime_type, size_kb = optimizar_imagen(
            image_url, titulo_articulo, output_format
        )
        
        if img_bytes is None:
            st.error("❌ Error al optimizar la imagen.")
            st.stop()
        
        # Mostrar resultados en dos columnas
        res_col1, res_col2 = st.columns([1, 1])
        
        with res_col1:
            st.image(image_url, caption="🖼️ Vista previa (Flux 2 Pro)", use_container_width=True)
            st.download_button(
                label=f"📥 Descargar Imagen Optimizada ({output_format.upper()})",
                data=img_bytes,
                file_name=filename,
                mime=mime_type,
                use_container_width=True
            )
        
        with res_col2:
            st.subheader("📊 Metadatos SEO")
            st.code(f"📁 Nombre de archivo:\n{filename}", language="text")
            st.code(f"🏷️  Alt Text:\n{alt_text}", language="text")
            
            # Indicador de peso
            if size_kb < 100:
                st.success(f"⚖️ Peso: **{size_kb:.2f} KB** (¡Excelente para Core Web Vitals!)")
            elif size_kb < 200:
                st.info(f"⚖️ Peso: **{size_kb:.2f} KB** (Aceptable)")
            else:
                st.warning(f"️ Peso: **{size_kb:.2f} KB** (Considera reducir calidad)")
            
            # Prompts utilizados
            with st.expander("👀 Ver prompts utilizados"):
                st.markdown("**Prompt:**")
                st.text(prompt)
                st.markdown("**Negative Prompt:**")
                st.text(negative_prompt)
