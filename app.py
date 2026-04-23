import streamlit as st  # This MUST stay at the top
import cv2
import numpy as np
from PIL import Image
import ezdxf
import io
import math

# 1. This must be the FIRST Streamlit command called
st.set_page_config(page_title="CNC Art Studio", layout="wide")

# --- 2. PROCESSING CORE ---
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
        for r in range(0, max_r, spacing):
            sample_y = max(0, center[1] - r)
            brightness = img[sample_y, center[0]]
            t = int(((255 - brightness) / 255) * (spacing / 2) * weight)
            if t > 0:
                cv2.circle(output, center, r, 0, max(1, t))

    elif style == "Dots":
        for y in range(0, h, spacing):
            for x in range(0, w, spacing):
                brightness = img[y, x]
                r = int(((255 - brightness) / 255) * (spacing / 2) * weight)
                if r > 0:
                    cv2.circle(output, (x, y), r, 0, -1)

    elif style == "Spiral":
        max_r = int(math.sqrt(w**2 + h**2) / 2)
        b = spacing / (2 * math.pi)
        angle = 0.0
        while True:
            r = b * angle
            if r > max_r: break
            x_pos = int(center[0] + r * math.cos(angle))
            y_pos = int(center[1] + r * math.sin(angle))
            if 0 <= x_pos < w and 0 <= y_pos < h:
                brightness = img[y_pos, x_pos]
                t = int(((255 - brightness) / 255) * (spacing / 2) * weight)
                if t > 0:
                    cv2.circle(output, (x_pos, y_pos), t, 0, -1)
            angle += 0.1 / (r/spacing + 1)

    return output

# --- 3. VECTOR EXPORT ---
def create_dxf_data(img_array, style, spacing, weight, contrast):
    doc = ezdxf.new('R2010')
    msp = doc.modelspace()
    img = cv2.cvtColor(img_array, cv2.COLOR_RGB2GRAY)
    img = cv2.convertScaleAbs(img, alpha=contrast, beta=0)
    h, w = img.shape
    scale = 0.1 

    if style == "Dots" or style == "Spiral" or style == "Circles":
        step = spacing if style == "Dots" else 5
        for y in range(0, h, step):
            for x in range(0, w, step):
                b = img[y, x]
                r = ((255 - b) / 255) * (spacing / 2) * weight
                if r > 0.5:
                    msp.add_circle((x * scale, (h - y) * scale), radius=r * scale)
    else:
        for x in range(0, w, spacing):
            msp.add_line((x * scale, 0), (x * scale, h * scale))

    out_str = io.StringIO()
    doc.write(out_str)
    return out_str.getvalue()

# --- 4. UI LAYOUT ---
st.title("🎨 CNC Design Engine")

st.write("### 🛠️ Step 1: Adjust Design Settings")
col_a, col_b, col_c, col_d = st.columns(4)
with col_a:
    style_choice = st.selectbox("Pattern Type", ["Vertical", "Crosshatch", "Circles", "Dots", "Spiral"])
with col_b:
    line_density = st.slider("Density", 4, 40, 12)
with col_c:
    line_weight = st.slider("Thickness", 0.1, 3.0, 1.0)
with col_d:
    img_contrast = st.slider("Contrast", 1.0, 3.0, 1.5)

st.write("### 📸 Step 2: Upload Image")
uploaded_file = st.file_uploader("Choose a Portrait", type=["jpg", "png", "jpeg"])

if uploaded_file:
    image = Image.open(uploaded_file)
    img_np = np.array(image)
    
    with st.spinner("Generating Art..."):
        preview_img = generate_cnc_art(img_np, style_choice, line_density, line_weight, img_contrast)
        st.image(preview_img, caption="CNC Preview", use_container_width=True)

    st.write("### 💾 Step 3: Download")
    c1, c2 = st.columns(2)
    with c1:
        ret, tiff_buffer = cv2.imencode(".tif", preview_img)
        st.download_button("Download TIFF", tiff_buffer.tobytes(), "cnc_art.tif", "image/tiff")
    with c2:
        dxf_data = create_dxf_data(img_np, style_choice, line_density, line_weight, img_contrast)
        st.download_button("Download DXF", dxf_data, "cnc_art.dxf", "application/dxf")
            
