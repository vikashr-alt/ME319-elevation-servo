function p = servo_plant()
% Elevation-axis small-signal model, with angle in radians.
p.N = 100;
p.Jload = 1200;  p.Jmotor = 0.20;
p.b = 1500;
p.Kt = 10;       p.Ke = 10;
p.R = 1.0;       p.L = 0.10;
p.angle_limits = [-10, 85] * pi/180;
p.J = p.Jload + p.N^2*p.Jmotor;

% x = [angle; angular velocity; armature current], u = armature volts.
p.A = [0, 1, 0; 0, -p.b/p.J, p.N*p.Kt/p.J;
       0, -p.N*p.Ke/p.L, -p.R/p.L];
p.B = [0; 0; 1/p.L];
p.C = [1, 0, 0];
p.num = p.N*p.Kt;
p.den = [p.L*p.J, p.R*p.J+p.L*p.b, p.R*p.b+p.N^2*p.Ke*p.Kt, 0];
end
