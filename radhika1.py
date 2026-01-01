from OpenGL.GL import *
from OpenGL.GLU import *
from OpenGL.GLUT import *
import random
import time
import math
import sys

# Window and World Configuration
WINDOW_W, WINDOW_H = 1200, 900
WORLD_W, WORLD_H = 1000.0, 700.0

# Game Configuration
INITIAL_LIVES = 3
INITIAL_AMMO = 20
AMMO_RECHARGE_TIME = 3.0

# Background Colors
BG_COLORS = {
    1: {"top": [0.05, 0.05, 0.15], "bot": [0.0, 0.0, 0.05]},
    2: {"top": [0.15, 0.05, 0.25], "bot": [0.05, 0.0, 0.1]},
    3: {"top": [0.25, 0.1, 0.1], "bot": [0.1, 0.0, 0.0]}
}

# Global Game State
game_state = {
    "paused": False,
    "level": 1,
    "score": 0,
    "lives": INITIAL_LIVES,
    "ammo": INITIAL_AMMO,
    "last_ammo_recharge": 0.0,
    "camera_mode": "third_person",
    "last_time": 0.0
}

# Spaceship Configuration
spaceship = {
    "x": -200.0,
    "y": 0.0,
    "z": 0.0,
    "rotation": 0.0,
    "health": 100,
    "max_health": 100
}

# Collections
stars = []
nebulas = []
planets = []
obstacles = []
projectiles = []
particles = []

# Level Configuration
LEVEL_CONFIG = {
    1: {
        "obstacle_speed": 200.0,
        "obstacle_count": 15,
        "obstacle_health": 1,
        "spawn_penalty_obstacles": False,
        "penalty_ratio": 0.0
    },
    2: {
        "obstacle_speed": 280.0,
        "obstacle_count": 20,
        "obstacle_health": 1,
        "spawn_penalty_obstacles": True,
        "penalty_ratio": 0.3
    },
    3: {
        "obstacle_speed": 400.0,
        "obstacle_count": 25,
        "obstacle_health": 3,
        "spawn_penalty_obstacles": True,
        "penalty_ratio": 0.25
    }
}

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
        if not game_state["paused"]:
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
        if not game_state["paused"]:
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
        if not game_state["paused"]:
            self.x -= 60 * dt
            self.rotation += self.rotation_speed * dt
            if self.x < -WORLD_W/2 - 100:
                self.x = WORLD_W/2 + 100

class Obstacle:
    def __init__(self, level=1, is_penalty=False):
        self.x = WORLD_W/2 + 200
        self.y = random.uniform(-WORLD_H/2 + 100, WORLD_H/2 - 100)
        self.z = random.uniform(-170, 170)
        self.size = random.uniform(15, 30)
        self.rotation = random.uniform(0, 360)
        self.rotation_speed = random.uniform(30, 100)
        
        config = LEVEL_CONFIG[level]
        self.health = config["obstacle_health"]
        self.max_health = config["obstacle_health"]
        self.speed = config["obstacle_speed"]
        
        self.is_penalty = is_penalty
        if is_penalty:
            self.color = [1.0, 0.0, 0.0]
            self.glow_phase = random.uniform(0, 6.28)
        else:
            self.color = [
                random.uniform(0.3, 0.9),
                random.uniform(0.3, 0.9),
                random.uniform(0.3, 0.9)
            ]
        
        self.shape = random.choice(['cube', 'sphere', 'pyramid', 'torus'])
    
    def update(self, dt):
        if not game_state["paused"]:
            self.x -= self.speed * dt
            self.rotation += self.rotation_speed * dt
            if self.is_penalty:
                self.glow_phase += dt * 3
    
    def draw(self):
        glPushMatrix()
        glTranslatef(self.x, self.y, self.z)
        
        if self.is_penalty:
            glow = 0.5 + 0.5 * math.sin(self.glow_phase)
            glColor3f(1.0, glow * 0.3, glow * 0.3)
        else:
            intensity = self.health / self.max_health
            glColor3f(self.color[0] * intensity, 
                     self.color[1] * intensity, 
                     self.color[2] * intensity)
        
        if self.shape == 'cube':
            glRotatef(self.rotation, 1, 1, 0)
            glutSolidCube(self.size)
        elif self.shape == 'sphere':
            glutSolidSphere(self.size/2, 15, 15)
        elif self.shape == 'pyramid':
            glRotatef(self.rotation, 0, 1, 0)
            glBegin(GL_TRIANGLES)
            s = self.size/2
            glVertex3f(0, s, 0)
            glVertex3f(-s, -s, s)
            glVertex3f(s, -s, s)
            
            glVertex3f(0, s, 0)
            glVertex3f(s, -s, s)
            glVertex3f(s, -s, -s)
            
            glVertex3f(0, s, 0)
            glVertex3f(s, -s, -s)
            glVertex3f(-s, -s, -s)
            
            glVertex3f(0, s, 0)
            glVertex3f(-s, -s, -s)
            glVertex3f(-s, -s, s)
            glEnd()
        elif self.shape == 'torus':
            glRotatef(self.rotation, 1, 0, 1)
            glutSolidTorus(self.size/4, self.size/2, 10, 15)
        
        glPopMatrix()
        
        if self.max_health > 1:
            self.draw_health_bar()
    
    def draw_health_bar(self):
        glPushMatrix()
        glTranslatef(self.x, self.y + self.size + 10, self.z)
        
        glColor3f(0.2, 0.2, 0.2)
        glBegin(GL_QUADS)
        glVertex3f(-15, 0, 0)
        glVertex3f(15, 0, 0)
        glVertex3f(15, 3, 0)
        glVertex3f(-15, 3, 0)
        glEnd()
        
        health_width = 30 * (self.health / self.max_health)
        if self.health / self.max_health > 0.5:
            glColor3f(0.0, 1.0, 0.0)
        elif self.health / self.max_health > 0.25:
            glColor3f(1.0, 1.0, 0.0)
        else:
            glColor3f(1.0, 0.0, 0.0)
        
        glBegin(GL_QUADS)
        glVertex3f(-15, 0, 0)
        glVertex3f(-15 + health_width, 0, 0)
        glVertex3f(-15 + health_width, 3, 0)
        glVertex3f(-15, 3, 0)
        glEnd()
        
        glPopMatrix()

class Projectile:
    def __init__(self, x, y, z):
        self.x = x
        self.y = y
        self.z = z
        self.speed = 600.0
        self.life = 2.0
    
    def update(self, dt):
        if not game_state["paused"]:
            self.x += self.speed * dt
            self.life -= dt
    
    def draw(self):
        glPushMatrix()
        glTranslatef(self.x, self.y, self.z)
        
        glColor3f(0.0, 1.0, 1.0)
        glutSolidSphere(3, 8, 8)
        
        glColor4f(0.0, 0.8, 1.0, 0.3)
        for i in range(1, 4):
            glPushMatrix()
            glTranslatef(-i * 8, 0, 0)
            glutSolidSphere(2, 6, 6)
            glPopMatrix()
        
        glPopMatrix()

class Particle:
    def __init__(self, x, y, z, color):
        self.x = x
        self.y = y
        self.z = z
        self.vx = random.uniform(-100, 100)
        self.vy = random.uniform(-100, 100)
        self.vz = random.uniform(-100, 100)
        self.life = random.uniform(0.3, 0.8)
        self.color = color
        self.size = random.uniform(2, 5)
    
    def update(self, dt):
        self.x += self.vx * dt
        self.y += self.vy * dt
        self.z += self.vz * dt
        self.life -= dt
    
    def draw(self):
        if self.life <= 0:
            return
        glPushMatrix()
        glTranslatef(self.x, self.y, self.z)
        alpha = self.life
        glColor4f(self.color[0], self.color[1], self.color[2], alpha)
        glutSolidSphere(self.size, 6, 6)
        glPopMatrix()

# =========================
# GAME FUNCTIONS
# =========================

def initialize_scene():
    global stars, nebulas, planets, obstacles
    
    stars.clear()
    nebulas.clear()
    planets.clear()
    obstacles.clear()
    
    for _ in range(600):
        stars.append(Star())
    for _ in range(8):
        nebulas.append(Nebula())
    for _ in range(5):
        planets.append(Planet())
    
    spawn_obstacles()

def spawn_obstacles():
    global obstacles
    
    level = game_state["level"]
    config = LEVEL_CONFIG[level]
    
    obstacles.clear()
    
    spacing = 150.0
    for i in range(config["obstacle_count"]):
        is_penalty = False
        if config["spawn_penalty_obstacles"]:
            is_penalty = random.random() < config["penalty_ratio"]
        
        obs = Obstacle(level=level, is_penalty=is_penalty)
        obs.x = WORLD_W/2 + 200 + i * spacing
        obstacles.append(obs)

def create_explosion(x, y, z, color):
    for _ in range(15):
        particles.append(Particle(x, y, z, color))

def shoot_projectile():
    if game_state["ammo"] > 0:
        proj = Projectile(
            spaceship["x"] + 40,
            spaceship["y"],
            spaceship["z"]
        )
        projectiles.append(proj)
        game_state["ammo"] -= 1

def check_collisions():
    ship_x, ship_y, ship_z = spaceship["x"], spaceship["y"], spaceship["z"]
    ship_radius = 30
    
    # Projectile vs Obstacle
    for proj in projectiles[:]:
        if proj.life <= 0:
            projectiles.remove(proj)
            continue
        
        for obs in obstacles[:]:
            dx = proj.x - obs.x
            dy = proj.y - obs.y
            dz = proj.z - obs.z
            dist = math.sqrt(dx*dx + dy*dy + dz*dz)
            collision_threshold = obs.size + 5
            if dist < collision_threshold:
                if proj in projectiles:
                    projectiles.remove(proj)
                
                if obs.is_penalty:
                    game_state["lives"] -= 1
                    spaceship["health"] -= 30
                    create_explosion(obs.x, obs.y, obs.z, [1.0, 0.0, 0.0])
                    if spaceship["health"] < 0:
                        spaceship["health"] = 0
                    print("WARNING: Hit penalty obstacle! Lives:", game_state["lives"])
                else:
                    obs.health -= 1
                    create_explosion(obs.x, obs.y, obs.z, obs.color)
                    
                    if obs.health <= 0:
                        obstacles.remove(obs)
                        game_state["score"] += 10
                        
                        level = game_state["level"]
                        config = LEVEL_CONFIG[level]
                        is_penalty = False
                        if config["spawn_penalty_obstacles"]:
                            is_penalty = random.random() < config["penalty_ratio"]
                        new_obs = Obstacle(level=level, is_penalty=is_penalty)
                        obstacles.append(new_obs)
                        
                        if game_state["score"] >= game_state["level"] * 100 and game_state["level"] < 3:
                            advance_level()
                break
    
    # Ship vs Obstacle
    for obs in obstacles[:]:
        dx = ship_x - obs.x
        dy = ship_y - obs.y
        dz = ship_z - obs.z
        dist = math.sqrt(dx*dx + dy*dy + dz*dz)
        collision_threshold = ship_radius + obs.size + 10
        if dist < collision_threshold:
            game_state["lives"] -= 1
            spaceship["health"] -= 40
            create_explosion(obs.x, obs.y, obs.z, obs.color)
            
            obs.x = WORLD_W/2 + 200
            obs.y = random.uniform(-WORLD_H/2 + 100, WORLD_H/2 - 100)
            
            if spaceship["health"] < 0:
                spaceship["health"] = 0
            
            print("COLLISION! Lives:", game_state["lives"], "Health:", spaceship["health"])
            break

def advance_level():
    game_state["level"] += 1
    print("\nLEVEL", game_state["level"], "REACHED!")
    spawn_obstacles()

def update_game(dt):
    if game_state["paused"]:
        return
    
    for star in stars:
        star.update(dt)
    for nebula in nebulas:
        nebula.update(dt)
    for planet in planets:
        planet.update(dt)
    
    for obs in obstacles[:]:
        obs.update(dt)
        if obs.x < -WORLD_W/2 - 200:
            obstacles.remove(obs)
            level = game_state["level"]
            config = LEVEL_CONFIG[level]
            is_penalty = False
            if config["spawn_penalty_obstacles"]:
                is_penalty = random.random() < config["penalty_ratio"]
            obstacles.append(Obstacle(level=level, is_penalty=is_penalty))
            game_state["score"] += 1
    
    for proj in projectiles[:]:
        proj.update(dt)
        if proj.life <= 0 or proj.x > WORLD_W/2 + 200:
            projectiles.remove(proj)
    
    for particle in particles[:]:
        particle.update(dt)
        if particle.life <= 0:
            particles.remove(particle)
    
    current_time = time.time()
    if current_time - game_state["last_ammo_recharge"] >= AMMO_RECHARGE_TIME:
        if game_state["ammo"] < INITIAL_AMMO:
            game_state["ammo"] += 1
        game_state["last_ammo_recharge"] = current_time
    
    check_collisions()

# =========================
# DRAWING FUNCTIONS
# =========================

def draw_gradient_background():
    level = min(game_state["level"], 3)
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
    glPointSize(2.0)
    for star in stars:
        twinkle = 0.5 + 0.5 * math.sin(time.time() * star.twinkle_speed + star.twinkle_offset)
        brightness = star.brightness * twinkle
        glColor3f(brightness, brightness, brightness)
        glBegin(GL_POINTS)
        glVertex3f(star.x, star.y, star.z)
        glEnd()

def draw_nebulas():
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
    for planet in planets:
        glPushMatrix()
        glTranslatef(planet.x, planet.y, planet.z)
        glRotatef(planet.rotation, 0, 1, 0)
        glColor3f(*planet.color)
        glutSolidSphere(planet.size, 25, 25)
        glPopMatrix()

def draw_spaceship():
    x, y, z = spaceship["x"], spaceship["y"], spaceship["z"]
    
    glPushMatrix()
    glTranslatef(x, y, z)
    glRotatef(spaceship["rotation"], 0, 1, 0)
    
    glColor3f(0.8, 0.8, 0.9)
    glPushMatrix()
    glScalef(3, 1, 1)
    glutSolidSphere(15, 20, 20)
    glPopMatrix()
    
    glColor3f(0.2, 0.6, 1.0)
    glPushMatrix()
    glTranslatef(30, 8, 0)
    glScalef(1.5, 0.8, 0.8)
    glutSolidSphere(10, 15, 15)
    glPopMatrix()
    
    glColor3f(0.6, 0.6, 0.7)
    glPushMatrix()
    glTranslatef(0, 15, 0)
    glRotatef(45, 1, 0, 0)
    glScalef(1.5, 0.2, 2)
    glutSolidCube(12)
    glPopMatrix()
    
    glPushMatrix()
    glTranslatef(0, -15, 0)
    glRotatef(-45, 1, 0, 0)
    glScalef(1.5, 0.2, 2)
    glutSolidCube(12)
    glPopMatrix()
    
    glColor3f(0.0, 0.8, 1.0)
    glPushMatrix()
    glTranslatef(-35, 0, 0)
    glutSolidSphere(5, 12, 12)
    glPopMatrix()
    
    glPopMatrix()

def set_camera():
    glMatrixMode(GL_PROJECTION)
    glLoadIdentity()
    gluPerspective(60.0, WINDOW_W / WINDOW_H, 1.0, 2000.0)
    
    glMatrixMode(GL_MODELVIEW)
    glLoadIdentity()
    
    if game_state["camera_mode"] == "first_person":
        gluLookAt(
            spaceship["x"] + 30, spaceship["y"] + 20, spaceship["z"],
            spaceship["x"] + 150, spaceship["y"], spaceship["z"],
            0, 1, 0
        )
    else:
        gluLookAt(
            spaceship["x"] - 200, spaceship["y"] + 100, spaceship["z"] + 300,
            spaceship["x"], spaceship["y"], spaceship["z"],
            0, 1, 0
        )

# =========================
# GLUT CALLBACKS
# =========================

def display():
    glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
    
    draw_gradient_background()
    set_camera()
    
    glEnable(GL_DEPTH_TEST)
    
    draw_stars()
    draw_nebulas()
    draw_planets()
    
    for obs in obstacles:
        obs.draw()
    
    for proj in projectiles:
        proj.draw()
    
    glEnable(GL_BLEND)
    glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)
    for particle in particles:
        particle.draw()
    glDisable(GL_BLEND)
    
    draw_spaceship()
    
    glDisable(GL_DEPTH_TEST)
    
    if game_state["paused"]:
        glMatrixMode(GL_PROJECTION)
        glPushMatrix()
        glLoadIdentity()
        glOrtho(0, WINDOW_W, 0, WINDOW_H, -1, 1)
        
        glMatrixMode(GL_MODELVIEW)
        glPushMatrix()
        glLoadIdentity()
        
        glEnable(GL_BLEND)
        glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)
        glColor4f(0, 0, 0, 0.5)
        glBegin(GL_QUADS)
        glVertex2f(0, 0)
        glVertex2f(WINDOW_W, 0)
        glVertex2f(WINDOW_W, WINDOW_H)
        glVertex2f(0, WINDOW_H)
        glEnd()
        glDisable(GL_BLEND)
        
        glColor3f(1, 1, 0)
        glRasterPos2f(WINDOW_W//2 - 50, WINDOW_H//2)
        text = "PAUSED"
        for char in text:
            glutBitmapCharacter(GLUT_BITMAP_TIMES_ROMAN_24, ord(char))
        
        glPopMatrix()
        glMatrixMode(GL_PROJECTION)
        glPopMatrix()
        glMatrixMode(GL_MODELVIEW)
    
    glutSwapBuffers()

def idle():
    if game_state["paused"]:
        glutPostRedisplay()
        return
    
    now = time.time()
    if game_state["last_time"] == 0:
        game_state["last_time"] = now
    
    dt = now - game_state["last_time"]
    game_state["last_time"] = now
    dt = min(dt, 0.1)
    
    update_game(dt)
    glutPostRedisplay()

def keyboard(key, x, y):
    if key == b' ':
        shoot_projectile()
    elif key in [b'c', b'C']:
        if game_state["camera_mode"] == "third_person":
            game_state["camera_mode"] = "first_person"
            print("First-person camera")
        else:
            game_state["camera_mode"] = "third_person"
            print("Third-person camera")
    elif key in [b'p', b'P']:
        game_state["paused"] = not game_state["paused"]
        if game_state["paused"]:
            print("Paused")
        else:
            print("Resumed")
            game_state["last_time"] = time.time()
    elif key in [b'q', b'Q', b'\x1b']:
        print("Thanks for playing!")
        sys.exit()

def special_keys(key, x, y):
    if game_state["paused"]:
        return
    
    move_speed = 15
    
    if key == GLUT_KEY_UP:
        spaceship["y"] += move_speed
        spaceship["y"] = min(spaceship["y"], WORLD_H/2 - 50)
    elif key == GLUT_KEY_DOWN:
        spaceship["y"] -= move_speed
        spaceship["y"] = max(spaceship["y"], -WORLD_H/2 + 50)
    elif key == GLUT_KEY_LEFT:
        spaceship["z"] -= move_speed
        spaceship["z"] = max(spaceship["z"], -170)
    elif key == GLUT_KEY_RIGHT:
        spaceship["z"] += move_speed
        spaceship["z"] = min(spaceship["z"], 170)

def reshape(w, h):
    glViewport(0, 0, max(1, w), max(1, h))

def init_gl():
    glClearColor(0.0, 0.0, 0.0, 1.0)
    glEnable(GL_DEPTH_TEST)
    glShadeModel(GL_SMOOTH)
    glEnable(GL_COLOR_MATERIAL)

# =========================
# MAIN
# =========================

def main():
    glutInit()
    glutInitDisplayMode(GLUT_DOUBLE | GLUT_RGB | GLUT_DEPTH)
    glutInitWindowSize(WINDOW_W, WINDOW_H)
    glutCreateWindow(b"Cosmic Flight - Commit 2: Core Gameplay")
    
    init_gl()
    initialize_scene()
    game_state["last_time"] = time.time()
    game_state["last_ammo_recharge"] = time.time()
    
    glutDisplayFunc(display)
    glutIdleFunc(idle)
    glutKeyboardFunc(keyboard)
    glutSpecialFunc(special_keys)
    glutReshapeFunc(reshape)
    
    print("\n" + "="*60)
    print("COSMIC FLIGHT - COMMIT 2: CORE GAMEPLAY")
    print("="*60)
    print("\nPlayable game with:")
    print("  • Spaceship movement (Y & Z axes)")
    print("  • Obstacles (normal + penalty)")
    print("  • Shooting mechanics")
    print("  • Collision detection")
    print("  • Particle explosions")
    print("  • Camera toggle")
    print("\nControls:")
    print("  Arrow keys - Move spaceship")
    print("  SPACE      - Shoot")
    print("  C          - Toggle camera")
    print("  P          - Pause")
    print("  Q/ESC      - Quit")
    print("\nScore: Terminal only (no HUD yet)")
    print("Lives:", game_state["lives"], " | Ammo:", game_state["ammo"])
    print("\nNext: Add UI, screens, HUD (Commit 3)")
    print("="*60 + "\n")
    
    glutMainLoop()

if __name__ == "__main__":
    main()
