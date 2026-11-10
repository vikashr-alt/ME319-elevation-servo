function run_servo_study(outdir)
% Reproduce all numerical results without add-on packages.
if nargin == 0
    outdir = fullfile(fileparts(mfilename('fullpath')), '..', 'results');
end
if ~exist(outdir,'dir'), mkdir(outdir); end
p = servo_plant();
m = servo_analysis(p);
assert(p.J == 3200 && isequal(p.den,[320,3350,1001500,0]));
[qdot, wdot, idot] = turret_plant(0, 24, .2, .03, .4);
expected = [.03; (100*10*.4-1500*.03)/3200; (24-.4-100*10*.03)/.1];
assert(norm([qdot;wdot;idot]-expected,inf) < 1e-12);
assert(all(real(m.poles) < 0));
assert(norm(poly(m.A) - m.char/m.char(1),inf) < 1e-8);
assert(numel(m.wgc) == 1 && numel(m.wpc) == 1);
assert(m.gm_db > 6 && m.pm > 60 && m.wgc > 2 && m.wgc < 4);
assert(abs(m.C*(-m.A\m.B)-1) < 1e-12);

dt = 0.001;
t = (0:10000)'*dt;
stride = 50;
ticks = (1:stride:numel(t))';
radians = pi/180;
initial = 20*radians;
smooth = @(time) (20 + 6*sin(2*pi*0.30*time) + 2*sin(2*pi*0.70*time))*radians;
rng(319,'twister');
noise = 0.02*radians*randn(size(ticks));
invalid = ticks >= 1001 & ticks < 1501;
assert(sum(invalid) == 10);
clean = smooth(t(ticks)); % Angle commands at the update instants.
noisy = clean + noise;
held = noisy;
for k = 2:numel(ticks)
    if invalid(k), held(k) = held(k-1); end
end
last_good = find(invalid,1)-1;
assert(all(held(invalid) == noisy(last_good)));
assert(all(held(~invalid) == noisy(~invalid)));

target = [30*radians*ones(size(t)), repmat(smooth(t),1,3)];
tick_cmd = [30*radians*ones(size(ticks)), clean, noisy, held];
tick_cmd = min(max(tick_cmd,p.angle_limits(1)),p.angle_limits(2));
[theta, volts, amps, applied] = simulate_servo(m,tick_cmd,initial,dt,stride);
assert(all(isfinite([theta(:);volts(:);amps(:)])));
assert(min(theta(:)) > p.angle_limits(1) && max(theta(:)) < p.angle_limits(2));

% Independent ODE integration of the same closed-loop step.
options = odeset('RelTol',1e-10,'AbsTol',1e-12);
[~, state] = ode45(@(~,x) m.A*x + m.B*30*radians, ...
                   t,[initial;0;0;0],options);
ode_delta = max(abs(state(:,1)-theta(:,1)));
assert(ode_delta < 1e-8);
[theta_fine, ~, ~, ~] = simulate_servo(m,tick_cmd,initial,dt/2,2*stride);
grid_delta = max(max(abs(theta_fine(1:2:end,:)-theta)));
assert(grid_delta < 1e-10);

err = (target-theta)/radians;
output_deg = theta/radians;
peak = max(output_deg(:,1));
k_rise = find(output_deg(:,1)>=29,1);
k_start = find(output_deg(:,1)>=21,1);
k_last = find(abs(err(:,1)) > 0.2,1,'last');
assert(k_last < numel(t));
rms_error = sqrt(mean(err.^2,1));
max_error = max(abs(err),[],1);
noise_delta = (theta(:,3)-theta(:,2))/radians;
hold_delta = (theta(:,4)-theta(:,3))/radians;
during_hold = t>=1 & t<1.5;
after_hold = t>=1.5;
recovery_index = find(after_hold & abs(hold_delta)>0.1,1,'last');
if isempty(recovery_index), recovery_time = 0;
else, recovery_time = t(recovery_index+1)-1.5;
end

metrics = fopen(fullfile(outdir,'metrics.txt'),'w');
assert(metrics >= 0);
fprintf(metrics,'Plant poles [1/s]\n');
fprintf(metrics,'%.10f %+.10fi\n',[real(roots(p.den)),imag(roots(p.den))]');
fprintf(metrics,'Closed-loop poles [1/s]\n');
fprintf(metrics,'%.10f %+.10fi\n',[real(m.poles),imag(m.poles)]');
fprintf(metrics,'wgc_rad_s %.10g\nwpc_rad_s %.10g\npm_deg %.10g\ngm_dB %.10g\nbandwidth_rad_s %.10g\nKv_per_s %.10g\n', ...
    m.wgc,m.wpc,m.pm,m.gm_db,m.bw,m.Kv);
fprintf(metrics,'step_rise_s %.10g\nstep_settle_s %.10g\nstep_overshoot_percent %.10g\nstep_final_error_deg %.10g\n', ...
    t(k_rise)-t(k_start),t(k_last+1),max(0,10*(peak-30)),err(end,1));
fprintf(metrics,'noise_output_rms_delta_deg %.10g\nloss_peak_delta_during_deg %.10g\nloss_peak_delta_after_deg %.10g\nloss_recovery_s %.10g\n', ...
    sqrt(mean(noise_delta.^2)),max(abs(hold_delta(during_hold))), ...
    max(abs(hold_delta(after_hold))),recovery_time);
fprintf(metrics,'angle_min_deg %.10g\nangle_max_deg %.10g\node45_delta_rad %.10g\nhalf_grid_delta_rad %.10g\n', ...
    min(output_deg(:)),max(output_deg(:)),ode_delta,grid_delta);
fprintf(metrics,'noise_sample_std_deg %.10g\nhold_last_deg %.10g\n',std(noise/radians),held(last_good)/radians);
fprintf(metrics,'\ncase,rms_error_deg,peak_error_deg,peak_voltage_V,peak_current_A\n');
labels = {'step','smooth','noise','hold'};
for k = 1:numel(labels)
    fprintf(metrics,'%s,%.10g,%.10g,%.10g,%.10g\n',labels{k},rms_error(k), ...
        max_error(k),max(abs(volts(:,k))),max(abs(amps(:,k))));
    write_csv(outdir,[labels{k} '.csv'], ...
        't_s,ideal_deg,applied_deg,output_deg,error_deg,voltage_V,current_A', ...
        [t,target(:,k)/radians,applied(:,k)/radians,output_deg(:,k), ...
         err(:,k),volts(:,k),amps(:,k)]);
end
fclose(metrics);

w = logspace(-1,3,1201)';
s = 1i*w;
loop = polyval(m.num,s)./polyval(m.den,s);
baseline = m.K*p.num./polyval(p.den,s);
write_csv(outdir,'frequency.csv','omega_rad_s,loop_dB,loop_phase_deg,p_only_dB,p_only_phase_deg,T_dB', ...
    [w,20*log10(abs(loop)),unwrap(angle(loop))/radians, ...
     20*log10(abs(baseline)),unwrap(angle(baseline))/radians, ...
     20*log10(abs(loop./(1+loop)))]);
fprintf('Verified four servo cases and wrote data to %s\n',outdir);
end

function write_csv(outdir, name, header, data)
fid = fopen(fullfile(outdir,name),'w');
assert(fid >= 0);
fprintf(fid,'%s\n',header);
format = [repmat('%.12g,',1,size(data,2)-1),'%.12g\n'];
fprintf(fid,format,data');
fclose(fid);
end
