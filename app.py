import streamlit as st
import cv2
import numpy as np
from PIL import Image
import ezdxf
import io
import math

# 1. Page Config
st.set_page_config(page_title="CNC Art Studio Pro", layout="wide")

# --- 2. VECTOR ENGINE (FOR SMOOTH CNC PATHS) ---
def create_dxf_data(img_array, style, spacing, weight, contrast):
    doc = ezdxf.new('R2010')
    msp = doc.modelspace()
    img = cv2.cvtColor(img_array, cv2.COLOR_RGB2GRAY)
    img = cv2.convertScaleAbs(img, alpha=contrast, beta=0)
    h, w = img.shape
    scale = 0.1 

    if style == "Vertical":
        for x in range(0, w, spacing):
            points = []
            for y in range(0, h, 2):
                b = img[y, x]
                # Variation in X based on darkness creates the "engraved" look
                t = ((255 - b) / 255) * (spacing / 2) * weight
                points.append(((x + t) * scale, (h - y) * scale))
            if len(points) > 1:
                msp.add_lwpolyline(points)

    elif style == "Spiral":
        center = (w // 2, h // 2)
        max_r = int(math.sqrt(w**2 + h**2) / 2)
        b_val = spacing / (2 * math.pi)
        angle = 0.0
        points = []
        while True:
            r = b_val * angle
            if r > max_r: break
            px, py = center[0] + r * math.cos(angle), center[1] + r * math.sin(angle)
            if 0 <= int(px) < w and 0 <= int(py) < h:
                b = img[int(py), int(px)]
                # Modulate the radius slightly based on brightness for a smooth path
                t = ((255 - b) / 255) * (spacing / 4) * weight
                adj_r = r + t
                points.append(((center[0] + adj_r * math.cos(angle)) * scale, 
                               (h - (center[1] + adj_r * math.sin(angle))) * scale))
            angle += 0.1 / (r/spacing + 1)
        if len(points) > 1:
            msp.add_lwpolyline(points)

    elif style == "Dots":
        for y in range(0, h, spacing):
            for x in range(0, w, spacing):
                b = img[y, x]
                r = ((255 - b) / 255) * (spacing / 2) * weight
                if r > 0.5:
                    msp.add_circle((x * scale, (h - y) * scale), radius=r * scale)

    out_str = io.StringIO()
    doc.write(out_str)
    return out_str.getvalue()

# --- 3. RASTER PREVIEW ENGINE ---
def generate_preview(img_array, style, spacing, weight, contrast):
    img = cv2.cvtColor(img_array, cv2.COLOR_RGB2GRAY)
    img = cv2.convertScaleAbs(img, alpha=contrast, beta=0)
    h, w = img.shape
    upscale = 2
    output = np.full((h * upscale, w * upscale), 255, dtype=np.uint8)
    
    if style == "Dots":
        for y in range(0, h, spacing):
            for x in range(0, w, spacing):
                b = img[y, x]
                r = int(((255 - b) / 255) * (spacing / 2) * weight * upscale)
                if r > 0:
                    cv2.circle(output, (x * upscale, y * upscale), r, 0, -1)
    else:
        # Use a thinner sampling for Vertical/Spiral previews to show lines
        for x in range(0, w, spacing):
            for y in range(0, h, 1):
                b = img[y, x]
                t = int(((255 - b) / 255) * (spacing / 2) * weight * upscale)
                if t > 0:
                    cv2.line(output, (x*upscale, y*upscale), (x*upscale + t, y*upscale), 0, 1)

    return cv2.resize(output, (w, h), interpolation=cv2.INTER_AREA)

# --- 4. UI ---
st.title("🎨 CNC Vector Design Studio")

col_a, col_b, col_c, col_d = st.columns(4)
with col_a: 
    # Spiral is now back in the list!
    style_choice = st.selectbox("Style", ["Vertical", "Spiral", "Dots"])
with col_b: space = st.slider("Spacing", 4, 40, 12)
with col_c: thick = st.slider("Weight", 0.1, 3.0, 1.2)
with col_d: cont = st.slider("Contrast", 1.0, 3.0, 1.5)

uploaded_file = st.file_uploader("Upload Image", type=["jpg", "png", "jpeg"])

if uploaded_file:
    img = Image.open(uploaded_file)
    img_np = np.array(img)
    
    with st.spinner("Processing..."):
        preview = generate_preview(img_np, style_choice, space, thick, cont)
        st.image(preview, caption=f"CNC {style_choice} Preview", use_container_width=True)

    st.write("### 📥 Export Options")
    b1, b2 = st.columns(2)
    with b1:
        ret, png_buf = cv2.imencode(".png", preview)
        st.download_button("Download HD PNG", png_buf.tobytes(), "cnc_art.png", "image/png")
    with b2:
        dxf_data = create_dxf_data(img_np, style_choice, space, thick, cont)
        st.download_button("Download DXF (Vector)", dxf_data, "cnc_art.dxf", "application/dxf")
        
