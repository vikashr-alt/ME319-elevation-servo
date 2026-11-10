# Verification record

## Seven-page assignment review

The attachment from “Complete Assignment Review” was inspected in full by extracting text and rendering the pages. Its SHA-256 was `03ff641ce5b133ec067f8acfafcffdd07c5ba2f1bf111ec7b60c8a99372628d8`.

| Page | Requirement reviewed | Package treatment |
|---|---|---|
| 1 | Assignment scope, submission format, team size and deadline | Servo-only report and reproducible local repository files. The paper and individual peer evaluation remain separate submissions. |
| 2 | Elevation-drive parameters, mechanical angle envelope, sensing and disturbance assumptions | All physical drive parameters retained. The 20 Hz, 0.02° and 0.50 s conditions are used as bench command tests. Radar range and motion inference are outside this study. |
| 3 | Full 10 s standardized cases and evaluation interfaces | All bench traces span [0, 10] s. The passive `turret_plant.m` derivative interface is included. Standardized target motion, engagement and the engagement controller interface are not implemented. |
| 4 | Predictive architecture, fixed LTI compensator and formatting | One fixed lead compensator, with analytical design and stability checks. Target prediction and future-elevation generation are not implemented. The report uses an independently typeset two-column IEEE-style layout. |
| 5 | Paper structure, figures, comparison and instructor final evaluation | Model derivation, block diagram, controller analysis and numerical bench comparison included. Instructor final-evaluation scripts and cases were unavailable and were not run. No interception metrics are reported. |
| 6 | Rubric, one-page AI appendix and individual evaluation | AI appendix records contributions and validation. Targeting-related rubric items and final evaluation remain outside the servo-only scope. Individual peer evaluation remains with each team member. |
| 7 | Final PDF, public repository URL and submission forms | Three main pages plus one AI page. Code, results and figures are packaged locally. The named course PDF and private author metadata are distributed separately. The two forms are linked in the README. |

## Executed checks

| Check | Observed result |
|---|---|
| Plant derivation | Reflected inertia 3200 kg·m² and denominator coefficients [320, 3350, 1001500, 0]. Direct derivative test passed for the passive plant entry point at nonzero speed and current. |
| Nominal loop | Characteristic polynomial agrees with the augmented state matrix. All closed-loop poles have strictly negative real parts. The Routh first column is positive. |
| Crossings and margins | One positive gain crossover at 2.758605 rad/s and one negative-real-axis crossing at 56.312913 rad/s. Phase margin 105.036662° and gain margin 6.986734 dB. |
| Independent frequency-domain computation | SciPy root searches matched the margins. Plant state-space and transfer-function evaluations agreed to 7.44 × 10⁻¹⁴ maximum relative residual. Exported loop magnitude agreed within 1.39 × 10⁻¹⁰ dB. |
| Independent time-domain computation | All four output traces were reconstructed using transfer-function pole residues and the exported held commands. Maximum difference was 8.36 × 10⁻¹¹°. |
| Step integration and time grid | Adaptive `ode45` matched the exact held-input step to 7.56 × 10⁻¹³ rad or better. Halving the grid spacing changed common samples by less than 3 × 10⁻¹⁴ rad. |
| Update timing | Exactly ten updates omitted on [1.00, 1.50) s. The 0.95 s command is retained during the gap. Noisy and gap-case applied commands agree elsewhere. |
| Logged outputs | All finite, with 10,001 records per case and sampled angle range 14.63°–30.00°. Error columns match ideal command minus output. |
| Report | Four pages rendered and visually checked. The fourth page is the AI appendix. Figures and table values match the included run outputs. |

## Verification boundaries

The checks cover nominal small-signal simulation. Actuator voltage/current limits, drive nonlinearities, sensor dynamics and mechanical stop contact were not modeled. The finite grid supports the stated sampled peak and settling measurements. MATLAB syntax compatibility is intended. The available MATLAB installation failed at launch, so the completed runtime check was in GNU Octave 11.3.0. Student review and a verified public repository URL remain pending.
