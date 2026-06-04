import pygame
import sys
import os
import csv

pygame.init()

WIDTH, HEIGHT = 1000, 400
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Six Dots")

BG = (30, 30, 30)
font = pygame.font.SysFont("couriernew", 14)
small_font = pygame.font.SysFont("couriernew", 11)

DOT_R = 18
DOT_Y = 80
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
SIXD_DIR = os.path.join(SCRIPT_DIR, "sixd")

labels = ["orchestrator", "causal diagram", "double triangle", "bus", "log", "do"]
colors = [
    (100, 160, 240),
    (80, 210, 120),
    (230, 90, 90),
    (230, 190, 60),
    (180, 100, 220),
    (60, 200, 200),
]

n = len(labels)
spacing = WIDTH // (n + 1)
dot_positions = [(spacing * (i + 1), DOT_Y) for i in range(n)]

KP_MAP = {
    pygame.K_KP1: '1', pygame.K_KP2: '2', pygame.K_KP3: '3',
    pygame.K_KP4: '4', pygame.K_KP5: '5', pygame.K_KP6: '6',
    pygame.K_KP7: '7', pygame.K_KP8: '8', pygame.K_KP9: '9',
}

active = 0
combo_text = None
combo_number = 0
csv_lines = []
csv_error = None


def load_csv(name):
    global csv_lines, csv_error
    path = os.path.join(SIXD_DIR, name + ".csv")
    try:
        with open(path, newline="", encoding="utf-8") as f:
            rows = list(csv.reader(f))
        csv_lines = [", ".join(row) for row in rows]
        csv_error = None
    except FileNotFoundError:
        csv_lines = []
        csv_error = f"not found: {path}"


clock = pygame.time.Clock()

while True:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            pygame.quit()
            sys.exit()
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_RIGHT:
                active = (active + 1) % n
                combo_number = 0
                combo_text = None
                csv_lines, csv_error = [], None
            elif event.key == pygame.K_LEFT:
                active = (active - 1) % n
                combo_number = 0
                combo_text = None
                csv_lines, csv_error = [], None
            elif event.key == pygame.K_DOWN:
                combo_number = (combo_number % 9) + 1
                combo_text = labels[active].replace(" ", "") + str(combo_number)
                csv_lines, csv_error = [], None
            elif pygame.K_1 <= event.key <= pygame.K_9:
                combo_text = labels[active].replace(" ", "") + chr(event.key)
                csv_lines, csv_error = [], None
            elif event.key in KP_MAP:
                combo_text = labels[active].replace(" ", "") + KP_MAP[event.key]
                csv_lines, csv_error = [], None
            elif event.key in (pygame.K_RETURN, pygame.K_KP_ENTER):
                if combo_text:
                    load_csv(combo_text)

    screen.fill(BG)

    for i, (x, y) in enumerate(dot_positions):
        r = DOT_R + 4 if i == active else DOT_R
        pygame.draw.circle(screen, colors[i], (x, y), r)
        if i == active:
            pygame.draw.circle(screen, (255, 255, 255), (x, y), r + 4, 2)
        label_surf = font.render(labels[i], True, (255, 255, 255) if i == active else (200, 200, 200))
        screen.blit(label_surf, label_surf.get_rect(centerx=x, top=y + DOT_R + 14))

    content_top = DOT_Y + DOT_R + 44
    if combo_text:
        combo_surf = font.render(combo_text, True, (200, 200, 200))
        screen.blit(combo_surf, combo_surf.get_rect(centerx=WIDTH // 2, top=content_top))
        content_top += 28

    if csv_error:
        err_surf = small_font.render(csv_error, True, (220, 80, 80))
        screen.blit(err_surf, (20, content_top))
    else:
        y_pos = content_top
        for line in csv_lines:
            if y_pos > HEIGHT - 16:
                break
            screen.blit(small_font.render(line, True, (180, 180, 180)), (20, y_pos))
            y_pos += 16

    pygame.display.flip()
    clock.tick(60)
