import click
from cloudestimate.loaders.yaml_loader import load_software_config
from cloudestimate.calculations import calculate_total_resources, calculate_cloud_costs
import os
from datetime import datetime

@click.command()
@click.argument('software_name')
@click.option('--users', default=1000, help='Number of users or agents')
@click.option('--workload', default='medium', help='Workload type (simple, medium, complex)')
@click.option('--activity', default='moderate', help='Activity level (light, moderate, heavy)')
@click.option('--show-resources', is_flag=True, help='Show detailed resource usage (vCPU, memory, storage)')
def cli(software_name, users, workload, activity, show_resources):
    """
    CLI tool for estimating cloud costs for self-managed/hosted software across AWS, GCP, and Azure.
    """
    try:
        # Load the software configuration
        software_config = load_software_config(software_name)

        # Calculate total resources based on inputs
        total_vcpu, total_memory, total_storage = calculate_total_resources(software_config, users, workload, activity)

        # Show resource usage if requested
        if show_resources:
            click.echo(f"\nTotal estimated resources for {users} users, {workload} workload, {activity} activity:")
            click.echo(f"  vCPU: {total_vcpu}")
            click.echo(f"  Memory: {total_memory} GB")
            click.echo(f"  Storage: {total_storage} GB")

        # Get cost estimates for AWS, GCP, and Azure
        click.echo(f"\nEstimated Annual Cloud Costs for {software_name}:")
        for provider in ['aws', 'gcp', 'azure']:
            costs = calculate_cloud_costs(total_vcpu, total_storage, provider)
            click.echo(f"  {provider.upper()}: ${format(costs['total_cost'], ',.2f')} USD per year")

        # Pricing data "as of" date
        pricing_file = os.path.join(os.getcwd(), 'cloudestimate', 'cloud_pricing', f'{provider}_pricing.json')
        if os.path.exists(pricing_file):
            as_of_date = datetime.fromtimestamp(os.path.getmtime(pricing_file)).strftime('%Y-%m-%d')
            click.echo(f"\nPrices are based on data as of {as_of_date}.")

        # Disclaimer
        click.echo("\nDisclaimer: This is just an estimate and actual costs may vary based on factors such as discounts, reserved instances, and real-world usage patterns.")
        click.echo("\nPowered by CloudEstimate - an Open Source Cloud Cost Estimation Tool")

    except FileNotFoundError as e:
        click.echo(f"Error: {e}")
    except Exception as e:
        click.echo(f"Error: {str(e)}")

if __name__ == '__main__':
    cli()
