# ME319 elevation servo study

A non-weaponized study of the geared elevation axis specified in ME319 Assignment 2, Autumn 2026. A prescribed bench angle drives a fixed lead compensator. The case results cover 0–10 seconds and were generated in GNU Octave 11.3.0.

## Contents

| Path | Purpose |
|---|---|
| `matlab/servo_plant.m` | Physical parameters, state-space model and voltage-to-angle transfer function |
| `matlab/turret_plant.m` | Assignment-compatible derivative function for the elevation axis |
| `matlab/servo_analysis.m` | Lead compensator, loop poles, crossovers, margins and augmented LTI model |
| `matlab/simulate_servo.m` | Reusable exact held-input simulation for generic angle commands |
| `matlab/run_servo_study.m` | Four bench cases, assertions and reproducible data export |
| `results/` | Trace CSVs, loop frequency data, metrics and independent check output |
| `figures/` | Schematic and plots in PNG and vector PDF formats |
| `make_figures.py`, `verify_results.py` | Figure generation and independent pole-residue verification |
| `report/` | Editable author metadata, report source and equation renderer |
| `VERIFICATION.md` | Test evidence, seven-page requirements review and submission status |

## Reproduce the results

From the extracted package root, in GNU Octave or MATLAB, run:

```matlab
addpath('matlab');
run_servo_study;
```

Or run from a terminal:

```sh
octave --no-gui --quiet --eval "addpath('matlab'); run_servo_study"
matlab -batch "addpath('matlab'); run_servo_study"
```

The numerical code uses core language functions. GNU Octave was verified. The local MATLAB application failed to launch, so execution in MATLAB is pending. The seed is fixed within a runtime. MATLAB and Octave can produce different Gaussian draws for the same seed.

To make the figures, verify the traces independently and rebuild the report, use Python with NumPy, SciPy, Matplotlib, Pillow and ReportLab installed. From the package root:

```sh
python3 make_figures.py
python3 verify_results.py
python3 report/math_labels.py report/equations
python3 report/make_report.py report/equations Elevation_Servo_Study.pdf
```

Each case CSV contains time, ideal and applied commands, simulated angle, ideal-command error, voltage and current. Angle columns are in degrees. The simulation functions use radians. `metrics.txt` contains pole and margin estimates, timing, checks and one row per bench case. The report builder uses these metrics for the simulation values printed in the paper.

## Use your own bench angle command

```matlab
addpath('matlab');
p = servo_plant();
model = servo_analysis(p);
dt = 0.001;
stride = 50;
t_updates = (0:0.05:10)';
r = (20 + 4*sin(2*pi*0.25*t_updates))*pi/180;
r = min(max(r,p.angle_limits(1)),p.angle_limits(2));
[theta, volts, amps, applied] = simulate_servo(model,r,20*pi/180,dt,stride);
t = (0:numel(theta)-1)'*dt;
```

The reusable simulator propagates the continuous controller and plant under the supplied held reference. Its mechanical state starts at the given angle with zero speed and current. Each command column is simulated separately. Reference clipping is done by the caller. The linear model has no hard stops or voltage/current limits.

## Scope and submission fields

Automated targeting, target-state estimation, future interception, laser engagement and `fire_cmd` are **not implemented**. The bench tests are separate from the assignment’s target scenarios. Instructor final evaluation was not run, and there are no interception metrics in the report.

- Add the author name, roll number and public repository URL to a local copy of `report/submission.json` before rebuilding the course submission PDF. Rebuild the PDF using the commands above.
- Review the engineering assumptions and AI appendix before submitting. The PDF uses an independently typeset IEEE-style two-column layout. The assignment supplies separate [Overleaf](https://www.overleaf.com/latex/templates/ieee-conference-template/grfzhhncsfqn) and [Word](https://ieee-org.widen.net/content/ge5anzdecd/original/conference-template-a4.docx) templates.
- The assignment lists the [team submission form](https://forms.gle/mzaFe6e4qUFGtWzPA) and the separate [confidential peer-evaluation form](https://forms.gle/KGo68Po8yuqNrjV49). The designated team representative submits the paper. Each team member completes their own peer evaluation.
