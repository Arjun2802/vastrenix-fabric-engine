"""
Generates high-resolution, photorealistic 2D templates for the 5 garments:
1. kurta
2. saree
3. shirt
4. palazzo
5. nehru_jacket
"""
import os
import numpy as np
from PIL import Image, ImageDraw, ImageFilter

TEMPLATES_DIR = "/Users/codekajugad/Desktop/vastrenix-fabric-engine/app/templates"
WIDTH, HEIGHT = 800, 1000

def create_kurta_template(out_dir):
    os.makedirs(out_dir, exist_ok=True)
    mask = Image.new("L", (WIDTH, HEIGHT), 0)
    draw = ImageDraw.Draw(mask)

    # Kurta Silhouette Points
    # Shoulders, 3/4 sleeves, straight torso, side slits, bottom hem
    points = [
        (330, 140),  # left neck
        (220, 180),  # left shoulder
        (130, 360),  # left sleeve cuff top
        (165, 410),  # left sleeve cuff bottom
        (270, 320),  # left armpit
        (265, 580),  # left waist to hip (slit top)
        (250, 880),  # left hem corner
        (550, 880),  # right hem corner
        (535, 580),  # right slit top
        (530, 320),  # right armpit
        (635, 410),  # right sleeve cuff bottom
        (670, 360),  # right sleeve cuff top
        (580, 180),  # right shoulder
        (470, 140),  # right neck
    ]
    draw.polygon(points, fill=255)
    # Neck notch
    draw.pieslice([370, 110, 430, 190], 0, 180, fill=0)
    # Center slit
    draw.line([(400, 150), (400, 240)], fill=0, width=4)

    # Smooth the mask edges slightly
    mask = mask.filter(ImageFilter.GaussianBlur(1.0))
    mask.save(os.path.join(out_dir, "silhouette_mask.png"))

    # Shading Overlay (Folds, Torso Cylindrical Lighting, Armpit creases)
    shading = Image.new("RGB", (WIDTH, HEIGHT), (220, 220, 220))
    sdraw = ImageDraw.Draw(shading)

    # 1. Torso cylindrical highlight down the center
    for x in range(250, 550):
        # Center peak at 400
        dist = abs(x - 400) / 150.0
        val = int(245 - (dist ** 1.5) * 45)
        sdraw.line([(x, 160), (x, 880)], fill=(val, val, val))

    # 2. Vertical drape pleats & fall shadows
    folds = [310, 360, 440, 490]
    for fx in folds:
        sdraw.line([(fx, 420), (fx - 15, 875)], fill=(160, 160, 160), width=6)
        sdraw.line([(fx + 8, 420), (fx - 7, 875)], fill=(250, 250, 250), width=4)

    # 3. Armpit creases
    sdraw.line([(270, 320), (330, 380)], fill=(150, 150, 150), width=8)
    sdraw.line([(530, 320), (470, 380)], fill=(150, 150, 150), width=8)

    # 4. Sleeve folds
    sdraw.line([(220, 220), (150, 380)], fill=(175, 175, 175), width=5)
    sdraw.line([(580, 220), (650, 380)], fill=(175, 175, 175), width=5)

    # Gaussian blur to turn lines into soft fabric folds
    shading = shading.filter(ImageFilter.GaussianBlur(12.0))
    shading.save(os.path.join(out_dir, "shading_overlay.png"))

    # Accent Overlay (Neckline placket, buttons)
    accent = Image.new("RGBA", (WIDTH, HEIGHT), (0, 0, 0, 0))
    adraw = ImageDraw.Draw(accent)
    # Placket band
    adraw.rectangle([393, 150, 407, 300], fill=(230, 225, 215, 240), outline=(120, 115, 105, 180), width=1)
    # 4 small gold buttons
    for by in [175, 210, 245, 280]:
        adraw.ellipse([396, by, 404, by + 8], fill=(215, 175, 75, 255), outline=(140, 100, 30, 255))
    accent.save(os.path.join(out_dir, "accent_overlay.png"))

def create_saree_template(out_dir):
    os.makedirs(out_dir, exist_ok=True)
    mask = Image.new("L", (WIDTH, HEIGHT), 0)
    draw = ImageDraw.Draw(mask)

    # Saree Drape Silhouette (Draped blouse, sweeping pallu across left shoulder, pleated skirt)
    # Blouse & Pallu top
    points_pallu = [
        (320, 160), (230, 190), (180, 320), (140, 520), (160, 720), (220, 820),
        (280, 680), (330, 460), (370, 360), (460, 360), (510, 430),
        (560, 360), (620, 260), (560, 190), (460, 160)
    ]
    # Draped Skirt bottom
    points_skirt = [
        (330, 460), (260, 890), (540, 890), (480, 460)
    ]
    draw.polygon(points_pallu, fill=255)
    draw.polygon(points_skirt, fill=255)
    draw.ellipse([360, 130, 440, 210], fill=0) # Neck

    mask = mask.filter(ImageFilter.GaussianBlur(1.0))
    mask.save(os.path.join(out_dir, "silhouette_mask.png"))

    # Shading (Dramatic diagonal S-curve pleats & cascading pallu folds)
    shading = Image.new("RGB", (WIDTH, HEIGHT), (225, 225, 225))
    sdraw = ImageDraw.Draw(shading)

    # Diagonal drape pleats across chest
    for offset in range(-60, 80, 25):
        sdraw.line([(240 + offset, 190), (460 + offset, 440)], fill=(155, 155, 155), width=8)
        sdraw.line([(248 + offset, 190), (468 + offset, 440)], fill=(255, 255, 255), width=5)

    # Skirt vertical pleats
    for px in [330, 370, 400, 430, 470]:
        sdraw.line([(px, 460), (px - 10, 885)], fill=(145, 145, 145), width=7)
        sdraw.line([(px + 6, 460), (px - 4, 885)], fill=(250, 250, 250), width=4)

    # Pallu falling drape shadow
    sdraw.line([(180, 320), (160, 720)], fill=(140, 140, 140), width=14)

    shading = shading.filter(ImageFilter.GaussianBlur(14.0))
    shading.save(os.path.join(out_dir, "shading_overlay.png"))

    # Saree Gold Zari Border Accent
    accent = Image.new("RGBA", (WIDTH, HEIGHT), (0, 0, 0, 0))
    adraw = ImageDraw.Draw(accent)
    # Pallu border line in rich gold
    adraw.line([(230, 190), (140, 520), (160, 720), (220, 820)], fill=(218, 165, 32, 230), width=10)
    adraw.line([(260, 885), (540, 885)], fill=(218, 165, 32, 240), width=12) # Hem border
    accent.save(os.path.join(out_dir, "accent_overlay.png"))

def create_shirt_template(out_dir):
    os.makedirs(out_dir, exist_ok=True)
    mask = Image.new("L", (WIDTH, HEIGHT), 0)
    draw = ImageDraw.Draw(mask)

    # Men's Tailored Shirt Silhouette
    points = [
        (330, 160),  # left collar
        (190, 220),  # left shoulder
        (110, 480),  # left sleeve cuff top
        (150, 520),  # left cuff bottom
        (250, 380),  # left armpit
        (270, 720),  # left waist / curved hem
        (340, 750),  # left hem scoop
        (400, 760),  # center hem
        (460, 750),  # right hem scoop
        (530, 720),  # right waist
        (550, 380),  # right armpit
        (650, 520),  # right cuff bottom
        (690, 480),  # right cuff top
        (610, 220),  # right shoulder
        (470, 160),  # right collar
    ]
    draw.polygon(points, fill=255)
    # Collar V opening
    draw.polygon([(360, 160), (400, 250), (440, 160)], fill=0)

    mask = mask.filter(ImageFilter.GaussianBlur(1.0))
    mask.save(os.path.join(out_dir, "silhouette_mask.png"))

    # Shading (Chest contours, side body curves, sleeve elbow creases)
    shading = Image.new("RGB", (WIDTH, HEIGHT), (225, 225, 225))
    sdraw = ImageDraw.Draw(shading)

    # Torso gradient
    for x in range(260, 540):
        dist = abs(x - 400) / 140.0
        val = int(250 - (dist ** 2) * 55)
        sdraw.line([(x, 180), (x, 750)], fill=(val, val, val))

    # Waist side taper shadows
    sdraw.line([(250, 380), (270, 720)], fill=(160, 160, 160), width=10)
    sdraw.line([(550, 380), (530, 720)], fill=(160, 160, 160), width=10)

    # Elbow folds
    sdraw.line([(190, 340), (130, 480)], fill=(165, 165, 165), width=7)
    sdraw.line([(610, 340), (670, 480)], fill=(165, 165, 165), width=7)

    shading = shading.filter(ImageFilter.GaussianBlur(12.0))
    shading.save(os.path.join(out_dir, "shading_overlay.png"))

    # Accents (Collar wings, button placket, white pearl buttons)
    accent = Image.new("RGBA", (WIDTH, HEIGHT), (0, 0, 0, 0))
    adraw = ImageDraw.Draw(accent)
    # Collar wings
    adraw.polygon([(330, 160), (370, 240), (400, 210), (370, 160)], fill=(240, 240, 245, 245), outline=(130, 130, 140, 200))
    adraw.polygon([(470, 160), (430, 240), (400, 210), (430, 160)], fill=(240, 240, 245, 245), outline=(130, 130, 140, 200))
    # Front button placket
    adraw.rectangle([393, 210, 407, 740], fill=(245, 245, 250, 230), outline=(140, 140, 150, 180))
    # Pearl buttons with thread cross
    for by in [250, 320, 390, 460, 530, 600, 670]:
        adraw.ellipse([396, by, 404, by + 8], fill=(255, 255, 255, 255), outline=(120, 120, 130, 255))
        adraw.line([(398, by + 4), (402, by + 4)], fill=(100, 100, 110, 200))
    accent.save(os.path.join(out_dir, "accent_overlay.png"))

def create_palazzo_template(out_dir):
    os.makedirs(out_dir, exist_ok=True)
    mask = Image.new("L", (WIDTH, HEIGHT), 0)
    draw = ImageDraw.Draw(mask)

    # Wide-leg flowy Palazzo pants
    points = [
        (300, 240),  # waistband left
        (500, 240),  # waistband right
        (560, 460),  # right hip
        (640, 890),  # right hem outer
        (430, 890),  # right hem inner
        (400, 520),  # crotch center
        (370, 890),  # left hem inner
        (160, 890),  # left hem outer
        (240, 460),  # left hip
    ]
    draw.polygon(points, fill=255)

    mask = mask.filter(ImageFilter.GaussianBlur(1.0))
    mask.save(os.path.join(out_dir, "silhouette_mask.png"))

    # Shading (Deep vertical pleats & flowing drape flared toward hem)
    shading = Image.new("RGB", (WIDTH, HEIGHT), (225, 225, 225))
    sdraw = ImageDraw.Draw(shading)

    # Vertical pleats for each leg
    for lx in [220, 270, 320, 360]:
        sdraw.line([(lx + 40, 260), (lx - 20, 885)], fill=(150, 150, 150), width=9)
        sdraw.line([(lx + 48, 260), (lx - 12, 885)], fill=(255, 255, 255), width=5)

    for rx in [440, 480, 530, 580]:
        sdraw.line([(rx - 40, 260), (rx + 20, 885)], fill=(150, 150, 150), width=9)
        sdraw.line([(rx - 32, 260), (rx + 28, 885)], fill=(255, 255, 255), width=5)

    # Inseam shadow
    sdraw.line([(400, 520), (370, 890)], fill=(130, 130, 130), width=10)
    sdraw.line([(400, 520), (430, 890)], fill=(130, 130, 130), width=10)

    shading = shading.filter(ImageFilter.GaussianBlur(15.0))
    shading.save(os.path.join(out_dir, "shading_overlay.png"))

    # Accent (Elastic waistband & drawstring tie)
    accent = Image.new("RGBA", (WIDTH, HEIGHT), (0, 0, 0, 0))
    adraw = ImageDraw.Draw(accent)
    adraw.rectangle([300, 240, 500, 265], fill=(235, 230, 220, 240), outline=(130, 125, 115, 200), width=1)
    # Drawstring knot
    adraw.ellipse([395, 250, 405, 260], fill=(210, 200, 185, 255))
    adraw.line([(398, 258), (390, 290)], fill=(210, 200, 185, 255), width=2)
    adraw.line([(402, 258), (410, 288)], fill=(210, 200, 185, 255), width=2)
    accent.save(os.path.join(out_dir, "accent_overlay.png"))

def create_nehru_jacket_template(out_dir):
    os.makedirs(out_dir, exist_ok=True)
    mask = Image.new("L", (WIDTH, HEIGHT), 0)
    draw = ImageDraw.Draw(mask)

    # Sleeveless Nehru Jacket / Modi Coat
    points = [
        (340, 170),  # left neck
        (230, 200),  # left shoulder
        (260, 360),  # left armhole
        (265, 680),  # left waist hem
        (535, 680),  # right waist hem
        (540, 360),  # right armhole
        (570, 200),  # right shoulder
        (460, 170),  # right neck
    ]
    draw.polygon(points, fill=255)
    # Mandarin collar
    draw.rectangle([340, 140, 460, 175], fill=255)

    mask = mask.filter(ImageFilter.GaussianBlur(1.0))
    mask.save(os.path.join(out_dir, "silhouette_mask.png"))

    # Shading (Crisp tailored darts, chest pocket depth, structured shoulders)
    shading = Image.new("RGB", (WIDTH, HEIGHT), (225, 225, 225))
    sdraw = ImageDraw.Draw(shading)

    # Front chest depth
    for x in range(270, 530):
        dist = abs(x - 400) / 130.0
        val = int(248 - (dist ** 2) * 50)
        sdraw.line([(x, 180), (x, 675)], fill=(val, val, val))

    # Tailored dart lines
    sdraw.line([(330, 350), (325, 620)], fill=(160, 160, 160), width=4)
    sdraw.line([(470, 350), (475, 620)], fill=(160, 160, 160), width=4)

    shading = shading.filter(ImageFilter.GaussianBlur(10.0))
    shading.save(os.path.join(out_dir, "shading_overlay.png"))

    # Accents (Mandarin band collar, left chest welt pocket with pocket square, brass buttons)
    accent = Image.new("RGBA", (WIDTH, HEIGHT), (0, 0, 0, 0))
    adraw = ImageDraw.Draw(accent)
    # Mandarin band collar
    adraw.rectangle([340, 142, 460, 172], fill=(235, 235, 240, 220), outline=(130, 130, 140, 220), width=1)
    # Center placket line
    adraw.line([(400, 172), (400, 678)], fill=(100, 100, 110, 220), width=2)
    # Chest pocket on left chest
    adraw.rectangle([305, 280, 365, 292], fill=(230, 230, 235, 240), outline=(120, 120, 130, 220))
    # Silk pocket square tip
    adraw.polygon([(325, 280), (335, 260), (345, 280)], fill=(220, 50, 60, 255))
    # 6 Antique brass buttons
    for by in [220, 300, 380, 460, 540, 620]:
        adraw.ellipse([395, by, 405, by + 10], fill=(195, 155, 60, 255), outline=(110, 80, 20, 255), width=1)
    accent.save(os.path.join(out_dir, "accent_overlay.png"))

def build_all():
    print("Building 5 garment templates...")
    templates = {
        "kurta": create_kurta_template,
        "saree": create_saree_template,
        "shirt": create_shirt_template,
        "palazzo": create_palazzo_template,
        "nehru_jacket": create_nehru_jacket_template,
    }
    for name, func in templates.items():
        tdir = os.path.join(TEMPLATES_DIR, name)
        func(tdir)
        print(f"  ✓ {name} template created in {tdir}")
    print("All 5 templates generated successfully!")

if __name__ == "__main__":
    build_all()
