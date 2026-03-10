import numpy as np
#import matplotlib.subplots
import matplotlib.pyplot as plt
from matplotlib.patches import Wedge, Circle, FancyArrowPatch, Ellipse
import matplotlib
from matplotlib.colors import to_rgb
import math
from datetime import datetime, timedelta
from matplotlib import animation
import calendar
from astral import LocationInfo
from astral.sun import sun
import pytz
from lunardate import LunarDate
from matplotlib.widgets import RadioButtons
import os
import sys

# ======================
# 中文字体
# ======================
matplotlib.rcParams['font.sans-serif'] = ['Microsoft YaHei']
matplotlib.rcParams['axes.unicode_minus'] = False

# ======================
# 时区字典映射
# ======================
tz_data = {
    "UTC-11 萨摩亚": ("Pacific/Midway", -14.27, -170.13),
    "UTC-10 夏威夷": ("Pacific/Honolulu", 21.30, -157.85),
    "UTC-9 阿拉斯加": ("America/Anchorage", 61.21, -149.90),
    "UTC-8 洛杉矶": ("America/Los_Angeles", 34.05, -118.24),
    "UTC-7 丹佛": ("America/Denver", 39.73, -104.99),
    "UTC-6 芝加哥": ("America/Chicago", 41.87, -87.62),
    "UTC-5 纽约": ("America/New_York", 40.71, -74.00),
    "UTC-4 加拉加斯": ("America/Caracas", 10.48, -66.90),
    "UTC-3 布宜诺斯": ("America/Argentina/Buenos_Aires", -34.60, -58.38),
    "UTC-2 费尔南多": ("America/Noronha", -3.84, -32.42),
    "UTC-1 亚速尔": ("Atlantic/Azores", 37.74, -25.66),
    "UTC+0 伦敦": ("Europe/London", 51.50, -0.12),
    "UTC+1 巴黎": ("Europe/Paris", 48.85, 2.35),
    "UTC+2 开罗": ("Africa/Cairo", 30.04, 31.23),
    "UTC+3 莫斯科": ("Europe/Moscow", 55.75, 37.61),
    "UTC+4 迪拜": ("Asia/Dubai", 25.20, 55.27),
    "UTC+5 卡拉奇": ("Asia/Karachi", 24.86, 67.00),
    "UTC+6 达卡": ("Asia/Dhaka", 23.81, 90.41),
    "UTC+7 曼谷": ("Asia/Bangkok", 13.75, 100.50),
    "UTC+8 北京": ("Asia/Shanghai", 39.90, 116.40),
    "UTC+9 东京": ("Asia/Tokyo", 35.67, 139.65),
    "UTC+10 悉尼": ("Australia/Sydney", -33.86, 151.20),
    "UTC+11 努美阿": ("Pacific/Noumea", -22.27, 166.45),
    "UTC+12 奥克兰": ("Pacific/Auckland", -36.84, 174.76)
}

TIMEZONE = "Asia/Tokyo"
LAT = 35.6762
LON = 139.6503

# ======================
# 半径常量
# ======================
R_OUTER = 1.45  
R_SEASON = 1.45
SEASON_WIDTH = 0.08
R_TERM_NEW = R_SEASON - SEASON_WIDTH / 2  

R_MONTH = 1.30 - 0.015
R_ANIMAL = 0.90  
R_DAY = 1.12  
R_LUNAR_DAY = R_DAY + 0.1  
R_HOLIDAY_TEXT = R_DAY + 0.04  
R_LUNAR_HOLIDAY_TEXT = R_LUNAR_DAY + 0.04
R_ZODIAC_INNER = 0.85  
R_ZODIAC_TEXT = 0.70  

R_MOON_RING = 0.55
R_TIDE_RING = 0.45

CLOCK_RADIUS = 1.37  

GRADIENT_STEPS = 60
TRAIL_LENGTH = 30        
TRAIL_STEPS = 25         
TRAIL_COLOR = "#FF3030"

R_HALF_DAY1_OUTER = 1.08  
R_HALF_DAY1_INNER = 1.06
R_HALF_DAY2_OUTER = 1.06   
R_HALF_DAY2_INNER = 1.04   
HALF_DAY_WIDTH1 = R_HALF_DAY1_OUTER - R_HALF_DAY1_INNER
HALF_DAY_WIDTH2 = R_HALF_DAY2_OUTER - R_HALF_DAY2_INNER

R_WEEK_OUTER = 1.01  
R_WEEK_INNER = 0.95
WEEK_WIDTH = R_WEEK_OUTER - R_WEEK_INNER

LUNAR_DAY_WIDTH_LONG = 0.03
LUNAR_DAY_WIDTH_SHORT = 0.01

HOLIDAY_DOT_RADIUS = 0.012
HOLIDAY_DOT_COLOR = 'yellow'
HOLIDAY_DOT_ALPHA = 0.8

TERM_DOT_RADIUS = 0.012  
TERM_DOT_COLOR = 'blue'
TERM_DOT_ALPHA = 0.8

TOTAL_STEPS = 600
DAY_WIDTH_LONG = 0.03
DAY_WIDTH_SHORT = 0.01

IMG_RADIUS = R_ZODIAC_INNER - 0.7

def clock_angle(number): return 90 - number * 30
def date_to_angle(month, day): return 90 - (month + day/30) * 30
def normalize_angle(start, end):
    if end > start: end -= 360
    return start, end

def get_lunar_year_days(year):
    days = 0
    for month in range(1, 13):
        try:
            ld = LunarDate(year, month, 1)
            next_month = month + 1 if month < 12 else 1
            next_year = year if month < 12 else year + 1
            next_ld = LunarDate(next_year, next_month, 1)
            delta = (next_ld.toSolarDate() - ld.toSolarDate()).days
            days += delta
        except:
            break
    return days

# ======================
# 初始化画布
# ======================
fig, ax = plt.subplots(figsize=(10, 8))
fig.canvas.manager.set_window_title("天文时钟")
ax.set_aspect('equal')
ax.set_xlim(-1.5, 1.5)
ax.set_ylim(-1.5, 1.5)
ax.axis('off')
plt.margins(0)
fig.subplots_adjust(left=0.2, right=1.0, top=1, bottom=0)

ax_tz = plt.axes([0.02, 0.05, 0.16, 0.9], facecolor='whitesmoke')
ax_tz.set_title("时区选择", fontsize=10, weight='bold')
radio_tz = RadioButtons(ax_tz, list(tz_data.keys()), active=20) 
for label in radio_tz.labels: label.set_fontsize(8)

def tz_changed(label):
    global TIMEZONE, LAT, LON, last_sun_date
    TIMEZONE, LAT, LON = tz_data[label]
    last_sun_date = None 
radio_tz.on_clicked(tz_changed)

now = datetime.now(pytz.timezone(TIMEZONE))
current_year = now.year

# ======================
# 静态图层与渐变
# ======================
ax.add_patch(Circle((0, 0), R_OUTER, fill=False, linewidth=2))
flash_dot_radius = 0.01
# 【优化】提升闪烁点的 zorder 并保证其始终可见
flash_dot = Circle((0,0), flash_dot_radius, facecolor='red', edgecolor='white', linewidth=0.5, zorder=15)
ax.add_patch(flash_dot)

def draw_gradient_season(start_angle, end_angle, c1, c2):
    start_angle, end_angle = normalize_angle(start_angle, end_angle)
    angles = np.linspace(start_angle, end_angle, GRADIENT_STEPS)
    rgb1, rgb2 = np.array(to_rgb(c1)), np.array(to_rgb(c2))
    for i in range(len(angles)-1):
        t = i / (len(angles)-1)
        color = rgb1*(1-t) + rgb2*t
        ax.add_patch(Wedge((0, 0), R_SEASON, angles[i+1], angles[i], width=SEASON_WIDTH, facecolor=color, edgecolor='none'))

draw_gradient_season(date_to_angle(2,4), date_to_angle(5,6), "#889FDF", "#00C853")  
draw_gradient_season(date_to_angle(5,6), date_to_angle(8,8), "#00C853", "#FF3D00")  
draw_gradient_season(date_to_angle(8,8), date_to_angle(11,7), "#FF1E00", "#FFD04D") 
draw_gradient_season(date_to_angle(11,7), date_to_angle(2,4), "#FFD04D", "#889FDF") 

season_names, season_dates = ["春", "夏", "秋", "冬"], [(2,4), (5,6), (8,8), (11,7)]
for i in range(4):
    sm, sd = season_dates[i]
    em, ed = season_dates[(i+1)%4]
    start, end = normalize_angle(date_to_angle(sm, sd), date_to_angle(em, ed))
    rad = np.deg2rad((start + end) / 2)
    ax.text((R_SEASON - 0.14) * np.cos(rad), (R_SEASON - 0.14) * np.sin(rad), season_names[i], color="#5B5B5F", fontsize=12, weight='bold', ha='center', va='center')

for m in range(1, 13):
    rad = np.deg2rad(clock_angle(m))
    ax.text(R_MONTH*np.cos(rad), R_MONTH*np.sin(rad), f"{m}", ha='center', va='center', fontsize=14)

solar_terms = [
    ("小寒",1,5),("大寒",1,20), ("立春",2,4),("雨水",2,19),
    ("惊蛰",3,6),("春分",3,21), ("清明",4,5),("谷雨",4,20),
    ("立夏",5,6),("小满",5,21), ("芒种",6,6),("夏至",6,21),
    ("小暑",7,7),("大暑",7,23), ("立秋",8,8),("处暑",8,23),
    ("白露",9,8),("秋分",9,23), ("寒露",10,8),("霜降",10,23),
    ("立冬",11,7),("小雪",11,22), ("大雪",12,7),("冬至",12,22),
]
for name, month, day in solar_terms:
    angle = date_to_angle(month, day)
    rad = np.deg2rad(angle)
    ax.text((R_TERM_NEW+0.015)*np.cos(rad), (R_TERM_NEW+0.015)*np.sin(rad), f"{name}{month}/{day}", ha='center', va='center', fontsize=8, rotation=angle + 90, rotation_mode='anchor', color='black')
    ax.add_patch(Circle(((R_TERM_NEW-0.03) * np.cos(rad), (R_TERM_NEW-0.03) * np.sin(rad)), TERM_DOT_RADIUS, facecolor=TERM_DOT_COLOR, alpha=TERM_DOT_ALPHA, zorder=5))

animals1 = ["鼠","牛","虎","兔","龙","蛇","马","羊","猴","鸡","狗","猪"]
animal_texts = []
for i in range(12):
    rad = np.deg2rad(clock_angle(i+1))
    txt = ax.text(R_ANIMAL*np.cos(rad), R_ANIMAL*np.sin(rad), f"{animals1[i]}", ha='center', va='center', fontsize=10)
    animal_texts.append(txt)

# ======================
# 农历与阳历刻度生成
# ======================
fixed_holidays = [
    ("元旦", 1, 1), ("情人节", 2, 14), ("妇女节", 3, 8), ("愚人节", 4, 1),
    ("劳动节", 5, 1), ("青年节", 5, 4), ("儿童节", 6, 1), ("建军节", 8, 1),
    ("国庆节", 10, 1), ("万圣节", 10, 31), ("圣诞节", 12, 25),
]
lunar_holidays = [("春节", 1, 1), ("元宵节", 1, 15), ("清明节", 4, 5), ("端午节", 5, 5), ("中秋节", 8, 15)]

is_leap = calendar.isleap(current_year)
total_days = 366 if is_leap else 365

day_angles = []
for m in range(1, 13):
    dim = calendar.monthrange(current_year, m)[1]
    for d in range(1, dim + 1): day_angles.append((m, d))

for day_index, (month, day) in enumerate(day_angles, start=1):
    angle = 60 - day_index * 360 / total_days
    rad = math.radians(angle)
    length, width = (DAY_WIDTH_LONG, 2) if day == 1 else (DAY_WIDTH_SHORT, 1)
    color = 'red' if day_index < now.timetuple().tm_yday else 'green' # modify
    ax.plot([(R_DAY - length) * math.cos(rad), R_DAY * math.cos(rad)], [(R_DAY - length) * math.sin(rad), R_DAY * math.sin(rad)], linewidth=width, color=color)

for name, month, day in fixed_holidays:
    day_index = sum(calendar.monthrange(current_year, m)[1] for m in range(1, month)) + day
    rad = math.radians(60 - day_index * 360 / total_days)
    ax.add_patch(Circle((R_DAY * math.cos(rad), R_DAY * math.sin(rad)), HOLIDAY_DOT_RADIUS, facecolor=HOLIDAY_DOT_COLOR, alpha=HOLIDAY_DOT_ALPHA, zorder=5))
    ax.text(R_HOLIDAY_TEXT * math.cos(rad), R_HOLIDAY_TEXT * math.sin(rad), f"{name}{month}/{day}", fontsize=8, ha='center', va='center', color='red', rotation=60 - day_index * 360 / total_days + 90, rotation_mode='anchor')

lunar_today = LunarDate.fromSolarDate(current_year, now.month, now.day)
lunar_year = lunar_today.year
lunar_total_days = get_lunar_year_days(lunar_year)
lunar_day_index = sum((LunarDate(lunar_year, m+1 if m<12 else 1, 1).toSolarDate() - LunarDate(lunar_year, m, 1).toSolarDate()).days for m in range(1, lunar_today.month)) + lunar_today.day

for i in range(1, lunar_total_days + 1):
    angle = 60 - i * 360 / lunar_total_days
    rad = math.radians(angle)
    solar_date = LunarDate(lunar_year, 1, 1).toSolarDate() + timedelta(days=i - 1)
    is_month_start = LunarDate.fromSolarDate(solar_date.year, solar_date.month, solar_date.day).day == 1
    length, width = (LUNAR_DAY_WIDTH_LONG, 2) if is_month_start else (LUNAR_DAY_WIDTH_SHORT, 1)
    color = 'red' if i <= lunar_day_index-1 else 'green' # modify
    ax.plot([(R_LUNAR_DAY - length) * math.cos(rad), R_LUNAR_DAY * math.cos(rad)], [(R_LUNAR_DAY - length) * math.sin(rad), R_LUNAR_DAY * math.sin(rad)], linewidth=width, color=color)

for name, lm, ld in lunar_holidays:
    day_idx = 0
    valid = True
    for m in range(1, lm):
        try:
            ld_start = LunarDate(lunar_year, m, 1)
            next_m, next_y = (m + 1, lunar_year) if m < 12 else (1, lunar_year + 1)
            next_ld = LunarDate(next_y, next_m, 1)
            day_idx += (next_ld.toSolarDate() - ld_start.toSolarDate()).days
        except:
            valid = False
            break
    if not valid: continue
    day_idx += ld
    angle = 60 - day_idx * 360 / lunar_total_days
    rad = math.radians(angle)
    ax.add_patch(Circle((R_LUNAR_DAY * math.cos(rad), R_LUNAR_DAY * math.sin(rad)), HOLIDAY_DOT_RADIUS, facecolor=HOLIDAY_DOT_COLOR, alpha=HOLIDAY_DOT_ALPHA, zorder=5))
    ax.text(R_LUNAR_HOLIDAY_TEXT * math.cos(rad), R_LUNAR_HOLIDAY_TEXT * math.sin(rad), f"{name}{lm}/{ld}", fontsize=8, ha='center', va='center', color='purple', rotation=angle + 90, rotation_mode='anchor')

# 半日环等
halfday1_patches, halfday2_patches = [], []
for i in range(TOTAL_STEPS):
    angle_start = 90 - i * 360 / TOTAL_STEPS
    angle_end = 90 - (i + 1) * 360 / TOTAL_STEPS
    w1 = ax.add_patch(Wedge((0, 0), R_HALF_DAY1_OUTER, angle_end, angle_start, width=HALF_DAY_WIDTH1, facecolor="#C8CCD6", edgecolor='none', zorder=0))
    w2 = ax.add_patch(Wedge((0, 0), R_HALF_DAY2_OUTER, angle_end, angle_start, width=HALF_DAY_WIDTH2, facecolor='#C8CCD6', edgecolor='none', zorder=0))
    halfday1_patches.append(w1); halfday2_patches.append(w2)

week_patches = []
last_week = datetime(current_year, 12, 28).isocalendar()[1]
for w in range(1, last_week + 1):
    angle_start = 60 - (w - 1) * 360 / last_week
    angle_end = 60 - w * 360 / last_week
    wedge = ax.add_patch(Wedge((0, 0), R_WEEK_OUTER, angle_end, angle_start, width=WEEK_WIDTH, facecolor="#E6E6E6", edgecolor="white", linewidth=0.5, zorder=0.5))
    week_patches.append(wedge)
    rad = math.radians((angle_start + angle_end) / 2)
    ax.text((R_WEEK_INNER + WEEK_WIDTH / 2) * math.cos(rad), (R_WEEK_INNER + WEEK_WIDTH / 2) * math.sin(rad), f"{w}", fontsize=6, ha='center', va='center')

zodiacs = [
    ("摩羯座",12,22,1,19), ("水瓶座",1,20,2,18), ("双鱼座",2,19,3,20),
    ("白羊座",3,21,4,19), ("金牛座",4,20,5,20), ("双子座",5,21,6,21),
    ("巨蟹座",6,22,7,22), ("狮子座",7,23,8,22), ("处女座",8,23,9,22),
    ("天秤座",9,23,10,23), ("天蝎座",10,24,11,22), ("射手座",11,23,12,21),
]
for name, sm, sd, em, ed in zodiacs:
    start, end = normalize_angle(date_to_angle(sm, sd), date_to_angle(em, ed))
    ax.add_patch(Wedge((0, 0), R_ZODIAC_INNER, end, start, width=0.25, alpha=0.25))
    rad = np.deg2rad((start + end)/2)
    ax.text(R_ZODIAC_TEXT * np.cos(rad), R_ZODIAC_TEXT * np.sin(rad), f"{name}\n{sm}/{sd}-{em}/{ed}", ha='center', va='center', fontsize=8)

# 中心图片保护判断
def resource_path(relative_path):
    if hasattr(sys, '_MEIPASS'): return os.path.join(sys._MEIPASS, relative_path)
    return os.path.join(os.path.abspath("."), relative_path)

try:
    img = plt.imread(resource_path("world.jpg"))
    im = ax.imshow(img, extent=[-IMG_RADIUS, IMG_RADIUS, -IMG_RADIUS, IMG_RADIUS], zorder=0)
    im.set_clip_path(Circle((0, 0), IMG_RADIUS, transform=ax.transData))
except FileNotFoundError:
    pass

# ======================
# 月相与潮汐环增强
# ======================
ax.add_patch(Circle((0, 0), R_MOON_RING, fill=False, color='#A0A0A0', linestyle='--', linewidth=1, zorder=2))
ax.add_patch(Circle((0, 0), R_TIDE_RING, fill=False, color='#C0D8F0', linewidth=1, zorder=2))
ax.text(0, R_MOON_RING - 0.03, "新月", ha='center', va='bottom', fontsize=8, color='#555555')
ax.text(R_MOON_RING - 0.04, 0, "上弦", ha='left', va='center', fontsize=8, color='#555555')
ax.text(0, -(R_MOON_RING - 0.03), "满月", ha='center', va='top', fontsize=8, color='#555555')
ax.text(-(R_MOON_RING - 0.04), 0, "下弦", ha='right', va='center', fontsize=8, color='#555555')

for i in range(24):
    angle = i * 15 * math.pi / 180
    ax.text((R_TIDE_RING - 0.04) * math.cos(angle), (R_TIDE_RING - 0.04) * math.sin(angle), str(i), fontsize=7, color="#555555", ha='center', va='center', alpha=0.8)

tide_time_dot = Circle((0,0), 0.015, facecolor='red', edgecolor='white', linewidth=0.5, zorder=6)
ax.add_patch(tide_time_dot)

r_moon = 0.042

# 【优化】使用复合Patch（圆底 + 半圆遮罩 + 椭圆晨昏线）完美模拟月相
moon_color_bright = "#F5D76E" # 月亮亮部颜色
moon_color_dark = "#1A1A24"   # 月亮暗部颜色

moon_base = Circle((0, 0), r_moon, facecolor=moon_color_bright, edgecolor="#A0A0A0", linewidth=0.5, zorder=3)
moon_dark_half = Wedge((0, 0), r_moon, 0, 180, facecolor=moon_color_dark, edgecolor="none", zorder=4)
moon_terminator = Ellipse((0, 0), 2*r_moon, 2*r_moon, facecolor=moon_color_dark, edgecolor="none", zorder=5)

ax.add_patch(moon_base)
ax.add_patch(moon_dark_half)
ax.add_patch(moon_terminator)

tide_angles = np.linspace(0, 2*math.pi, 200)
tide_path, = ax.plot([], [], color='#007AFF', linewidth=1.5, alpha=0.7, zorder=3)

tide_tick_patches = []
for _ in range(24):
    tick, = ax.plot([], [], linewidth=1.5, zorder=4)
    tide_tick_patches.append(tick)

# ======================
# 交互拉环系统 
# ======================
info_text = ax.text(1.4, 1.4, "拖动圆环查看日期节假日", fontsize=10, ha='right', va='top', 
                    bbox=dict(facecolor='whitesmoke', alpha=0.9, edgecolor='#C8CCD6', boxstyle='round,pad=0.5'), zorder=15)

greg_init_angle = math.radians(60 - (now.timetuple().tm_yday) * 360 / total_days)
greg_ring = Circle((R_DAY * math.cos(greg_init_angle), R_DAY * math.sin(greg_init_angle)), 0.025, fill=False, edgecolor='#007AFF', linewidth=2, zorder=10)
greg_dot = Circle((greg_ring.center), 0.005, facecolor='#007AFF', zorder=10)

lunar_init_angle = math.radians(60 - lunar_day_index * 360 / lunar_total_days)
lunar_ring = Circle((R_LUNAR_DAY * math.cos(lunar_init_angle), R_LUNAR_DAY * math.sin(lunar_init_angle)), 0.025, fill=False, edgecolor='purple', linewidth=2, zorder=10)
lunar_dot = Circle((lunar_ring.center), 0.005, facecolor='purple', zorder=10)

ax.add_patch(greg_ring); ax.add_patch(greg_dot)
ax.add_patch(lunar_ring); ax.add_patch(lunar_dot)

drag_state = {'active': None}

def on_press(event):
    if event.inaxes != ax: return
    x, y = event.xdata, event.ydata
    if math.hypot(x - greg_ring.center[0], y - greg_ring.center[1]) < 0.05:
        drag_state['active'] = 'greg'
    elif math.hypot(x - lunar_ring.center[0], y - lunar_ring.center[1]) < 0.05:
        drag_state['active'] = 'lunar'

def on_motion(event):
    if drag_state['active'] is None or event.inaxes != ax: return
    x, y = event.xdata, event.ydata
    angle = math.atan2(y, x)
    if drag_state['active'] == 'greg':
        greg_ring.center = (R_DAY * math.cos(angle), R_DAY * math.sin(angle))
        greg_dot.center = greg_ring.center
    elif drag_state['active'] == 'lunar':
        lunar_ring.center = (R_LUNAR_DAY * math.cos(angle), R_LUNAR_DAY * math.sin(angle))
        lunar_dot.center = lunar_ring.center
    fig.canvas.draw_idle()

def on_release(event):
    if drag_state['active'] is None: return
    x, y = event.xdata, event.ydata
    if x is None or y is None:
        drag_state['active'] = None; return
    
    angle = math.atan2(y, x)
    deg = math.degrees(angle)
    
    if drag_state['active'] == 'greg':
        day_exact = (60 - deg) / 360 * total_days
        day_idx = int(round(day_exact)) % total_days
        if day_idx == 0: day_idx = total_days
        snap_angle = math.radians(60 - day_idx * 360 / total_days)
        greg_ring.center = (R_DAY * math.cos(snap_angle), R_DAY * math.sin(snap_angle))
        greg_dot.center = greg_ring.center
        
        m, d = day_angles[day_idx - 1]
        hol = "无"
        for hn, hm, hd in fixed_holidays:
            if hm == m and hd == d: hol = hn; break
        info_text.set_text(f"【公历】{current_year}年{m}月{d}日\n节日: {hol}")

    elif drag_state['active'] == 'lunar':
        day_exact = (60 - deg) / 360 * lunar_total_days
        l_idx = int(round(day_exact)) % lunar_total_days
        if l_idx == 0: l_idx = lunar_total_days
        snap_angle = math.radians(60 - l_idx * 360 / lunar_total_days)
        lunar_ring.center = (R_LUNAR_DAY * math.cos(snap_angle), R_LUNAR_DAY * math.sin(snap_angle))
        lunar_dot.center = lunar_ring.center
        
        s_date = LunarDate(lunar_year, 1, 1).toSolarDate() + timedelta(days=l_idx - 1)
        l_date = LunarDate.fromSolarDate(s_date.year, s_date.month, s_date.day)
        hol = "无"
        for hn, hm, hd in lunar_holidays:
            if hm == l_date.month and hd == l_date.day: hol = hn; break
        info_text.set_text(f"【农历】{l_date.year}年{l_date.month}月{l_date.day}日\n节日: {hol}")

    drag_state['active'] = None
    fig.canvas.draw_idle()

fig.canvas.mpl_connect('button_press_event', on_press)
fig.canvas.mpl_connect('motion_notify_event', on_motion)
fig.canvas.mpl_connect('button_release_event', on_release)

# ======================
# 时钟核心
# ======================
ax.add_patch(Circle((0, 0), CLOCK_RADIUS, fill=False, linewidth=2))
for i in range(60):
    angle = math.radians(i * 6)
    length, width = (0.05, 2) if i % 5 == 0 else (0.03, 1)
    ax.plot([(CLOCK_RADIUS - length) * math.cos(angle), CLOCK_RADIUS * math.cos(angle)], 
            [(CLOCK_RADIUS - length) * math.sin(angle), CLOCK_RADIUS * math.sin(angle)], linewidth=width, color='black')

hour_hand, = ax.plot([], [], linewidth=6, color='#333333')
minute_hand, = ax.plot([], [], linewidth=4, color='#333333')
second_hand, = ax.plot([], [], color='red', linewidth=1.5)
ax.plot(0, 0, 'ko', markersize=6)

trail_patches = []
second_label = ax.text(0, 0, "", fontsize=10, color='red', weight='bold', ha='center', va='center')
day_arrow = FancyArrowPatch((0,0), (0,0), arrowstyle='-|>', mutation_scale=15, color="blue", linewidth=1); ax.add_patch(day_arrow)
day_label = ax.text(0, 0, "", fontsize=8, color="blue", ha='center', va='center')
day_holiday_label = ax.text(0, 0, "", fontsize=8, color="blue", ha='center', va='center')

lunar_arrow = FancyArrowPatch((0,0), (0,0), arrowstyle='-|>', mutation_scale=15, color="purple", linewidth=1); ax.add_patch(lunar_arrow)
lunar_label = ax.text(0, 0, "", fontsize=8, color="purple", ha='center', va='center')
lunar_holiday_label = ax.text(0, 0, "", fontsize=8, color="purple", ha='center', va='center') 

halfday_percent_label = ax.text(0, 0, "", fontsize=8, weight='bold', color="#FF0000D2", ha='center', va='center', zorder=6)

sunrise_hour, sunset_hour = None, None
last_sun_date = None
weekdays = ["日", "一", "二", "三", "四", "五", "六"]

def get_sun_times(now):
    global sunrise_hour, sunset_hour, last_sun_date
    current_date = now.date()
    if last_sun_date != current_date:
        city = LocationInfo(latitude=LAT, longitude=LON, timezone=TIMEZONE)
        s = sun(city.observer, date=current_date, tzinfo=pytz.timezone(TIMEZONE))
        sunrise_hour = s["sunrise"].hour + s["sunrise"].minute / 60
        sunset_hour = s["sunset"].hour + s["sunset"].minute / 60
        last_sun_date = current_date
    return sunrise_hour, sunset_hour

def smooth_day_night_color(hour, sunrise_hour, sunset_hour):
    if sunrise_hour <= hour <= sunset_hour:
        t = (hour - sunrise_hour) / (sunset_hour - sunrise_hour)
        solar = math.sin(math.pi * t)
    else:
        t = (hour + 24 - sunset_hour) / (24 - sunset_hour + sunrise_hour) if hour < sunrise_hour else (hour - sunset_hour) / (24 - sunset_hour + sunrise_hour)
        solar = -math.sin(math.pi * t)
    brightness = ((solar + 1) / 2) ** 1.3
    return (0.20 + 0.80 * brightness, 0.10 + 0.45 * brightness, 0.05 + 0.20 * brightness)

def update(frame):
    now = datetime.now(pytz.timezone(TIMEZONE)) 
    current_year, month, day = now.year, now.month, now.day
    current_hour, current_minute, current_second = now.hour, now.minute, now.second
    sec = current_second + now.microsecond / 1_000_000
    minute = current_minute + sec / 60
    hour = (current_hour % 12) + minute / 60

    current_week = now.isocalendar()[1]
    for i, wedge in enumerate(week_patches, start=1):
        wedge.set_facecolor("yellow" if i == current_week else "#E6E6E6")

    current_animal_index = (current_year - 2020) % 12
    for i, txt in enumerate(animal_texts):
        txt.set_fontsize(14) if i == current_animal_index else txt.set_fontsize(10)
        txt.set_weight('bold') if i == current_animal_index else txt.set_weight('normal')
        txt.set_color("#0026FFD4") if i == current_animal_index else txt.set_color('black')

    sunrise_hour, sunset_hour = get_sun_times(now)
    total_minutes = current_minute + current_second / 60
    passed_minutes1 = current_hour * 60 + total_minutes if current_hour < 12 else 12 * 60
    passed_minutes2 = (current_hour - 12) * 60 + total_minutes if current_hour >= 12 else 0
    passed_steps1, passed_steps2 = int(passed_minutes1 / 720 * TOTAL_STEPS), int(passed_minutes2 / 720 * TOTAL_STEPS)
    for i in range(TOTAL_STEPS):
        halfday1_patches[i].set_facecolor("#F0F0F0CC" if i < passed_steps1 else smooth_day_night_color(i * 12 / TOTAL_STEPS, sunrise_hour, sunset_hour))
        halfday2_patches[i].set_facecolor("#F0F0F0CC" if i < passed_steps2 else smooth_day_night_color(12 + i * 12 / TOTAL_STEPS, sunrise_hour, sunset_hour))

    percent = (now.hour * 3600 + now.minute * 60 + now.second + now.microsecond / 1_000_000) / 86400
    boundary_angle_rad = math.radians(90 - percent * 720)
    R_DOT = (R_HALF_DAY1_OUTER + R_HALF_DAY1_INNER) / 2 if current_hour < 12 else (R_HALF_DAY2_OUTER + R_HALF_DAY2_INNER) / 2
    halfday_percent_label.set_position((R_DOT * math.cos(boundary_angle_rad + 0.05), R_DOT * math.sin(boundary_angle_rad + 0.05)))
    halfday_percent_label.set_text(f"{percent * 100:.1f}%")
    
    # 红点更新保留原样
    flash_dot.center = (R_DOT * math.cos(boundary_angle_rad), R_DOT * math.sin(boundary_angle_rad))
    flash_dot.set_alpha(0.5 + 0.5 * math.sin(2 * math.pi * sec / 0.8))

    sec_angle, min_angle, hour_angle = math.radians(90 - sec * 6), math.radians(90 - minute * 6), math.radians(90 - hour * 30)
    sec_len = 0.9 * CLOCK_RADIUS + 0.02
    second_label.set_position(((sec_len + 0.04) * math.cos(sec_angle), (sec_len + 0.04) * math.sin(sec_angle)))
    second_label.set_text(f"{int(sec):02d}")
    second_hand.set_data([-0.15 * sec_len * math.cos(sec_angle), sec_len * math.cos(sec_angle)], [-0.15 * sec_len * math.sin(sec_angle), sec_len * math.sin(sec_angle)])
    min_len = 0.75 * CLOCK_RADIUS
    minute_hand.set_data([-0.12 * min_len * math.cos(min_angle), min_len * math.cos(min_angle)], [-0.12 * min_len * math.sin(min_angle), min_len * math.sin(min_angle)])
    hour_len = 0.55 * CLOCK_RADIUS
    hour_hand.set_data([-0.10 * hour_len * math.cos(hour_angle), hour_len * math.cos(hour_angle)], [-0.10 * hour_len * math.sin(hour_angle), hour_len * math.sin(hour_angle)])

    for patch in trail_patches: patch.remove()
    trail_patches.clear()
    current_angle_deg = math.degrees(sec_angle)
    for i in range(TRAIL_STEPS):
        wedge = ax.add_patch(Wedge((0, 0), 0.9 * CLOCK_RADIUS + 0.02, current_angle_deg + i * (TRAIL_LENGTH / TRAIL_STEPS), current_angle_deg + (i + 1) * (TRAIL_LENGTH / TRAIL_STEPS), width=0.9 * CLOCK_RADIUS, facecolor=TRAIL_COLOR, alpha=0.4 * (1 - i / TRAIL_STEPS), zorder=1))
        trail_patches.append(wedge)

    # 【优化】精细化逼真月相计算：椭圆模拟晨昏线
    ref_new_moon = datetime(2000, 1, 6, 18, 14, tzinfo=pytz.utc)
    diff = now.astimezone(pytz.utc) - ref_new_moon
    synodic_month = 29.53058867
    moon_phase_percent = ((diff.total_seconds() / 86400) % synodic_month) / synodic_month
    
    moon_angle_rad = math.radians(90 - moon_phase_percent * 360)
    cx, cy = R_MOON_RING * math.cos(moon_angle_rad), R_MOON_RING * math.sin(moon_angle_rad)
    
    # 更新位置
    moon_base.center = (cx, cy)
    moon_dark_half.set_center((cx, cy))
    moon_terminator.set_center((cx, cy))

    # 判断半球暗面的方向
    if moon_phase_percent < 0.5:
        # 上半月(盈月)：左半边是暗的
        moon_dark_half.set_theta1(90)
        moon_dark_half.set_theta2(270)
    else:
        # 下半月(亏月)：右半边是暗的
        moon_dark_half.set_theta1(-90)
        moon_dark_half.set_theta2(90)

    # 计算中间晨昏线椭圆的宽度（利用三维投影的余弦值）
    phase_angle = moon_phase_percent * 2 * math.pi
    moon_terminator.set_width(2 * r_moon * abs(math.cos(phase_angle)))
    moon_terminator.set_height(2 * r_moon)

    # 判断椭圆颜色：凸月阶段为亮色，弦月阶段为暗色
    if 0.25 <= moon_phase_percent <= 0.75:
        moon_terminator.set_facecolor(moon_color_bright)
    else:
        moon_terminator.set_facecolor(moon_color_dark)

    # 潮汐增强逻辑
    tide_time_angle = (current_hour + minute/60) * 15 * math.pi / 180
    tide_time_dot.center = (R_TIDE_RING * math.cos(tide_time_angle), R_TIDE_RING * math.sin(tide_time_angle))
    tide_time_dot.set_alpha(0.5 + 0.5 * math.sin(2 * math.pi * sec / 0.8))

    envelope = 0.04 + 0.03 * math.cos(4 * math.pi * moon_phase_percent)  
    tide_r = R_TIDE_RING + envelope * np.cos(2 * (tide_angles - moon_angle_rad))
    tide_path.set_data(tide_r * np.cos(tide_angles), tide_r * np.sin(tide_angles))

    for i in range(24):
        angle = i * 15 * math.pi / 180
        phase = 2 * (angle - moon_angle_rad)
        local_height = math.cos(phase)
        tick_length = 0.02 + 0.035 * (local_height + 1) / 2  
        slope = -math.sin(phase)
        tick_color = 'red' if slope > 0 else 'green'

        x1, y1 = R_TIDE_RING * math.cos(angle), R_TIDE_RING * math.sin(angle)
        x2, y2 = (R_TIDE_RING + tick_length) * math.cos(angle), (R_TIDE_RING + tick_length) * math.sin(angle)

        tide_tick_patches[i].set_data([x1, x2], [y1, y2])
        tide_tick_patches[i].set_color(tick_color)
        tide_tick_patches[i].set_linewidth(2.5 if local_height > 0.5 else 1.5) 

    # 标签刷新
    day_index = sum(calendar.monthrange(current_year, m)[1] for m in range(1, month)) + day
    angle_rad = math.radians(60 - (day_index + 0) * 360 / total_days) # modify
    x_end, y_end = R_DAY * math.cos(angle_rad), R_DAY * math.sin(angle_rad)
    day_arrow.set_positions((0, 0), (x_end, y_end))
    day_label.set_position((x_end * 0.3, y_end * 0.3 + 0.02))
    day_label.set_text(f"{now.strftime('%Y-%m-%d')} ({weekdays[int(now.strftime('%w'))]}) {day_index}/{total_days}")
    rotation_deg = -math.degrees(angle_rad) - 13
    day_label.set_rotation(rotation_deg)
    
    holiday_name = "平日"
    for h_name, h_m, h_d in fixed_holidays:
        if (h_m, h_d) == (month, day): holiday_name = h_name; break
    day_holiday_label.set_position((x_end * 0.25, y_end * 0.25 - 0.03))
    day_holiday_label.set_text(holiday_name)
    day_holiday_label.set_rotation(rotation_deg)

    lunar_today = LunarDate.fromSolarDate(current_year, month, day)
    lunar_year_now = lunar_today.year
    l_tot_days = get_lunar_year_days(lunar_year_now)
    # l_day_idx = sum((LunarDate(lunar_year_now, m+1 if m<12 else 1, 1).toSolarDate() - LunarDate(lunar_year_now, m, 1).toSolarDate()).days for m in range(1, lunar_today.month)) + lunar_today.day
    lunar_year_start = LunarDate(lunar_today.year, 1, 1).toSolarDate()
    l_day_idx = (now.date() - lunar_year_start).days + 1

    lunar_angle_rad = math.radians(60 - l_day_idx * 360 / l_tot_days)
    x_end_lunar, y_end_lunar = R_LUNAR_DAY * math.cos(lunar_angle_rad), R_LUNAR_DAY * math.sin(lunar_angle_rad)
    lunar_arrow.set_positions((0, 0), (x_end_lunar, y_end_lunar))
    lunar_label.set_position((x_end_lunar * 0.3, y_end_lunar * 0.3 + 0.03))
    lunar_label.set_text(f"农历 {lunar_today.month}月{lunar_today.day}日 ({l_day_idx}/{l_tot_days})")
    rotation_deg_lunar = -math.degrees(lunar_angle_rad) + 80
    lunar_label.set_rotation(rotation_deg_lunar)

    l_holiday_name = "平日"
    for h_name, h_m, h_d in lunar_holidays:
        if h_m == lunar_today.month and h_d == lunar_today.day: l_holiday_name = h_name; break
    lunar_holiday_label.set_position((x_end_lunar * 0.25, y_end_lunar * 0.25 - 0.03)) 
    lunar_holiday_label.set_text(l_holiday_name)
    lunar_holiday_label.set_rotation(rotation_deg_lunar)

    # 【核心修复】将 flash_dot 加入 blit 返回列表，并将原本的2个月相图层替换为新的3个月相图层
    return (hour_hand, minute_hand, second_hand, day_arrow, day_label, day_holiday_label,
            lunar_arrow, lunar_label, lunar_holiday_label, second_label, halfday_percent_label, 
            tide_path, tide_time_dot, info_text, greg_ring, greg_dot, lunar_ring, lunar_dot, 
            flash_dot, # 修复红点不闪烁的问题
            *trail_patches, moon_base, moon_dark_half, moon_terminator, *tide_tick_patches,
            *halfday1_patches, *halfday2_patches)

ani = animation.FuncAnimation(fig, update, interval=50, blit=True)
plt.show()
