# -*- coding: utf-8 -*-
"""
重新生成 app.ico（蓝色水滴，透明背景，多尺寸）。
用法：python tools/make_icon.py
"""
import math
import os

from PIL import Image, ImageDraw

OUT = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                   "app.ico")
S = 256
CX, CY, R = 128.0, 162.0, 86.0     # 圆心与半径
APEX = (128.0, 22.0)               # 水滴尖

d = math.hypot(APEX[0] - CX, APEX[1] - CY)                   # 尖到圆心距离
half = math.degrees(math.acos(R / d))                        # 切点张角
base = math.degrees(math.atan2(APEX[1] - CY, APEX[0] - CX))  # 尖在圆心方向

pts = [APEX]
a = base + half
while a <= base + 360 - half:
    rad = math.radians(a)
    pts.append((CX + R * math.cos(rad), CY + R * math.sin(rad)))
    a += 3.0

img = Image.new("RGBA", (S, S), (0, 0, 0, 0))
dr = ImageDraw.Draw(img)
dr.polygon(pts, fill=(76, 154, 255, 255))
dr.ellipse([88, 150, 122, 200], fill=(150, 199, 255, 210))   # 高光
dr.ellipse([96, 162, 116, 194], fill=(200, 228, 255, 255))

img.save(OUT, format="ICO",
         sizes=[(16, 16), (24, 24), (32, 32), (48, 48),
                (64, 64), (128, 128), (256, 256)])
print("已生成:", OUT, os.path.getsize(OUT), "bytes")
