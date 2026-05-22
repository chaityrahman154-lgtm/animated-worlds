###TASK 1

# ===== OpenGL 2D Point Drawing Example =====
# This program displays a single yellow point using PyOpenGL + GLUT.

from OpenGL.GL import *     # Core OpenGL functions (drawing, colors, etc.)
from OpenGL.GLUT import *   # GLUT library (window creation, display, loop)
from OpenGL.GLU import *    # OpenGL Utility Library (projection utilities)


# --- Global coordinates of the point ---
x, y = 250, 250
max = 15   # maximum sideways bending
offset = 0
speed = 0.5
direction = 0   # 0 = straight, negative = left, positive = right
r, g, b = 0.5, 0.8, 1.0  # light blue for day
step = 0.01                 # step for gradual change

# ===== Function to draw a single point =====
def draw_points():

    glPointSize(5)
    glColor3f(0.0, 0.0, 0.0)
    glBegin(GL_POINTS)
    glVertex2f(320, 290)
    glEnd()

def triangle():

    glBegin(GL_TRIANGLES)
    glColor3f(0.4, 0.26, 0.13)
    glVertex2f(0.0, 0.0)
    glVertex2f(600, 0.0)
    glVertex2f(0.0, 400)
    glVertex2f(600, 0.0)
    glVertex2f(600, 400)
    glVertex2f(0.0, 400)

    x=0
    y=50
    z=25

    for i in range(12):
        glColor3f(0.49, 0.99, 0.0)
        glVertex2f(x, 350)
        glVertex2f(y, 350)
        glColor3f(0.10, 0.15, 0.0)
        glVertex2f(z, 400)
        x+=50
        y+=50
        z+=50

    glColor3f(1.0, 0.99, 0.94) # rectangle part of the house
    glVertex2f(150, 250)
    glVertex2f(450, 250)
    glVertex2f(150, 360)
    glVertex2f(450, 250)
    glVertex2f(450, 360)
    glVertex2f(150, 360)

    glColor3f(0.4, 0.2, 0.8) # triangle part of the house
    glVertex2f(130, 360)
    glVertex2f(470, 360)
    glVertex2f(300, 430)

    glColor3f(0.2, 0.6, 1.0) # door
    glVertex2f(275, 250)
    glVertex2f(335, 250)
    glVertex2f(275, 330)
    glVertex2f(335, 250)
    glVertex2f(335, 330)
    glVertex2f(275, 330)

    glVertex2f(200, 300) # window 1
    glVertex2f(250, 300)
    glVertex2f(200, 330)
    glVertex2f(250, 300)
    glVertex2f(250, 330)
    glVertex2f(200, 330)

    glVertex2f(360, 300) # window 2
    glVertex2f(410, 300)
    glVertex2f(360, 330)
    glVertex2f(410, 300)
    glVertex2f(410, 330)
    glVertex2f(360, 330)

    glEnd()

def lines():

    glLineWidth(1)
    glColor3f(0.0, 0.0, 0.0)
    glBegin(GL_LINES)
    glVertex2f(200,315)
    glVertex2f(250,315)
    glVertex2f(225,300)
    glVertex2f(225,330)

    glVertex2f(360,315)
    glVertex2f(410,315)
    glVertex2f(385,300)
    glVertex2f(385,330)
    glEnd()

def rain():
    global offset, direction

    glLineWidth(1)
    glColor3f(0.2, 0.6, 1.0)

    glBegin(GL_LINES)

    for i in range(120):

        # Generate scattered X using sine formula
        x = (i * 37) % 600

        # Generate varying Y using offset + wave
        y = (600 - ((i * 53 + offset) % 600))

        length = 15 + (i % 10)   # different lengths

        glVertex2f(x, y)
        glVertex2f(x + direction, y - length)

    glEnd()

def animate():
    global offset
    offset += speed
    glutPostRedisplay()

def special_key_listener(key, x, y):
    global direction

    if key == GLUT_KEY_LEFT:
        if direction > -max:
            direction -= 5   # bend left gradually

    elif key == GLUT_KEY_RIGHT:
        if direction < max:
            direction += 5   # bend right gradually

    glutPostRedisplay()

def keyboard_listener(key, x, y):
    global r, g, b, step

    key = key.decode("utf-8")  # convert bytes to string

    if key == 'd':
        if r < 0.5:
            r += step
        if g < 0.8:
            g += step
        if b < 1.0:
            b += step

    elif key == 'n':
        if r > 0.05:
            r -= step
        if g > 0.05:
            g -= step
        if b > 0.1:
            b -= step

    glutPostRedisplay()

# ===== Set up 2D coordinate system =====
def setup_projection():
    glViewport(0, 0, 600, 600)     # Define the portion of the window to render to
    glMatrixMode(GL_PROJECTION)    # Switch to the projection matrix
    glLoadIdentity()               # Reset the projection matrix
    glOrtho(0.0, 600, 0.0, 600, 0.0, 1.0)  # Define a 2D orthographic projection
    glMatrixMode(GL_MODELVIEW)     # Switch back to the modelview matrix


# ===== Display callback =====
def display():
    glClearColor(r, g, b, 1.0)  # set the background color
    glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
    glLoadIdentity()                                    # Reset transformations
    setup_projection()                                  # Set up coordinate system
    triangle()
    lines()
    draw_points()
    rain()
    glutSwapBuffers()   # Swap buffers (double buffering)


# ===== Main entry point =====
def main():
    glutInit()                               # Initialize GLUT
    glutInitDisplayMode(GLUT_RGBA | GLUT_DOUBLE)           # Set display mode: RGBA color
    glutInitWindowSize(600, 600)             # Set window size (width, height)
    glutInitWindowPosition(250, 100)         # Set window position (top-left corner)
    glutCreateWindow(b"Assignment 1")        # Create window with a title
    glutDisplayFunc(display)                 # Register display callback
    glutIdleFunc(animate)
    glutSpecialFunc(special_key_listener)
    glutKeyboardFunc(keyboard_listener)
    glutMainLoop()                           # Start the main event-processing loop


# ===== Run the program =====
if __name__ == "__main__":
    main()




from OpenGL.GL import *
from OpenGL.GLUT import *
from OpenGL.GLU import *
import random

WIDTH = 800
HEIGHT = 800

l, r = -400, 400
b, t = -400, 400

points = []
speed = 0.3
blink = False
state = True
f = False

def convert_coordinate(x, y):
    a = x - (WIDTH / 2)
    b = (HEIGHT / 2) - y
    return a, b


def draw_point(x, y, size):
    glPointSize(size)
    glBegin(GL_POINTS)
    glVertex2f(x, y)
    glEnd()


def display():
    global state

    glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
    glLoadIdentity()

    glViewport(0, 0, WIDTH, HEIGHT)
    glMatrixMode(GL_PROJECTION)
    glLoadIdentity()
    glOrtho(-400, 400, -400, 400, 0, 1)
    glMatrixMode(GL_MODELVIEW)

    for p in points:
        r, g, b = p["color"]

        if blink:
            if state:
                glColor3f(r, g, b)
            else:
                glColor3f(0, 0, 0)
        else:
            glColor3f(r, g, b)

        draw_point(p["x"], p["y"], 6)

    # Toggle blinking every redraw
    if blink:
        state = not state

    glutSwapBuffers()

def animate():
    if not f:
        for p in points:
            p["x"] += p["dx"] * speed
            p["y"] += p["dy"] * speed

            # Bounce horizontally
            if p["x"] >= r or p["x"] <= l:
                p["dx"] *= -1

            # Bounce vertically
            if p["y"] >= t or p["y"] <= b:
                p["dy"] *= -1

    glutPostRedisplay()


def mouse_listener(button, state, x, y):
    global blink

    if f:
        return

    if button == GLUT_RIGHT_BUTTON and state == GLUT_DOWN:
        px, py = convert_coordinate(x, y)

        dx = random.choice([-1, 1])
        dy = random.choice([-1, 1])

        color = (random.random(), random.random(), random.random())

        points.append({"x": px,"y": py,"dx": dx,"dy": dy,"color": color})

    if button == GLUT_LEFT_BUTTON and state == GLUT_DOWN:
        blink = not blink


def special_key_listener(key, x, y):
    global speed

    if f:
        return

    if key == GLUT_KEY_UP:
        speed *= 2

    elif key == GLUT_KEY_DOWN:
        speed /= 2


def keyboard_listener(key, x, y):
    global f

    if key == b' ':
        f = not f



def main():
    glutInit()
    glutInitDisplayMode(GLUT_RGBA)
    glutInitWindowSize(WIDTH, HEIGHT)
    glutCreateWindow(b"Task 2")

    glutDisplayFunc(display)
    glutIdleFunc(animate)
    glutMouseFunc(mouse_listener)
    glutSpecialFunc(special_key_listener)
    glutKeyboardFunc(keyboard_listener)

    glutMainLoop()


if __name__ == "__main__":
    main()