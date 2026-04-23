import streamlit as st
import cv2
import numpy as np
from PIL import Image
import io
import math

# --- PROCESSING ENGINE WITH SUPER-SAMPLING ---
def generate_smooth_cnc_art(img_array, style, spacing, weight, contrast):
    # 1. Prepare base image
    img = cv2.cvtColor(img_array, cv2.COLOR_RGB2GRAY)
    img = cv2.convertScaleAbs(img, alpha=contrast, beta=0)
    h, w = img.shape
    
    # 2. Super-Sampling: Create a canvas 4x larger for ultra-smooth edges
    upscale = 4
    h_up, w_up = h * upscale, w * upscale
    output_up = np.full((h_up, w_up), 255, dtype=np.uint8)
    
    center_up = (w_up // 2, h_up // 2)
    up_spacing = spacing * upscale

    if style == "Vertical":
        for x in range(0, w_up, up_spacing):
            # Sample from the original small image to find thickness
            orig_x = min(x // upscale, w - 1)
            column_img = img[:, orig_x]
            
            for y_orig in range(h):
                thickness = ((255 - column_img[y_orig]) / 255) * (up_spacing / 2) * weight
                t = int(thickness)
                if t > 0:
                    y_up = y_orig * upscale
                    # Draw a smooth rectangle for the segment
                    cv2.rectangle(output_up, (x - t, y_up), (x + t, y_up + upscale), 0, -1)

    elif style == "Circles":
        max_r = int(math.sqrt(w_up**2 + h_up**2) / 2)
        for r in range(up_spacing, max_r, up_spacing):
            # Higher number of steps for the larger canvas
            steps = int(2 * math.pi * r / 2) 
            for i in range(steps):
                angle = (i / steps) * 2 * math.pi
                x = int(center_up[0] + r * math.cos(angle))
                y = int(center_up[1] + r * math.sin(angle))
                
                # Check bounds on original image for brightness
                orig_x, orig_y = min(x // upscale, w-1), min(y // upscale, h-1)
                if 0 <= orig_x < w and 0 <= orig_y < h:
                    b = img[orig_y, orig_x]
                    t = int(((255 - b) / 255) * (up_spacing / 2) * weight)
                    if t > 0:
                        cv2.circle(output_up, (x, y), t, 0, -1)

    # 3. Downscale with Area Interpolation to "Anti-Alias" the pixels
    # This creates smooth gray edges that CNC lasers/software read as smooth curves
    final_raster = cv2.resize(output_up, (w, h), interpolation=cv2.INTER_AREA)
    
    return final_raster, output_up

# --- UI LOGIC ---
st.title("🚀 High-Precision CNC Designer")

# ... (Insert sliders here: style_choice, line_density, line_weight, img_contrast)

if uploaded_file:
    image = Image.open(uploaded_file)
    img_np = np.array(image)
    
    # Generate images
    preview, hd_raw = generate_smooth_cnc_art(img_np, style_choice, line_density, line_weight, img_contrast)
    
    st.image(preview, caption="Smooth Anti-Aliased Preview", use_container_width=True)

    # Export HD PNG
    st.write("### 📥 Export Ultra-HD File")
    # Using the upscaled raw image for the PNG download to keep maximum detail
    ret, png_buf = cv2.imencode(".png", hd_raw)
    st.download_button(
        label="Download 4K PNG (For Smooth CNC Path)",
        data=png_buf.tobytes(),
        file_name="cnc_ultra_hd.png",
        mime="image/png"
    )
    
