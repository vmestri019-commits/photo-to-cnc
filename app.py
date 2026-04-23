import cv2
import numpy as np
import streamlit as st
from PIL import Image
import ezdxf
import io

def create_dxf(img_array, style, spacing, thickness_mult, contrast):
    # Setup DXF document
    doc = ezdxf.new('R2010')
    msp = doc.modelspace()
    
    # Process image
    img = cv2.cvtColor(img_array, cv2.COLOR_RGB2GRAY)
    img = cv2.convertScaleAbs(img, alpha=contrast, beta=0)
    h, w = img.shape
    
    # Scale factor to keep DXF coordinates manageable (e.g., mm)
    scale = 0.1 

    if style == "Vertical":
        for x in range(0, w, spacing):
            for y in range(0, h, 2): # Step 2 for performance
                brightness = img[y, x]
                # Map brightness to line thickness
                t = ((255 - brightness) / 255) * (spacing / 2) * thickness_mult
                if t > 0.1:
                    # Create a thin rectangle (box) to represent the variable line
                    # CNCs usually treat these as "pockets" or "fills"
                    p1 = (x * scale - t*scale, (h-y) * scale)
                    p2 = (x * scale + t*scale, (h-y) * scale)
                    msp.add_line(p1, p2)

    elif style == "Dots":
        for y in range(0, h, spacing):
            for x in range(0, w, spacing):
                brightness = img[y, x]
                r = ((255 - brightness) / 255) * (spacing / 2) * thickness_mult
                if r > 0.5:
                    msp.add_circle((x * scale, (h-y) * scale), radius=r*scale)

    # Save to a byte stream
    dxf_stream = io.StringIO()
    doc.write(dxf_stream)
    return dxf_stream.getvalue()

def create_tiff(img_array):
    # Convert numpy array to PIL and save as TIFF
    # Use '1' for 1-bit (strict B&W) or 'L' for grayscale
    pil_img = Image.fromarray(img_array)
    img_byte_arr = io.BytesIO()
    pil_img.save(img_byte_arr, format='TIFF', compression='tiff_lzw')
    return img_byte_arr.getvalue()

# --- Streamlit UI Additions ---

if st.button('Process Design'):
    # Generate the raster image for preview
    final_raster = generate_cnc_art(img_array, style_choice, line_spacing, weight, contrast_val)
    st.image(final_raster, caption="Preview")

    # Column layout for downloads
    col1, col2 = st.columns(2)
    
    with col1:
        # Download TIFF (Best for Laser/Engraving software like LightBurn)
        tiff_data = create_tiff(final_raster)
        st.download_button("Download TIFF", tiff_data, "cnc_art.tiff", "image/tiff")
        
    with col2:
        # Download DXF (Best for Routers/Plotters like AutoCAD, VCarve)
        dxf_string = create_dxf(img_array, style_choice, line_spacing, weight, contrast_val)
        st.download_button("Download DXF", dxf_string, "cnc_art.dxf", "application/dxf")
        
