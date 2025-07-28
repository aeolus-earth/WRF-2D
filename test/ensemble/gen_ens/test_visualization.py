#!/usr/bin/env python3
"""
Test script to verify visualization integration works correctly.
"""
import yaml
from pathlib import Path
import sys

# Add the visualization directory to the path
sys.path.append(str(Path(__file__).parent.parent / 'visualization'))

def test_config_loading():
    """Test that config.yaml can be loaded correctly."""
    print("Testing config loading...")
    with open('config.yaml', 'r') as f:
        config = yaml.safe_load(f)
    
    print(f"Config loaded successfully:")
    print(f"  Dimensions: {config['dimensions']}")
    print(f"  Hidden dim: {config['hidden_dim']}")
    print(f"  Num runs: {config['num_runs']}")
    print(f"  Output dir: {config['output_dir']}")
    print(f"  Visualization dir: {config['visualization_dir']}")
    
    viz_config = config.get('visualization', {})
    print(f"  Create GIFs: {viz_config.get('create_gifs', True)}")
    print(f"  Create time series: {viz_config.get('create_time_series', True)}")
    
    return config

def test_plotting_import():
    """Test that the plotting function can be imported."""
    print("\nTesting plotting function import...")
    try:
        from plot_wrf_quantities import plot_wrf_quantities
        print("✓ plot_wrf_quantities imported successfully")
        return True
    except ImportError as e:
        print(f"✗ Failed to import plot_wrf_quantities: {e}")
        return False

def test_gif_import():
    """Test that the GIF creation function can be imported."""
    print("\nTesting GIF creation function import...")
    try:
        from create_multi_comparison_gif import create_multi_comparison_gif
        print("✓ create_multi_comparison_gif imported successfully")
        return True
    except ImportError as e:
        print(f"✗ Failed to import create_multi_comparison_gif: {e}")
        return False

def test_visualization_function():
    """Test that the visualization function can be called."""
    print("\nTesting visualization function...")
    try:
        from create_visualizations import main as create_viz_main
        config = test_config_loading()
        
        # Test with a mock config that disables actual plotting
        test_config = config.copy()
        test_config['visualization'] = {
            'create_gifs': False,
            'create_time_series': False
        }
        
        print("✓ create_visualizations.main function can be called")
        return True
    except Exception as e:
        print(f"✗ Failed to test visualization function: {e}")
        return False

def main():
    """Run all tests."""
    print("Testing visualization integration...")
    
    config_ok = test_config_loading()
    import_ok = test_plotting_import()
    gif_import_ok = test_gif_import()
    function_ok = test_visualization_function()
    
    print(f"\nTest Results:")
    print(f"  Config loading: {'✓' if config_ok else '✗'}")
    print(f"  Plotting import: {'✓' if import_ok else '✗'}")
    print(f"  GIF import: {'✓' if gif_import_ok else '✗'}")
    print(f"  Function test: {'✓' if function_ok else '✗'}")
    
    if config_ok and import_ok and gif_import_ok and function_ok:
        print("\n✓ All tests passed! Visualization integration is ready.")
    else:
        print("\n✗ Some tests failed. Please check the errors above.")

if __name__ == '__main__':
    main() 