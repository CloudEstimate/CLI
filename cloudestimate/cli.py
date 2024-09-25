import click
import yaml
import os
from cloudestimate.calculations import calculate_total_resources, display_cloud_costs

# Load the YAML configuration file for the given software
def load_software_config(software_name):
    base_path = os.path.join(os.getcwd(), 'cloudestimate', 'config', 'software')
    file_path = os.path.join(base_path, f"{software_name}.yaml")

    if not os.path.exists(file_path):
        raise FileNotFoundError(f"Configuration file for {software_name} not found at {file_path}.")

    with open(file_path, 'r') as file:
        return yaml.safe_load(file)

@click.command()
@click.argument('software')
@click.option('--users', default=1000, help='Number of users.')
@click.option('--workload', default='medium', type=click.Choice(['simple', 'medium', 'complex']), help='Type of workload.')
@click.option('--activity', default='moderate', type=click.Choice(['light', 'moderate', 'heavy']), help='Level of activity.')
@click.option('--show-resources', is_flag=True, help='Show detailed resource breakdown.')
def cli(software, users, workload, activity, show_resources):
    """Estimate cloud costs for the given software based on user input."""
    
    software_config = load_software_config(software)
    
    total_vcpu, total_memory, total_storage, total_gpus, total_gpu_memory = calculate_total_resources(software_config, users, workload, activity)

    if show_resources:
        print(f"Total estimated resources for {users} users, {workload} workload, {activity} activity:")
        print(f"  vCPU: {total_vcpu}")
        print(f"  Memory: {total_memory} GB")
        print(f"  Storage: {total_storage} GB")
        if total_gpus:
            print(f"  GPUs: {total_gpus}")
            print(f"  GPU Memory: {total_gpu_memory} GB")

    # Display cloud costs
    display_cloud_costs(software_config, total_vcpu, total_storage, total_gpus)

if __name__ == '__main__':
    cli()
