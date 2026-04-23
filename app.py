import streamlit as st
import cv2
import numpy as np
from PIL import Image
import ezdxf
import io
import math

st.set_page_config(page_title="CNC Art Studio", layout="wide")

# --- 1. THE REFINED ENGINE ---
def generate_cnc_art(img_array, style, spacing, weight, contrast):
    img = cv2.cvtColor(img_array, cv2.COLOR_RGB2GRAY)
    img = cv2.convertScaleAbs(img, alpha=contrast, beta=0)
    h, w = img.shape
    output = np.full((h, w), 255, dtype=np.uint8)
    center = (w // 2, h // 2)

    if style == "Vertical" or style == "Crosshatch":
        for x in range(0, w, spacing):
            col = img[:, min(x, w-1)]
            thicknesses = ((255 - col) / 255) * (spacing / 2) * weight
            for y in range(h):
                t = int(thicknesses[y])
                if t > 0:
                    output[y, max(0, x-t):min(w, x+t)] = 0
        if style == "Crosshatch":
            for y in range(0, h, spacing):
                row = img[y, :]
                thicknesses = ((255 - row) / 255) * (spacing / 2) * weight
                for x in range(w):
                    t = int(thicknesses[x])
                    if t > 0:
                        output[max(0, y-t):min(h, y+t), x] = 0

    elif style == "Circles":
        max_r = int(math.sqrt(w**2 + h**2) / 2)
        for r in range(spacing, max_r, spacing):
            # We must draw the circle pixel-by-pixel to vary thickness
            # Circumference = 2 * pi * r. We step based on that.
            steps = int(2 * math.pi * r) 
            for i in range(steps):
                angle = (i / steps) * 2 * math.pi
                x = int(center[0] + r * math.cos(angle))
                y = int(center[1] + r * math.sin(angle))
                if 0 <= x < w and 0 <= y < h:
                    b = img[y, x]
                    t = int(((255 - b) / 255) * (spacing / 2) * weight)
                    if t > 0:
                        cv2.circle(output, (x, y), t, 0, -1)

    elif style == "Dots":
        for y in range(0, h, spacing):
            for x in range(0, w, spacing):
                b = img[y, x]
                r = int(((255 - b) / 255) * (spacing / 2) * weight)
                if r > 0:
                    cv2.circle(output, (x, y), r, 0, -1)

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
                brightness = img[y, x]
                t = int(((255 - brightness) / 255) * (spacing / 2) * weight)
                if t > 0:
                    cv2.circle(output, (x, y), t, 0, -1)
            angle += 0.1 / (r/spacing + 1)

    return output

# --- 2. EXPORT FUNCTIONS ---
def create_dxf_data(img_array, style, spacing, weight, contrast):
    doc = ezdxf.new('R2010')
    msp = doc.modelspace()
    scale = 0.1 
    # Logic similar to generate_cnc_art but using msp.add_circle/line
    # For now, a simple placeholder or the Dots logic works well here
    return "DXF Data String" # Placeholder for brevity

# --- 3. UI ---
st.title("🎨 CNC Design Engine Pro")

st.write("### 🛠️ Step 1: Design Settings")
c_a, c_b, c_c, c_d = st.columns(4)
with c_a: style_choice = st.selectbox("Style", ["Vertical", "Crosshatch", "Circles", "Dots", "Spiral"])
with c_b: line_density = st.slider("Spacing", 4, 40, 10)
with c_c: line_weight = st.slider("Thickness", 0.1, 3.0, 1.2)
with c_d: img_contrast = st.slider("Contrast", 1.0, 3.0, 1.8)

uploaded_file = st.file_uploader("Upload Image", type=["jpg", "png", "jpeg"])

if uploaded_file:
    image = Image.open(uploaded_file)
    img_np = np.array(image)
    
    with st.spinner("Calculating Pattern..."):
        preview_img = generate_cnc_art(img_np, style_choice, line_density, line_weight, img_contrast)
        st.image(preview_img, caption="CNC Preview", use_container_width=True)

    st.write("### 💾 Step 2: Download HD Files")
    btn_col1, btn_col2, btn_col3 = st.columns(3)
    
    with btn_col1:
        # HD PNG
        ret1, png_buf = cv2.imencode(".png", preview_img)
        st.download_button("Download HD PNG", png_buf.tobytes(), "cnc_art_hd.png", "image/png")
        
    with btn_col2:
        # TIFF
        ret2, tif_buf = cv2.imencode(".tif", preview_img)
        st.download_button("Download TIFF", tif_buf.tobytes(), "cnc_art.tif", "image/tiff")
        
    with btn_col3:
        # DXF Placeholder
        st.download_button("Download DXF", "dxf_content", "cnc_art.dxf", "application/dxf")
        
