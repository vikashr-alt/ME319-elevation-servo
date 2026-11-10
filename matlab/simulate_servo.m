function [theta, volts, amps, applied] = simulate_servo(m, tick_cmd, initial, dt, stride)
% Apply one column of radians commands per run, with one row per update.
% All commands are held for stride integration intervals. The last row
% is evaluated at the final sample. Angles, effort and current use SI units.
n = (size(tick_cmd,1)-1)*stride + 1;
applied = tick_cmd(floor((0:n-1)'/stride)+1,:);
case_count = size(applied,2);
state = repmat([initial;0;0;0],1,case_count);
theta = zeros(n,case_count);
volts = theta;
amps = theta;
transition = expm([m.A,m.B;zeros(1,5)]*dt);
Ad = transition(1:4,1:4);
Bd = transition(1:4,5);
for k = 1:n
    command = applied(k,:);
    theta(k,:) = m.C*state;
    amps(k,:) = state(3,:);
    volts(k,:) = m.Cu*state + m.Khf*command;
    state = Ad*state + Bd*command;
end
end
