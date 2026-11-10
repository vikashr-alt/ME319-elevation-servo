function [theta_dot, theta_ddot, i_dot] = turret_plant(~, volts, theta, omega, current)
% Assignment-compatible interface for the passive elevation-axis plant.
persistent p
if isempty(p), p = servo_plant(); end
dx = p.A*[theta;omega;current] + p.B*volts;
theta_dot = dx(1);
theta_ddot = dx(2);
i_dot = dx(3);
end
