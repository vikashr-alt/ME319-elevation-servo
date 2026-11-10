"""Render numbered report equations from LaTeX syntax using Matplotlib mathtext."""
from pathlib import Path
import sys
from matplotlib.mathtext import math_to_image
from matplotlib.font_manager import FontProperties

equations = [
    r"J = J_{\mathrm{load}} + N^2 J_m = 3200\ \mathrm{kg\,m^2}",
    r"J\dot{\omega} + b\omega = NK_t i,\qquad \dot{\theta}=\omega",
    r"L\dot{i}+Ri = V-NK_e\omega",
    r"\frac{\Theta(s)}{V(s)} = \frac{NK_t}{s[(Ls+R)(Js+b)+N^2 K_tK_e]}",
    r"G_p(s) = \frac{1000}{320s^3+3350s^2+1001500s}",
    r"G_c(s)=2400\,\frac{1+s/4}{1+s/8}",
    r"\dot{z}=8(e-z),\quad V=4800e-2400z",
    r"T(s)=\frac{G_cG_p}{1+G_cG_p},\qquad S(s)=\frac{1}{1+G_cG_p}",
    r"\frac{\Delta(s)}{320}=s^4+18.46875s^3+3213.4375s^2",
    r"{}+40037.5s+60000",
    r"r(t)=20^\circ+6^\circ\sin(0.6\pi t)+2^\circ\sin(1.4\pi t)",
    r"\mathrm{RMSE}=\sqrt{\frac{1}{n}\sum_{k=1}^{n}(r_k-\theta_k)^2}",
]

out = Path(sys.argv[1])
out.mkdir(exist_ok=True)
for k, expr in enumerate(equations, 1):
    math_to_image(f"${expr}$", out / f"eq{k}.png",
                  prop=FontProperties(size=10, math_fontfamily="stix"), dpi=400)
