import pygame
import sys
import os
import time
import shutil
import pandas as pd
if not os.path.exists("./SentinelENV.py"):
    print("The Env File Doesnt Exist.")
    sys.exit(1)
import SentinelENV
shutil.rmtree("./tmp", ignore_errors=True)
os.mkdir("tmp")


# old sim params dict - keeping just in case
# defP = {
#     "n_days": 365, "timestep": 5, "sensor_int": 60,
#     "catchment": 12000.0, "sewage": 6.0, "pipe_cap": 350.0,
#     "max_lvl": 100.0, "runoff": 0.75,
# }


# live control variables
blk=0
pop=1.0
rn=0
s_idx=0 
seasons=["auto", "winter", "pre_monsoon", "monsoon", "post_monsoon"]
hr_add=0
sp=5
psd=False

# step amounts for +/-
# blk_step = 5 # too slow
blk_step=10
pop_step=0.2
rn_step=5
sp_step=2


class Env():
    def __init__(self):
        t0 = time.perf_counter()

        # default drain
        drain = SentinelENV.DrainConfig(
            name="Manhole_1",
            catchment_area_m2=12000.0,
            base_sewage_lps=6.0,
            pipe_capacity_lps=350.0,
            max_level_cm=100.0,
            runoff_coefficient=0.75,
        )

        readings, events = SentinelENV.run_simulation(
            start_date="2026-01-01",
            n_days=365,
            timestep_minutes=5,
            sensor_interval_minutes=60,
            drain=drain,
            seed=None)

        elapsed = time.perf_counter() - t0
        print(f"Simulated in {elapsed}")
        readings.to_csv(os.path.join("tmp","tmp.csv"))
        df=pd.read_csv(os.path.join("tmp","tmp.csv"))
        df['timestamp'] = pd.to_datetime(df['timestamp'])
        df = df.sort_values('timestamp').reset_index(drop=True)

        df['hour'] = df['timestamp'].dt.hour
        df['month_num'] = df['timestamp'].dt.month
        self.data=df
        self.i=0
        self.maxI = len(df) - 1

    def getInfo(self):
        info=self.data.loc[self.i, ["season", "temp_c", "weather_state", "rain_mm", "level_cm", "demand_index", "hour"]]
        return info

    def next(self):
        if self.i < self.maxI:
            self.i+=1

    # not used anymore but keeping it
    # def ChangeParam(self):
    #     pass

    # def dump_readings(self, fname="test_run.csv"):
    #     with open(fname, "w") as f:
    #         for idx in range(len(self.data)):
    #             row = self.data.iloc[idx]
    #             f.write(f"{row['timestamp']},{row['level_cm']}\n")
    #     print("dumped to", fname)

    def reset(self):
        self.i = 0



ENV=Env()
print("Loaded ENV")

pygame.init()

WIDTH=1200
HEIGHT=700  # was 600

screen=pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Sentinel SIM")

# sky=(135, 206, 235)
# # skyN=(0, 0, 0)
# skyN=(10, 15, 41)
c1=(135, 206, 235)
c2=(10, 15, 41)

b_1=(169, 169, 169)
b_2=(105, 105, 105)

road=(50, 50, 50)

brown=(101, 67, 33)

pipeLine=(192, 192, 192)
pipe=(30, 30, 30)
water=(0, 119, 190)

dash=(128, 128, 128)

# settings panel colors
setBg = (55, 55, 60)
btnUp = (70, 165, 70)
btnDn = (175, 70, 70)
btnRun = (45, 130, 210)
btnP = (200, 140, 40)
# btnHov = (60, 150, 230)

px = 0
py = 530  # shifted down cuz extra height
pw = 800
ph = 100

# ft = pygame.font.SysFont('Arial', 32, bold=True)
ft=pygame.font.SysFont('couriernew',32, bold=True)
ftext = pygame.font.SysFont('Arial', 24)
fsmall = pygame.font.SysFont('Arial', 18)
ftiny = pygame.font.SysFont('Arial', 14)


# def GetWL():
#     return 65

def dayCyle(screen,t):
    r = c1[0] + (c2[0] - c1[0]) * t
    g = c1[1] + (c2[1] - c1[1]) * t
    b = c1[2] + (c2[2] - c1[2]) * t
    screen.fill((r,g,b))


def drawBG(screen):
    pygame.draw.rect(screen, b_1, (50, 150, 100, 250))
    pygame.draw.rect(screen, b_2, (180, 100, 120, 300))
    # pygame.draw.rect(screen, b_1, (0, 100, 150, 200))

    pygame.draw.rect(screen, b_1, (320, 200, 90, 200))

    pygame.draw.rect(screen, b_2, (450, 80, 150, 320))
    pygame.draw.rect(screen, b_1, (650, 180, 100, 220))

    pygame.draw.rect(screen, road, (0, 400, WIDTH, 100))
    pygame.draw.rect(screen, brown, (0, 500, WIDTH, 200))

    pygame.draw.rect(screen, pipe, (0, py, pw, ph))



# calculate factor outputs directly - no fancy sim
def getModifiedValues():
    info = ENV.getInfo()

    base_wl = float(info['level_cm'])

    # blockage factor - just scale it up
    # wl = base_wl * (1 + blk/10) # overflows too quick
    # wl = base_wl + blk * 1.2
    mod_wl = base_wl * (1.0 + (blk / 100.0) * 2.2) + (blk * 0.4)

    # pop mul
    mod_wl = mod_wl * pop

    # rain boost
    mod_rain = float(info['rain_mm'])
    if rn > 0:
        mod_rain = mod_rain + rn
        mod_wl = mod_wl + rn * 0.5

    # clamp
    mod_wl = max(0.0, min(100.0, mod_wl))

    cur_hr = int((info['hour'] + hr_add) % 24)
    cur_seas = seasons[s_idx] if s_idx != 0 else info['season']

    return mod_wl, cur_hr, cur_seas, mod_rain, info


def drawDash(screen):
    pygame.draw.rect(screen, dash, (825, 0, 400, 310))

    ts = ft.render("Environment Data", True, (0,0,0))
    screen.blit(ts, (850, 20))

    wl, cur_hr, cur_seas, cur_rain, info = getModifiedValues()

    stats = [
        f"Time : {cur_hr}:00",
        f"Water Lvl: {wl:.2f} cm",
        f"Temp: {info['temp_c']:.2f} C",
        f"Season: {cur_seas}",
        f"Weather: {info['weather_state']}",
        f"Rain: {cur_rain:.2f} mm",
        f"Demand: {info['demand_index'] * pop:.2f}",
        f"Blockage: {blk}%",
    ]

    y = 65
    for stat_text in stats:
        text_surface = ftext.render(stat_text, True, (255,255,255))
        screen.blit(text_surface, (850, y))
        y += 28

    return wl, cur_hr



bRects = []
pRect = None
rstRect = None

def drawSettings(screen):
    global bRects, pRect, rstRect
    bRects = []

    panY = 320
    pygame.draw.rect(screen, setBg, (825, panY, 400, HEIGHT - panY))

    # section title
    st = ftext.render("-- Controls --", True, (210, 210, 210))
    screen.blit(st, (880, panY + 8))

    # items to render
    ctrls = [
        ("Blockage", f"{blk}%", "blk"),
        ("Population", f"{pop:.1f}x", "pop"),
        ("Rain", f"+{rn}mm", "rn"),
        ("Season", f"{seasons[s_idx]}", "seas"),
        ("Time(hr)", f"{'+' if hr_add>=0 else ''}{hr_add}h", "hr"),
        ("Speed", f"{sp} fps", "sp"),
    ]

    sy = panY + 38
    for lbl, val_str, tag in ctrls:
        ls = fsmall.render(f"{lbl}:", True, (200, 200, 200))
        screen.blit(ls, (835, sy + 2))

        vs = fsmall.render(val_str, True, (255, 255, 255))
        screen.blit(vs, (975, sy + 2))

        # + button
        uR = pygame.Rect(1070, sy, 26, 22)
        pygame.draw.rect(screen, btnUp, uR)
        ut = ftiny.render("+", True, (255,255,255))
        screen.blit(ut, (uR.x + 8, uR.y + 3))

        # - button
        dR = pygame.Rect(1105, sy, 26, 22)
        pygame.draw.rect(screen, btnDn, dR)
        dt = ftiny.render("-", True, (255,255,255))
        screen.blit(dt, (dR.x + 9, dR.y + 3))

        bRects.append((tag, "up", uR))
        bRects.append((tag, "dn", dR))

        sy += 28


    # buttons at bottom
    ry = sy + 15

    # pause button
    pRect = pygame.Rect(840, ry, 95, 32)
    pColor = (180, 50, 50) if psd else btnP
    pygame.draw.rect(screen, pColor, pRect, border_radius=4)
    pTxt = "Resume" if psd else "Pause"
    pt_surf = fsmall.render(pTxt, True, (255, 255, 255))
    screen.blit(pt_surf, (pRect.x + 18, pRect.y + 6))

    # reset button
    rstRect = pygame.Rect(950, ry, 80, 32)
    pygame.draw.rect(screen, btnRun, rstRect, border_radius=4)
    rt = fsmall.render("Reset", True, (255, 255, 255))
    screen.blit(rt, (rstRect.x + 18, rstRect.y + 6))

    # progress
    ptxt = f"Step {ENV.i}/{ENV.maxI}"
    ps = ftiny.render(ptxt, True, (160, 160, 160))
    screen.blit(ps, (1045, ry + 10))



def doClick(mx, my):
    global blk, pop, rn, s_idx, hr_add, sp, psd

    for tag, dr, rect in bRects:
        if rect.collidepoint(mx, my):
            if tag == "blk":
                blk = min(100, blk + blk_step) if dr == "up" else max(0, blk - blk_step)
            elif tag == "pop":
                pop = round(min(5.0, pop + pop_step), 1) if dr == "up" else round(max(0.2, pop - pop_step), 1)
            elif tag == "rn":
                rn = min(100, rn + rn_step) if dr == "up" else max(0, rn - rn_step)
            elif tag == "seas":
                s_idx = (s_idx + 1) % len(seasons) if dr == "up" else (s_idx - 1) % len(seasons)
            elif tag == "hr":
                hr_add = (hr_add + 1) % 24 if dr == "up" else (hr_add - 1) % 24
            elif tag == "sp":
                sp = min(60, sp + sp_step) if dr == "up" else max(1, sp - sp_step)
            return

    # pause toggle
    if pRect and pRect.collidepoint(mx, my):
        psd = not psd
        return

    # reset
    if rstRect and rstRect.collidepoint(mx, my):
        blk = 0
        pop = 1.0
        rn = 0
        s_idx = 0
        hr_add = 0
        sp = 5
        psd = False
        ENV.reset()
        print("Reset values")
        return



def drawW(screen, wl):
    wh = (ph * wl) / 100
    y = py + ph - wh
    pygame.draw.rect(screen, water, (px, y, pw, wh))

    pygame.draw.rect(screen, pipeLine, (px, py, pw, ph), 5)



# def draw(t):
#     wl = GetWL()
#     wl = max(0, min(100, wl))
#     dayCyle(screen,t)
#     drawBG(screen)
#     drawDash(screen,t)
#
#     water_pixel_height = (ph * wl) / 100
#     water_y = py + ph - water_pixel_height
#     pygame.draw.rect(screen, water, (px, water_y, pw, water_pixel_height))
#     pygame.draw.rect(screen, pipeLine, (px, py, pw, ph), 5)


clock = pygame.time.Clock()
r = True

t=0
while r:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            r = False
        if event.type == pygame.MOUSEBUTTONDOWN:
            if event.button == 1:
                doClick(event.pos[0], event.pos[1])
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_SPACE:
                psd = not psd  # quick pause shortcut

    dayCyle(screen,t)
    drawBG(screen)

    wl, cur_hr = drawDash(screen)

    t = (cur_hr - 1) / 23.0
    t = max(0.0, min(1.0, t))

    drawW(screen, wl)
    drawSettings(screen)

    if not psd:
        ENV.next()

    pygame.display.flip()
    clock.tick(sp)

pygame.quit()
shutil.rmtree("./tmp", ignore_errors=True)
sys.exit()
