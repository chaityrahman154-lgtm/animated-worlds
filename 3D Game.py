from OpenGL.GL import *
from OpenGL.GLUT import *
from OpenGL.GLU import *
import random, math
cam_angle = 45
cam_height = 600
cam_dist = 700
WORLD = 600
x_player = 0
y_player = 0
angle_player = 0
angle_gun = 0
bullet = []
enemy = []
total_life = 5
total_score = 0
missed = 0
cheat_mode = False
cheat_vision = False
first_person = False
is_game_over = False

def draw_text(x,y,text):
    glColor3f(1,1,1)
    glMatrixMode(GL_PROJECTION)
    glPushMatrix()
    glLoadIdentity()
    gluOrtho2D(0,1000,0,800)
    glMatrixMode(GL_MODELVIEW)
    glPushMatrix()
    glLoadIdentity()
    glRasterPos2f(x,y)
    for ch in text:
        glutBitmapCharacter(GLUT_BITMAP_HELVETICA_18, ord(ch))

    glPopMatrix()
    glMatrixMode(GL_PROJECTION)
    glPopMatrix()
    glMatrixMode(GL_MODELVIEW)

def drawGrid():
    tile = 40
    for x in range(-WORLD, WORLD, tile):
        for y in range(-WORLD, WORLD, tile):
            if (x//tile + y//tile) % 2 == 0:
                glColor3f(1,1,1)
            else:
                glColor3f(0.75,0.55,0.95)

            glBegin(GL_QUADS)
            glVertex3f(x,y,0)
            glVertex3f(x+tile,y,0)
            glVertex3f(x+tile,y+tile,0)
            glVertex3f(x,y+tile,0)
            glEnd()

def drawBoundary():
    h = 120
    b = WORLD

    glBegin(GL_QUADS)
    glColor3f(0,0,1)
    glVertex3f(-b,-b,0); glVertex3f(-b,-b,h)
    glVertex3f(-b,b,h);  glVertex3f(-b,b,0)
    glColor3f(0,1,0)
    glVertex3f(b,-b,0); glVertex3f(b,-b,h)
    glVertex3f(b,b,h);  glVertex3f(b,b,0)
    glColor3f(0,1,1)
    glVertex3f(-b,b,0); glVertex3f(-b,b,h)
    glVertex3f(b,b,h);  glVertex3f(b,b,0)
    glEnd()

def drawPlayer():
    glPushMatrix()
    glTranslatef(x_player, y_player, 0)
    if is_game_over:
        glRotatef(-90, 1, 0, 0) 
        glTranslatef(0, 0, 10) 
    glRotatef(-angle_player, 0, 0, 1)
    quad = gluNewQuadric()
    leg_offset = 10
    # LEFT LEG
    glPushMatrix()
    glTranslatef(-leg_offset, 0, 0)
    glColor3f(0.1, 0.1, 0.8)
    gluCylinder(quad, 5, 5, 25, 10, 10)
    glPopMatrix()
    # RIGHT LEG
    glPushMatrix()
    glTranslatef(leg_offset, 0, 0)
    glColor3f(0.1, 0.1, 0.8)
    gluCylinder(quad, 5, 5, 25, 10, 10)
    glPopMatrix()
    # BODY
    glPushMatrix()
    glTranslatef(0, 0, 45) 
    glColor3f(0.2, 0.6, 0.2)
    glScalef(1.5, 0.8, 2.0)
    glutSolidCube(20)
    glPopMatrix()
    # HEAD
    glPushMatrix()
    glTranslatef(0, 0, 75)
    glColor3f(0, 0, 0)
    gluSphere(quad, 12, 16, 16)
    glPopMatrix()

    glPushMatrix()
    glRotatef(angle_player - angle_gun, 0, 0, 1)

    arm_z = 55
    arm_offset = 18

    # LEFT ARM
    glPushMatrix()
    glTranslatef(-arm_offset, -5, arm_z)
    glRotatef(-90, 1, 0, 0)
    glColor3f(1.0, 0.75, 0.6)
    gluCylinder(quad, 4, 4, 25, 10, 10)
    glPopMatrix()

    # RIGHT ARM
    glPushMatrix()
    glTranslatef(arm_offset, -5, arm_z)
    glRotatef(-90, 1, 0, 0)
    glColor3f(1.0, 0.75, 0.6)
    gluCylinder(quad, 4, 4, 25, 10, 10)
    glPopMatrix()

    # GUN
    glPushMatrix()
    glTranslatef(0, 15, arm_z) 
    glRotatef(-90, 1, 0, 0)
    glColor3f(0.7, 0.7, 0.7)
    gluCylinder(quad, 4, 4, 40, 10, 10)
    glPopMatrix()
    glPopMatrix()
    glPopMatrix()

def spawnenemy():
    global enemy
    enemy = []
    for i in range(5):
        enemy.append({
            "x": random.randint(-450,450),
            "y": random.randint(-450,450),
            "scale": 1,
            "dir": 1
        })
def draw_Enemy():
    for e in enemy:
        glPushMatrix()
        glTranslatef(e["x"], e["y"], 20)
        glScalef(e["scale"],e["scale"],e["scale"])

        glColor3f(1,0,0)
        gluSphere(gluNewQuadric(),20,20,20)

        glTranslatef(0,0,30)
        glColor3f(0,0,0)
        gluSphere(gluNewQuadric(),10,20,20)

        glPopMatrix()

def update_Enemy():
    global total_life, is_game_over
    for e in enemy:
        dx = x_player - e["x"]
        dy = y_player - e["y"]
        dist = math.sqrt(dx*dx + dy*dy)
        if dist != 0:
            e["x"] += (dx/dist) * 0.3
            e["y"] += (dy/dist) * 0.3
        # Shrink & expand continuously
        e["scale"] += 0.02 * e["dir"]
        if e["scale"] > 1.5 or e["scale"] < 0.5:
            e["dir"] *= -1
        # Check interaction with player
        if dist < 30:
            total_life -= 1
            print(f"Remaining Player Life: {total_life}")
            e["x"] = random.randint(-450,450)
            e["y"] = random.randint(-450,450)
            if total_life <= 0:
                is_game_over = True

def shoot():
    bullet.append({
        "x": x_player,
        "y": y_player,
        "angle": angle_gun
    })
    print("Player Bullet Fired!")
def update_Bullet():
    global missed, total_score, bullet
    active_bullet = []
    
    for b in bullet:
        b["x"] += 15*math.sin(math.radians(b["angle"]))
        b["y"] += 15*math.cos(math.radians(b["angle"]))

        hit = False
        for e in enemy:
            dist = math.sqrt((b["x"]-e["x"])**2 + (b["y"]-e["y"])**2)
            if dist < 25:
                total_score += 1
                e["x"] = random.randint(-450,450)
                e["y"] = random.randint(-450,450)
                hit = True
                break
        if not hit:
            # Clean up out-of-bounds bullet
            if abs(b["x"]) > WORLD or abs(b["y"]) > WORLD:
                missed += 1
                print(f"Bullet missed: {missed}")
            else:
                active_bullet.append(b) 
    bullet = active_bullet 
def draw_Bullet():
    glColor3f(1,0,0)
    for b in bullet:
        glPushMatrix()
        glTranslatef(b["x"],b["y"],55) # Match the height of the gun
        glutSolidCube(10)
        glPopMatrix()

def cheating_mode():
    global angle_gun
    if cheat_mode:
        angle_gun += 3 

        for e in enemy:
            dx = e["x"] - x_player
            dy = e["y"] - y_player
            target_angle = math.degrees(math.atan2(dx,dy))
            
            diff = (target_angle - angle_gun) % 360
            if diff > 180: diff -= 360
            
            if abs(diff) <= 1.5: 
                shoot()

def keyboardListener(key,x,y):
    global x_player, y_player, angle_player, angle_gun, cheat_mode, cheat_vision

    if is_game_over and key != b'r': 
        return
    step = 10
    if key == b'w':
        x_player += step * math.sin(math.radians(angle_player))
        y_player += step * math.cos(math.radians(angle_player))
    elif key == b's':
        x_player -= step * math.sin(math.radians(angle_player))
        y_player -= step * math.cos(math.radians(angle_player))
    elif key == b'a':
        angle_player += 5
        if not cheat_mode: angle_gun = angle_player
    elif key == b'd':
        angle_player -= 5
        if not cheat_mode: angle_gun = angle_player
    elif key == b'c':
        cheat_mode = not cheat_mode
        if not cheat_mode: angle_gun = angle_player # Snap gun back to body
    elif key == b'v':
        if cheat_mode:
            cheat_vision = not cheat_vision
    elif key == b'r':
        reset_the_game()
    limit = WORLD - 20
    x_player = max(-limit, min(limit, x_player))
    y_player = max(-limit, min(limit, y_player))

def specialKeyListener(key,x,y):
    global cam_angle, cam_height
    if key == GLUT_KEY_LEFT:
        cam_angle -= 5
    elif key == GLUT_KEY_RIGHT:
        cam_angle += 5
    elif key == GLUT_KEY_UP:
        cam_height = min(cam_height + 20, 1200)
    elif key == GLUT_KEY_DOWN:
        cam_height = max(cam_height - 20, 10)
def mouseListener(button,state,x,y):
    global first_person
    if is_game_over: 
        return
    if button == GLUT_LEFT_BUTTON and state == GLUT_DOWN:
        shoot()
    if button == GLUT_RIGHT_BUTTON and state == GLUT_DOWN:
        first_person = not first_person
def set_up_cam():
    glMatrixMode(GL_PROJECTION)
    glLoadIdentity()
    gluPerspective(90,1.25,0.1,2000)

    glMatrixMode(GL_MODELVIEW)
    glLoadIdentity()
    if first_person:
        # Determine cam direction based on 'V' key 
        
        if (cheat_mode and cheat_vision):
            cam_dir = angle_gun 
        else:
            cam_dir = angle_player
        
        gluLookAt(x_player, y_player, 75,x_player + math.sin(math.radians(cam_dir)),y_player + math.cos(math.radians(cam_dir)),75, 0, 0, 1)
    else:
        camX = cam_dist * math.sin(math.radians(cam_angle))
        camY = cam_dist * math.cos(math.radians(cam_angle))
        gluLookAt(camX, camY, cam_height, 0, 0, 0, 0, 0, 1)

def reset_the_game():
    global total_life, total_score, missed, x_player, y_player, angle_player, angle_gun
    global is_game_over, cheat_mode, cheat_vision, bullet

    total_life = 5
    total_score = 0
    missed = 0
    x_player = 0
    y_player = 0
    angle_player = 0
    angle_gun = 0
    is_game_over = False
    cheat_mode = False
    cheat_vision = False
    bullet = []
    spawnenemy()

def idle():
    global is_game_over
    if not is_game_over:
        update_Bullet()
        update_Enemy()
        cheating_mode()
        if missed >= 10:
            is_game_over = True
    glutPostRedisplay()

def display():
    glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
    glViewport(0,0,1000,800)
    set_up_cam()
    drawGrid()
    drawBoundary()
    if not first_person:
        drawPlayer()
    draw_Enemy()
    draw_Bullet()
    if is_game_over:
        draw_text(10, 750, f"Game is Over. Your total_score is {total_score}.")
        draw_text(10, 720, 'Press "R" to RESTART the Game.')
    else:
        draw_text(10, 750, f"Player Life Remaining: {total_life}")
        draw_text(10, 720, f"Game total_score: {total_score}")
        draw_text(10, 690, f"Player Bullet Missed: {missed}")
        
   

    glutSwapBuffers()
def main():
    glutInit()
    glutInitDisplayMode(GLUT_DOUBLE | GLUT_RGB | GLUT_DEPTH)
    glutInitWindowSize(1000,800)
    glutCreateWindow(b"Bullet Frenzy")
    glEnable(GL_DEPTH_TEST)
    glClearColor(0,0,0,1)
    spawnenemy()
    glutDisplayFunc(display)
    glutKeyboardFunc(keyboardListener)
    glutSpecialFunc(specialKeyListener)
    glutMouseFunc(mouseListener)
    glutIdleFunc(idle)
    glutMainLoop()

if __name__ == "__main__":
    main()