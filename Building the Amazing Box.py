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