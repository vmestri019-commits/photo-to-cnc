    elif style == "Spiral":
        # Calculate maximum radius
        max_r = int(math.sqrt(w**2 + h**2) / 2)
        # 'a' controls the starting gap, 'b' controls the growth per turn
        b = spacing / (2 * math.pi)
        angle = 0.0
        
        while True:
            r = b * angle
            if r > max_r:
                break
            
            # Convert polar (r, angle) to Cartesian (x, y)
            x_pos = int(center[0] + r * math.cos(angle))
            y_pos = int(center[1] + r * math.sin(angle))
            
            if 0 <= x_pos < w and 0 <= y_pos < h:
                brightness = img[y_pos, x_pos]
                t = int(((255 - brightness) / 255) * (spacing / 2) * weight)
                if t > 0:
                    cv2.circle(output, (x_pos, y_pos), t, 0, -1)
            
            # Increment angle based on r to keep dot density consistent
            # As radius increases, we need smaller angle steps
            angle += 0.05 / (r/spacing + 1)
            
