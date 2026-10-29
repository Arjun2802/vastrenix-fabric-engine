"""
Generates 4 authentic textile test swatches with realistic weave textures:
1. royal_banarasi_silk.jpg
2. maroon_floral_chanderi.jpg
3. emerald_cotton_linen.jpg
4. mustard_bandhani_print.jpg
"""
import os
import math
import numpy as np
from PIL import Image, ImageDraw

SAMPLES_DIR = "/Users/codekajugad/Desktop/vastrenix-fabric-engine/test_samples"
os.makedirs(SAMPLES_DIR, exist_ok=True)
SW_SIZE = 500

def create_banarasi_silk():
    # Rich royal blue/indigo silk with golden brocade motifs
    img = Image.new("RGB", (SW_SIZE, SW_SIZE), (28, 32, 92))
    draw = ImageDraw.Draw(img)
    
    # Weave micro-noise
    arr = np.array(img).astype(np.float32)
    noise = np.random.normal(0, 5, arr.shape)
    arr = np.clip(arr + noise, 0, 255).astype(np.uint8)
    img = Image.fromarray(arr)
    draw = ImageDraw.Draw(img)

    # Gold Paisley / floral zari motifs repeated
    gold = (220, 180, 75)
    gold_dark = (170, 130, 45)
    for y in range(50, SW_SIZE, 100):
        for x in range(50, SW_SIZE, 100):
            # Mango / Paisley shape
            draw.ellipse([x - 18, y - 24, x + 18, y + 24], outline=gold, width=2)
            draw.ellipse([x - 8, y - 12, x + 8, y + 12], fill=gold_dark)
            # Connecting vines
            draw.arc([x - 40, y - 40, x + 40, y + 40], 0, 180, fill=gold, width=1)
            
    out_path = os.path.join(SAMPLES_DIR, "royal_banarasi_silk.jpg")
    img.save(out_path, "JPEG", quality=95)
    return out_path

def create_maroon_chanderi():
    # Deep crimson maroon with delicate zari bootas
    img = Image.new("RGB", (SW_SIZE, SW_SIZE), (120, 20, 35))
    arr = np.array(img).astype(np.float32)
    noise = np.random.normal(0, 6, arr.shape)
    arr = np.clip(arr + noise, 0, 255).astype(np.uint8)
    img = Image.fromarray(arr)
    draw = ImageDraw.Draw(img)

    # Delicate gold diamond bootas
    gold = (235, 195, 90)
    for y in range(40, SW_SIZE, 70):
        for x in range(40, SW_SIZE, 70):
            draw.polygon([(x, y - 10), (x + 10, y), (x, y + 10), (x - 10, y)], fill=gold)
            draw.ellipse([x - 3, y - 3, x + 3, y + 3], fill=(120, 20, 35))

    out_path = os.path.join(SAMPLES_DIR, "maroon_floral_chanderi.jpg")
    img.save(out_path, "JPEG", quality=95)
    return out_path

def create_emerald_linen():
    # Forest emerald green with horizontal & vertical slub weave texture
    img = Image.new("RGB", (SW_SIZE, SW_SIZE), (24, 95, 65))
    arr = np.array(img).astype(np.float32)
    # Add crosshatch weave lines
    for i in range(0, SW_SIZE, 4):
        arr[i, :, :] += np.random.uniform(-10, 12)
        arr[:, i, :] += np.random.uniform(-10, 12)
    arr = np.clip(arr, 0, 255).astype(np.uint8)
    img = Image.fromarray(arr)
    
    out_path = os.path.join(SAMPLES_DIR, "emerald_cotton_linen.jpg")
    img.save(out_path, "JPEG", quality=95)
    return out_path

def create_mustard_bandhani():
    # Vibrant mustard yellow with white & red tie-dye Bandhani dots
    img = Image.new("RGB", (SW_SIZE, SW_SIZE), (230, 175, 25))
    draw = ImageDraw.Draw(img)
    
    # Bandhani concentric clusters
    for cy in range(60, SW_SIZE, 110):
        for cx in range(60, SW_SIZE, 110):
            # Cluster of dots forming a diamond
            for dx, dy in [(0, 0), (14, 0), (-14, 0), (0, 14), (0, -14), (10, 10), (-10, -10), (10, -10), (-10, 10)]:
                x, y = cx + dx, cy + dy
                draw.ellipse([x - 5, y - 5, x + 5, y + 5], fill=(190, 35, 30))  # red ring
                draw.ellipse([x - 3, y - 3, x + 3, y + 3], fill=(255, 255, 255)) # white center
                draw.point((x, y), fill=(230, 175, 25))

    out_path = os.path.join(SAMPLES_DIR, "mustard_bandhani_print.jpg")
    img.save(out_path, "JPEG", quality=95)
    return out_path

if __name__ == "__main__":
    p1 = create_banarasi_silk()
    p2 = create_maroon_chanderi()
    p3 = create_emerald_linen()
    p4 = create_mustard_bandhani()
    print("Created 4 sample fabrics:")
    print(" ", p1)
    print(" ", p2)
    print(" ", p3)
    print(" ", p4)
