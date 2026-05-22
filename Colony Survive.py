"""
3D Planet Colonizer - CSE 423 Group Project (Group 1, Section 4)
Members:
  - Safayat Rahman  [24101587] - Building System + Resource Management
  - Samia Rahman    [23201064] - Meteor System + Defense + Collision
  - Tahmidul Islam  [23201440] - Camera + Terrain + HUD + Game Flow

Only OpenGL functions used in the Assignment 3 template are used here, plus
glEnable(GL_DEPTH_TEST) for proper 3D occlusion.

Novel mechanics on top of the spec:
  * Central Core Reactor that must be defended (game ends if it dies even with lives left)
  * Visible energy beams from each Mine to its bound Resource node
  * Three meteor archetypes:
        Standard (red)    - falls straight
        Splitter (orange) - splits into two smaller meteors when destroyed
        Seeker  (magenta) - drifts toward the nearest building while falling
  * Day/Night cycle that scales meteor fall speed (night is dangerous)
  * Wormhole Event - a swirling ring appears every few waves; entering with the
    cursor teleports you to a mirrored grid cell, useful for emergency repairs
"""

from OpenGL.GL import *
from OpenGL.GLUT import *
from OpenGL.GLU import *
import math
import random

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------
WIN_W, WIN_H = 1000, 800
GRID_N = 12                       # cells per side (even number => no center cell conflict with reactor)
CELL  = 80                        # world units per cell
GRID_HALF = (GRID_N * CELL) / 2.0 # = 480
WALL_H = 120

FOVY = 90
NEAR_CLIP, FAR_CLIP = 0.1, 5000.0

# Building type ids
B_NONE, B_HOUSE, B_MINE, B_SHIELD, B_REACTOR = 0, 1, 2, 3, 4
BUILD_COST   = {B_HOUSE: 30, B_MINE: 50, B_SHIELD: 80}
UPGRADE_COST = {B_HOUSE: 40, B_MINE: 60, B_SHIELD: 90}

# Meteor archetypes
M_STANDARD, M_SPLITTER, M_SEEKER = 0, 1, 2

# Camera modes
CAM_OVERVIEW, CAM_BUILDER, CAM_CINEMATIC = 0, 1, 2

# ---------------------------------------------------------------------------
# Game State (globals - matches template style)
# ---------------------------------------------------------------------------
def fresh_state():
    return {
        # Player / economy
        "resources": 120,
        "lives": 3,
        "score": 0,
        "wave": 0,
        "wave_timer": 240,            # frames until first wave
        "wave_announce": 0,           # countdown for the on-screen banner (0 = no banner)
        "shield_energy": 100.0,
        "shield_max": 100.0,
        "game_over": False,

        # Player cursor (grid coords, 0..GRID_N-1)
        "cursor": [GRID_N // 2, GRID_N // 2 - 2],

        # Grid state: each cell holds a dict or None
        "grid": [[None for _ in range(GRID_N)] for _ in range(GRID_N)],

        # Resource nodes: list of {gx, gy, amount, scale}
        "nodes": [],

        # Live meteors: list of dicts
        "meteors": [],

        # Visual fx (explosions, craters, beams temp, popups)
        "explosions": [],
        "craters": {},

        # Central core
        "reactor_hp": 100,

        # Wormhole event
        "wormhole": None,             # {gx, gy, age}

        # Camera
        "cam_mode": CAM_OVERVIEW,
        "cam_yaw": 35.0,              # degrees
        "cam_pitch": 45.0,
        "cam_pitch_target": 45.0,     # smooth animation target
        "cam_dist": 950.0,
        "cam_orbit_t": 0.0,           # used in cinematic mode
        "cam_blend": 0.0,             # 0..1 for transition blending

        # Time / cycle
        "t": 0,                       # frame counter
        "day_phase": 0.0,             # 0..1 day, 1..2 night, modulo 2

        # Cheat / debug
        "cheat_vision": False,
        "cheat_mode": False,          # god-mode toggle (C key)

        # Pending ground impact warnings (cell highlighted red)
        "warn_cells": {},
    }

S = fresh_state()


# ---------------------------------------------------------------------------
# Utility helpers
# ---------------------------------------------------------------------------
def cell_to_world(gx, gy):
    """Center of cell (gx, gy) in world coords on the floor (z=0)."""
    wx = -GRID_HALF + (gx + 0.5) * CELL
    wy = -GRID_HALF + (gy + 0.5) * CELL
    return wx, wy

def in_bounds(gx, gy):
    return 0 <= gx < GRID_N and 0 <= gy < GRID_N

def find_node(gx, gy):
    for n in S["nodes"]:
        if n["gx"] == gx and n["gy"] == gy:
            return n
    return None

def neighbors4(gx, gy):
    return [(gx + dx, gy + dy) for dx, dy in ((1,0),(-1,0),(0,1),(0,-1)) if in_bounds(gx+dx, gy+dy)]

def is_reactor_cell(gx, gy):
    # Reactor occupies the 2x2 around the geometric center
    c = GRID_N // 2
    return gx in (c-1, c) and gy in (c-1, c)

def can_place(gx, gy):
    if not in_bounds(gx, gy):
        return False
    if is_reactor_cell(gx, gy):
        return False
    if S["grid"][gx][gy] is not None:
        return False
    if find_node(gx, gy) is not None:
        return False
    return True


def shield_effective_radius(gx, gy, level):
    """Calculate shield dome radius with proper boundary capping."""
    wx, wy = cell_to_world(gx, gy)
    base = 110 + 50 * (level - 1)
    # Cap radius so it can never extend past grid boundaries
    dx = min(GRID_HALF - wx, wx + GRID_HALF)
    dy = min(GRID_HALF - wy, wy + GRID_HALF)
    return min(base, dx, dy)


# ---------------------------------------------------------------------------
# Initialisation
# ---------------------------------------------------------------------------
def spawn_initial_nodes(count=8):
    placed = 0
    tries = 0
    while placed < count and tries < 500:
        tries += 1
        gx = random.randint(0, GRID_N - 1)
        gy = random.randint(0, GRID_N - 1)
        if is_reactor_cell(gx, gy):
            continue
        if find_node(gx, gy) is not None:
            continue
        if S["grid"][gx][gy] is not None:
            continue
        S["nodes"].append({"gx": gx, "gy": gy, "amount": 100.0, "scale": 1.0})
        placed += 1

def reset_game():
    global S
    S = fresh_state()
    spawn_initial_nodes()


# ---------------------------------------------------------------------------
# Drawing primitives
# ---------------------------------------------------------------------------
def draw_text(x, y, text, font=GLUT_BITMAP_HELVETICA_18, color=(1, 1, 1)):
    glColor3f(*color)
    glMatrixMode(GL_PROJECTION)
    glPushMatrix()
    glLoadIdentity()
    gluOrtho2D(0, WIN_W, 0, WIN_H)
    glMatrixMode(GL_MODELVIEW)
    glPushMatrix()
    glLoadIdentity()
    glRasterPos2f(x, y)
    for ch in text:
        glutBitmapCharacter(font, ord(ch))
    glPopMatrix()
    glMatrixMode(GL_PROJECTION)
    glPopMatrix()
    glMatrixMode(GL_MODELVIEW)


def draw_grid_floor():
    """Alternating-color tile floor. Highlights cursor, warning cells, craters."""
    cur_gx, cur_gy = S["cursor"]
    glBegin(GL_QUADS)
    for gx in range(GRID_N):
        for gy in range(GRID_N):
            x0 = -GRID_HALF + gx * CELL
            y0 = -GRID_HALF + gy * CELL
            x1 = x0 + CELL
            y1 = y0 + CELL

            # base checker color (subtly modulated by day phase)
            day = day_factor()
            if (gx + gy) % 2 == 0:
                base = (0.55*day + 0.10, 0.40*day + 0.08, 0.30*day + 0.10)
            else:
                base = (0.42*day + 0.08, 0.30*day + 0.06, 0.22*day + 0.08)

            # crater darkening
            ck = (gx, gy)
            if ck in S["craters"]:
                base = (0.10, 0.05, 0.05)

            # warn flash
            if ck in S["warn_cells"] and (S["t"] // 6) % 2 == 0:
                base = (0.9, 0.15, 0.15)

            # cursor highlight
            if gx == cur_gx and gy == cur_gy and (S["t"] // 8) % 2 == 0:
                base = (0.95, 0.95, 0.30)

            # reactor pad
            if is_reactor_cell(gx, gy):
                base = (0.20, 0.55, 0.85)

            glColor3f(*base)
            glVertex3f(x0, y0, 0)
            glVertex3f(x1, y0, 0)
            glVertex3f(x1, y1, 0)
            glVertex3f(x0, y1, 0)
    glEnd()

    # Grid lines on top
    glColor3f(0.05, 0.05, 0.05)
    glBegin(GL_LINES)
    for i in range(GRID_N + 1):
        v = -GRID_HALF + i * CELL
        glVertex3f(v, -GRID_HALF, 0.5)
        glVertex3f(v,  GRID_HALF, 0.5)
        glVertex3f(-GRID_HALF, v, 0.5)
        glVertex3f( GRID_HALF, v, 0.5)
    glEnd()


def draw_walls():
    """Four boundary walls using glutSolidCube + scaling via translate stacks."""
    h = WALL_H
    s = GRID_HALF
    color = (0.30, 0.30, 0.42)

    # We don't have glScalef-only walls because glutSolidCube takes single size,
    # so we tile cubes along each side.
    glColor3f(*color)
    cube_size = 60
    n_cubes = int((2 * s) // cube_size) + 1
    for i in range(n_cubes):
        cx = -s + i * cube_size + cube_size / 2
        # north / south walls
        glPushMatrix(); glTranslatef(cx,  s + cube_size/2, h/2); glutSolidCube(cube_size); glPopMatrix()
        glPushMatrix(); glTranslatef(cx, -s - cube_size/2, h/2); glutSolidCube(cube_size); glPopMatrix()
        # east / west walls
        glPushMatrix(); glTranslatef( s + cube_size/2, cx, h/2); glutSolidCube(cube_size); glPopMatrix()
        glPushMatrix(); glTranslatef(-s - cube_size/2, cx, h/2); glutSolidCube(cube_size); glPopMatrix()


def draw_sky():
    """A scatter of distant 'star' spheres + a moon/sun depending on day phase."""
    # Stars - drawn as GL_POINTS so cheap; only at night-ish
    night = 1.0 - day_factor()
    if night > 0.05:
        glPointSize(2.0)
        glColor3f(0.9, 0.9, 1.0)
        glBegin(GL_POINTS)
        # Use a deterministic pseudo-random scatter so they stay fixed
        random.seed(7)
        for _ in range(120):
            sx = random.uniform(-1, 1) * 1800
            sy = random.uniform(-1, 1) * 1800
            sz = random.uniform(900, 1500)
            glVertex3f(sx, sy, sz)
        random.seed()
        glEnd()

    # Sun / moon
    phase = S["day_phase"] % 2.0
    angle = phase * math.pi
    sun_x = math.cos(angle) * 1300
    sun_z = math.sin(angle) * 600 + 600
    sun_y = -1300

    glPushMatrix()
    glTranslatef(sun_x, sun_y, sun_z)
    if phase < 1.0:
        glColor3f(1.0, 0.9, 0.5)         # sun
    else:
        glColor3f(0.85, 0.85, 1.0)       # moon
    gluSphere(gluNewQuadric(), 70, 16, 16)
    glPopMatrix()


def day_factor():
    """1.0 at noon, 0.15 at midnight."""
    phase = S["day_phase"] % 2.0
    if phase < 1.0:
        # 0..1 -> daylight curve
        return 0.15 + 0.85 * math.sin(phase * math.pi)
    else:
        return 0.15


# ---------------------------------------------------------------------------
# Building rendering
# ---------------------------------------------------------------------------
def draw_house(scale, level, dmg):
    glPushMatrix()
    base_h = 70 + 25 * (level - 1)
    s = scale
    # main body - cuboid via cube + scale
    color = (0.25, 0.45, 0.95)
    if dmg == 1:
        color = (0.18, 0.30, 0.55)
    glColor3f(*color)
    glPushMatrix()
    glTranslatef(0, 0, (base_h * s) / 2)
    glScalef(0.8 * s, 0.8 * s, (base_h / 60.0) * s)
    glutSolidCube(60)
    glPopMatrix()
    # roof - small cube on top
    glColor3f(0.85, 0.30, 0.30)
    glPushMatrix()
    glTranslatef(0, 0, base_h * s + 8 * s)
    glScalef(0.9 * s, 0.9 * s, 0.25 * s)
    glutSolidCube(60)
    glPopMatrix()
    glPopMatrix()


def draw_mine(scale, level, dmg):
    glPushMatrix()
    glColor3f(0.95, 0.85, 0.20) if dmg == 0 else glColor3f(0.55, 0.45, 0.10)
    h = 50 + 20 * (level - 1)
    glPushMatrix()
    glScalef(scale, scale, scale)
    gluCylinder(gluNewQuadric(), 30, 18, h, 16, 4)
    glPopMatrix()
    # animated drill on top
    glColor3f(0.7, 0.7, 0.75)
    glPushMatrix()
    glTranslatef(0, 0, h * scale)
    glRotatef((S["t"] * 8) % 360, 0, 0, 1)
    glScalef(scale, scale, scale)
    gluCylinder(gluNewQuadric(), 12, 0, 35, 8, 2)
    glPopMatrix()
    glPopMatrix()


def draw_shield_tower(scale, level, dmg, radius):
    glPushMatrix()
    glColor3f(0.30, 0.85, 0.40) if dmg == 0 else glColor3f(0.18, 0.45, 0.22)
    h = 60 + 15 * (level - 1)
    glPushMatrix()
    glScalef(scale, scale, scale)
    gluCylinder(gluNewQuadric(), 22, 22, h, 12, 3)
    glPopMatrix()
    # top crystal
    glColor3f(0.4, 1.0, 0.6)
    glPushMatrix()
    glTranslatef(0, 0, h * scale + 25 * scale)
    gluSphere(gluNewQuadric(), 22 * scale, 12, 12)
    glPopMatrix()

    # Wireframe protective dome (only if energy > 0)
    if S["shield_energy"] > 0:
        flicker = 1.0 if S["shield_energy"] > 15 else (0.3 + 0.7 * ((S["t"] // 4) % 2))
        glColor3f(0.3 * flicker, 1.0 * flicker, 0.6 * flicker)
        draw_wire_dome(radius, h * scale + 25 * scale)
    glPopMatrix()


def draw_wire_dome(radius, base_z):
    """Wireframe hemisphere using GL_LINES (template-only primitives)."""
    rings = 6
    slices = 16
    glBegin(GL_LINES)
    # latitude rings
    for i in range(1, rings + 1):
        phi = (i / rings) * (math.pi / 2.0)
        z = math.cos(phi) * radius
        r = math.sin(phi) * radius
        prev = None
        for j in range(slices + 1):
            th = (j / slices) * 2.0 * math.pi
            x = math.cos(th) * r
            y = math.sin(th) * r
            if prev is not None:
                glVertex3f(prev[0], prev[1], base_z + z)
                glVertex3f(x, y, base_z + z)
            prev = (x, y)
    # longitude lines
    for j in range(slices):
        th = (j / slices) * 2.0 * math.pi
        prev = None
        for i in range(rings + 1):
            phi = (i / rings) * (math.pi / 2.0)
            x = math.cos(th) * math.sin(phi) * radius
            y = math.sin(th) * math.sin(phi) * radius
            z = math.cos(phi) * radius
            if prev is not None:
                glVertex3f(prev[0], prev[1], base_z + prev[2])
                glVertex3f(x, y, base_z + z)
            prev = (x, y, z)
    glEnd()


def draw_reactor():
    """Central pulsing core - novel: gameplay objective to defend."""
    cx, cy = 0, 0  # at origin (between the four reactor cells)
    glPushMatrix()
    glTranslatef(cx, cy, 40)
    # base
    glColor3f(0.15, 0.30, 0.50)
    gluCylinder(gluNewQuadric(), 80, 70, 40, 18, 3)
    # core
    pulse = 1.0 + 0.15 * math.sin(S["t"] * 0.1)
    glPushMatrix()
    glTranslatef(0, 0, 60)
    hp = max(0.0, S["reactor_hp"] / 100.0) if "reactor_hp" in S else 1.0
    glColor3f(0.3 + 0.7 * (1 - hp), 0.6 * hp, 0.9 * hp)
    gluSphere(gluNewQuadric(), 45 * pulse, 18, 18)
    glPopMatrix()
    # spinning ring made of cube tokens
    glColor3f(0.8, 0.9, 1.0)
    for k in range(8):
        a = (S["t"] * 1.2 + k * 45) % 360
        glPushMatrix()
        glRotatef(a, 0, 0, 1)
        glTranslatef(95, 0, 70)
        glutSolidCube(10)
        glPopMatrix()
    glPopMatrix()


def draw_buildings():
    for gx in range(GRID_N):
        for gy in range(GRID_N):
            b = S["grid"][gx][gy]
            if b is None:
                continue
            wx, wy = cell_to_world(gx, gy)
            glPushMatrix()
            # tilt if damaged
            if b["dmg"] > 0:
                glTranslatef(wx, wy, 0)
                glRotatef(8, 1, 1, 0)
            else:
                glTranslatef(wx, wy, 0)
            if b["type"] == B_HOUSE:
                draw_house(b["scale"], b["level"], b["dmg"])
            elif b["type"] == B_MINE:
                draw_mine(b["scale"], b["level"], b["dmg"])
            elif b["type"] == B_SHIELD:
                radius = shield_effective_radius(gx, gy, b["level"])
                b["radius"] = radius
                draw_shield_tower(b["scale"], b["level"], b["dmg"], radius)
            glPopMatrix()


def draw_resource_nodes():
    for n in S["nodes"]:
        wx, wy = cell_to_world(n["gx"], n["gy"])
        glPushMatrix()
        glTranslatef(wx, wy, 18)
        pulse = 1.0 + 0.08 * math.sin(S["t"] * 0.15 + n["gx"] + n["gy"])
        glColor3f(1.0, 0.85, 0.20)
        gluSphere(gluNewQuadric(), 18 * n["scale"] * pulse, 12, 12)
        # small particles above
        glColor3f(1.0, 1.0, 0.6)
        glPointSize(3)
        glBegin(GL_POINTS)
        for k in range(4):
            ph = (S["t"] * 2 + k * 30) % 60
            glVertex3f(0, 0, 25 + ph)
        glEnd()
        glPopMatrix()


def draw_energy_beams():
    """Novel: energy beams from each mine to its nearest active resource node."""
    glBegin(GL_LINES)
    for gx in range(GRID_N):
        for gy in range(GRID_N):
            b = S["grid"][gx][gy]
            if b is None or b["type"] != B_MINE or b["dmg"] >= 2:
                continue
            target = mine_target_node(gx, gy)
            if target is None:
                continue
            wx, wy = cell_to_world(gx, gy)
            tx, ty = cell_to_world(target["gx"], target["gy"])
            # animate beam color
            phase = (S["t"] * 0.2) % 1.0
            glColor3f(1.0, 0.8 - 0.3 * phase, 0.2)
            glVertex3f(wx, wy, 50)
            glVertex3f(tx, ty, 25)
    glEnd()


def mine_target_node(gx, gy):
    """A mine drains the nearest adjacent (within 2 cells) resource node."""
    best = None
    best_d = 99
    for n in S["nodes"]:
        if n["amount"] <= 0:
            continue
        d = abs(n["gx"] - gx) + abs(n["gy"] - gy)
        if d <= 2 and d < best_d:
            best_d = d
            best = n
    return best


def draw_meteors():
    for m in S["meteors"]:
        glPushMatrix()
        glTranslatef(m["x"], m["y"], m["z"])
        glRotatef(m["spin"], 1, 1, 0)
        if m["kind"] == M_STANDARD:
            glColor3f(0.95, 0.30, 0.10)
        elif m["kind"] == M_SPLITTER:
            glColor3f(1.0, 0.55, 0.10)
        else:  # seeker
            glColor3f(0.95, 0.30, 0.85)
        gluSphere(gluNewQuadric(), m["r"], 10, 10)
        # trailing tail using GL_LINES
        glColor3f(1.0, 0.7, 0.3)
        glBegin(GL_LINES)
        glVertex3f(0, 0, 0)
        glVertex3f(0, 0, 60 + m["r"])
        glEnd()
        glPopMatrix()

    # Cheat vision: draw a predicted impact line for every falling meteor
    if S["cheat_vision"]:
        glColor3f(0.2, 1.0, 1.0)
        glBegin(GL_LINES)
        for m in S["meteors"]:
            if m["vz"] >= 0:
                continue
            steps = m["z"] / max(1.0, abs(m["vz"]))
            px = m["x"] + m["vx"] * steps
            py = m["y"] + m["vy"] * steps
            # also clamp the predicted line to grid bounds
            px = max(-GRID_HALF, min(GRID_HALF, px))
            py = max(-GRID_HALF, min(GRID_HALF, py))
            glVertex3f(m["x"], m["y"], m["z"])
            glVertex3f(px, py, 0)
        glEnd()


def draw_explosions():
    for e in S["explosions"]:
        glPushMatrix()
        glTranslatef(e["x"], e["y"], e["z"])
        glColor3f(1.0, 0.55 - 0.3 * (e["age"] / e["life"]), 0.15)
        gluSphere(gluNewQuadric(), e["r"], 12, 12)
        glPopMatrix()


def draw_wormhole():
    w = S["wormhole"]
    if w is None:
        return
    wx, wy = cell_to_world(w["gx"], w["gy"])
    glPushMatrix()
    glTranslatef(wx, wy, 30)
    # Spinning purple ring made of small cubes
    for k in range(20):
        a = (S["t"] * 4 + k * 18) % 360
        glPushMatrix()
        glRotatef(a, 0, 0, 1)
        glTranslatef(45, 0, 0)
        glRotatef(a, 0, 1, 0)
        glColor3f(0.6 + 0.4 * math.sin(a * 0.05), 0.2, 0.9)
        glutSolidCube(8)
        glPopMatrix()
    glPopMatrix()


def draw_cursor_beacon():
    if S["cam_mode"] == CAM_CINEMATIC:
        return
    gx, gy = S["cursor"]
    wx, wy = cell_to_world(gx, gy)
    glPushMatrix()
    glTranslatef(wx, wy, 0)
    # vertical beam using GL_LINES
    glColor3f(1.0, 1.0, 0.2)
    glBegin(GL_LINES)
    glVertex3f(0, 0, 0)
    glVertex3f(0, 0, 240)
    glEnd()
    # floating diamond marker
    glPushMatrix()
    glTranslatef(0, 0, 60 + 10 * math.sin(S["t"] * 0.2))
    glRotatef(S["t"] * 2, 0, 0, 1)
    glColor3f(1.0, 1.0, 0.2)
    glutSolidCube(14)
    glPopMatrix()
    glPopMatrix()


# ---------------------------------------------------------------------------
# Game logic
# ---------------------------------------------------------------------------
def start_wave():
    S["wave"] += 1
    S["wave_announce"] = 180
    base = 4 + S["wave"]
    # LOWERED: Base speed from 1.6 to 0.6, wave multiplier from 0.25 to 0.1
    speed = 0.6 + 0.1 * S["wave"]
    # LOWERED: Night penalty from 0.6 (60% faster) to 0.3 (30% faster)
    night_mul = 1.0 + (1.0 - day_factor()) * 0.3
    speed *= night_mul

    # Spawn margin keeps meteors comfortably inside the grid from frame one
    margin = 50

    for _ in range(base):
        kind = M_STANDARD
        roll = random.random()
        if S["wave"] >= 2 and roll < 0.25:
            kind = M_SPLITTER
        elif S["wave"] >= 3 and roll < 0.45:
            kind = M_SEEKER
        x = random.uniform(-GRID_HALF + margin, GRID_HALF - margin)
        y = random.uniform(-GRID_HALF + margin, GRID_HALF - margin)
        z = random.uniform(900, 1300)
        r = random.uniform(20, 30) + 0.7 * S["wave"]
        S["meteors"].append({
            "x": x, "y": y, "z": z,
            "vx": random.uniform(-0.4, 0.4),
            "vy": random.uniform(-0.4, 0.4),
            "vz": -speed,
            "r": r, "kind": kind,
            "spin": 0,
        })

    # Sometimes spawn the wormhole event
    if S["wave"] % 2 == 0 and S["wormhole"] is None:
        for _ in range(80):
            gx = random.randint(0, GRID_N - 1)
            gy = random.randint(0, GRID_N - 1)
            if can_place(gx, gy):
                S["wormhole"] = {"gx": gx, "gy": gy, "age": 0}
                break


def clamp_meteor_in_grid(m):
    """Bounce a meteor off the grid walls so it can never escape the play field."""
    lo_x = -GRID_HALF + m["r"]
    hi_x =  GRID_HALF - m["r"]
    lo_y = -GRID_HALF + m["r"]
    hi_y =  GRID_HALF - m["r"]
    if m["x"] < lo_x:
        m["x"] = lo_x
        m["vx"] = abs(m["vx"])
    elif m["x"] > hi_x:
        m["x"] = hi_x
        m["vx"] = -abs(m["vx"])
    if m["y"] < lo_y:
        m["y"] = lo_y
        m["vy"] = abs(m["vy"])
    elif m["y"] > hi_y:
        m["y"] = hi_y
        m["vy"] = -abs(m["vy"])


def update_meteors():
    new_list = []
    spawned = []  # accumulator for splitter children so they survive the rebind
    for m in list(S["meteors"]):
        m["spin"] = (m["spin"] + 6) % 360
        m["x"] += m["vx"]
        m["y"] += m["vy"]
        m["z"] += m["vz"]

        # Seeker drifts toward nearest building
        if m["kind"] == M_SEEKER:
            target = nearest_building(m["x"], m["y"])
            if target is not None:
                tx, ty = cell_to_world(*target)
                dx, dy = tx - m["x"], ty - m["y"]
                d = math.hypot(dx, dy) + 1e-3
                m["vx"] += (dx / d) * 0.05
                m["vy"] += (dy / d) * 0.05
                # Cap horizontal speed so seekers don't spiral out of control
                m["vx"] *= 0.96
                m["vy"] *= 0.96
                vh = math.hypot(m["vx"], m["vy"])
                if vh > 1.5:
                    m["vx"] *= 1.5 / vh
                    m["vy"] *= 1.5 / vh

        # Keep every meteor inside the grid - bounce off the walls
        clamp_meteor_in_grid(m)

        # Shield interception
        intercepted = False
        if S["shield_energy"] > 0:
            for gx in range(GRID_N):
                for gy in range(GRID_N):
                    b = S["grid"][gx][gy]
                    if b is None or b["type"] != B_SHIELD or b["dmg"] >= 2:
                        continue
                    bx, by = cell_to_world(gx, gy)
                    R = b.get("radius", 110) + m["r"]   # account for meteor's own radius
                    bz = 60 + 15 * (b["level"] - 1) + 25  # crystal height
                    if (m["x"] - bx) ** 2 + (m["y"] - by) ** 2 + (m["z"] - bz) ** 2 <= R * R:
                        intercepted = True
                        S["shield_energy"] = max(0, S["shield_energy"] - 8)
                        break
                if intercepted:
                    break
        if intercepted:
            handle_meteor_destroyed(m, by_shield=True, spawned=spawned)
            continue

        # Hit ground?
        if m["z"] <= m["r"]:
            ground_impact(m)
            continue

        new_list.append(m)
    S["meteors"] = new_list + spawned


def nearest_building(x, y):
    best = None
    best_d = 1e9
    for gx in range(GRID_N):
        for gy in range(GRID_N):
            b = S["grid"][gx][gy]
            if b is None:
                continue
            wx, wy = cell_to_world(gx, gy)
            d = (wx - x) ** 2 + (wy - y) ** 2
            if d < best_d:
                best_d = d
                best = (gx, gy)
    return best


def handle_meteor_destroyed(m, by_shield, spawned=None):
    S["explosions"].append({"x": m["x"], "y": m["y"], "z": m["z"], "r": 8, "age": 0, "life": 18})
    sink = spawned if spawned is not None else S["meteors"]
    if m["kind"] == M_SPLITTER and m["r"] > 18:
        for _ in range(2):
            sink.append({
                "x": m["x"] + random.uniform(-30, 30),
                "y": m["y"] + random.uniform(-30, 30),
                "z": m["z"],
                "vx": random.uniform(-0.6, 0.6),
                "vy": random.uniform(-0.6, 0.6),
                "vz": m["vz"] * 0.85,
                "r": m["r"] * 0.6,
                "kind": M_STANDARD,
                "spin": 0,
            })
    if by_shield:
        S["score"] += 10


def ground_impact(m):
    # find which cell (if any) and what's there
    gx = int((m["x"] + GRID_HALF) // CELL)
    gy = int((m["y"] + GRID_HALF) // CELL)
    # safety clamp - meteors are bounced inside the grid, but be defensive
    gx = max(0, min(GRID_N - 1, gx))
    gy = max(0, min(GRID_N - 1, gy))

    S["craters"][(gx, gy)] = 240
    S["explosions"].append({"x": m["x"], "y": m["y"], "z": 5, "r": 18, "age": 0, "life": 30})

    # In cheat mode, the explosion still plays for spectacle but nothing takes damage
    if S["cheat_mode"]:
        return

    # Reactor hit?
    if is_reactor_cell(gx, gy):
        S["reactor_hp"] = S.get("reactor_hp", 100) - 20
        if S["reactor_hp"] <= 0:
            S["lives"] = 0
            S["game_over"] = True
        return

    # Building hit?
    b = S["grid"][gx][gy]
    if b is not None:
        b["dmg"] += 1
        if b["dmg"] >= 2:
            S["grid"][gx][gy] = None
        return

    # Resource node hit?
    n = find_node(gx, gy)
    if n is not None:
        n["amount"] = max(0, n["amount"] - 50)
        return

    # Empty ground in front of cursor area => life loss if very close
    cgx, cgy = S["cursor"]
    if abs(cgx - gx) + abs(cgy - gy) <= 1:
        S["lives"] -= 1
        if S["lives"] <= 0:
            S["game_over"] = True


def update_economy():
    # Mines pull from bound resource nodes
    if S["t"] % 30 == 0:
        gain = 0
        for gx in range(GRID_N):
            for gy in range(GRID_N):
                b = S["grid"][gx][gy]
                if b is None or b["type"] != B_MINE or b["dmg"] >= 2:
                    continue
                target = mine_target_node(gx, gy)
                if target is None:
                    continue
                rate = 2 + (b["level"] - 1)
                rate = min(rate, target["amount"])
                target["amount"] -= rate
                gain += rate
                if target["amount"] <= 0:
                    target["scale"] = max(0.0, target["scale"] - 0.05)
        S["resources"] += int(gain)

    # Drop empty / shrunken nodes, occasionally spawn new
    S["nodes"] = [n for n in S["nodes"] if not (n["amount"] <= 0 and n["scale"] <= 0.05)]
    for n in S["nodes"]:
        if n["amount"] <= 0:
            n["scale"] = max(0.0, n["scale"] - 0.01)
    if S["t"] % 600 == 0 and len(S["nodes"]) < 12:
        for _ in range(40):
            gx = random.randint(0, GRID_N - 1)
            gy = random.randint(0, GRID_N - 1)
            if can_place(gx, gy):
                S["nodes"].append({"gx": gx, "gy": gy, "amount": 80.0, "scale": 0.1})
                break

    # Growth animation
    for gx in range(GRID_N):
        for gy in range(GRID_N):
            b = S["grid"][gx][gy]
            if b is None:
                continue
            if b["scale"] < 1.0:
                b["scale"] = min(1.0, b["scale"] + 0.04)

    for n in S["nodes"]:
        if n["scale"] < 1.0 and n["amount"] > 0:
            n["scale"] = min(1.0, n["scale"] + 0.03)

    # Shield slow recharge (instant in cheat mode)
    if S["cheat_mode"]:
        S["shield_energy"] = S["shield_max"]
    elif S["shield_energy"] < S["shield_max"]:
        S["shield_energy"] = min(S["shield_max"], S["shield_energy"] + 0.05)

    # Cheat mode: free resources trickle, reactor self-heals, lives stay full
    if S["cheat_mode"]:
        S["resources"] += 2
        S["lives"] = max(S["lives"], 9)
        S["reactor_hp"] = min(100, S["reactor_hp"] + 1)

    # Population score
    pop = sum(b["level"] * 5 for row in S["grid"] for b in row if b and b["type"] == B_HOUSE)
    if S["t"] % 60 == 0:
        S["score"] += pop


def update_world():
    if S["game_over"]:
        # Run a simple crumble animation: shrink any surviving buildings to zero.
        for row in S["grid"]:
            for b in row:
                if b is not None and b["scale"] > 0.0:
                    b["scale"] = max(0.0, b["scale"] - 0.02)
        return
    S["t"] += 1
    S["day_phase"] = (S["day_phase"] + 1.0 / 1800.0) % 2.0

    # Smooth camera pitch animation
    S["cam_pitch"] += (S["cam_pitch_target"] - S["cam_pitch"]) * 0.15
    # Animate blend for transition effect
    if S["cam_blend"] < 1.0:
        S["cam_blend"] += 0.08

    # explosion / crater bookkeeping
    new_ex = []
    for e in S["explosions"]:
        e["age"] += 1
        e["r"] += 1.6
        if e["age"] < e["life"]:
            new_ex.append(e)
    S["explosions"] = new_ex
    for ck in list(S["craters"].keys()):
        S["craters"][ck] -= 1
        if S["craters"][ck] <= 0:
            del S["craters"][ck]
    for ck in list(S["warn_cells"].keys()):
        S["warn_cells"][ck] -= 1
        if S["warn_cells"][ck] <= 0:
            del S["warn_cells"][ck]

    # wormhole life
    if S["wormhole"] is not None:
        S["wormhole"]["age"] += 1
        if S["wormhole"]["age"] > 900:
            S["wormhole"] = None

    # Wave timing
    if not S["meteors"] and S["wave_timer"] <= 0:
        start_wave()
        S["wave_timer"] = 360
    elif not S["meteors"]:
        S["wave_timer"] -= 1

    # Predictive warn cells (where falling meteors will probably land)
    for m in S["meteors"]:
        if m["vz"] >= 0:
            continue
        steps = m["z"] / max(1.0, abs(m["vz"]))
        px = m["x"] + m["vx"] * steps
        py = m["y"] + m["vy"] * steps
        gx = int((px + GRID_HALF) // CELL)
        gy = int((py + GRID_HALF) // CELL)
        if in_bounds(gx, gy):
            S["warn_cells"][(gx, gy)] = 10

    update_meteors()
    update_economy()


# ---------------------------------------------------------------------------
# Camera
# ---------------------------------------------------------------------------
def setup_camera():
    glMatrixMode(GL_PROJECTION)
    glLoadIdentity()
    gluPerspective(FOVY, WIN_W / WIN_H, NEAR_CLIP, FAR_CLIP)
    glMatrixMode(GL_MODELVIEW)
    glLoadIdentity()

    if S["cam_mode"] == CAM_OVERVIEW:
        yaw = math.radians(S["cam_yaw"])
        pitch = math.radians(S["cam_pitch"])
        d = S["cam_dist"]
        ex = math.cos(yaw) * math.cos(pitch) * d
        ey = math.sin(yaw) * math.cos(pitch) * d
        ez = math.sin(pitch) * d
        gluLookAt(ex, ey, ez, 0, 0, 60, 0, 0, 1)

    elif S["cam_mode"] == CAM_BUILDER:
        gx, gy = S["cursor"]
        wx, wy = cell_to_world(gx, gy)

        # FIX: Make the Builder camera respect S["cam_yaw"]
        yaw = math.radians(S["cam_yaw"])
        dist = 280  # Distance behind the cursor

        ex = wx + math.cos(yaw) * dist
        ey = wy + math.sin(yaw) * dist
        ez = 180    # Low angle for that 3rd-person feel

        # Look directly at the cursor
        gluLookAt(ex, ey, ez, wx, wy, 30, 0, 0, 1)

    else:  # CAM_CINEMATIC
        S["cam_orbit_t"] += 0.004
        ang = S["cam_orbit_t"]
        d = 950
        ex = math.cos(ang) * d
        ey = math.sin(ang) * d
        ez = 380 + 120 * math.sin(ang * 0.5)
        gluLookAt(ex, ey, ez, 0, 0, 60, 0, 0, 1)


# ---------------------------------------------------------------------------
# Input
# ---------------------------------------------------------------------------
def keyboardListener(key, x, y):
    if S["game_over"]:
        if key == b'r':
            reset_game()
        return

    cgx, cgy = S["cursor"]

    # Cursor movement (Camera-Relative)
    if key in (b'w', b'a', b's', b'd'):
        # Determine which of the 4 cardinal directions the camera is facing
        # Adding 45 shifts the sectors to perfectly bracket 0, 90, 180, and 270 degrees
        quadrant = int((S["cam_yaw"] + 45) % 360) // 90

        dx, dy = 0, 0

        # Map WASD based on camera quadrant
        if key == b'w':
            if quadrant == 0: dx, dy = -1, 0
            elif quadrant == 1: dx, dy = 0, -1
            elif quadrant == 2: dx, dy = 1, 0
            elif quadrant == 3: dx, dy = 0, 1
        elif key == b's':
            if quadrant == 0: dx, dy = 1, 0
            elif quadrant == 1: dx, dy = 0, 1
            elif quadrant == 2: dx, dy = -1, 0
            elif quadrant == 3: dx, dy = 0, -1
        elif key == b'a':
            if quadrant == 0: dx, dy = 0, -1
            elif quadrant == 1: dx, dy = 1, 0
            elif quadrant == 2: dx, dy = 0, 1
            elif quadrant == 3: dx, dy = -1, 0
        elif key == b'd':
            if quadrant == 0: dx, dy = 0, 1
            elif quadrant == 1: dx, dy = -1, 0
            elif quadrant == 2: dx, dy = 0, -1
            elif quadrant == 3: dx, dy = 1, 0

        # Apply the movement and keep the cursor inside the grid boundaries
        new_gx = cgx + dx
        new_gy = cgy + dy
        if 0 <= new_gx < GRID_N and 0 <= new_gy < GRID_N:
            S["cursor"] = [new_gx, new_gy]

    # Build commands
    elif key == b'1': try_build(B_HOUSE)
    elif key == b'2': try_build(B_MINE)
    elif key == b'3': try_build(B_SHIELD)

    # Upgrade / Repair
    elif key == b'u': try_upgrade()
    elif key == b'e': try_repair()

    # Wormhole travel
    elif key == b'q': try_wormhole()

    # Cheat / vision
    elif key == b'c':
        S["cheat_mode"] = not S["cheat_mode"]
    elif key == b'v':
        S["cheat_vision"] = not S["cheat_vision"]

    # Restart
    elif key == b'r':
        reset_game()


def specialKeyListener(key, x, y):
    if key == GLUT_KEY_UP:
        S["cam_pitch_target"] = min(85, S["cam_pitch_target"] + 5)
        S["cam_blend"] = 0.0  # Start blend animation
    elif key == GLUT_KEY_DOWN:
        S["cam_pitch_target"] = max(10, S["cam_pitch_target"] - 5)
        S["cam_blend"] = 0.0  # Start blend animation
    elif key == GLUT_KEY_LEFT:
        S["cam_yaw"] -= 3
    elif key == GLUT_KEY_RIGHT:
        S["cam_yaw"] += 3


def mouseListener(button, state, x, y):
    if button == GLUT_RIGHT_BUTTON and state == GLUT_DOWN:
        S["cam_mode"] = (S["cam_mode"] + 1) % 3
    elif button == GLUT_LEFT_BUTTON and state == GLUT_DOWN:
        # Left click acts as a quick-place: cycles to next affordable building
        for t in (B_HOUSE, B_MINE, B_SHIELD):
            if S["resources"] >= BUILD_COST[t]:
                try_build(t)
                break


def shield_overlaps_other(gx, gy):
    """Check if a shield at (gx, gy) would overlap with any existing shield."""
    wx, wy = cell_to_world(gx, gy)
    new_radius = shield_effective_radius(gx, gy, 1)  # level 1 at placement

    for ogx in range(GRID_N):
        for ogy in range(GRID_N):
            b = S["grid"][ogx][ogy]
            if b is None or b["type"] != B_SHIELD:
                continue
            owx, owy = cell_to_world(ogx, ogy)
            other_radius = b.get("radius", shield_effective_radius(ogx, ogy, b["level"]))
            # Check if domes overlap (distance between centers < sum of radii)
            dist = math.hypot(wx - owx, wy - owy)
            if dist < new_radius + other_radius:
                return True
    return False


def try_build(kind):
    gx, gy = S["cursor"]
    if not can_place(gx, gy):
        return
    # Shield-specific overlap check
    if kind == B_SHIELD and shield_overlaps_other(gx, gy):
        return
    cost = BUILD_COST[kind]
    if S["resources"] < cost:
        return
    S["resources"] -= cost
    S["grid"][gx][gy] = {
        "type": kind, "level": 1, "dmg": 0, "scale": 0.05,
    }


def try_upgrade():
    gx, gy = S["cursor"]
    b = S["grid"][gx][gy]
    if b is None or b["level"] >= 3:
        return
    cost = UPGRADE_COST[b["type"]]
    if S["resources"] < cost:
        return
    # For shields, check if upgraded size would overlap with other shields
    if b["type"] == B_SHIELD:
        wx, wy = cell_to_world(gx, gy)
        upgraded_radius = shield_effective_radius(gx, gy, b["level"] + 1)
        for ogx in range(GRID_N):
            for ogy in range(GRID_N):
                if (ogx, ogy) == (gx, gy):
                    continue
                ob = S["grid"][ogx][ogy]
                if ob is None or ob["type"] != B_SHIELD:
                    continue
                owx, owy = cell_to_world(ogx, ogy)
                other_radius = ob.get("radius", shield_effective_radius(ogx, ogy, ob["level"]))
                dist = math.hypot(wx - owx, wy - owy)
                if dist < upgraded_radius + other_radius:
                    return  # Upgrade would cause overlap, reject it
    S["resources"] -= cost
    b["level"] += 1
    b["scale"] = 0.6  # re-grow animation


def try_repair():
    gx, gy = S["cursor"]
    b = S["grid"][gx][gy]
    if b is None or b["dmg"] == 0:
        return
    if S["resources"] < 20:
        return
    S["resources"] -= 20
    b["dmg"] = 0
    b["scale"] = 0.7


def try_wormhole():
    w = S["wormhole"]
    if w is None:
        return
    gx, gy = S["cursor"]
    if (gx, gy) != (w["gx"], w["gy"]):
        return
    # Mirror across center
    S["cursor"] = [GRID_N - 1 - gx, GRID_N - 1 - gy]
    S["wormhole"] = None
    S["score"] += 25


# ---------------------------------------------------------------------------
# HUD
# ---------------------------------------------------------------------------
def draw_hud():
    rh = S.get("reactor_hp", 100)
    draw_text(10, WIN_H - 25, f"Resources: {S['resources']}    Lives: {S['lives']}    Reactor: {int(rh)}HP", color=(1, 1, 0.6))
    draw_text(10, WIN_H - 50, f"Wave: {S['wave']}    Score: {S['score']}    Shield: {int(S['shield_energy'])}/{int(S['shield_max'])}", color=(0.6, 1, 0.8))
    pop = sum(b["level"] * 5 for row in S["grid"] for b in row if b and b["type"] == B_HOUSE)
    mines = sum(1 for row in S["grid"] for b in row if b and b["type"] == B_MINE)
    shields = sum(1 for row in S["grid"] for b in row if b and b["type"] == B_SHIELD)
    draw_text(10, WIN_H - 75, f"Pop: {pop}   Mines: {mines}   Shields: {shields}", color=(0.8, 0.9, 1.0))

    cam_name = ["Overview", "Builder", "Cinematic"][S["cam_mode"]]
    phase = S["day_phase"] % 2.0
    tod = "Day" if phase < 1.0 else "Night"
    cv = "  [VISION]" if S["cheat_vision"] else ""
    cm = "  [GOD MODE]" if S["cheat_mode"] else ""
    draw_text(10, WIN_H - 100, f"Camera: {cam_name}   Time: {tod} ({day_factor():.2f}){cv}{cm}", color=(0.9, 0.9, 0.9))

    # Help / controls
    draw_text(10, 110, "WASD: move cursor | 1=House(30) 2=Mine(50) 3=Shield(80)", color=(0.85, 0.85, 0.85))
    draw_text(10, 90,  "U: upgrade   E: repair   Q: wormhole   C: god mode   V: vision", color=(0.85, 0.85, 0.85))
    draw_text(10, 70,  "Right click: cycle camera | Arrows: rotate camera | R: restart", color=(0.85, 0.85, 0.85))

    # Building hover tooltip
    gx, gy = S["cursor"]
    b = S["grid"][gx][gy]
    if b is not None:
        names = {B_HOUSE: "Housing", B_MINE: "Mine", B_SHIELD: "Shield Tower"}
        tip = f"[{names[b['type']]}]  Lvl {b['level']}  DMG {b['dmg']}/2"
        draw_text(WIN_W - 320, WIN_H - 25, tip, color=(1, 1, 0.4))
    elif find_node(gx, gy) is not None:
        n = find_node(gx, gy)
        draw_text(WIN_W - 320, WIN_H - 25, f"[Resource Node]  amt={int(n['amount'])}", color=(1, 0.85, 0.2))
    elif is_reactor_cell(gx, gy):
        draw_text(WIN_W - 320, WIN_H - 25, "[Core Reactor] (do not let it die)", color=(0.4, 0.9, 1))

    # Wave warning banner
    if S["wave_announce"] > 0:
        S["wave_announce"] -= 1
        if (S["t"] // 8) % 2 == 0:
            draw_text(WIN_W // 2 - 110, WIN_H - 150, f">>> WAVE {S['wave']} INCOMING <<<", color=(1, 0.2, 0.2))

    # Wormhole hint
    if S["wormhole"] is not None and (gx, gy) == (S["wormhole"]["gx"], S["wormhole"]["gy"]):
        draw_text(WIN_W // 2 - 130, 150, "Press Q to teleport through the wormhole", color=(0.9, 0.6, 1.0))

    # Game over
    if S["game_over"]:
        draw_text(WIN_W // 2 - 90, WIN_H // 2 + 40, "*** COLONY LOST ***", color=(1, 0.2, 0.2))
        draw_text(WIN_W // 2 - 90, WIN_H // 2 + 10, f"Final Score: {S['score']}", color=(1, 1, 0.6))
        draw_text(WIN_W // 2 - 90, WIN_H // 2 - 20, "Press R to start a new colony", color=(0.9, 0.9, 0.9))


# ---------------------------------------------------------------------------
# Main render
# ---------------------------------------------------------------------------
def showScreen():
    # Background colour shifts with day phase
    df = day_factor()
    glClearColor(0.02 + 0.05 * df, 0.04 + 0.10 * df, 0.10 + 0.30 * df, 1.0)
    glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
    glLoadIdentity()
    glViewport(0, 0, WIN_W, WIN_H)
    setup_camera()

    # Apply slight brightness pulse during camera transitions for 3D vibe
    if S["cam_blend"] < 1.0:
        pulse = 1.0 - (S["cam_blend"] * 0.3)
        glMatrixMode(GL_MODELVIEW)
        glPushMatrix()
        glLoadIdentity()
        glMatrixMode(GL_PROJECTION)
        glPushMatrix()
        glLoadIdentity()
        gluOrtho2D(0, WIN_W, 0, WIN_H)
        glMatrixMode(GL_MODELVIEW)
        glDisable(GL_DEPTH_TEST)
        glColor4f(0, 0, 0, 0.2 * (1.0 - S["cam_blend"]))
        glBegin(GL_QUADS)
        glVertex2f(0, 0)
        glVertex2f(WIN_W, 0)
        glVertex2f(WIN_W, WIN_H)
        glVertex2f(0, WIN_H)
        glEnd()
        glEnable(GL_DEPTH_TEST)
        glPopMatrix()
        glMatrixMode(GL_PROJECTION)
        glPopMatrix()
        glMatrixMode(GL_MODELVIEW)

    draw_sky()
    draw_grid_floor()
    draw_walls()
    draw_reactor()
    draw_resource_nodes()
    draw_buildings()
    draw_energy_beams()
    draw_meteors()
    draw_explosions()
    draw_wormhole()
    draw_cursor_beacon()

    draw_hud()

    glutSwapBuffers()


def idle():
    update_world()
    glutPostRedisplay()


# ---------------------------------------------------------------------------
# Bootstrapping
# ---------------------------------------------------------------------------
def main():
    glutInit()
    glutInitDisplayMode(GLUT_DOUBLE | GLUT_RGB | GLUT_DEPTH)
    glutInitWindowSize(WIN_W, WIN_H)
    glutInitWindowPosition(40, 40)
    glutCreateWindow(b"3D Planet Colonizer - CSE 423 Group 1")

    glEnable(GL_DEPTH_TEST)

    spawn_initial_nodes()

    glutDisplayFunc(showScreen)
    glutKeyboardFunc(keyboardListener)
    glutSpecialFunc(specialKeyListener)
    glutMouseFunc(mouseListener)
    glutIdleFunc(idle)

    glutMainLoop()


if __name__ == "__main__":
    main()
