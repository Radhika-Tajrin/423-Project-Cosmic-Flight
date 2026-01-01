from OpenGL.GL import *
from OpenGL.GLU import *
from OpenGL.GLUT import *
import random
import time
import math

# Window and World Configuration
WINDOW_W, WINDOW_H = 1200, 900
WORLD_W, WORLD_H = 1000.0, 700.0

# Background Colors (will change with levels)
BG_COLORS = {
    1: {"top": [0.05, 0.05, 0.15], "bot": [0.0, 0.0, 0.05]},
    2: {"top": [0.15, 0.05, 0.25], "bot": [0.05, 0.0, 0.1]},
    3: {"top": [0.25, 0.1, 0.1], "bot": [0.1, 0.0, 0.0]}
}

# Collections
stars = []
nebulas = []
planets = []

# Current level for background (can change with keyboard for testing)
current_level = 1

# =========================
# HELPER CLASSES
# =========================

class Star:
    def __init__(self):
        self.x = random.uniform(-WORLD_W/2, WORLD_W/2)
        self.y = random.uniform(-WORLD_H/2, WORLD_H/2)
        self.z = random.uniform(-800, 800)
        self.brightness = random.uniform(0.3, 1.0)
        self.twinkle_speed = random.uniform(0.5, 2.0)
        self.twinkle_offset = random.uniform(0, 6.28)
    
    def update(self, dt):
        self.x -= 80 * dt
        if self.x < -WORLD_W/2 - 100:
            self.x = WORLD_W/2 + 100
            self.y = random.uniform(-WORLD_H/2, WORLD_H/2)

class Nebula:
    def __init__(self):
        self.x = random.uniform(-WORLD_W/2, WORLD_W/2)
        self.y = random.uniform(-WORLD_H/2, WORLD_H/2)
        self.z = random.uniform(-600, -200)
        self.size = random.uniform(40, 80)
        self.color = [
            random.uniform(0.3, 0.8),
            random.uniform(0.1, 0.5),
            random.uniform(0.5, 1.0)
        ]
        self.rotation = random.uniform(0, 360)
    
    def update(self, dt):
        self.x -= 40 * dt
        self.rotation += 10 * dt
        if self.x < -WORLD_W/2 - 100:
            self.x = WORLD_W/2 + 100

class Planet:
    def __init__(self):
        self.x = random.uniform(-WORLD_W/2, WORLD_W/2)
        self.y = random.uniform(-WORLD_H/2, WORLD_H/2)
        self.z = random.uniform(-500, -200)
        self.size = random.uniform(30, 60)
        self.color = [random.uniform(0.2, 0.9) for _ in range(3)]
        self.rotation = random.uniform(0, 360)
        self.rotation_speed = random.uniform(5, 15)
    
    def update(self, dt):
        self.x -= 60 * dt
        self.rotation += self.rotation_speed * dt
        if self.x < -WORLD_W/2 - 100:
            self.x = WORLD_W/2 + 100

# =========================
# SCENE FUNCTIONS
# =========================

def initialize_scene():
    """Initialize all scene objects"""
    global stars, nebulas, planets
    
    stars.clear()
    nebulas.clear()
    planets.clear()
    
    # Create stars
    for _ in range(600):
        stars.append(Star())
    
    # Create nebulas
    for _ in range(8):
        nebulas.append(Nebula())
    
    # Create planets
    for _ in range(5):
        planets.append(Planet())

def update_scene(dt):
    """Update all scene objects"""
    for star in stars:
        star.update(dt)
    for nebula in nebulas:
        nebula.update(dt)
    for planet in planets:
        planet.update(dt)

# =========================
# DRAWING FUNCTIONS
# =========================

def draw_gradient_background():
    """Draw gradient background based on level"""
    level = min(current_level, 3)
    colors = BG_COLORS[level]
    
    glMatrixMode(GL_PROJECTION)
    glPushMatrix()
    glLoadIdentity()
    glOrtho(0, 1, 0, 1, -1, 1)
    
    glMatrixMode(GL_MODELVIEW)
    glPushMatrix()
    glLoadIdentity()
    
    glBegin(GL_QUADS)
    glColor3f(*colors["top"])
    glVertex2f(0, 1)
    glVertex2f(1, 1)
    glColor3f(*colors["bot"])
    glVertex2f(1, 0)
    glVertex2f(0, 0)
    glEnd()
    
    glPopMatrix()
    glMatrixMode(GL_PROJECTION)
    glPopMatrix()
    glMatrixMode(GL_MODELVIEW)

def draw_stars():
    """Draw twinkling stars"""
    glPointSize(2.0)
    for star in stars:
        twinkle = 0.5 + 0.5 * math.sin(time.time() * star.twinkle_speed + star.twinkle_offset)
        brightness = star.brightness * twinkle
        glColor3f(brightness, brightness, brightness)
        glBegin(GL_POINTS)
        glVertex3f(star.x, star.y, star.z)
        glEnd()

def draw_nebulas():
    """Draw nebula clouds"""
    glEnable(GL_BLEND)
    glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)
    
    for nebula in nebulas:
        glPushMatrix()
        glTranslatef(nebula.x, nebula.y, nebula.z)
        glRotatef(nebula.rotation, 0, 0, 1)
        glColor4f(nebula.color[0], nebula.color[1], nebula.color[2], 0.3)
        glutSolidSphere(nebula.size, 20, 20)
        glPopMatrix()
    
    glDisable(GL_BLEND)

def draw_planets():
    """Draw planets"""
    for planet in planets:
        glPushMatrix()
        glTranslatef(planet.x, planet.y, planet.z)
        glRotatef(planet.rotation, 0, 1, 0)
        glColor3f(*planet.color)
        glutSolidSphere(planet.size, 25, 25)
        glPopMatrix()

def set_camera():
    """Set camera perspective"""
    glMatrixMode(GL_PROJECTION)
    glLoadIdentity()
    gluPerspective(60.0, WINDOW_W / WINDOW_H, 1.0, 2000.0)
    
    glMatrixMode(GL_MODELVIEW)
    glLoadIdentity()
    
    # Third-person camera looking at center
    gluLookAt(
        -200, 100, 300,  # Camera position
        0, 0, 0,         # Look at point
        0, 1, 0          # Up vector
    )

# =========================
# GLUT CALLBACKS
# =========================

last_time = 0.0

def display():
    """Main display function"""
    glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
    
    draw_gradient_background()
    set_camera()
    
    glEnable(GL_DEPTH_TEST)
    
    draw_stars()
    draw_nebulas()
    draw_planets()
    
    glDisable(GL_DEPTH_TEST)
    
    glutSwapBuffers()

def idle():
    """Idle callback for animation"""
    global last_time
    
    now = time.time()
    if last_time == 0:
        last_time = now
    
    dt = now - last_time
    last_time = now
    dt = min(dt, 0.1)
    
    update_scene(dt)
    glutPostRedisplay()

def keyboard(key, x, y):
    """Keyboard input"""
    global current_level
    
    if key in [b'1']:
        current_level = 1
        print("Background: Level 1 (Deep space)")
    elif key in [b'2']:
        current_level = 2
        print("Background: Level 2 (Purple nebula)")
    elif key in [b'3']:
        current_level = 3
        print("Background: Level 3 (Red danger zone)")
    elif key in [b'q', b'Q', b'\x1b']:
        print("Exiting...")
        import sys
        sys.exit()

def reshape(w, h):
    """Window reshape callback"""
    glViewport(0, 0, max(1, w), max(1, h))

def init_gl():
    """Initialize OpenGL settings"""
    glClearColor(0.0, 0.0, 0.0, 1.0)
    glEnable(GL_DEPTH_TEST)
    glShadeModel(GL_SMOOTH)
    glEnable(GL_COLOR_MATERIAL)

# =========================
# MAIN
# =========================

def main():
    """Main entry point"""
    glutInit()
    glutInitDisplayMode(GLUT_DOUBLE | GLUT_RGB | GLUT_DEPTH)
    glutInitWindowSize(WINDOW_W, WINDOW_H)
    glutCreateWindow(b"Cosmic Flight - Commit 1: Scene Setup")
    
    init_gl()
    initialize_scene()
    
    glutDisplayFunc(display)
    glutIdleFunc(idle)
    glutKeyboardFunc(keyboard)
    glutReshapeFunc(reshape)
    
    print("\n" + "="*50)
    print("COSMIC FLIGHT - COMMIT 1: SCENE FOUNDATION")
    print("="*50)
    print("\nAnimated space scene with:")
    print("  • 600 twinkling stars")
    print("  • 8 rotating nebulas")
    print("  • 5 rotating planets")
    print("\nControls:")
    print("  1, 2, 3 - Change background theme")
    print("  Q/ESC   - Quit\n")
    print("Next: Add spaceship and obstacles (Commit 2)")
    print("="*50 + "\n")
    
    glutMainLoop()

if __name__ == "__main__":
    main()
