import pygame
import sys
import os
import subprocess

pygame.init()

WIDTH, HEIGHT = 900, 500
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Glasses Launcher")

BG = (248, 244, 238)
LINK_COLOR = (20, 80, 200)
LINK_HOVER = (210, 55, 20)

font = pygame.font.SysFont("couriernew", 15)

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))

# Load glasses image
img_path = os.path.join(SCRIPT_DIR, "glasses.png")
glasses_img = pygame.image.load(img_path).convert_alpha()
orig_w, orig_h = glasses_img.get_size()

scale = (HEIGHT - 40) / orig_h
img_w = int(orig_w * scale)
img_h = int(orig_h * scale)
glasses_img = pygame.transform.smoothscale(glasses_img, (img_w, img_h))
img_x = (WIDTH - img_w) // 2
img_y = 20

# Lens centers estimated from image fractions
left_cx  = img_x + int(img_w * 0.28)
right_cx = img_x + int(img_w * 0.76)
lens_cy  = img_y + int(img_h * 0.72)

links = [
    {"label": "six_dots.py",      "file": os.path.join(SCRIPT_DIR, "six_dots.py"),       "cx": left_cx,  "cy": lens_cy - 24},
    {"label": "yellow.py",        "file": os.path.join(SCRIPT_DIR, "yellow.py"),          "cx": left_cx,  "cy": lens_cy + 24},
    {"label": "prompt maker.exe", "file": os.path.join(SCRIPT_DIR, "prompt maker.exe"),  "cx": right_cx, "cy": lens_cy},
]

for link in links:
    link["surf"]       = font.render(link["label"], True, LINK_COLOR)
    link["surf_hover"] = font.render(link["label"], True, LINK_HOVER)
    link["rect"]       = link["surf"].get_rect(center=(link["cx"], link["cy"]))

clock = pygame.time.Clock()

while True:
    mx, my = pygame.mouse.get_pos()

    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            pygame.quit()
            sys.exit()
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            for link in links:
                if link["rect"].collidepoint(event.pos):
                    try:
                        if link["file"].endswith(".py"):
                            subprocess.Popen([sys.executable, link["file"]])
                        else:
                            os.startfile(link["file"])
                    except Exception:
                        pass

    screen.fill(BG)
    screen.blit(glasses_img, (img_x, img_y))

    for link in links:
        hovered = link["rect"].collidepoint(mx, my)
        surf = link["surf_hover"] if hovered else link["surf"]
        screen.blit(surf, link["rect"])
        if hovered:
            pygame.draw.line(screen, LINK_HOVER,
                             (link["rect"].left, link["rect"].bottom + 1),
                             (link["rect"].right, link["rect"].bottom + 1), 1)

    pygame.display.flip()
    clock.tick(60)
