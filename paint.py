import pygame
from datetime import datetime
from collections import deque

pygame.init()

WIDTH, HEIGHT = 1000, 700
TOOLBAR_H = 80

screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("TSIS 2 Paint")

canvas = pygame.Surface((WIDTH, HEIGHT - TOOLBAR_H))
canvas.fill((255, 255, 255))

font = pygame.font.SysFont("Arial", 20)
text_font = pygame.font.SysFont("Arial", 32)

BLACK = (0, 0, 0)
WHITE = (255, 255, 255)
GRAY = (210, 210, 210)
RED = (255, 0, 0)
GREEN = (0, 180, 0)
BLUE = (0, 0, 255)
YELLOW = (255, 220, 0)

colors = [BLACK, RED, GREEN, BLUE, YELLOW]
current_color = BLACK

tools = [
    "pencil", "line", "rect", "circle",
    "square", "right_tri", "eq_tri", "rhombus",
    "eraser", "fill", "text"
]

current_tool = "pencil"
brush_size = 5

drawing = False
start_pos = None
last_pos = None

typing = False
text_pos = None
typed_text = ""

undo_stack = []
redo_stack = []

clock = pygame.time.Clock()


def save_state():
    undo_stack.append(canvas.copy())
    if len(undo_stack) > 20:
        undo_stack.pop(0)
    redo_stack.clear()


def undo():
    global canvas
    if undo_stack:
        redo_stack.append(canvas.copy())
        canvas = undo_stack.pop()


def redo():
    global canvas
    if redo_stack:
        undo_stack.append(canvas.copy())
        canvas = redo_stack.pop()


def clear_canvas():
    save_state()
    canvas.fill(WHITE)


def canvas_pos(pos):
    return pos[0], pos[1] - TOOLBAR_H


def in_canvas(pos):
    return pos[1] >= TOOLBAR_H


def draw_toolbar():
    pygame.draw.rect(screen, GRAY, (0, 0, WIDTH, TOOLBAR_H))

    x = 10
    for tool in tools:
        rect = pygame.Rect(x, 10, 80, 28)
        color = (170, 170, 170) if tool == current_tool else (235, 235, 235)

        pygame.draw.rect(screen, color, rect)
        pygame.draw.rect(screen, BLACK, rect, 1)

        txt = font.render(tool, True, BLACK)
        screen.blit(txt, (x + 5, 15))

        x += 85

    x = 10
    y = 48

    for c in colors:
        rect = pygame.Rect(x, y, 28, 22)
        pygame.draw.rect(screen, c, rect)
        pygame.draw.rect(screen, BLACK, rect, 2)
        x += 35

    info = font.render(
        f"Brush: {brush_size}px | 1/2/3 size | Ctrl+S save | U undo | R redo | C clear",
        True,
        BLACK
    )
    screen.blit(info, (210, 50))


def get_tool_by_click(pos):
    x = 10
    for tool in tools:
        rect = pygame.Rect(x, 10, 80, 28)
        if rect.collidepoint(pos):
            return tool
        x += 85
    return None


def get_color_by_click(pos):
    x = 10
    y = 48

    for c in colors:
        rect = pygame.Rect(x, y, 28, 22)
        if rect.collidepoint(pos):
            return c
        x += 35

    return None


def flood_fill(surface, x, y, new_color):
    width, height = surface.get_size()

    if x < 0 or x >= width or y < 0 or y >= height:
        return

    target_color = surface.get_at((x, y))
    new_color = pygame.Color(*new_color)

    if target_color == new_color:
        return

    queue = deque()
    queue.append((x, y))

    while queue:
        px, py = queue.popleft()

        if px < 0 or px >= width or py < 0 or py >= height:
            continue

        if surface.get_at((px, py)) != target_color:
            continue

        surface.set_at((px, py), new_color)

        queue.append((px + 1, py))
        queue.append((px - 1, py))
        queue.append((px, py + 1))
        queue.append((px, py - 1))


def draw_shape(surface, tool, start, end, color, width):
    x1, y1 = start
    x2, y2 = end

    rect = pygame.Rect(
        min(x1, x2),
        min(y1, y2),
        abs(x2 - x1),
        abs(y2 - y1)
    )

    if tool == "line":
        pygame.draw.line(surface, color, start, end, width)

    elif tool == "rect":
        pygame.draw.rect(surface, color, rect, width)

    elif tool == "circle":
        radius = int(((x2 - x1) ** 2 + (y2 - y1) ** 2) ** 0.5)
        pygame.draw.circle(surface, color, start, radius, width)

    elif tool == "square":
        side = min(abs(x2 - x1), abs(y2 - y1))
        sx = x1 if x2 >= x1 else x1 - side
        sy = y1 if y2 >= y1 else y1 - side
        pygame.draw.rect(surface, color, (sx, sy, side, side), width)

    elif tool == "right_tri":
        points = [(x1, y1), (x1, y2), (x2, y2)]
        pygame.draw.polygon(surface, color, points, width)

    elif tool == "eq_tri":
        points = [(x1, y2), ((x1 + x2) // 2, y1), (x2, y2)]
        pygame.draw.polygon(surface, color, points, width)

    elif tool == "rhombus":
        cx = (x1 + x2) // 2
        cy = (y1 + y2) // 2
        points = [(cx, y1), (x2, cy), (cx, y2), (x1, cy)]
        pygame.draw.polygon(surface, color, points, width)


def save_canvas():
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"paint_{timestamp}.png"
    pygame.image.save(canvas, filename)
    print(f"Saved: {filename}")


running = True

while running:
    screen.fill(WHITE)
    screen.blit(canvas, (0, TOOLBAR_H))

    mouse_pos = pygame.mouse.get_pos()

    if drawing and start_pos and current_tool in [
        "line", "rect", "circle", "square",
        "right_tri", "eq_tri", "rhombus"
    ]:
        preview = canvas.copy()
        end = canvas_pos(mouse_pos)
        draw_shape(preview, current_tool, start_pos, end, current_color, brush_size)
        screen.blit(preview, (0, TOOLBAR_H))

    if typing and text_pos is not None:
        temp = text_font.render(typed_text + "|", True, current_color)
        screen.blit(temp, (text_pos[0], text_pos[1] + TOOLBAR_H))

    draw_toolbar()
    pygame.display.flip()

    for event in pygame.event.get():

        if event.type == pygame.QUIT:
            running = False

        elif event.type == pygame.KEYDOWN:

            if event.key == pygame.K_1:
                brush_size = 2

            elif event.key == pygame.K_2:
                brush_size = 5

            elif event.key == pygame.K_3:
                brush_size = 10

            elif event.key == pygame.K_s and pygame.key.get_mods() & pygame.KMOD_CTRL:
                save_canvas()

            elif event.key == pygame.K_u:
                undo()

            elif event.key == pygame.K_r:
                redo()

            elif event.key == pygame.K_c:
                clear_canvas()

            elif typing:
                if event.key == pygame.K_RETURN:
                    save_state()
                    rendered = text_font.render(typed_text, True, current_color)
                    canvas.blit(rendered, text_pos)

                    typing = False
                    typed_text = ""
                    text_pos = None

                elif event.key == pygame.K_ESCAPE:
                    typing = False
                    typed_text = ""
                    text_pos = None

                elif event.key == pygame.K_BACKSPACE:
                    typed_text = typed_text[:-1]

                else:
                    typed_text += event.unicode

        elif event.type == pygame.MOUSEBUTTONDOWN:
            pos = pygame.mouse.get_pos()

            selected_tool = get_tool_by_click(pos)
            if selected_tool:
                current_tool = selected_tool
                continue

            selected_color = get_color_by_click(pos)
            if selected_color:
                current_color = selected_color
                continue

            if in_canvas(pos):
                cpos = canvas_pos(pos)

                if current_tool == "fill":
                    save_state()
                    flood_fill(canvas, cpos[0], cpos[1], current_color)

                elif current_tool == "text":
                    typing = True
                    text_pos = cpos
                    typed_text = ""

                else:
                    save_state()
                    drawing = True
                    start_pos = cpos
                    last_pos = cpos

        elif event.type == pygame.MOUSEMOTION:
            if drawing and in_canvas(event.pos):
                cpos = canvas_pos(event.pos)

                if current_tool == "pencil":
                    pygame.draw.line(canvas, current_color, last_pos, cpos, brush_size)
                    last_pos = cpos

                elif current_tool == "eraser":
                    pygame.draw.line(canvas, WHITE, last_pos, cpos, brush_size)
                    last_pos = cpos

        elif event.type == pygame.MOUSEBUTTONUP:
            if drawing and in_canvas(event.pos):
                end_pos = canvas_pos(event.pos)

                if current_tool in [
                    "line", "rect", "circle", "square",
                    "right_tri", "eq_tri", "rhombus"
                ]:
                    draw_shape(canvas, current_tool, start_pos, end_pos, current_color, brush_size)

            drawing = False
            start_pos = None
            last_pos = None

    clock.tick(60)

pygame.quit()