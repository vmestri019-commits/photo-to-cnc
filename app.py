import streamlit as st
import cv2
import numpy as np
from PIL import Image
import ezdxf
import io
import math

st.set_page_config(page_title="CNC Vector Studio", layout="wide")

# --- 1. CORE MATH FUNCTIONS ---
def get_processed_img(img_array, contrast):
    img = cv2.cvtColor(img_array, cv2.COLOR_RGB2GRAY)
    return cv2.convertScaleAbs(img, alpha=contrast, beta=0)

# --- 2. VECTOR ENGINE (DXF) ---
def create_dxf_data(img, style, spacing, weight):
    doc = ezdxf.new('R2010')
    msp = doc.modelspace()
    h, w = img.shape
    scale = 0.1 
    center = (w // 2, h // 2)

    if style == "Vertical":
        for x in range(0, w, spacing):
            points = [( (x + (((255 - img[y, x])/255)*(spacing/2)*weight)) * scale, (h-y)*scale ) 
                      for y in range(0, h, 4)]
            if len(points) > 1: msp.add_lwpolyline(points)

    elif style == "Spiral":
        max_r = int(math.sqrt(w**2 + h**2) / 2)
        b_val = spacing / (2 * math.pi)
        angle, points = 0.0, []
        while True:
            r = b_val * angle
            if r > max_r: break
            px, py = int(center[0] + r * math.cos(angle)), int(center[1] + r * math.sin(angle))
            if 0 <= px < w and 0 <= py < h:
                t = ((255 - img[py, px]) / 255) * (spacing / 4) * weight
                points.append(((center[0] + (r + t) * math.cos(angle)) * scale, (h - (center[1] + (r + t) * math.sin(angle))) * scale))
            angle += 0.2 # Increased step for speed
        if len(points) > 1: msp.add_lwpolyline(points)

    elif style == "Circles":
        max_r = int(math.sqrt(w**2 + h**2) / 2)
        for r in range(spacing, max_r, spacing):
            points = []
            steps = int(2 * math.pi * r / 5) # Optimized step
            for i in range(steps + 1):
                angle = (i / steps) * 2 * math.pi
                px, py = int(center[0] + r * math.cos(angle)), int(center[1] + r * math.sin(angle))
                if 0 <= px < w and 0 <= py < h:
                    t = ((255 - img[py, px]) / 255) * (spacing / 4) * weight
                    points.append(((center[0] + (r+t)*math.cos(angle))*scale, (h-(center[1] + (r+t)*math.sin(angle)))*scale))
            if len(points) > 1: msp.add_lwpolyline(points, dxfattribs={'closed': True})

    elif style == "Dots":
        for y in range(0, h, spacing):
            for x in range(0, w, spacing):
                r = ((255 - img[y, x]) / 255) * (spacing / 2) * weight
                if r > 0.5: msp.add_circle((x * scale, (h - y) * scale), radius=r * scale)

    out_str = io.StringIO()
    doc.write(out_str)
    return out_str.getvalue()

# --- 3. UI LAYOUT ---
st.title("🚀 High-Speed CNC Engine")

# Move settings to a container to prevent accidental refreshes
with st.container():
    c1, c2, c3, c4 = st.columns(4)
    with c1: style_choice = st.selectbox("Design Style", ["Vertical", "Spiral", "Circles", "Dots"])
    with c2: space = st.slider("Spacing", 5, 50, 15)
    with c3: thick = st.slider("Weight", 0.5, 3.0, 1.2)
    with c4: cont = st.slider("Contrast", 1.0, 3.0, 1.5)

uploaded_file = st.file_uploader("Upload Image", type=["jpg", "png", "jpeg"])

if uploaded_file:
    # 1. Load and process
    raw_img = Image.open(uploaded_file)
    # Resize for preview speed (Crucial for performance!)
    raw_img.thumbnail((800, 800)) 
    img_np = np.array(raw_img)
    processed = get_processed_img(img_np, cont)
    
    # 2. Display Preview
    st.image(processed, caption="Source Preview (Adjust Contrast)", width=400)
    
    if st.button("Generate Final CNC Files"):
        with st.spinner("Processing High-Resolution Vectors..."):
            dxf_out = create_dxf_data(processed, style_choice, space, thick)
            
            # Create a simple representation for PNG
            ret, png_buf = cv2.imencode(".png", processed)
            
            st.success("Generation Complete!")
            
            b1, b2 = st.columns(2)
            with b1:
                st.download_button("💾 Download DXF (Smooth Path)", dxf_out, "cnc_vector.dxf", "application/dxf")
            with b2:
                st.download_button("🖼️ Download PNG", png_buf.tobytes(), "cnc_raster.png", "image/png")
                
