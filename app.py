import cv2
import numpy as np

def generate_cnc_engraving(image_path, line_spacing=10, contrast_boost=1.5):
    # 1. Load image and convert to Grayscale
    img = cv2.imread(image_path, cv2.IMREAD_GRAYSCALE)
    if img is None:
        return "Error: Image not found."

    # 2. Enhance Contrast (CNC looks better with deep blacks and bright whites)
    # Applying simple linear scaling for high contrast
    img = cv2.convertScaleAbs(img, alpha=contrast_boost, beta=0)
    
    height, width = img.shape
    # Create a blank white canvas for the output
    output = np.full((height, width), 255, dtype=np.uint8)

    # 3. Iterate through the image in steps of 'line_spacing'
    for x in range(0, width, line_spacing):
        # Sample the column of the original image
        column_pixels = img[:, x]
        
        # Calculate thickness: (255 - brightness) / 255 
        # Darker (0) = thicker line. Lighter (255) = thinner line.
        thicknesses = (255 - column_pixels).astype(float) / 255.0
        
        # 4. Draw the vertical line with varying width
        for y in range(height):
            # Calculate half-width based on thickness and spacing
            # We multiply by line_spacing to ensure lines can touch in dark areas
            half_w = int((thicknesses[y] * line_spacing) / 2)
            
            if half_w > 0:
                # Fill pixels around the center 'x' to create the line
                start_x = max(0, x - half_w)
                end_x = min(width - 1, x + half_w)
                output[y, start_x:end_x] = 0 # Set to Black

    return output

# --- Implementation ---
result = generate_cnc_engraving('marilyn_source.jpg', line_spacing=8, contrast_boost=1.8)
cv2.imwrite('cnc_ready_art.png', result)
