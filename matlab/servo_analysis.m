function m = servo_analysis(p)
% Unity-feedback lead design. Uses core MATLAB/Octave polynomial algebra.
m.K = 2400;
m.wz = 4;
m.wp = 8;
m.Khf = m.K*m.wp/m.wz;
m.num = p.num*m.Khf*[1, m.wz];
m.den = conv(p.den, [1, m.wp]);
m.char = m.den + [0, 0, 0, m.num];
m.poles = roots(m.char);

% Form exact crossing polynomials in x = omega^2. For a real
% descending-power polynomial q(s), q(-s) has alternating signs.
den_neg = m.den.*(-1).^(length(m.den)-1:-1:0);
num_neg = m.num.*(-1).^(length(m.num)-1:-1:0);
power_diff = conv(m.den, den_neg) - [zeros(1, 6), conv(m.num, num_neg)];
m.wgc = positive_frequencies(power_diff(1:2:end).*(-1).^(4:-1:0));
loop = @(s) polyval(m.num,s)./polyval(m.den,s);
m.pm = 180 + angle(loop(1i*m.wgc))*180/pi;
cross = conv(m.num, den_neg);
wpc = positive_frequencies(cross(1:2:end).*(-1).^(2:-1:0));
value = loop(1i*wpc);
m.wpc = wpc(real(value) < 0);
m.gm_db = -20*log10(abs(loop(1i*m.wpc)));

% z_dot = wp*(e-z), u = Khf*e + (K-Khf)*z, e = r - C*x.
m.A = [p.A-p.B*m.Khf*p.C, p.B*(m.K-m.Khf); -m.wp*p.C, -m.wp];
m.B = [p.B*m.Khf; m.wp];
m.C = [p.C, 0];
m.Cu = [-m.Khf*p.C, m.K-m.Khf];

% T = N/(D+N), so |T|^2 = 1/2 when |D+N|^2 - 2|N|^2 = 0.
char_neg = m.char.*(-1).^(length(m.char)-1:-1:0);
bw_poly = conv(m.char, char_neg) - [zeros(1, 6), 2*conv(m.num, num_neg)];
m.bw = min(positive_frequencies(bw_poly(1:2:end).*(-1).^(4:-1:0)));
m.Kv = m.K*p.num/p.den(3);
end

function w = positive_frequencies(c)
x = roots(c);
x = real(x(abs(imag(x)) < 1e-9 & real(x) > 0));
w = sort(sqrt(x));
end
