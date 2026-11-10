"""Build the four-page report from the study data and the editable author record."""
from pathlib import Path
import argparse
import json
from xml.sax.saxutils import escape

from PIL import Image
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_JUSTIFY
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.utils import ImageReader
from reportlab.pdfgen import canvas
from reportlab.platypus import Paragraph, Table, TableStyle

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
W, H = 612, 792
LEFT, RIGHT, GUTTER = 43, 569, 18
WIDTH = RIGHT - LEFT
COL = (WIDTH - GUTTER) / 2
SECOND = LEFT + COL + GUTTER
INK = colors.HexColor("#151b23")
MUTED = colors.HexColor("#475563")
RULE = colors.HexColor("#b3bec7")

BODY = ParagraphStyle("body", fontName="Times-Roman", fontSize=10,
                      leading=11.6, alignment=TA_JUSTIFY, textColor=INK)
CAPTION = ParagraphStyle("caption", parent=BODY, fontSize=8.5, leading=10.2)
HEADING = ParagraphStyle("heading", parent=BODY, fontSize=10.3, leading=12,
                         fontName="Times-Bold", alignment=TA_CENTER)
SUB = ParagraphStyle("sub", parent=BODY, fontName="Times-Italic", leading=12)
SMALL = ParagraphStyle("small", parent=BODY, fontSize=8.8, leading=10.7)


class Page:
    def __init__(self, pdf, number, label):
        self.pdf, self.number = pdf, number
        pdf.setStrokeColor(RULE)
        pdf.setLineWidth(.45)
        pdf.line(LEFT, 752, RIGHT, 752)
        pdf.setFillColor(MUTED)
        pdf.setFont("Helvetica", 8)
        pdf.drawString(LEFT, 762, "ME319  /  CONTROL SYSTEMS  /  AUTUMN 2026")
        pdf.drawRightString(RIGHT, 762, label)

    def end(self):
        self.pdf.setFillColor(MUTED)
        self.pdf.setFont("Helvetica", 8)
        self.pdf.drawCentredString(W/2, 30, str(self.number))
        self.pdf.showPage()

    def text(self, text, x, y, w=COL, style=BODY, gap=6):
        para = Paragraph(text, style)
        _, h = para.wrap(w, H)
        if y-h < 47:
            raise ValueError(f"Page {self.number} overflows at y={y:.1f}, h={h:.1f} {text[:55]}")
        para.drawOn(self.pdf, x, y-h)
        return y-h-gap

    def head(self, title, x, y, w=COL):
        return self.text(title, x, y-4, w, HEADING, 7)

    def sub(self, title, x, y, w=COL):
        return self.text(title, x, y, w, SUB, 4)

    def figure(self, name, x, y, caption, w=COL):
        path = ROOT / "figures" / f"{name}.png"
        with Image.open(path) as im:
            h = w*im.height/im.width
        self.pdf.drawImage(ImageReader(str(path)), x, y-h, w, h)
        return self.text(caption, x, y-h-5, w, CAPTION, 9)

    def equation(self, assets, number, x, y, label=None, gap=9):
        path = assets / f"eq{number}.png"
        with Image.open(path) as im:
            w = min(COL-27, im.width*72/400)
            h = w*im.height/im.width
        self.pdf.drawImage(ImageReader(str(path)), x+(COL-18-w)/2, y-h, w, h)
        if label:
            self.pdf.setFont("Times-Roman", 9)
            self.pdf.setFillColor(INK)
            self.pdf.drawRightString(x+COL, y-h/2-2, f"({label})")
        return y-h-gap

    def table(self, data, widths, x, y):
        table = Table(data, colWidths=widths, hAlign="LEFT")
        table.setStyle(TableStyle([
            ("FONTNAME",(0,0),(-1,0),"Times-Bold"),
            ("FONTNAME",(0,1),(-1,-1),"Times-Roman"),
            ("FONTSIZE",(0,0),(-1,-1),9),
            ("ALIGN",(1,0),(-1,-1),"RIGHT"),
            ("TOPPADDING",(0,0),(-1,-1),4),
            ("BOTTOMPADDING",(0,0),(-1,-1),4),
            ("LINEABOVE",(0,0),(-1,0),.55,INK),
            ("LINEBELOW",(0,0),(-1,0),.35,RULE),
            ("LINEBELOW",(0,-1),(-1,-1),.55,INK),
        ]))
        _, h = table.wrap(sum(widths), H)
        table.drawOn(self.pdf, x, y-h)
        return y-h-9


def read_metrics():
    metrics, rows = {}, {}
    for line in (ROOT / "results/metrics.txt").read_text().splitlines():
        if line.split(",")[0] in ("step", "smooth", "noise", "hold"):
            name, *data = line.split(",")
            rows[name] = [float(value) for value in data]
        else:
            tokens = line.split()
            if len(tokens)==2 and "_" in tokens[0]:
                metrics[tokens[0]] = float(tokens[1])
    return metrics, rows


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("assets", type=Path, help="Equation image directory")
    parser.add_argument("output", type=Path)
    args = parser.parse_args()
    e = args.assets
    data, rows = read_metrics()
    fields = json.loads((HERE/"submission.json").read_text())
    authors = ", ".join(fields["authors"]) or "Author names and roll numbers pending"
    repo = fields["repository_url"]
    c = canvas.Canvas(str(args.output), pagesize=(W,H), pageCompression=1)
    c.setTitle("Modeling and Lead Compensation of an Elevation Servo")
    if fields["authors"]:
        c.setAuthor(authors)

    p = Page(c, 1, "ASSIGNMENT 2")
    c.setFont("Times-Roman", 22)
    c.setFillColor(INK)
    c.drawCentredString(W/2, 711, "Modeling and Lead Compensation")
    c.drawCentredString(W/2, 686, "of an Elevation Servo")
    c.setFont("Times-Roman", 11)
    c.drawCentredString(W/2, 658, authors)
    c.drawCentredString(W/2, 642, "Department of Mechanical Engineering, IIT Bombay")

    y = p.text(f"<b><i>Abstract</i></b> — A geared DC motor model is derived from the elevation-axis parameters in ME319 Assignment 2. A fixed lead compensator is designed and checked using the characteristic polynomial and frequency response. The nominal loop has a {data['pm_deg']:.1f}° phase margin and a {data['gm_dB']:.2f} dB gain margin. A 10° command step settles within 2% in {data['step_settle_s']:.2f} s. A generic command sequence tests 20 Hz updates, additive angle noise and a half-second interruption. Tracking lag and the voltage demand of the ideal model limit the conclusions to simulation.", LEFT, 619)
    y = p.text("<b><i>Index Terms</i></b> — DC motor, elevation servo, lead compensation, sampled reference, stability margins.", LEFT, y)
    y = p.head("I. INTRODUCTION", LEFT, y)
    y = p.text("The assignment specifies an elevation axis driven by an armature-controlled DC motor [1, Sec. 2]. This study isolates the axis and treats it as a bench position servo. The input is a prescribed angle command. The objectives are to derive the voltage-to-angle plant, establish nominal feedback stability and quantify how the axis follows representative commands.", LEFT, y)
    y = p.text("The simulated plant has ideal gearing and viscous loss. It assumes a balanced load, or an operating point with constant load torque compensated at equilibrium. Incremental gravity stiffness, backlash, Coulomb friction, compliance, actuator saturation and hard-stop contact are outside the model.", LEFT, y)
    y = p.head("II. SERVO ARCHITECTURE", LEFT, y)
    y = p.figure("architecture", LEFT, y, "Fig. 1. Motor and load schematic (a) and the negative-feedback position loop (b).")
    p.text("The command source feeds a sample-and-hold and an angle limiter. The held value <i>r</i><sub>h</sub> is compared with the axis angle. The controller produces armature voltage from the error. Axis position feedback is continuous and ideal in this study.", LEFT, y)

    y = p.head("III. ELECTROMECHANICAL MODEL", SECOND, 619)
    y = p.sub("A. Gear reduction and reflected inertia", SECOND, y)
    y = p.text("Let <i>N</i> = 100 be motor speed divided by load speed, <i>ω</i> the load angular velocity and <i>i</i> the armature current. Ideal power transfer maps motor torque <i>K</i><sub>t</sub><i>i</i> to load-side torque <i>NK</i><sub>t</sub><i>i</i>. Equating kinetic energy on the load side reflects rotor inertia by <i>N</i><super>2</super>.", SECOND, y)
    y = p.equation(e,1,SECOND,y,1)
    y = p.text("The torque balance and Kirchhoff voltage law then give", SECOND, y)
    y = p.equation(e,2,SECOND,y,2)
    y = p.equation(e,3,SECOND,y,3)
    y = p.text("Back EMF uses motor speed <i>Nω</i>. With zero initial perturbations, eliminate current and use Ω(<i>s</i>) = <i>s</i>Θ(<i>s</i>) to obtain", SECOND, y)
    y = p.equation(e,4,SECOND,y,4)
    y = p.equation(e,5,SECOND,y,5)
    y = p.sub("B. Parameter values and operating envelope", SECOND, y)
    y = p.table([
        ["Parameter","Value","SI unit"], ["Load inertia","1200","kg·m²"],
        ["Rotor inertia","0.20","kg·m²"], ["Viscous damping","1500","N·m·s/rad"],
        ["Torque constant","10","N·m/A"], ["Back EMF constant","10","V·s/rad"],
        ["Resistance","1.0","Ω"], ["Inductance","0.10","H"],
    ],[116,48,90],SECOND,y)
    y = p.text("Equations (2)–(3) define the plant states [angle, angular velocity, current]. The plant has one pole at zero and an electromechanical pair at −5.234 ± j55.698 s<super>−1</super>. The command is bounded to −10° through +85° as specified in [1]. A bounded reference alone cannot prevent overshoot past a mechanical limit.", SECOND, y)
    p.end()

    p = Page(c, 2, "CONTROLLER AND NOMINAL RESPONSE")
    y = p.head("IV. CONTROLLER DESIGN", LEFT, 735)
    y = p.sub("A. Lead shaping", LEFT, y)
    y = p.text("Below the electromechanical resonance, the plant is approximately an integrator with gain 1000/1001500. A proportional gain near 2400 V/rad therefore gives a crossover near 2.4 rad/s. The bench design targets a 2–4 rad/s crossover, phase margin above 60° and gain margin above 6 dB. These are study design criteria.", LEFT, y)
    y = p.text("A zero at 4 rad/s and pole at 8 rad/s add positive phase near crossover. The ratio of two limits the increase in high-frequency loop gain near the lightly damped motor mode. The design uses the same gains in all simulations.", LEFT, y)
    y = p.equation(e,6,LEFT,y,6)
    y = p.text("For the implementation, <i>z</i> is the low-pass-filtered error with initial value zero. Use the equations below with radians and volts.", LEFT, y)
    y = p.equation(e,7,LEFT,y,7)
    y = p.sub("B. Stability and tracking implications", LEFT, y)
    y = p.text("For unity negative feedback, the reference-to-angle and reference-to-error transfer functions are", LEFT, y)
    y = p.equation(e,8,LEFT,y,8)
    y = p.text("Writing the characteristic polynomial as the sum of the loop denominator and numerator gives", LEFT, y)
    y = p.equation(e,9,LEFT,y,gap=3)
    y = p.equation(e,10,LEFT,y,9)
    y = p.text("The unnormalized Routh first column is 320, 5910, 3.346 × 10<super>5</super>, 1.247 × 10<super>7</super> and 1.920 × 10<super>7</super>. Its positive signs imply stability. The nominal poles are −1.739, −11.052 and −2.839 ± j55.799 s<super>−1</super>.", LEFT, y)
    y = p.text("The integrator makes the loop type 1. A constant reference has zero steady-state error. For a ramp of slope <i>a</i>, the error tends to <i>a</i>/<i>K</i><sub>v</sub> in the linear model, where <i>K</i><sub>v</sub> = 2400(1000)/1001500 = 2.396 s<super>−1</super>. Sustained ramps eventually leave the physical range.", LEFT, y)
    y = p.figure("frequency", LEFT, y, "Fig. 2. Open-loop responses for the lead compensator and the same DC gain with proportional control.")
    y = p.sub("C. Frequency response", SECOND, 731)
    y = p.text(f"The loop has one gain crossover at {data['wgc_rad_s']:.3f} rad/s and one negative-real-axis crossing at {data['wpc_rad_s']:.3f} rad/s. The resulting phase and gain margins are {data['pm_deg']:.2f}° and {data['gm_dB']:.2f} dB. The closed-loop −3 dB bandwidth is {data['bandwidth_rad_s']:.3f} rad/s.", SECOND, y)
    y = p.text("Proportional control at the same DC gain gives 2.401 rad/s crossover, 89.54° phase margin and 12.81 dB gain margin. Lead trades some gain margin for phase margin. The high-frequency crossing near the motor mode explains why a large phase margin at low frequency does not by itself justify increasing gain.", SECOND, y)
    y = p.head("V. SIMULATION METHOD", SECOND, y)
    y = p.text("Each case starts at 20° with zero angular velocity, armature current and controller state. The continuous LTI loop is propagated exactly for each constant held reference using a matrix exponential. Reference updates occur every 50 ms and state and effort are recorded every 1 ms on [0, 10] s. Feedback remains continuous.", SECOND, y)
    y = p.sub("A. Step benchmark", SECOND, y)
    y = p.figure("step", SECOND, y, "Fig. 3. Step from 20° to 30° at time zero. The shaded band spans ±2% of the step amplitude.")
    y = p.text(f"The 10–90% rise time is {data['step_rise_s']:.3f} s and the 2% settling time is {data['step_settle_s']:.3f} s, with no observed overshoot. The computed error at 10 s is below 10<super>−6</super>°. The initial proportional feedthrough requests about {rows['step'][2]:.0f} V and the simulated peak current is {rows['step'][3]:.0f} A. No voltage or current rating is supplied in the assignment. These are model demands and cannot establish hardware feasibility.", SECOND, y)
    p.end()

    p = Page(c, 3, "BENCH TRACKING AND SCOPE")
    y = p.figure("tracking", LEFT, 738, "Fig. 4. Angle, ideal-command error and the output difference caused by the gap. Shading marks 1.00–1.50 s. Horizontal dashed lines in the bottom panel mark ±0.10°.", WIDTH)
    y0 = y
    y = p.sub("B. Generic command, noise and interrupted updates", LEFT, y)
    y = p.text("The two-tone setpoint spans one component near the servo bandwidth and another above it. The analytic command in degrees is", LEFT, y)
    y = p.equation(e,11,LEFT,y,10)
    y = p.text("The clean case samples (10) at 20 Hz. The noise case adds independent, zero-mean Gaussian perturbations to those samples with 0.02° standard deviation and seed 319. The hold case uses the same noise realization and holds the 0.95 s command until 1.50 s, omitting ten updates. Axis feedback continues during the interruption.", LEFT, y)
    y = p.equation(e,12,LEFT,y,11)
    y = p.text("Errors use the ideal unsampled command on all 10,001 logged instants. Peaks use the same grid.", LEFT, y)
    y = p.text("TABLE I. TRACKING ERROR AND VOLTAGE DEMAND", LEFT, y, COL, SMALL, 4)
    y = p.table([["Case","RMS (°)","Peak (°)","Peak |V| (V)"]] +
                [[label,f"{rows[k][0]:.3f}",f"{rows[k][1]:.3f}",f"{rows[k][2]:.1f}"]
                 for k,label in [("step","Step"),("smooth","Clean"),("noise","Noise"),("hold","Hold")]],
                [62,57,57,78],LEFT,y)
    y = p.text(f"The noise-only output difference is {data['noise_output_rms_delta_deg']:.4f}° RMS. Relative to the noisy run, the gap adds up to {data['loss_peak_delta_during_deg']:.3f}° during the interruption and {data['loss_peak_delta_after_deg']:.3f}° after updates resume. The difference stays within 0.10° from {data['loss_recovery_s']:.3f} s after resumption.", LEFT, y)

    y = p.sub("C. Interpretation and numerical checks", SECOND, y0)
    y = p.text("At 0.30 and 0.70 Hz, the analog closed-loop amplitude ratios are 0.740 and 0.511, with phase lags of 31.9° and 42.9°. This accounts for most of the smooth-command error. The hold disturbance persists after resumption because the loop state remains displaced.", SECOND, y)
    y = p.text(f"All logged angles are within {data['angle_min_deg']:.2f}° to {data['angle_max_deg']:.2f}°. Repeating the exact propagation on a 0.5 ms grid and checking the step with an adaptive ODE solver both agree to less than 10<super>−8</super> rad. These checks establish numerical agreement for the model and runs shown.", SECOND, y)
    y = p.head("VI. FINAL EVALUATION STATUS", SECOND, y)
    y = p.text("Target-state estimation, future interception, automated targeting, laser engagement and <font name='Courier'>fire_cmd</font> are not implemented. The generic bench cases are separate from the assignment’s standardized target scenarios. The instructor’s evaluation was not run and no interception results are reported.", SECOND, y)
    y = p.head("VII. CONCLUSION", SECOND, y)
    y = p.text("A fixed lead compensator stabilizes the specified small-signal axis and achieves zero nominal step offset. Servo bandwidth limits the moving-command response, while a stale command adds transient lag. The ideal model omits actuator limits and contact physics, so its effort and angle traces characterize this simulation only.", SECOND, y)
    y = p.text("Repository URL: " + (escape(repo) if repo else "Pending publication."), SECOND, y, COL, SMALL)
    y = p.head("REFERENCES", SECOND, y)
    y = p.text("[1] P. Agarwal, “ME319: Control Systems, Assignment 2,” Dept. Mech. Eng., IIT Bombay, Autumn 2026, 7 pp.", SECOND, y, COL, SMALL)
    p.end()

    p = Page(c, 4, "MANDATORY AI DISCLOSURE")
    c.setFillColor(INK)
    c.setFont("Times-Roman", 20)
    c.drawCentredString(W/2, 708, "Appendix A. AI and Computational Tools")
    y = p.text("This appendix records the role of AI and computational tools in the bench elevation-servo study. It describes the checks performed while preparing the package. Author review and sign-off are pending.", LEFT, 673, WIDTH)
    y = p.head("A. TOOLS AND CONTRIBUTIONS", LEFT, y, WIDTH)
    y = p.text("<b>OpenAI Codex (GPT-6-based agent).</b> Reviewed the seven-page assignment, identified the servo-only scope, derived the plant and feedback equations, drafted the scripts and paper, and prepared the reproducibility and verification notes.", LEFT, y, WIDTH)
    y = p.text("<b>GNU Octave 11.3.0.</b> Computed plant and loop poles, solved gain and phase crossover polynomials, simulated all four cases and wrote the CSV and metric files. The MATLAB-compatible scripts use core functions. The available MATLAB installation failed to start, so MATLAB runtime behavior remains unverified.", LEFT, y, WIDTH)
    y = p.text("<b>Python tools.</b> NumPy and SciPy provided an independent transfer-function check. Matplotlib generated the figures and typeset the numbered equations. ReportLab assembled the two-column PDF and Poppler rendered it for visual inspection.", LEFT, y, WIDTH)
    y = p.head("B. ACCEPTED, MODIFIED AND EXCLUDED OUTPUTS", LEFT, y, WIDTH)
    y = p.text("<b>Accepted.</b> The plant equations, fixed lead compensator and numerical results were included after checking parameter reflection, polynomial stability, loop margins and agreement between the two numerical representations.", LEFT, y, WIDTH)
    y = p.text("<b>Modified.</b> The assignment’s simulation scope was changed to direct bench angle commands. The 20 Hz update rate, 0.02° noise scale, 0.50 s interruption and 10 s duration were retained as generic command-test conditions. The gap is modeled as a hold on the reference path, with axis feedback still active.", LEFT, y, WIDTH)
    y = p.text("<b>Excluded.</b> Target-state estimation, future interception, automated targeting and engagement logic were excluded by scope. Instructor-evaluation values and a public repository link were left pending. The author supplied the name and roll number.", LEFT, y, WIDTH)
    y = p.head("C. ENGINEERING VALIDATION", LEFT, y, WIDTH)
    y = p.text("<b>Physical model.</b> The kinetic-energy relation gives the load-side rotor inertia <i>N</i><super>2</super><i>J</i><sub>m</sub>. Torque and back EMF were mapped through the same gear ratio. A frequency-domain comparison checks the resulting transfer function against the state-space realization.", LEFT, y, WIDTH)
    y = p.text("<b>Controller and simulations.</b> The Routh signs, direct pole calculation and independent frequency check assess nominal stability. The reported tracking cases share the same controller and the two noisy cases share the same random realization. Exact held-input propagation was checked with a finer output grid and with an independent ODE step integration.", LEFT, y, WIDTH)
    y = p.text("<b>Limits on interpretation.</b> The effort traces are unconstrained model predictions. The reported angle bounds apply to the logged samples in the four bench tests. There was no hardware validation or instructor evaluation. The verification notes identify each assignment section addressed and the checks that can be rerun locally.", LEFT, y, WIDTH)
    p.end()
    c.save()


if __name__ == "__main__":
    main()
