Astronomical Calendar Clock (Python + Matplotlib)
Overview

This project implements an interactive astronomical calendar clock using Python and Matplotlib.
The visualization integrates multiple time systems and astronomical information into a single circular interface, including:

Real-time analog clock

Gregorian calendar

Chinese lunar calendar

24 solar terms

Zodiac signs

Moon phases

Tide simulation

Sunrise and sunset visualization

Week numbers

Interactive date exploration

The application runs as a desktop graphical visualization and updates in real time using Matplotlib animation.

Main Features
1. Real-Time Analog Clock

The center of the visualization contains a traditional analog clock.

Features:

Hour, minute, and second hands

Smooth second hand movement

Second hand trail visualization

Second number label at the tip of the hand

Implementation highlights:

Time obtained from datetime.now() with timezone support.

Angles calculated as:

second_angle = 90 - seconds * 6
minute_angle = 90 - minutes * 6
hour_angle   = 90 - hours * 30

The clock updates using:

matplotlib.animation.FuncAnimation
2. Timezone Selection

A radio button panel allows users to switch time zones dynamically.

Example supported zones:

Tokyo

Beijing

London

New York

Sydney

Honolulu

Implementation:

RadioButtons(ax_tz, list(tz_data.keys()))

Each entry maps to:

(TimezoneName, Latitude, Longitude)

The latitude and longitude are used for sunrise/sunset calculations.

3. Seasonal Gradient Ring

The outer ring visualizes the four seasons.

Season ranges:

Season	Start	End
Spring	Feb 4	May 6
Summer	May 6	Aug 8
Autumn	Aug 8	Nov 7
Winter	Nov 7	Feb 4

A color gradient is generated using multiple wedges:

draw_gradient_season()

Example gradient:

Spring  : blue → green
Summer  : green → red
Autumn  : red → yellow
Winter  : yellow → blue
4. 24 Solar Terms

The program plots 24 Chinese solar terms (节气) around the seasonal ring.

Examples:

立春 (Beginning of Spring)

春分 (Spring Equinox)

夏至 (Summer Solstice)

冬至 (Winter Solstice)

Each solar term includes:

Marker dot

Rotated label

Gregorian date

5. Gregorian Calendar Ring

A circular scale shows all days of the current year.

Features:

Daily tick marks

First day of month marked with longer ticks

Past days shown in red

Future days shown in green

Angle calculation:

angle = 60 - day_index * 360 / total_days

Where:

total_days = 365 or 366
6. Lunar Calendar Ring

A second ring visualizes the Chinese lunar calendar.

Information shown:

Lunar day progression

Lunar month start markers

Lunar holidays

Example lunar festivals:

Chinese New Year

Lantern Festival

Dragon Boat Festival

Mid-Autumn Festival

Conversion is handled using:

lunardate.LunarDate
7. Interactive Date Explorer

Users can drag circular handles to inspect calendar dates.

Two draggable rings exist:

Gregorian ring

Displays:

YYYY-MM-DD
Holiday name
Lunar ring

Displays:

Lunar year / month / day
Lunar holiday

Interaction events:

button_press_event
motion_notify_event
button_release_event
8. Moon Phase Simulation

The program calculates realistic moon phases.

Reference new moon:

2000-01-06 18:14 UTC

Moon phase is computed using the synodic month:

29.53058867 days

Rendering technique:

The moon is built from three layered patches:

Bright base circle

Dark half-circle mask

Elliptical terminator (sunlight boundary)

This produces accurate waxing and waning phases.

9. Tide Simulation

A simplified tidal model is drawn based on the moon's position.

Features:

Tide envelope deformation

24-hour tidal markers

Rising and falling indicators

Animated tide curve

Tide amplitude depends on:

cos(4π * moon_phase)

This simulates spring and neap tides.

10. Day/Night Visualization

A half-day ring shows progress of the current day.

Sunrise and sunset times are computed using:

astral.sun

The ring color transitions smoothly between:

Night

Sunrise

Day

Sunset

Color brightness uses a sinusoidal solar elevation model.

11. Week Number Ring

Another ring displays ISO week numbers.

Example:

Week 1 → Week 52

The current week is highlighted in yellow.

12. Zodiac Signs

Western zodiac constellations are displayed inside the calendar.

Examples:

Aries

Taurus

Gemini

Cancer

Each sector includes:

Name
Date range
13. Chinese Zodiac

The Chinese zodiac animal for the current year is highlighted.

Cycle:

Rat
Ox
Tiger
Rabbit
Dragon
Snake
Horse
Goat
Monkey
Rooster
Dog
Pig

The current year animal appears:

Larger

Bold

Colored

14. Center Image

The center supports a circular clipped image.

Example:

world.jpg

This is loaded dynamically using:

resource_path()

which ensures compatibility with PyInstaller packaged builds.

Software Architecture

Main modules used:

numpy
matplotlib
astral
pytz
lunardate
calendar
datetime

Core components:

Component	Purpose
Matplotlib patches	Draw circular rings
Animation loop	Real-time updates
Astral	Sunrise / sunset
LunarDate	Lunar calendar conversion
Event handlers	Interactive dragging
Animation System

The visualization updates using:

FuncAnimation(fig, update, interval=50)

Refresh rate:

20 FPS

The update loop recalculates:

clock hands

moon phase

tide shape

day/night progress

calendar highlights

Running the Program

Install dependencies:

pip install numpy matplotlib astral pytz lunardate

Run the script:

python astronomical_clock.py
Possible Future Improvements

Potential enhancements include:

Planetary position visualization

Real astronomical tide predictions

Weather integration

Interactive zoom layers

GPU accelerated rendering

License

This project is intended for educational and visualization purposes.
