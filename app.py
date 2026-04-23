import streamlit as st
import cv2
import numpy as np
from PIL import Image
import ezdxf
import io
import math

# 1. Page Config
st.set_page_config(page_title="CNC Art Studio", layout="wide")

# --- 2. THE ENGINE ---
def generate_cnc_style(img, style, spacing, weight):
    h, w = img.shape
    canvas = np.full((h, w), 255, dtype=np.uint8)
    center = (w // 2, h // 2)

    if style == "Vertical":
        for x in range(0, w, spacing):
            for y in range(0, h, 2):
                brightness = img[y, min(x, w-1)]
                t = int(((255 - brightness) / 255) * (spacing / 2) * weight)
                if t > 0:
                    cv2.line(canvas, (x, y), (x + t, y), 0, 1)

    elif style == "Spiral":
        max_r = int(math.sqrt(w**2 + h**2) / 2)
        b_spiral = spacing / (2 * math.pi)
        angle = 0.0
        while angle < (max_r / b_spiral) * 1.5:
            r = b_spiral * angle
            x, y = int(center[0] + r * math.cos(angle)), int(center[1] + r * math.sin(angle))
            if 0 <= x < w and 0 <= y < h:
                t = int(((255 - img[y, x]) / 255) * (spacing / 3) * weight)
                if t > 0: cv2.circle(canvas, (x, y), t, 0, -1)
            angle += 0.1

    elif style == "Circles":
        max_r = int(math.sqrt(w**2 + h**2) / 2)
        for r in range(spacing, max_r, spacing):
            steps = int(2 * math.pi * r / 4)
            for i in range(steps):
                angle = (i / steps) * 2 * math.pi
                x, y = int(center[0] + r * math.cos(angle)), int(center[1] + r * math.sin(angle))
                if 0 <= x < w and 0 <= y < h:
                    t = int(((255 - img[y, x]) / 255) * (spacing / 3) * weight)
                    if t > 0: cv2.circle(canvas, (x, y), t, 0, -1)

    elif style == "Dots":
        for y in range(0, h, spacing):
            for x in range(0, w, spacing):
                r = int(((255 - img[y, x]) / 255) * (spacing / 2) * weight)
                if r > 0: cv2.circle(canvas, (x, y), r, 0, -1)
    
    return canvas

# --- 3. UI ---
st.title("🎨 CNC Design Studio")

# Settings at the top
c1, c2, c3, c4 = st.columns(4)
with c1: style_choice = st.selectbox("Style", ["Vertical", "Spiral", "Circles", "Dots"])
with c2: space = st.slider("Spacing", 5, 50, 15)
with c3: thick = st.slider("Weight", 0.1, 3.0, 1.2)
with c4: cont = st.slider("Contrast", 1.0, 3.0, 1.8)

uploaded_file = st.file_uploader("Upload Image", type=["jpg", "png", "jpeg"])

if uploaded_file:
    # 1. Process Source
    raw_img = Image.open(uploaded_file).convert('L')
    raw_img.thumbnail((800, 800)) # Keep it fast
    img_np = np.array(raw_img)
    img_np = cv2.convertScaleAbs(img_np, alpha=cont, beta=0)

    # 2. Generate Result
    with st.spinner("Processing..."):
        result = generate_cnc_style(img_np, style_choice, space, thick)
        
        # Display Side-by-Side
        col_left, col_right = st.columns(2)
        with col_left:
            st.image(img_np, caption="Adjusted Source", use_container_width=True)
        with col_right:
            st.image(result, caption=f"CNC {style_choice} Result", use_container_width=True)

    # 3. Downloads
    st.write("### 📥 Download Files")
    d1, d2, d3 = st.columns(3)
    with d1:
        _, png = cv2.imencode(".png", result)
        st.download_button("Download PNG", png.tobytes(), "cnc.png", "image/png")
    with d2:
        _, tif = cv2.imencode(".tif", result)
        st.download_button("Download TIFF", tif.tobytes(), "cnc.tif", "image/tiff")
    with d3:
        # DXF Export logic for smooth paths
        doc = ezdxf.new()
        msp = doc.modelspace()
        # (Dots example for DXF)
        if style_choice == "Dots":
            for y in range(0, img_np.shape[0], space):
                for x in range(0, img_np.shape[1], space):
                    r = ((255 - img_np[y, x])/255) * (space/2) * thick
                    if r > 1: msp.add_circle((x*0.1, -y*0.1), r*0.1)
        
        dxf_io = io.StringIO()
        doc.write(dxf_io)
        st.download_button("Download DXF", dxf_io.getvalue(), "cnc.dxf", "application/dxf")
        
