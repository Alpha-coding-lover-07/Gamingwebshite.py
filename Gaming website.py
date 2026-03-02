import pygame
import random
import math

# --- Core Setup ---
pygame.init()
WIDTH, HEIGHT = 600, 950
screen = pygame.display.set_mode((WIDTH, HEIGHT))
clock = pygame.time.Clock()

C = {
    'bg': (5, 5, 15),
    'p': (0, 255, 255),
    'e': (255, 0, 100),
    'b': (255, 255, 0),
    'eb': (255, 50, 50),  # Enemy Bullet (Red)
    's': (50, 255, 50),
    'tx': (255, 255, 255),
}

# --- Variables ---
player = {'pos': [WIDTH//2, HEIGHT-150], 'shield': 0, 'combo': 0, 'health': 3}
bullets, e_bullets, enemies, powerups, particles, stars = [], [], [], [], [], []
score, level, shake, game_active = 0, 1, 0, True

for _ in range(80):
    stars.append([random.randint(0, WIDTH), random.randint(0, HEIGHT), random.random() * 2 + 1])

def reset_game():
    global player, bullets, e_bullets, enemies, powerups, particles, score, level, shake, game_active, fire_timer, wave_timer
    player = {'pos': [WIDTH//2, HEIGHT-150], 'shield': 0, 'combo': 0, 'health': 3}
    bullets, e_bullets, enemies, powerups, particles = [], [], [], [], []
    score, level, shake, game_active = 0, 1, 0, True
    fire_timer, wave_timer = 0, 0

def spawn_wave():
    wave_size = 4 + (level // 2)
    for _ in range(wave_size):
        enemies.append({
            'pos': [random.randint(0, WIDTH-50), random.randint(-200, 0)],
            'hp': level, 
            's': random.uniform(3, 5 + level*0.3),
            'last_shot': pygame.time.get_ticks()
        })

def create_fx(x, y, color, n=15):
    for _ in range(n):
        particles.append([[x, y], [random.uniform(-5, 5), random.uniform(-5, 5)], random.randint(3, 6), color])

# --- Main Loop ---
running, fire_timer, wave_timer = True, 0, 0

while running:
    for event in pygame.event.get():
        if event.type == pygame.QUIT: running = False
        if event.type == pygame.MOUSEBUTTONDOWN and not game_active: reset_game()

    if game_active:
        shake = max(0, shake - 1)
        m_pos = pygame.mouse.get_pos()
        player['pos'][0] += (m_pos[0] - player['pos'][0] - 25) * 0.2
        player['pos'][1] += (m_pos[1] - player['pos'][1] - 40) * 0.2

        # 1. WAVE & AUTO-FIRE
        wave_timer += 1
        if wave_timer > max(50, 140 - (level * 10)):
            spawn_wave(); wave_timer = 0

        is_god = player['shield'] > 0
        if is_god: player['shield'] -= 1
        
        fire_timer += 1
        if fire_timer >= max(1, 4 - (player['combo'] // 25)):
            bullets.append([player['pos'][0] + 25, player['pos'][1], 0, C['b']])
            if player['combo'] > 15 or is_god:
                bullets.append([player['pos'][0]-5, player['pos'][1]+10, -1.2, C['p']])
                bullets.append([player['pos'][0]+55, player['pos'][1]+10, 1.2, C['p']])
            fire_timer = 0

        # 2. BULLET UPDATES
        for b in bullets[:]:
            b[1] -= 16; b[0] += b[2]
            if b[1] < 0: bullets.remove(b)
        
        for eb in e_bullets[:]:
            eb[1] += 10 # Enemy bullets are slower but deadly
            if eb[1] > HEIGHT: e_bullets.remove(eb)
            # Check if Player Hit
            p_rect = pygame.Rect(player['pos'][0], player['pos'][1], 50, 50)
            if p_rect.collidepoint(eb[0], eb[1]) and not is_god:
                player['health'] -= 1; e_bullets.remove(eb); shake = 20
                if player['health'] <= 0: game_active = False

        # 3. ENEMIES LOGIC
        now = pygame.time.get_ticks()
        for e in enemies[:]:
            e['pos'][1] += e['s']
            e_rect = pygame.Rect(e['pos'][0], e['pos'][1], 50, 50)
            
            # Enemy Shooting Logic
            if now - e['last_shot'] > random.randint(1500, 3000):
                e_bullets.append([e['pos'][0]+25, e['pos'][1]+50])
                e['last_shot'] = now

            if e_rect.colliderect(pygame.Rect(player['pos'][0], player['pos'][1], 50, 50)):
                if not is_god: player['health'] -= 1; enemies.remove(e); shake = 15
                if player['health'] <= 0: game_active = False
                else: enemies.remove(e)

            for b in bullets[:]:
                if e_rect.collidepoint(b[0], b[1]):
                    e['hp'] -= 1
                    if b in bullets: bullets.remove(b)
                    if e['hp'] <= 0:
                        create_fx(e['pos'][0]+25, e['pos'][1]+25, C['e'])
                        enemies.remove(e); score += 1; player['combo'] += 1
                        if score % 50 == 0: level += 1
                    break
            if e['pos'][1] > HEIGHT: enemies.remove(e); player['combo'] = max(0, player['combo'] - 3)

        if random.random() < 0.004: powerups.append([random.randint(50, WIDTH-50), -50])
        for p in powerups[:]:
            p[1] += 5
            if pygame.Rect(p[0]-20, p[1]-20, 40, 40).colliderect(pygame.Rect(player['pos'][0], player['pos'][1], 50, 50)):
                player['shield'] = 500; powerups.remove(p)

    # --- RENDERING ---
    off = [random.randint(-shake, shake), random.randint(-shake, shake)] if shake > 0 else [0,0]
    screen.fill(C['bg'])
    for s in stars: 
        s[1] += s[2]
        if s[1] > HEIGHT: s[1] = 0
        pygame.draw.circle(screen, (100, 100, 150), (int(s[0]), int(s[1])), 1)

    # Draw Player & Health
    px, py = player['pos'][0]+off[0], player['pos'][1]+off[1]
    if game_active:
        if is_god: pygame.draw.circle(screen, C['s'], (int(px+25), int(py+25)), 70, 2)
        pygame.draw.polygon(screen, C['p'], [(px+25, py), (px-15, py+60), (px+65, py+60)])
        # Health Bar
        for i in range(player['health']):
            pygame.draw.rect(screen, (0, 255, 0), (20 + (i*35), 70, 30, 10))

    for e in enemies: pygame.draw.rect(screen, C['e'], (e['pos'][0], e['pos'][1], 50, 50), 3, border_radius=5)
    for b in bullets: pygame.draw.circle(screen, b[3], (int(b[0]), int(b[1])), 5)
    for eb in e_bullets: pygame.draw.circle(screen, C['eb'], (int(eb[0]), int(eb[1])), 6)
    for p in powerups: pygame.draw.circle(screen, C['s'], (p[0], p[1]), 20, 4)

    # UI
    f = pygame.font.SysFont("Arial", 30, True)
    screen.blit(f.render(f"SCORE: {score}  LVL: {level}", True, C['tx']), (20, 20))
    
    if not game_active:
        screen.blit(f.render("GAME OVER - TAP TO RESTART", True, C['e']), (WIDTH//2-180, HEIGHT//2))

    pygame.display.flip()
    clock.tick(60)
pygame.quit()
              
