#!/usr/bin/env python3
import argparse
from setup_experiments import main as setup_main
from submit_jobs import main as submit_main
from create_visualizations import main as visualize_main


def main():
    parser = argparse.ArgumentParser(description="Run the full WRF autoencoder experiment workflow.")
    parser.add_argument('--setup', action='store_true', help='Set up experiment directories')
    parser.add_argument('--submit', action='store_true', help='Submit jobs')
    parser.add_argument('--visualize', action='store_true', help='Create visualizations')
    parser.add_argument('--all', action='store_true', help='Run all steps in order')
    args = parser.parse_args()

    if args.all or args.setup:
        print("Setting up experiments...")
        setup_main()
    if args.all or args.submit:
        print("Submitting jobs...")
        submit_main()
    if args.all or args.visualize:
        print("Creating visualizations...")
        visualize_main()

if __name__ == '__main__':
    main() 