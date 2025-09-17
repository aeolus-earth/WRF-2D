#!/usr/bin/env python3
"""
Create multiple restart runs from run0001 at different time points.
This script will:
1. Copy run0001 to new directories with time suffixes
2. Modify namelist files to set the correct start times
3. Submit WRF jobs for each restart run
"""
import yaml
import shutil
import subprocess
from pathlib import Path
import re
from datetime import datetime, timedelta


def parse_namelist_time(time_str):
    """Parse time string in format 'YYYY-MM-DD_HH:MM:SS' to datetime object."""
    return datetime.strptime(time_str, '%Y-%m-%d_%H:%M:%S')


def format_namelist_time(dt):
    """Format datetime object to namelist time string."""
    return dt.strftime('%Y-%m-%d_%H:%M:%S')


def create_namelist_from_template(template_path, output_path, start_time, end_time, nprocs=1):
    """Create namelist file from template with variable substitution."""
    
    # Read template
    with open(template_path, 'r') as f:
        template_content = f.read()
    
    # Calculate run duration
    duration = end_time - start_time
    run_minutes = int(duration.total_seconds() // 60)
    run_seconds = int(duration.total_seconds() % 60)
    
    # Prepare variable substitutions
    variables = {
        'start_year': start_time.year,
        'start_month': start_time.month,
        'start_day': start_time.day,
        'start_hour': start_time.hour,
        'start_minute': start_time.minute,
        'start_second': start_time.second,
        'end_year': end_time.year,
        'end_month': end_time.month,
        'end_day': end_time.day,
        'end_hour': end_time.hour,
        'end_minute': end_time.minute,
        'end_second': end_time.second,
        'run_minutes': run_minutes,
        'run_seconds': run_seconds,
        'nprocs': nprocs
    }
    
    # Perform variable substitution
    content = template_content
    for var_name, var_value in variables.items():
        content = content.replace(f'${{{var_name}}}', str(var_value))
    
    # Write output namelist
    with open(output_path, 'w') as f:
        f.write(content)


def create_restart_runs(config, base_run=None, time_points=None, end_time_minutes=None, submit_jobs=None, output_suffix=None):
    """
    Create restart runs from a base run at specified time points.
    
    Args:
        config: Configuration dictionary
        base_run: Base run directory name (overrides config if provided)
        time_points: List of time offsets in minutes from start (overrides config if provided)
        end_time_minutes: End time in minutes from start (all runs end at this time)
        submit_jobs: Whether to submit jobs (overrides config if provided)
        output_suffix: Suffix for output directory (overrides config if provided)
    """
    # Get settings from config
    restart_config = config.get('restart_runs', {})
    
    if base_run is None:
        base_run = restart_config.get('base_run', 'run0001')
    if time_points is None:
        time_points = restart_config.get('time_points', [0, 5, 10, 15, 20])
    if end_time_minutes is None:
        end_time_minutes = restart_config.get('end_time_minutes', 90)
    if submit_jobs is None:
        submit_jobs = restart_config.get('submit_jobs', True)
    if output_suffix is None:
        output_suffix = restart_config.get('output_suffix', 'restart')
    
    wrf_dir = Path(config['wrf_dir']).absolute()
    output_dir = Path(config['output_dir'])
    
    # Determine source and destination directories
    source_dir = Path(base_run) if Path(base_run).is_absolute() else output_dir / "full_simulation" / base_run
    dest_parent = output_dir / f"full_simulation_{output_suffix}"
    
    if not source_dir.exists():
        print(f"Error: Base run directory {source_dir} does not exist!")
        return False
    
    # Get the original start time from the base run's namelist
    base_namelist = source_dir / "namelist.input"
    if not base_namelist.exists():
        print(f"Error: Namelist file {base_namelist} does not exist!")
        return False
    
    # Read original start time from namelist
    with open(base_namelist, 'r') as f:
        content = f.read()
    
    # Extract start time from namelist (look for the first domain's start time)
    start_match = re.search(r'start_year\s*=\s*(\d+),\s*(\d+),\s*(\d+),\s*start_month\s*=\s*(\d+),\s*(\d+),\s*(\d+),\s*start_day\s*=\s*(\d+),\s*(\d+),\s*(\d+),\s*start_hour\s*=\s*(\d+),\s*(\d+),\s*(\d+),\s*start_minute\s*=\s*(\d+),\s*(\d+),\s*(\d+),\s*start_second\s*=\s*(\d+),\s*(\d+),\s*(\d+)', content)
    if not start_match:
        print("Error: Could not parse start time from namelist!")
        print("Namelist content preview:")
        print(content[:500])
        return False
    
    # Use the first domain's start time (first set of values)
    original_start = datetime(
        int(start_match.group(1)), int(start_match.group(4)), int(start_match.group(7)),
        int(start_match.group(10)), int(start_match.group(13)), int(start_match.group(16))
    )
    
    print(f"Original start time: {original_start}")
    print(f"Creating restart runs at time points: {time_points} minutes")
    print(f"All runs will end at: {end_time_minutes} minutes")
    print(f"Output directory: {dest_parent}")
    
    # Create destination parent directory
    dest_parent.mkdir(exist_ok=True)
    
    # Get template namelist path
    template_path = wrf_dir / 'test' / 'ensemble' / 'arch' / 'template_restart.namelist'
    if not template_path.exists():
        print(f"Warning: Template namelist {template_path} not found, using original namelist parsing")
        use_template = False
    else:
        use_template = True
        print(f"Using template namelist: {template_path}")
    
    # Create restart runs
    for time_offset in time_points:
        # Calculate restart time
        restart_time = original_start + timedelta(minutes=time_offset)
        end_time = original_start + timedelta(minutes=end_time_minutes)
        
        # Calculate duration for this specific run
        run_duration = end_time_minutes - time_offset
        
        # Create directory name with time suffix
        time_suffix = restart_time.strftime("%H:%M")
        new_run_name = f"{base_run.split('/')[-1]}_{time_suffix.replace(':', '')}"
        new_run_dir = dest_parent / new_run_name
        
        print(f"\nCreating restart run: {new_run_name}")
        print(f"  Restart time: {restart_time}")
        print(f"  End time: {end_time}")
        print(f"  Duration: {run_duration} minutes")
        print(f"  Directory: {new_run_dir}")
        
        # Copy base run directory
        if new_run_dir.exists():
            print(f"  Warning: Directory {new_run_dir} already exists, skipping...")
            continue
        
        print(f"  Copying {source_dir} to {new_run_dir}...")
        shutil.copytree(source_dir, new_run_dir, symlinks=True)
        
        # Create/modify namelist file
        new_namelist = new_run_dir / "namelist.input"
        print(f"  Creating namelist: {new_namelist}")
        
        if use_template:
            create_namelist_from_template(template_path, new_namelist, restart_time, end_time)
        else:
            # Fallback to regex replacement
            modify_namelist_file(new_namelist, restart_time, end_time)
        
        # Submit WRF job if requested
        if submit_jobs:
            submit_script = wrf_dir / 'test' / 'ensemble' / 'submit_wrf_no_namelist.sh'
            if submit_script.exists():
                print(f"  Submitting job for {new_run_dir}")
                try:
                    subprocess.run(['sbatch', str(submit_script), str(new_run_dir), str(wrf_dir)], 
                                 cwd=new_run_dir, check=True)
                    print(f"  Job submitted successfully")
                except subprocess.CalledProcessError as e:
                    print(f"  Error submitting job: {e}")
            else:
                print(f"  Warning: Submit script {submit_script} not found!")
        else:
            print(f"  Skipping job submission (submit_jobs=False)")
    
    print(f"\nCreated {len(time_points)} restart runs successfully!")
    return True


def modify_namelist_file(namelist_path, start_time, end_time):
    """Modify namelist file to set start and end times (fallback method)."""
    with open(namelist_path, 'r') as f:
        content = f.read()
    
    # Replace start and end times
    # Pattern: start_year = 2001, start_month = 01, start_day = 01, start_hour = 00, start_minute = 00, start_second = 00
    start_pattern = r'start_year\s*=\s*\d+,\s*start_month\s*=\s*\d+,\s*start_day\s*=\s*\d+,\s*start_hour\s*=\s*\d+,\s*start_minute\s*=\s*\d+,\s*start_second\s*=\s*\d+'
    end_pattern = r'end_year\s*=\s*\d+,\s*end_month\s*=\s*\d+,\s*end_day\s*=\s*\d+,\s*end_hour\s*=\s*\d+,\s*end_minute\s*=\s*\d+,\s*end_second\s*=\s*\d+'
    
    # Create new start time string
    start_str = f"start_year = {start_time.year}, start_month = {start_time.month:02d}, start_day = {start_time.day:02d}, start_hour = {start_time.hour:02d}, start_minute = {start_time.minute:02d}, start_second = {start_time.second:02d}"
    end_str = f"end_year = {end_time.year}, end_month = {end_time.month:02d}, end_day = {end_time.day:02d}, end_hour = {end_time.hour:02d}, end_minute = {end_time.minute:02d}, end_second = {end_time.second:02d}"
    
    # Replace in content
    content = re.sub(start_pattern, start_str, content)
    content = re.sub(end_pattern, end_str, content)
    
    # Write back to file
    with open(namelist_path, 'w') as f:
        f.write(content)


def main():
    """Main function to handle command line arguments and run the script."""
    import argparse
    
    parser = argparse.ArgumentParser(description='Create restart runs from a base run')
    parser.add_argument('--config', type=str, default='config.yaml', help='Path to config file')
    parser.add_argument('--base-run', type=str, help='Base run directory name (overrides config)')
    parser.add_argument('--time-points', nargs='+', type=int, 
                       help='Time points in minutes from start (overrides config)')
    parser.add_argument('--end-time', type=int, 
                       help='End time in minutes for all restart runs (overrides config)')
    parser.add_argument('--submit-jobs', action='store_true', 
                       help='Submit jobs after creating directories (overrides config)')
    parser.add_argument('--no-submit-jobs', action='store_true', 
                       help='Do not submit jobs (overrides config)')
    parser.add_argument('--output-suffix', type=str, 
                       help='Suffix for output directory (overrides config)')
    
    args = parser.parse_args()
    
    # Load config
    with open(args.config, 'r') as f:
        config = yaml.safe_load(f)
    
    # Check if restart runs are enabled
    restart_config = config.get('restart_runs', {})
    if not restart_config.get('enabled', False) and not any([args.base_run, args.time_points, args.end_time]):
        print("Restart runs are disabled in config. Set 'restart_runs.enabled: true' or provide command line arguments.")
        return
    
    # Determine submit_jobs setting
    submit_jobs = None
    if args.submit_jobs:
        submit_jobs = True
    elif args.no_submit_jobs:
        submit_jobs = False
    
    # Create restart runs
    success = create_restart_runs(
        config=config,
        base_run=args.base_run,
        time_points=args.time_points,
        end_time_minutes=args.end_time,
        submit_jobs=submit_jobs,
        output_suffix=args.output_suffix
    )
    
    if not success:
        import sys
        sys.exit(1)


if __name__ == '__main__':
    main() 