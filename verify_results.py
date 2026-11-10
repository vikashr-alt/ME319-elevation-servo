"""Check exported servo results against independently formed SciPy LTI models."""
from pathlib import Path
import argparse

import numpy as np
from scipy import signal
from scipy.optimize import brentq


def csv(path, name):
    return np.genfromtxt(path / f"{name}.csv", delimiter=",", names=True)


def verify(path):
    w = csv(path, "frequency")
    step = csv(path, "step")
    clean, noise, hold = (csv(path, name) for name in ("smooth", "noise", "hold"))
    # Rebuild the axis from torque and voltage balances in SI units.
    N, Jm, Jload, b, R, L, Kt, Ke = 100, .20, 1200, 1500, 1, .1, 10, 10
    J = Jload + N**2 * Jm
    a = np.array([[0, 1, 0], [0, -b/J, N*Kt/J], [0, -N*Ke/L, -R/L]])
    b_input = np.array([0, 0, 1/L])
    s = 1j * w["omega_rad_s"]
    plant_ss = np.array([np.linalg.solve(q*np.eye(3)-a, b_input)[0] for q in s])
    den_p = [L*J, R*J+L*b, R*b+N**2*Kt*Ke, 0]
    plant_tf = N*Kt / np.polyval(den_p, s)
    plant_residual = np.max(np.abs(plant_ss / plant_tf - 1))
    assert plant_residual < 1e-12

    num = 2400*N*Kt*np.array([2.0, 8.0])
    den = np.polymul(den_p, [1, 8])
    char = np.polyadd(den, num)

    def loop(omega):
        q = 1j*omega
        return np.polyval(num, q)/np.polyval(den, q)

    gain_cross = brentq(lambda omega: abs(loop(omega))-1, 2, 4)
    phase_cross = brentq(lambda omega: loop(omega).imag, 54, 58)
    margin = -20*np.log10(abs(loop(phase_cross)))
    pm = 180+np.angle(loop(gain_cross), deg=True)
    exported_loop = np.max(abs(20*np.log10(abs(loop(w["omega_rad_s"]))) - w["loop_dB"]))
    assert exported_loop < 1e-8
    assert abs(margin - 6.986734165) < 1e-7
    assert abs(pm - 105.0366617) < 1e-6
    assert np.all(np.roots(char).real < 0)

    # Propagate independent pole-residue modes under each exported ZOH input.
    residues, poles, direct = signal.residue(num, char)
    assert len(direct) == 0
    decay = np.exp(poles*.001)
    increment = np.expm1(poles*.001)/poles
    differences = []
    for case in (step, clean, noise, hold):
        t = case["t_s"]
        assert len(t) == 10001 and t[0] == 0 and t[-1] == 10
        np.testing.assert_allclose(case["ideal_deg"] - case["output_deg"],
                                   case["error_deg"], atol=1e-9)
        state = np.zeros(len(poles), dtype=complex)
        y = np.empty(len(t))
        for k, command in enumerate(case["applied_deg"]-20):
            y[k] = 20 + np.sum(residues*state).real
            state = decay*state + increment*command
        residual = np.max(np.abs(y-case["output_deg"]))
        assert residual < 1e-8
        differences.append(residual)

    t = hold["t_s"]
    gap = (t >= 1.0) & (t < 1.5)
    np.testing.assert_array_equal(hold["applied_deg"][~gap], noise["applied_deg"][~gap])
    np.testing.assert_array_equal(hold["applied_deg"][gap], noise["applied_deg"][950])
    print(f"Plant state-space/transfer-function max relative residual: {plant_residual:.3g}")
    print(f"Independent lead-loop margins: PM {pm:.6f} deg, GM {margin:.6f} dB")
    print(f"Exported Bode magnitude max residual: {exported_loop:.3g} dB")
    print(f"All four reconstructed output traces: max residual {max(differences):.3g} deg")
    print("Verified 0-10 s time axes, error columns and exact command hold interval.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("results", nargs="?", type=Path,
                        default=Path(__file__).resolve().parent / "results")
    verify(parser.parse_args().results)
