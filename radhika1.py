from OpenGL.GL import *
from OpenGL.GLU import *
from OpenGL.GLUT import *
import random
import time
import math
import sys

# Window and World Configuration
WINDOW_W, WINDOW_H = 1200, 900
WORLD_W, WORLD_H, WORLD_D = 1000.0, 700.0, 1000.0

# Game Configuration
INITIAL_LIVES = 3
INITIAL_AMMO = 20
AMMO_RECHARGE_TIME = 3.0  # Seconds to recharge 1 ammo

# Background Colors (will change with levels)
BG_COLORS = {
    1: {"top": [0.05, 0.05, 0.15], "bot": [0.0, 0.0, 0.05]},  # Deep space
    2: {"top": [0.15, 0.05, 0.25], "bot": [0.05, 0.0, 0.1]},  # Purple nebula
    3: {"top": [0.25, 0.1, 0.1], "bot": [0.1, 0.0, 0.0]}      # Red danger zone
}

# Global Game State
game_state = {
    "in_start_screen": True,
    "game_over": False,
    "paused": False,
    "level": 1,
    "score": 0,
    "lives": INITIAL_LIVES,
    "ammo": INITIAL_AMMO,
    "last_ammo_recharge": 0.0,
    "camera_mode": "third_person",  # or "first_person"
    "last_time": 0.0,
    "show_instructions": False
}

# Spaceship Configuration
spaceship = {
    "x": -200.0,
    "y": 0.0,
    "z": 0.0,
    "rotation": 0.0,
    "speed": 300.0,  # Movement speed
    "health": 100,
    "max_health": 100,
    "shield_active": False,
    "shield_time": 0.0
}

# Collections
stars = []
nebulas = []
planets = []
obstacles = []
projectiles = []
powerups = []
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
        "penalty_ratio": 0.3  # 30% of obstacles are penalty
    },
    3: {
        "obstacle_speed": 400.0,
        "obstacle_count": 25,
        "obstacle_health": 3,  # Require multiple hits
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
        
        # Level-based properties
        config = LEVEL_CONFIG[level]
        self.health = config["obstacle_health"]
        self.max_health = config["obstacle_health"]
        self.speed = config["obstacle_speed"]
        
        # Penalty obstacle (RED - shooting causes damage)
        self.is_penalty = is_penalty
        if is_penalty:
            self.color = [1.0, 0.0, 0.0]  # Red
            self.glow_phase = random.uniform(0, 6.28)
        else:
            # Normal obstacles (various colors)
            self.color = [
                random.uniform(0.3, 0.9),
                random.uniform(0.3, 0.9),
                random.uniform(0.3, 0.9)
            ]
        
        # Obstacle type (visual variety)
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
        
        # Glow effect for penalty obstacles
        if self.is_penalty:
            glow = 0.5 + 0.5 * math.sin(self.glow_phase)
            glColor3f(1.0, glow * 0.3, glow * 0.3)
        else:
            # Health-based color intensity
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
            # Draw pyramid
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
        
        # Draw health bar for obstacles with health > 1
        if self.max_health > 1:
            self.draw_health_bar()
    
    def draw_health_bar(self):
        glPushMatrix()
        glTranslatef(self.x, self.y + self.size + 10, self.z)
        
        # Background
        glColor3f(0.2, 0.2, 0.2)
        glBegin(GL_QUADS)
        glVertex3f(-15, 0, 0)
        glVertex3f(15, 0, 0)
        glVertex3f(15, 3, 0)
        glVertex3f(-15, 3, 0)
        glEnd()
        
        # Health
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
        self.life = 2.0  # Seconds before disappearing
    
    def update(self, dt):
        if not game_state["paused"]:
            self.x += self.speed * dt
            self.life -= dt
    
    def draw(self):
        glPushMatrix()
        glTranslatef(self.x, self.y, self.z)
        
        # Glowing projectile
        glColor3f(0.0, 1.0, 1.0)
        glutSolidSphere(3, 8, 8)
        
        # Trail effect
        glColor4f(0.0, 0.8, 1.0, 0.3)
        for i in range(1, 4):
            glPushMatrix()
            glTranslatef(-i * 8, 0, 0)
            glutSolidSphere(2, 6, 6)
            glPopMatrix()
        
        glPopMatrix()

class PowerUp:
    """NEW FEATURE 1: Power-ups that spawn randomly"""
    def __init__(self):
        self.x = WORLD_W/2 + 200
        self.y = random.uniform(-WORLD_H/2 + 100, WORLD_H/2 - 100)
        self.z = random.uniform(-30, 30)
        self.size = 15
        self.rotation = 0
        self.type = random.choice(['ammo', 'shield', 'health'])
        self.collected = False
        self.bob_offset = random.uniform(0, 6.28)
    
    def update(self, dt):
        if not game_state["paused"] and not self.collected:
            self.x -= 150 * dt
            self.rotation += 180 * dt
            self.bob_offset += dt * 2
    
    def draw(self):
        if self.collected:
            return
        
        glPushMatrix()
        glTranslatef(self.x, self.y + math.sin(self.bob_offset) * 5, self.z)
        glRotatef(self.rotation, 0, 1, 0)
        
        if self.type == 'ammo':
            glColor3f(1.0, 1.0, 0.0)  # Yellow
            glutSolidCube(self.size)
        elif self.type == 'shield':
            glColor3f(0.0, 0.5, 1.0)  # Blue
            glutSolidSphere(self.size/2, 12, 12)
        elif self.type == 'health':
            glColor3f(0.0, 1.0, 0.0)  # Green
            glutSolidTorus(self.size/4, self.size/2, 8, 12)
        
        glPopMatrix()

class Particle:
    """Explosion particle effect"""
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
    """Initialize all scene objects"""
    global stars, nebulas, planets, obstacles, powerups
    
    stars.clear()
    nebulas.clear()
    planets.clear()
    obstacles.clear()
    powerups.clear()
    
    # Create stars
    for _ in range(600):
        stars.append(Star())
    
    # Create nebulas
    for _ in range(8):
        nebulas.append(Nebula())
    
    # Create planets
    for _ in range(5):
        planets.append(Planet())
    
    # Create initial obstacles
    spawn_obstacles()

def spawn_obstacles():
    """Spawn obstacles based on current level"""
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

def spawn_powerup():
    """Spawn a random power-up"""
    if random.random() < 0.15:  # 15% chance per spawn cycle
        powerups.append(PowerUp())

def create_explosion(x, y, z, color):
    """Create particle explosion effect"""
    for _ in range(15):
        particles.append(Particle(x, y, z, color))

def shoot_projectile():
    """Fire a projectile from the spaceship"""
    if game_state["ammo"] > 0 and not game_state["game_over"]:
        proj = Projectile(
            spaceship["x"] + 40,
            spaceship["y"],
            spaceship["z"]
        )
        projectiles.append(proj)
        game_state["ammo"] -= 1

def check_collisions():
    """Check all collision types"""
    ship_x, ship_y, ship_z = spaceship["x"], spaceship["y"], spaceship["z"]
    ship_radius = 30  # Increased for better collision detection
    
    # Projectile vs Obstacle collisions
    for proj in projectiles[:]:
        if proj.life <= 0:
            projectiles.remove(proj)
            continue
        
        for obs in obstacles[:]:
            dx = proj.x - obs.x
            dy = proj.y - obs.y
            dz = proj.z - obs.z
            dist = math.sqrt(dx*dx + dy*dy + dz*dz)
            
            # More lenient collision detection - increased threshold
            collision_threshold = obs.size + 5  # Added buffer for better detection
            if dist < collision_threshold:
                # Hit!
                if proj in projectiles:
                    projectiles.remove(proj)
                
                if obs.is_penalty:
                    # Penalty: lose life for shooting red obstacles
                    game_state["lives"] -= 1
                    spaceship["health"] -= 30
                    create_explosion(obs.x, obs.y, obs.z, [1.0, 0.0, 0.0])
                    if spaceship["health"] < 0:
                        spaceship["health"] = 0
                    if game_state["lives"] <= 0:
                        game_state["game_over"] = True
                    print("WARNING: Hit penalty obstacle! Lives: " + str(game_state['lives']))
                else:
                    # Normal obstacle: reduce health
                    obs.health -= 1
                    create_explosion(obs.x, obs.y, obs.z, obs.color)
                    
                    if obs.health <= 0:
                        # Destroyed!
                        obstacles.remove(obs)
                        game_state["score"] += 10
                        
                        # Respawn new obstacle
                        level = game_state["level"]
                        config = LEVEL_CONFIG[level]
                        is_penalty = False
                        if config["spawn_penalty_obstacles"]:
                            is_penalty = random.random() < config["penalty_ratio"]
                        new_obs = Obstacle(level=level, is_penalty=is_penalty)
                        obstacles.append(new_obs)
                        
                        # Check level progression
                        if game_state["score"] >= game_state["level"] * 100 and game_state["level"] < 3:
                            advance_level()
                break
    
    # Ship vs Obstacle collisions (if shield not active)
    if not spaceship["shield_active"]:
        for obs in obstacles[:]:
            dx = ship_x - obs.x
            dy = ship_y - obs.y
            dz = ship_z - obs.z
            dist = math.sqrt(dx*dx + dy*dy + dz*dz)
            
            # More lenient collision detection for ship
            collision_threshold = ship_radius + obs.size + 10  # Added buffer
            if dist < collision_threshold:
                # Collision!
                game_state["lives"] -= 1
                spaceship["health"] -= 40
                create_explosion(obs.x, obs.y, obs.z, obs.color)
                
                # Respawn obstacle
                obs.x = WORLD_W/2 + 200
                obs.y = random.uniform(-WORLD_H/2 + 100, WORLD_H/2 - 100)
                
                if spaceship["health"] < 0:
                    spaceship["health"] = 0
                
                if game_state["lives"] <= 0:
                    game_state["game_over"] = True
                
                print("COLLISION! Lives remaining: " + str(game_state['lives']) + ", Health: " + str(spaceship['health']))
                break
    
    # Ship vs PowerUp collisions
    for pup in powerups[:]:
        if pup.collected:
            continue
        
        dx = ship_x - pup.x
        dy = ship_y - pup.y
        dz = ship_z - pup.z
        dist = math.sqrt(dx*dx + dy*dy + dz*dz)
        
        # Increased collision range for powerups
        powerup_collision_range = ship_radius + pup.size + 15
        if dist < powerup_collision_range:
            pup.collected = True
            powerups.remove(pup)
            
            if pup.type == 'ammo':
                game_state["ammo"] += 10
                print("Ammo +10! Total: " + str(game_state['ammo']))
            elif pup.type == 'shield':
                spaceship["shield_active"] = True
                spaceship["shield_time"] = time.time()
                print("Shield activated!")
            elif pup.type == 'health':
                spaceship["health"] = min(spaceship["health"] + 30, spaceship["max_health"])
                print("Health +30! Total: " + str(spaceship['health']))

def advance_level():
    """Advance to next level"""
    game_state["level"] += 1
    print("\nLEVEL " + str(game_state['level']) + " REACHED!")
    print("New obstacles incoming...")
    spawn_obstacles()

def update_game(dt):
    """Update all game objects"""
    if game_state["paused"] or game_state["game_over"]:
        return
    
    # Update stars, nebulas, planets
    for star in stars:
        star.update(dt)
    for nebula in nebulas:
        nebula.update(dt)
    for planet in planets:
        planet.update(dt)
    
    # Update obstacles
    for obs in obstacles[:]:
        obs.update(dt)
        if obs.x < -WORLD_W/2 - 200:
            obstacles.remove(obs)
            # Spawn new obstacle
            level = game_state["level"]
            config = LEVEL_CONFIG[level]
            is_penalty = False
            if config["spawn_penalty_obstacles"]:
                is_penalty = random.random() < config["penalty_ratio"]
            obstacles.append(Obstacle(level=level, is_penalty=is_penalty))
            
            # Award survival points
            game_state["score"] += 1
    
    # Update projectiles
    for proj in projectiles[:]:
        proj.update(dt)
        if proj.life <= 0 or proj.x > WORLD_W/2 + 200:
            projectiles.remove(proj)
    
    # Update powerups
    for pup in powerups[:]:
        pup.update(dt)
        if pup.x < -WORLD_W/2 - 200:
            powerups.remove(pup)
    
    # Update particles
    for particle in particles[:]:
        particle.update(dt)
        if particle.life <= 0:
            particles.remove(particle)
    
    # Spawn powerups randomly
    if random.random() < 0.002:  # Small chance each frame
        spawn_powerup()
    
    # Ammo recharge over time
    current_time = time.time()
    if current_time - game_state["last_ammo_recharge"] >= AMMO_RECHARGE_TIME:
        if game_state["ammo"] < INITIAL_AMMO:
            game_state["ammo"] += 1
        game_state["last_ammo_recharge"] = current_time
    
    # Shield duration check (NEW FEATURE 2: Temporary shield)
    if spaceship["shield_active"]:
        if time.time() - spaceship["shield_time"] > 5.0:  # 5 second shield
            spaceship["shield_active"] = False
            print("Shield deactivated")
    
    # Check collisions
    check_collisions()

# =========================
# DRAWING FUNCTIONS
# =========================

def draw_gradient_background():
    """Draw gradient background based on level"""
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

def draw_spaceship():
    """Draw the player's spaceship with new design"""
    x, y, z = spaceship["x"], spaceship["y"], spaceship["z"]
    
    glPushMatrix()
    glTranslatef(x, y, z)
    glRotatef(spaceship["rotation"], 0, 1, 0)
    
    # Main hull (elongated diamond shape)
    glColor3f(0.8, 0.8, 0.9)
    glPushMatrix()
    glScalef(3, 1, 1)
    glutSolidSphere(15, 20, 20)
    glPopMatrix()
    
    # Cockpit
    glColor3f(0.2, 0.6, 1.0)
    glPushMatrix()
    glTranslatef(30, 8, 0)
    glScalef(1.5, 0.8, 0.8)
    glutSolidSphere(10, 15, 15)
    glPopMatrix()
    
    # Wings
    glColor3f(0.6, 0.6, 0.7)
    # Top wing
    glPushMatrix()
    glTranslatef(0, 15, 0)
    glRotatef(45, 1, 0, 0)
    glScalef(1.5, 0.2, 2)
    glutSolidCube(12)
    glPopMatrix()
    
    # Bottom wing
    glPushMatrix()
    glTranslatef(0, -15, 0)
    glRotatef(-45, 1, 0, 0)
    glScalef(1.5, 0.2, 2)
    glutSolidCube(12)
    glPopMatrix()
    
    # Engine glow
    glColor3f(0.0, 0.8, 1.0)
    glPushMatrix()
    glTranslatef(-35, 0, 0)
    glutSolidSphere(5, 12, 12)
    glPopMatrix()
    
    # Shield effect if active
    if spaceship["shield_active"]:
        glEnable(GL_BLEND)
        glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)
        pulse = 0.5 + 0.3 * math.sin(time.time() * 5)
        glColor4f(0.0, 0.5, 1.0, pulse)
        glutSolidSphere(35, 25, 25)
        glDisable(GL_BLEND)
    
    glPopMatrix()

def draw_hud():
    """Draw heads-up display"""
    glMatrixMode(GL_PROJECTION)
    glPushMatrix()
    glLoadIdentity()
    glOrtho(0, WINDOW_W, 0, WINDOW_H, -1, 1)
    
    glMatrixMode(GL_MODELVIEW)
    glPushMatrix()
    glLoadIdentity()
    
    # Score
    glColor3f(1, 1, 1)
    draw_text(20, WINDOW_H - 30, f"SCORE: {game_state['score']}", GLUT_BITMAP_HELVETICA_18)
    
    # Level
    glColor3f(1, 1, 0)
    draw_text(20, WINDOW_H - 60, f"LEVEL: {game_state['level']}", GLUT_BITMAP_HELVETICA_18)
    
    # Lives
    glColor3f(1, 0.3, 0.3)
    draw_text(20, WINDOW_H - 90, f"LIVES: {game_state['lives']}", GLUT_BITMAP_HELVETICA_18)
    
    # Ammo
    glColor3f(0, 1, 1)
    draw_text(20, WINDOW_H - 120, f"AMMO: {game_state['ammo']}", GLUT_BITMAP_HELVETICA_18)
    
    # Health bar
    bar_width = 200
    bar_height = 20
    health_ratio = spaceship["health"] / spaceship["max_health"]
    
    # Background
    glColor3f(0.2, 0.2, 0.2)
    glBegin(GL_QUADS)
    glVertex2f(20, 30)
    glVertex2f(20 + bar_width, 30)
    glVertex2f(20 + bar_width, 30 + bar_height)
    glVertex2f(20, 30 + bar_height)
    glEnd()
    
    # Health
    if health_ratio > 0.5:
        glColor3f(0, 1, 0)
    elif health_ratio > 0.25:
        glColor3f(1, 1, 0)
    else:
        glColor3f(1, 0, 0)
    
    glBegin(GL_QUADS)
    glVertex2f(20, 30)
    glVertex2f(20 + bar_width * health_ratio, 30)
    glVertex2f(20 + bar_width * health_ratio, 30 + bar_height)
    glVertex2f(20, 30 + bar_height)
    glEnd()
    
    glColor3f(1, 1, 1)
    draw_text(25, 35, f"HEALTH: {int(spaceship['health'])}/{spaceship['max_health']}", GLUT_BITMAP_9_BY_15)
    
    # Instructions toggle hint
    glColor3f(0.7, 0.7, 0.7)
    draw_text(WINDOW_W - 200, 20, "Press H for help", GLUT_BITMAP_HELVETICA_12)
    
    glPopMatrix()
    glMatrixMode(GL_PROJECTION)
    glPopMatrix()
    glMatrixMode(GL_MODELVIEW)

def draw_text(x, y, text, font):
    """Helper to draw text"""
    glRasterPos2f(x, y)
    for char in text:
        glutBitmapCharacter(font, ord(char))

def draw_instructions():
    """Draw instruction overlay"""
    glMatrixMode(GL_PROJECTION)
    glPushMatrix()
    glLoadIdentity()
    glOrtho(0, WINDOW_W, 0, WINDOW_H, -1, 1)
    
    glMatrixMode(GL_MODELVIEW)
    glPushMatrix()
    glLoadIdentity()
    
    # Semi-transparent background
    glEnable(GL_BLEND)
    glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)
    glColor4f(0, 0, 0, 0.7)
    glBegin(GL_QUADS)
    glVertex2f(200, 150)
    glVertex2f(WINDOW_W - 200, 150)
    glVertex2f(WINDOW_W - 200, WINDOW_H - 150)
    glVertex2f(200, WINDOW_H - 150)
    glEnd()
    glDisable(GL_BLEND)
    
    # Title
    glColor3f(1, 1, 0)
    draw_text(WINDOW_W//2 - 100, WINDOW_H - 200, "GAME CONTROLS", GLUT_BITMAP_TIMES_ROMAN_24)
    
    # Instructions
    glColor3f(1, 1, 1)
    y_pos = WINDOW_H - 250
    instructions = [
        "UP/DOWN ARROW - Move spaceship vertically",
        "LEFT/RIGHT ARROW - Move spaceship horizontally (3D depth)",
        "SPACEBAR - Fire projectile (costs ammo)",
        "C - Toggle camera (Third/First person)",
        "P - Pause game",
        "H - Toggle this help screen",
        "Q/ESC - Quit game",
        "",
        "OBSTACLES:",
        "• Normal (colored) - Shoot to destroy (some need multiple hits)",
        "• RED (glowing) - PENALTY! Don't shoot or lose a life",
        "",
        "POWER-UPS:",
        "• Yellow cube - Ammo refill (+10)",
        "• Blue sphere - Temporary shield (5 seconds)",
        "• Green torus - Health restore (+30)",
        "",
        "SCORING:",
        "• Survive: +1 point per obstacle passed",
        "• Destroy: +10 points per obstacle destroyed",
        "• Level up every 100 points",
    ]
    
    for line in instructions:
        draw_text(250, y_pos, line, GLUT_BITMAP_HELVETICA_12)
        y_pos -= 25
    
    glColor3f(1, 1, 0)
    draw_text(WINDOW_W//2 - 80, 180, "Press H to close", GLUT_BITMAP_HELVETICA_18)
    
    glPopMatrix()
    glMatrixMode(GL_PROJECTION)
    glPopMatrix()
    glMatrixMode(GL_MODELVIEW)

def draw_start_screen():
    """Draw start screen"""
    glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
    
    glMatrixMode(GL_PROJECTION)
    glPushMatrix()
    glLoadIdentity()
    glOrtho(0, WINDOW_W, 0, WINDOW_H, -1, 1)
    
    glMatrixMode(GL_MODELVIEW)
    glPushMatrix()
    glLoadIdentity()
    
    # Background
    glBegin(GL_QUADS)
    glColor3f(0.05, 0.05, 0.2)
    glVertex2f(0, 0)
    glVertex2f(WINDOW_W, 0)
    glColor3f(0.0, 0.0, 0.05)
    glVertex2f(WINDOW_W, WINDOW_H)
    glVertex2f(0, WINDOW_H)
    glEnd()
    
    # Title
    glColor3f(0, 1, 1)
    draw_text(WINDOW_W//2 - 150, WINDOW_H//2 + 100, "COSMIC FLIGHT", GLUT_BITMAP_TIMES_ROMAN_24)
    
    glColor3f(1, 1, 1)
    draw_text(WINDOW_W//2 - 180, WINDOW_H//2 + 50, "Space Navigation Challenge", GLUT_BITMAP_HELVETICA_18)
    
    # Instructions
    glColor3f(0.8, 0.8, 0.8)
    draw_text(WINDOW_W//2 - 200, WINDOW_H//2 - 50, "Navigate through space avoiding obstacles", GLUT_BITMAP_HELVETICA_12)
    draw_text(WINDOW_W//2 - 200, WINDOW_H//2 - 80, "Shoot normal obstacles, avoid RED ones!", GLUT_BITMAP_HELVETICA_12)
    draw_text(WINDOW_W//2 - 180, WINDOW_H//2 - 110, "Collect power-ups to survive longer", GLUT_BITMAP_HELVETICA_12)
    
    # Start prompt
    glColor3f(1, 1, 0)
    glow = 0.5 + 0.5 * math.sin(time.time() * 3)
    glColor3f(glow, glow, 0)
    draw_text(WINDOW_W//2 - 120, WINDOW_H//2 - 180, "Click anywhere to start", GLUT_BITMAP_HELVETICA_18)
    
    glColor3f(0.6, 0.6, 0.6)
    draw_text(WINDOW_W//2 - 100, 50, "Press H in-game for controls", GLUT_BITMAP_HELVETICA_12)
    
    glPopMatrix()
    glMatrixMode(GL_PROJECTION)
    glPopMatrix()
    glMatrixMode(GL_MODELVIEW)
    
    glutSwapBuffers()

def draw_game_over_screen():
    """Draw game over screen"""
    glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
    
    glMatrixMode(GL_PROJECTION)
    glPushMatrix()
    glLoadIdentity()
    glOrtho(0, WINDOW_W, 0, WINDOW_H, -1, 1)
    
    glMatrixMode(GL_MODELVIEW)
    glPushMatrix()
    glLoadIdentity()
    
    # Background
    glBegin(GL_QUADS)
    glColor3f(0.1, 0.0, 0.0)
    glVertex2f(0, 0)
    glVertex2f(WINDOW_W, 0)
    glColor3f(0.0, 0.0, 0.0)
    glVertex2f(WINDOW_W, WINDOW_H)
    glVertex2f(0, WINDOW_H)
    glEnd()
    
    # Game Over text
    glColor3f(1, 0, 0)
    draw_text(WINDOW_W//2 - 100, WINDOW_H//2 + 80, "GAME OVER", GLUT_BITMAP_TIMES_ROMAN_24)
    
    # Stats
    glColor3f(1, 1, 1)
    draw_text(WINDOW_W//2 - 80, WINDOW_H//2 + 20, f"Final Score: {game_state['score']}", GLUT_BITMAP_HELVETICA_18)
    draw_text(WINDOW_W//2 - 80, WINDOW_H//2 - 20, f"Level Reached: {game_state['level']}", GLUT_BITMAP_HELVETICA_18)
    
    # Restart prompt
    glColor3f(1, 1, 0)
    glow = 0.5 + 0.5 * math.sin(time.time() * 3)
    glColor3f(glow, glow, 0)
    draw_text(WINDOW_W//2 - 120, WINDOW_H//2 - 80, "Click to restart", GLUT_BITMAP_HELVETICA_18)
    
    glPopMatrix()
    glMatrixMode(GL_PROJECTION)
    glPopMatrix()
    glMatrixMode(GL_MODELVIEW)
    
    glutSwapBuffers()

def set_camera():
    """Set camera based on mode"""
    glMatrixMode(GL_PROJECTION)
    glLoadIdentity()
    gluPerspective(60.0, WINDOW_W / WINDOW_H, 1.0, 2000.0)
    
    glMatrixMode(GL_MODELVIEW)
    glLoadIdentity()
    
    if game_state["camera_mode"] == "first_person":
        # First person: camera slightly in front to show front of spacecraft
        gluLookAt(
            spaceship["x"] + 30, spaceship["y"] + 20, spaceship["z"],  # Camera in front and above
            spaceship["x"] + 150, spaceship["y"], spaceship["z"],      # Looking forward
            0, 1, 0
        )
    else:
        # Third person: camera behind and above ship
        gluLookAt(
            spaceship["x"] - 200, spaceship["y"] + 100, spaceship["z"] + 300,
            spaceship["x"], spaceship["y"], spaceship["z"],
            0, 1, 0
        )

# =========================
# GLUT CALLBACKS
# =========================

def display():
    """Main display function"""
    glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
    
    if game_state["in_start_screen"]:
        draw_start_screen()
        return
    
    if game_state["game_over"]:
        draw_game_over_screen()
        return
    
    # Draw game
    draw_gradient_background()
    set_camera()
    
    # Enable depth testing
    glEnable(GL_DEPTH_TEST)
    
    # Draw scene
    draw_stars()
    draw_nebulas()
    draw_planets()
    
    # Draw obstacles
    for obs in obstacles:
        obs.draw()
    
    # Draw projectiles
    for proj in projectiles:
        proj.draw()
    
    # Draw power-ups
    for pup in powerups:
        pup.draw()
    
    # Draw particles
    glEnable(GL_BLEND)
    glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)
    for particle in particles:
        particle.draw()
    glDisable(GL_BLEND)
    
    # Draw spaceship (in third person mode, or partially visible in first person)
    draw_spaceship()
    
    glDisable(GL_DEPTH_TEST)
    
    # Draw HUD
    draw_hud()
    
    # Draw instructions if toggled
    if game_state["show_instructions"]:
        draw_instructions()
    
    # Draw pause overlay
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
        draw_text(WINDOW_W//2 - 50, WINDOW_H//2, "PAUSED", GLUT_BITMAP_TIMES_ROMAN_24)
        
        glPopMatrix()
        glMatrixMode(GL_PROJECTION)
        glPopMatrix()
        glMatrixMode(GL_MODELVIEW)
    
    glutSwapBuffers()

def idle():
    """Idle callback for animation"""
    if game_state["paused"] or game_state["in_start_screen"] or game_state["game_over"]:
        glutPostRedisplay()
        return
    
    now = time.time()
    if game_state["last_time"] == 0:
        game_state["last_time"] = now
    
    dt = now - game_state["last_time"]
    game_state["last_time"] = now
    
    # Cap dt to prevent large jumps
    dt = min(dt, 0.1)
    
    update_game(dt)
    glutPostRedisplay()

def keyboard(key, x, y):
    """Keyboard input"""
    if key == b' ':
        shoot_projectile()
    elif key in [b'c', b'C']:
        # Toggle camera
        if game_state["camera_mode"] == "third_person":
            game_state["camera_mode"] = "first_person"
            print("First-person camera")
        else:
            game_state["camera_mode"] = "third_person"
            print("Third-person camera")
    elif key in [b'p', b'P']:
        # Toggle pause
        game_state["paused"] = not game_state["paused"]
        if game_state["paused"]:
            print("Paused")
        else:
            print("Resumed")
            game_state["last_time"] = time.time()
    elif key in [b'h', b'H']:
        # Toggle instructions
        game_state["show_instructions"] = not game_state["show_instructions"]
    elif key in [b'q', b'Q', b'\x1b']:
        # Quit
        print("Thanks for playing!")
        sys.exit()

def special_keys(key, x, y):
    """Special key input (arrow keys)"""
    if game_state["paused"] or game_state["game_over"]:
        return
    
    move_speed = 15
    
    if key == GLUT_KEY_UP:
        spaceship["y"] += move_speed
        spaceship["y"] = min(spaceship["y"], WORLD_H/2 - 50)
    elif key == GLUT_KEY_DOWN:
        spaceship["y"] -= move_speed
        spaceship["y"] = max(spaceship["y"], -WORLD_H/2 + 50)
    elif key == GLUT_KEY_LEFT:
        # Add left movement with less restricted threshold
        spaceship["z"] -= move_speed
        spaceship["z"] = max(spaceship["z"], -170)  # Expanded to -250
    elif key == GLUT_KEY_RIGHT:
        # Add right movement with less restricted threshold
        spaceship["z"] += move_speed
        spaceship["z"] = min(spaceship["z"], 170)  # Expanded to +250

def mouse(button, state, x, y):
    """Mouse input"""
    if button == GLUT_LEFT_BUTTON and state == GLUT_DOWN:
        if game_state["in_start_screen"]:
            game_state["in_start_screen"] = False
            game_state["last_time"] = time.time()
            game_state["last_ammo_recharge"] = time.time()
            initialize_scene()
            print("\nGame started!")
        elif game_state["game_over"]:
            # Restart game
            game_state["game_over"] = False
            game_state["score"] = 0
            game_state["lives"] = INITIAL_LIVES
            game_state["ammo"] = INITIAL_AMMO
            game_state["level"] = 1
            spaceship["health"] = spaceship["max_health"]
            spaceship["x"] = -200.0
            spaceship["y"] = 0.0
            spaceship["shield_active"] = False
            game_state["last_time"] = time.time()
            game_state["last_ammo_recharge"] = time.time()
            initialize_scene()
            print("\nGame restarted!")

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
    glutCreateWindow(b"Cosmic Flight: Space Navigation")
    
    init_gl()
    
    glutDisplayFunc(display)
    glutIdleFunc(idle)
    glutKeyboardFunc(keyboard)
    glutSpecialFunc(special_keys)
    glutMouseFunc(mouse)
    glutReshapeFunc(reshape)
    
    print("\n" + "="*50)
    print("COSMIC FLIGHT: SPACE NAVIGATION GAME")
    print("="*50)
    print("\nWelcome, pilot! Prepare for your mission.")
    print("\nPress H in-game for full controls.")
    print("\nGood luck!\n")
    
    glutMainLoop()

if __name__ == "__main__":
    main()