function mason_analysis(expt_mat_file, track_selection, output_dir)
% MASON_ANALYSIS - Run reversal detection analysis (RetroVibez v1.0.0)
%
% Usage:
%   mason_analysis(expt_mat_file, track_selection, output_dir)
%
% Arguments:
%   expt_mat_file   - Path to experiment .mat file
%   track_selection - Comma-separated track numbers or 'all'
%   output_dir      - Directory to save results
%
% Supports two data formats:
%   1. Tracks in separate folder (e.g., 'GMR61@GMR61_202510291652 - tracks/')
%   2. Tracks embedded in experiment MAT file (eset.expt.track array)
%
% Example:
%   mason_analysis('D:\data\expt.mat', '1,2,5,10', 'D:\output\results')
%   mason_analysis('D:\data\expt.mat', 'all', 'D:\output\results')

fprintf('=== RetroVibez v1.0.0 - Reversal Detection ===\n');
fprintf('Experiment: %s\n', expt_mat_file);
fprintf('Tracks: %s\n', track_selection);
fprintf('Output: %s\n\n', output_dir);

%% Parse track selection
if strcmpi(track_selection, 'all')
    target_tracks = [];  % Will be populated after loading
else
    % Parse comma-separated list
    parts = strsplit(track_selection, ',');
    target_tracks = [];
    for i = 1:length(parts)
        target_tracks(end+1) = str2double(parts{i});
    end
end

%% Create output directory
if ~exist(output_dir, 'dir')
    mkdir(output_dir);
end

%% Load Experiment
fprintf('Loading experiment...\n');
load(expt_mat_file);

if exist('experiment', 'var')
    eset = ExperimentSet();
    eset.expt = experiment;
    clear experiment;
elseif ~exist('eset', 'var')
    error('No experiment or eset found in mat file');
end

fprintf('Experiment loaded successfully\n');

%% Calculate lengthPerPixel from camera calibration
if isprop(eset.expt(1), 'camcalinfo') && ~isempty(eset.expt(1).camcalinfo)
    cc = eset.expt(1).camcalinfo;
    test_pixels_x = [100, 500];
    test_pixels_y = [100, 500];
    real_coords_x = cc.c2rX(test_pixels_x, test_pixels_y);
    real_coords_y = cc.c2rY(test_pixels_x, test_pixels_y);
    pixel_dist = sqrt((test_pixels_x(2) - test_pixels_x(1))^2 + (test_pixels_y(2) - test_pixels_y(1))^2);
    real_dist = sqrt((real_coords_x(2) - real_coords_x(1))^2 + (real_coords_y(2) - real_coords_y(1))^2);
    lengthPerPixel = real_dist / pixel_dist;
    fprintf('lengthPerPixel: %.6f cm/pixel\n', lengthPerPixel);
else
    warning('No camera calibration found, using default');
    lengthPerPixel = 0.01;
end

%% Find tracks - either in separate folder or embedded in MAT file
[expt_dir, ~, ~] = fileparts(expt_mat_file);
tracks_dirs = dir(fullfile(expt_dir, '*tracks'));
if isempty(tracks_dirs)
    tracks_dirs = dir(fullfile(expt_dir, '*- tracks'));
end

use_embedded_tracks = isempty(tracks_dirs);

if use_embedded_tracks
    fprintf('No tracks directory found - using tracks embedded in MAT file\n');
    
    % Tracks are already in eset.expt.track from the loaded experiment
    if ~isempty(eset.expt(1).track)
        all_tracks = eset.expt(1).track;
        num_available = length(all_tracks);
        fprintf('Found %d tracks embedded in experiment\n', num_available);
        
        % Discover available track numbers (1 to N)
        if isempty(target_tracks)
            target_tracks = 1:num_available;
        end
        
        % Filter to requested tracks
        valid_targets = target_tracks(target_tracks <= num_available);
        tracks = all_tracks(valid_targets);
        loaded_track_nums = valid_targets;
    else
        error('No tracks found in experiment file');
    end
else
    tracks_dir = fullfile(expt_dir, tracks_dirs(1).name);
    fprintf('Tracks directory: %s\n', tracks_dir);
    
    % Discover available tracks if 'all' selected
    if isempty(target_tracks)
        track_files = dir(fullfile(tracks_dir, 'track*.mat'));
        target_tracks = [];
        for i = 1:length(track_files)
            match = regexp(track_files(i).name, 'track(\d+)\.mat', 'tokens');
            if ~isempty(match)
                target_tracks(end+1) = str2double(match{1}{1});
            end
        end
        target_tracks = sort(target_tracks);
    end
    
    % Load Target Tracks from separate files
    fprintf('Loading tracks from files...\n');
    tracks = [];
    loaded_track_nums = [];
    for t = 1:length(target_tracks)
        track_num = target_tracks(t);
        track_file = fullfile(tracks_dir, sprintf('track%d.mat', track_num));
        
        if exist(track_file, 'file')
            data = load(track_file);
            if isfield(data, 'track')
                tracks = [tracks, data.track];
                loaded_track_nums(end+1) = track_num;
                fprintf('  Loaded track %d\n', track_num);
            end
        else
            fprintf('  WARNING: track%d.mat not found\n', track_num);
        end
    end
end

fprintf('Target tracks: %d\n', length(target_tracks));

if isempty(tracks)
    error('No tracks loaded');
end

fprintf('Loaded %d tracks\n\n', length(tracks));

%% Run Segmentation
fprintf('Running segmentation...\n');
eset.expt(1).track = tracks;
try
    eset.executeTrackFunction('setSegmentSpeeds');
    eset.executeTrackFunction('segmentTrack');
    fprintf('Segmentation complete\n\n');
catch ME
    fprintf('Warning: Segmentation failed: %s\n', ME.message);
end

%% Extract experiment name from file
[~, expt_filename, ~] = fileparts(expt_mat_file);
% Try to extract timestamp
match = regexp(expt_filename, '_(\d{12})$', 'tokens');
if ~isempty(match)
    timestamp = match{1}{1};
else
    timestamp = datestr(now, 'yyyymmddHHMMSS');
end

%% Process Each Track
fprintf('Processing tracks...\n');
results = struct();
results.experiment = expt_filename;
results.timestamp = timestamp;
results.lengthPerPixel = lengthPerPixel;
results.target_tracks = loaded_track_nums;
results.total_tracks = length(tracks);
results.tracks_with_reversals = 0;
results.total_reversals = 0;
results.reversal_durations = [];

for t = 1:length(tracks)
    track = tracks(t);
    track_num = loaded_track_nums(t);
    
    fprintf('Processing track %d (%d/%d)...\n', track_num, t, length(tracks));
    
    try
        % Compute reversal detection
        [SpeedRunVel, times, reversals, xpos, ypos, eti] = compute_reversal_detection(track, lengthPerPixel);
        
        % Create output directory for this track
        track_output_dir = fullfile(output_dir, sprintf('track%d', track_num));
        if ~exist(track_output_dir, 'dir')
            mkdir(track_output_dir);
        end
        
        % Save to H5 file
        h5_file = fullfile(track_output_dir, 'track_data.h5');
        save_track_to_h5(h5_file, track_num, SpeedRunVel, times, xpos, ypos, eti, reversals, ...
                         expt_filename, timestamp, lengthPerPixel);
        
        % Update summary
        if ~isempty(reversals)
            results.tracks_with_reversals = results.tracks_with_reversals + 1;
            results.total_reversals = results.total_reversals + length(reversals);
            for r = 1:length(reversals)
                results.reversal_durations(end+1) = reversals(r).duration;
            end
        end
        
        fprintf('  Reversals found: %d\n', length(reversals));
        
    catch ME
        fprintf('  ERROR: %s\n', ME.message);
    end
end

%% Generate Summary Report
fprintf('\n=== Summary ===\n');
fprintf('Total tracks processed: %d\n', results.total_tracks);
fprintf('Tracks with reversals: %d\n', results.tracks_with_reversals);
fprintf('Total reversals: %d\n', results.total_reversals);

if ~isempty(results.reversal_durations)
    fprintf('Average reversal duration: %.2f s\n', mean(results.reversal_durations));
    fprintf('Min reversal duration: %.2f s\n', min(results.reversal_durations));
    fprintf('Max reversal duration: %.2f s\n', max(results.reversal_durations));
end

%% Save summary to JSON
summary_file = fullfile(output_dir, 'analysis_summary.json');
fid = fopen(summary_file, 'w');
fprintf(fid, '{\n');
fprintf(fid, '  "experiment": "%s",\n', results.experiment);
fprintf(fid, '  "timestamp": "%s",\n', results.timestamp);
fprintf(fid, '  "lengthPerPixel": %.6f,\n', lengthPerPixel);
fprintf(fid, '  "target_tracks": [%s],\n', strjoin(arrayfun(@num2str, loaded_track_nums, 'UniformOutput', false), ', '));
fprintf(fid, '  "total_tracks": %d,\n', results.total_tracks);
fprintf(fid, '  "tracks_with_reversals": %d,\n', results.tracks_with_reversals);
fprintf(fid, '  "total_reversals": %d,\n', results.total_reversals);
if ~isempty(results.reversal_durations)
    fprintf(fid, '  "avg_reversal_duration": %.2f,\n', mean(results.reversal_durations));
    fprintf(fid, '  "min_reversal_duration": %.2f,\n', min(results.reversal_durations));
    fprintf(fid, '  "max_reversal_duration": %.2f\n', max(results.reversal_durations));
else
    fprintf(fid, '  "avg_reversal_duration": null,\n');
    fprintf(fid, '  "min_reversal_duration": null,\n');
    fprintf(fid, '  "max_reversal_duration": null\n');
end
fprintf(fid, '}\n');
fclose(fid);

fprintf('\nAnalysis complete! Results saved to: %s\n', output_dir);

end

%% Helper Functions
function [SpeedRunVel, times, reversals, xpos, ypos, eti] = compute_reversal_detection(track, lengthPerPixel)
    eti = track.dq.eti;
    times = eti;
    
    % Extract positions
    pos = track.getDerivedQuantity('sloc');
    xpos = pos(1,:) * lengthPerPixel;
    ypos = pos(2,:) * lengthPerPixel;
    
    % Extract heading vectors
    headpos = track.dq.shead;
    midpos = track.dq.smid;
    HeadVec = headpos - midpos;
    
    % Normalize heading vectors
    HeadUnitVec = zeros(size(HeadVec));
    for k = 1:(size(HeadVec,2))
        norm_val = sqrt(HeadVec(1,k)^2 + HeadVec(2,k)^2);
        if norm_val > 0
            HeadUnitVec(:,k) = HeadVec(:,k) / norm_val;
        end
    end
    
    % Compute velocity vectors and dot product
    num_frames = length(times) - 1;
    SpeedRunVel = zeros(1, num_frames);
    
    dx = xpos(2:end) - xpos(1:end-1);
    dy = ypos(2:end) - ypos(1:end-1);
    dt = times(2:end) - times(1:end-1);
    
    distance = sqrt(dx.^2 + dy.^2);
    speed = distance ./ dt;
    
    VelocityVecx = dx ./ distance;
    VelocityVecy = dy ./ distance;
    
    for o = 1:num_frames
        if distance(o) > 0 && dt(o) > 0
            VelocityVec = [VelocityVecx(o); VelocityVecy(o)];
            dot_product = dot(VelocityVec, HeadUnitVec(:,o));
            SpeedRunVel(o) = speed(o) * dot_product;
        end
    end
    
    % Find reversals > 3 seconds
    reversal_mask = SpeedRunVel < 0;
    reversals = [];
    
    in_reversal = false;
    start_idx = 1;
    start_time = times(1);
    
    for i = 1:length(reversal_mask)
        if reversal_mask(i) && ~in_reversal
            in_reversal = true;
            start_idx = i;
            start_time = times(i);
        elseif ~reversal_mask(i) && in_reversal
            duration = times(i) - start_time;
            if duration >= 3.0
                rev = struct();
                rev.start_time = start_time;
                rev.end_time = times(i);
                rev.duration = duration;
                rev.start_idx = start_idx;
                rev.end_idx = i;
                reversals = [reversals, rev];
            end
            in_reversal = false;
        end
    end
    
    if in_reversal
        duration = times(end) - start_time;
        if duration >= 3.0
            rev = struct();
            rev.start_time = start_time;
            rev.end_time = times(end);
            rev.duration = duration;
            rev.start_idx = start_idx;
            rev.end_idx = length(times);
            reversals = [reversals, rev];
        end
    end
    
    % Trim times to match SpeedRunVel
    times = times(1:end-1);
end

function save_track_to_h5(h5_file, track_num, SpeedRunVel, times, xpos, ypos, eti, reversals, expt_name, timestamp, lengthPerPixel)
    % Delete existing file if present
    if exist(h5_file, 'file')
        delete(h5_file);
    end
    
    % Create and write datasets
    h5create(h5_file, '/track_num', 1);
    h5write(h5_file, '/track_num', track_num);
    
    h5create(h5_file, '/SpeedRunVel', size(SpeedRunVel));
    h5write(h5_file, '/SpeedRunVel', SpeedRunVel);
    
    h5create(h5_file, '/times', size(times));
    h5write(h5_file, '/times', times);
    
    h5create(h5_file, '/xpos', size(xpos));
    h5write(h5_file, '/xpos', xpos);
    
    h5create(h5_file, '/ypos', size(ypos));
    h5write(h5_file, '/ypos', ypos);
    
    h5create(h5_file, '/eti', size(eti));
    h5write(h5_file, '/eti', eti);
    
    % Write attributes
    h5writeatt(h5_file, '/', 'eset_name', expt_name);
    h5writeatt(h5_file, '/', 'expt_name', expt_name);
    h5writeatt(h5_file, '/', 'timestamp', timestamp);
    h5writeatt(h5_file, '/', 'lengthPerPixel', lengthPerPixel);
    
    % Write reversals
    for r = 1:length(reversals)
        rev = reversals(r);
        group_name = sprintf('/reversals/reversal_%d', r);
        h5create(h5_file, [group_name '/start_idx'], 1);
        h5write(h5_file, [group_name '/start_idx'], rev.start_idx);
        h5writeatt(h5_file, group_name, 'start_idx', rev.start_idx);
        h5writeatt(h5_file, group_name, 'end_idx', rev.end_idx);
        h5writeatt(h5_file, group_name, 'start_time', rev.start_time);
        h5writeatt(h5_file, group_name, 'end_time', rev.end_time);
        h5writeatt(h5_file, group_name, 'duration', rev.duration);
    end
end

