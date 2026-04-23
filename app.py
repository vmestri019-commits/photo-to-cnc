import streamlit as st
import cv2
import numpy as np
from PIL import Image
import ezdxf
import io
import math

st.set_page_config(page_title="CNC Vector Studio", layout="wide")

# --- 1. CORE PROCESSING ---
def generate_art(img, style, spacing, weight):
    h, w = img.shape
    # Create a fresh white canvas for every generation
    canvas = np.full((h, w), 255, dtype=np.uint8)
    center = (w // 2, h // 2)

    if style == "Vertical":
        for x in range(0, w, spacing):
            # Sample every few pixels for speed
            for y in range(0, h, 2):
                brightness = img[y, x]
                # Map darkness to thickness
                t = int(((255 - brightness) / 255) * (spacing / 2) * weight)
                if t > 0:
                    cv2.line(canvas, (x, y), (x + t, y), 0, 1)

    elif style == "Spiral":
        max_r = int(math.sqrt(w**2 + h**2) / 2)
        b_spiral = spacing / (2 * math.pi)
        angle = 0.0
        while True:
            r = b_spiral * angle
            if r > max_r: break
            x = int(center[0] + r * math.cos(angle))
            y = int(center[1] + r * math.sin(angle))
            if 0 <= x < w and 0 <= y < h:
                t = int(((255 - img[y, x]) / 255) * (spacing / 4) * weight)
                if t > 0: cv2.circle(canvas, (x, y), t, 0, -1)
            angle += 0.1 # Large steps for faster loading

    elif style == "Circles":
        max_r = int(math.sqrt(w**2 + h**2) / 2)
        for r in range(spacing, max_r, spacing):
            steps = int(2 * math.pi * r / 5)
            for i in range(steps):
                angle = (i / steps) * 2 * math.pi
                x, y = int(center[0] + r * math.cos(angle)), int(center[1] + r * math.sin(angle))
                if 0 <= x < w and 0 <= y < h:
                    t = int(((255 - img[y, x]) / 255) * (spacing / 4) * weight)
                    if t > 0: cv2.circle(canvas, (x, y), t, 0, -1)

    elif style == "Dots":
        for y in range(0, h, spacing):
            for x in range(0, w, spacing):
                r = int(((255 - img[y, x]) / 255) * (spacing / 2) * weight)
                if r > 0: cv2.circle(canvas, (x, y), r, 0, -1)

    return canvas

# --- 2. UI LAYOUT ---
st.title("🚀 CNC Style Engine")

# Use a form to prevent the app from re-running on every slider move
with st.sidebar:
    st.header("Settings")
    style_choice = st.selectbox("Pattern", ["Vertical", "Spiral", "Circles", "Dots"])
    space = st.slider("Spacing", 5, 40, 15)
    thick = st.slider("Thickness", 0.5, 3.0, 1.2)
    cont = st.slider("Image Contrast", 1.0, 3.0, 1.5)
    generate_btn = st.button("Apply & Generate")

uploaded_file = st.file_uploader("Upload Image", type=["jpg", "png", "jpeg"])

if uploaded_file:
    # Load and downscale immediately for speed
    raw_pil = Image.open(uploaded_file)
    raw_pil.thumbnail((1000, 1000)) 
    
    # Convert to Grayscale + Contrast
    img_np = np.array(raw_pil.convert('L'))
    img_np = cv2.convertScaleAbs(img_np, alpha=cont, beta=0)

    # Show original preview
    st.image(img_np, caption="Adjusted Source", width=300)

    if generate_btn:
        with st.spinner("Creating CNC Pattern..."):
            result = generate_art(img_np, style_choice, space, thick)
            st.image(result, caption=f"Result: {style_choice}", use_container_width=True)

            # Export Buttons
            st.write("### 📥 Download Files")
            c1, c2, c3 = st.columns(3)
            with c1:
                _, png = cv2.imencode(".png", result)
                st.download_button("Download PNG", png.tobytes(), "cnc.png", "image/png")
            with c2:
                _, tif = cv2.imencode(".tif", result)
                st.download_button("Download TIFF", tif.tobytes(), "cnc.tif", "image/tiff")
            with c3:
                # Basic DXF export
                doc = ezdxf.new()
                msp = doc.modelspace()
                # For circles/dots
                if style_choice == "Dots":
                    for y in range(0, img_np.shape[0], space):
                        for x in range(0, img_np.shape[1], space):
                            r = ((255 - img_np[y, x])/255) * (space/2) * thick
                            if r > 0.5: msp.add_circle((x*0.1, -y*0.1), r*0.1)
                
                dxf_io = io.StringIO()
                doc.write(dxf_io)
                st.download_button("Download DXF", dxf_io.getvalue(), "cnc.dxf", "application/dxf")
    
