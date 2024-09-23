import click
from cloudestimate.calculations import calculate_total_resources, display_cloud_costs
import yaml
import os

# Load the YAML configuration for the given software
def load_software_config(software_name):
    try:
        config_file = os.path.join(os.getcwd(), 'cloudestimate', 'config', 'software', f'{software_name}.yaml')

        if not os.path.exists(config_file):
            raise FileNotFoundError(f"Configuration file for {software_name} not found at {config_file}.")

        with open(config_file, 'r') as file:
            config = yaml.safe_load(file)
        return config
    except Exception as e:
        print(f"Error loading software configuration: {e}")
        return None

@click.command()
@click.argument('software_name')
@click.option('--users', default=1000, help='Number of users.')
@click.option('--workload', default='medium', help='Workload type: simple, medium, or complex.')
@click.option('--activity', default='moderate', help='Activity level: light, moderate, or heavy.')
@click.option('--show-resources', is_flag=True, help='Show calculated resources.')
def cli(software_name, users, workload, activity, show_resources):
    """CLI tool to estimate cloud costs for self-managed software."""
    
    # Load the software configuration
    software_config = load_software_config(software_name)

    if software_config is None:
        print(f"Failed to load configuration for {software_name}.")
        return

    # Calculate total resources (fixed + variable)
    total_vcpu, total_memory, total_storage = calculate_total_resources(software_config, users, workload, activity)

    # Optionally show the resources
    if show_resources:
        print(f"Total estimated resources for {users} users, {workload} workload, {activity} activity:")
        print(f"  vCPU: {total_vcpu}")
        print(f"  Memory: {total_memory} GB")
        print(f"  Storage: {total_storage} GB")

    # Minimalist output: Estimated cloud costs with a disclaimer and branding
    print(f"\nEstimated Annual Cloud Costs for {software_name} ({users} users, {workload} workload, {activity} activity):")
    display_cloud_costs(software_config, total_vcpu, total_storage)
    print(f"Prices are based on data as of 2024-09-21.")
    print("\nDisclaimer: This is just an estimate. Actual costs may vary based on factors such as discounts, reserved instances, and real-world usage patterns.")
    print("\nPowered by CloudEstimate - An Open Source Cloud Cost Estimation Tool")

if __name__ == '__main__':
    cli()
