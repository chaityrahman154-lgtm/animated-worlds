from OpenGL.GL import *
from OpenGL.GLUT import *
from OpenGL.GLU import *
import random
import time

x_diamond = 0
y_diamond = 250
x_catcher = 0
total_score = 0
is_is_game_over = False
pause = False
cheating_mode = False
speed = 120
ending_time = time.time()
color_diamond = (1, 1, 1)
WINDOW_WIDTH, WINDOW_HEIGHT = 600, 600

def draw_point(x, y):
    glBegin(GL_POINTS)
    glVertex2f(x, y)
    glEnd()

def identify_zone(x1, y1, x2, y2):
    zone=-1
    if abs(x2 - x1) >= abs(y2 - y1):
        if (x2 - x1) >= 0 and (y2 - y1) >= 0:
            zone = 0
        elif (x2 - x1) < 0 and (y2 - y1) >= 0:
            zone = 3
        elif (x2 - x1) < 0 and (y2 - y1) < 0:
            zone = 4
        else:
            zone = 7
    else:
        if (x2 - x1) >= 0 and (y2 - y1) >= 0:
            zone = 1
        elif (x2 - x1) < 0 and (y2 - y1) >= 0:
            zone = 2
        elif (x2 - x1) < 0 and (y2 - y1) < 0:
            zone = 5
        else:
            zone = 6
    return zone

def convert_to_zone_zero(x, y, zone):
    if zone == 0:
        return x, y
    elif zone == 1:
        return y, x
    elif zone == 2:
        return y, -x
    elif zone == 3:
        return -x, y
    elif zone == 4:
        return -x, -y
    elif zone == 5:
        return -y, -x
    elif zone == 6:
        return -y, x
    elif zone == 7:
        return x, -y

def convert_from_zone_zero(x, y, zone):
    if zone == 0:
        return x, y
    elif zone == 1:
        return y, x
    elif zone == 2:
        return -y, x
    elif zone == 3:
        return -x, y
    elif zone == 4:
        return -x, -y
    elif zone == 5:
        return -y, -x
    elif zone == 6:
        return y, -x
    elif zone == 7:
        return x, -y

def midpoint_line_algorithm(x1, y1, x2, y2, zone):
    dx = x2 - x1
    dy = y2 - y1
    d = 2 * dy - dx
    incrE = 2 * dy
    incrNE = 2 * (dy - dx)
    x = x1
    y = y1
    while x <= x2:
        real_x, real_y = convert_from_zone_zero(x, y, zone)
        draw_point(real_x, real_y)
        if d > 0:
            d += incrNE
            y = y + 1
            x = x + 1
        else:
            d += incrE
            x = x + 1

def draw_a_line(x1, y1, x2, y2):
    current_zone = identify_zone(x1, y1, x2, y2)
    x1_new, y1_new = convert_to_zone_zero(x1, y1, current_zone)
    x2_new, y2_new = convert_to_zone_zero(x2, y2, current_zone)
    if x1_new > x2_new:
        x1_new, x2_new = x2_new, x1_new
        y1_new, y2_new = y2_new, y1_new
    midpoint_line_algorithm(x1_new, y1_new, x2_new, y2_new, current_zone)

def draw_diamond(nx, ny):
    draw_a_line(nx - 20, ny, nx, ny + 20)
    draw_a_line(nx, ny + 20, nx + 20, ny)
    draw_a_line(nx + 20, ny, nx, ny - 20)
    draw_a_line(nx, ny - 20, nx - 20, ny)

def draw_catcher(nx):
    draw_a_line(nx - 75, -298, nx + 75, -298)
    draw_a_line(nx - 100, -275, nx + 100, -275)
    draw_a_line(nx - 75, -298, nx - 100, -275)
    draw_a_line(nx + 100, -275, nx + 75, -298)

def restart_button():
    draw_a_line(-280, 275, -240, 275)
    draw_a_line(-280, 275, -255, 295)
    draw_a_line(-280, 275, -255, 255)

def back_button():
    draw_a_line(250, 290, 290, 250)
    draw_a_line(250, 250, 290, 290)

def pause_button():
    draw_a_line(-30, 290, -30, 260)
    draw_a_line(-30, 290, 5, 275)
    draw_a_line(-30, 260, 5, 275)

def play_button():
    draw_a_line(-10, 290, -10, 260)
    draw_a_line(5, 290, 5, 260)

def reset_diamond_position():
    global x_diamond, y_diamond, color_diamond
    x_diamond = random.randint(-200, 200)
    y_diamond = 250
    color_diamond = (random.random(), random.random(), random.random())

def restart_the_game():
    global total_score, is_is_game_over, speed, cheating_mode
    cheating_mode=False
    total_score = 0
    is_is_game_over = False
    speed = 120
    reset_diamond_position()
  
def collision():
    diamond_left = x_diamond - 20
    diamond_right = x_diamond + 20
    diamond_top = y_diamond + 20
    diamond_bottom = y_diamond - 20
    catcher_left = x_catcher - 100
    catcher_right = x_catcher + 100
    catcher_top = -260
    catcher_bottom = -280
    return (diamond_left < catcher_right and diamond_right > catcher_left and
            diamond_bottom < catcher_top and diamond_top > catcher_bottom)

def special_key_listener(key, x, y):
    global x_catcher
    if is_is_game_over or pause:
        return
    if key == GLUT_KEY_LEFT:
        x_catcher -= 25
    elif key == GLUT_KEY_RIGHT:
        x_catcher += 25
    x_catcher = max(-200, min(200, x_catcher))
    glutPostRedisplay()

def keyboard_listener(key, x, y):
    global cheating_mode
    if key == b'c':
        cheating_mode = not cheating_mode
        print("Cheat Mode:", cheating_mode)
    glutPostRedisplay()

def mouse_listener(button, state, x, y):
    global pause, total_score, is_is_game_over, speed
    if state != GLUT_DOWN:
        return
    mx = x - 300
    my = 300 - y
    #Restart
    if -290 < mx < -240 and 250 < my < 300:
        print("Starting Over")
        restart_the_game()
    #Pause/Play
    elif -40 < mx < 40 and 250 < my < 300:
        pause = not pause
        if not pause:
            global ending_time
            ending_time = time.time()
    #Exit
    elif 240 < mx < 300 and 250 < my < 300:
        print("Goodbye! total_score:", total_score)
        glutLeaveMainLoop()
        
def animate():
    global y_diamond, ending_time, total_score, is_is_game_over, speed, x_catcher
    if is_is_game_over or pause:
        glutPostRedisplay()
        return
    present = time.time()
    difference = present - ending_time
    ending_time = present
    y_diamond -= speed * difference
    if cheating_mode:
        speed = 300 
        if abs(x_catcher - x_diamond) > 2:
            if x_catcher < x_diamond:
                x_catcher += speed * difference
            else:
                x_catcher -= speed * difference
    if collision():
        total_score += 1
        print("total_score:", total_score)
        reset_diamond_position()
        speed += 12
    if y_diamond < -300:
        print("Game Over! total_score:", total_score)
        is_is_game_over = True
    glutPostRedisplay()

def display():
    glClear(GL_COLOR_BUFFER_BIT)
    glLoadIdentity()
    #Diamond
    if not is_is_game_over:
        glColor3f(*color_diamond)
        draw_diamond(x_diamond, y_diamond)
    #Catcher
    if is_is_game_over:
        glColor3f(1, 0, 0)
    else:
        glColor3f(1, 1, 1)
    draw_catcher(x_catcher)

    glColor3f(0, 1, 1)
    restart_button()

    glColor3f(1, 0, 0)
    back_button()

    glColor3f(1, 1, 0)
    if pause:
        play_button()
    else:
        pause_button()

    glutSwapBuffers()

def setup():
    glViewport(0, 0, WINDOW_WIDTH, WINDOW_HEIGHT)
    glMatrixMode(GL_PROJECTION)
    glLoadIdentity()
    glOrtho(-300, 300, -300, 300, 0, 1)
    glMatrixMode(GL_MODELVIEW)

def main():
    glutInit()
    glutInitDisplayMode(GLUT_RGBA)
    glutInitWindowSize(WINDOW_WIDTH, WINDOW_HEIGHT)
    glutCreateWindow(b"Catch the Diamonds!")
    setup()
    reset_diamond_position()
    glutDisplayFunc(display)
    glutIdleFunc(animate)
    glutSpecialFunc(special_key_listener)
    glutKeyboardFunc(keyboard_listener)
    glutMouseFunc(mouse_listener)
    glutMainLoop()

if __name__ == "__main__":
    main()