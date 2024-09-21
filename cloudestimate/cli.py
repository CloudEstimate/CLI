import os
import json
import click
from cloudestimate.loaders.yaml_loader import load_software_config

@click.command()
@click.argument('software_name')
@click.option('--users', required=True, type=int, help='Number of users')
@click.option('--workload', required=True, type=click.Choice(['simple', 'medium', 'complex']), help='Workload complexity')
@click.option('--activity', required=True, type=click.Choice(['light', 'moderate', 'heavy']), help='User activity level')
def cli(software_name, users, workload, activity):
    try:
        # Load the configuration file for the specified software
        config = load_software_config(software_name)

        # Calculate total resources
        components = config.get('software', {}).get('components', {})
        variable_components = components.get('variable_components', {})
        usage_profiles = variable_components.get('usage_profiles', {})
        scaling_profile = usage_profiles.get(workload, {}).get(activity, {})
        
        total_vcpu = scaling_profile.get('average_vcpu_per_user', 0) * users
        total_memory_gb = scaling_profile.get('average_memory_per_user_gb', 0) * users
        total_storage_gb = scaling_profile.get('storage_per_user_gb', 0) * users

        click.echo(f"\nTotal estimated resources for {users} users, {workload} workload, {activity} activity:")
        click.echo(f"  vCPU: {total_vcpu}")
        click.echo(f"  Memory: {total_memory_gb} GB")
        click.echo(f"  Storage: {total_storage_gb} GB")

        # Use current working directory for cloud_pricing.json
        pricing_file_path = os.path.join(os.getcwd(), 'cloudestimate/cloud_pricing.json')

        # Load pricing data from the pre-scraped JSON file
        with open(pricing_file_path, 'r') as pricing_file:
            pricing_data = json.load(pricing_file)

        # Example: Fetch AWS pricing from JSON
        region = 'us-east-1'
        instance_type = 'c5.2xlarge'
        ec2_price_per_hour = pricing_data['aws']['regions'][region]['ec2'].get(instance_type, 'N/A')
        ebs_price_per_gb_month = pricing_data['aws']['regions'][region]['ebs'].get('general_purpose_ssd', 'N/A')

        # Calculate annual estimated costs
        if ec2_price_per_hour != 'N/A' and ebs_price_per_gb_month != 'N/A':
            # For simplicity, assume 730 hours/month
            ec2_annual_cost = total_vcpu * ec2_price_per_hour * 730 * 12
            ebs_annual_cost = total_storage_gb * ebs_price_per_gb_month * 12
            total_annual_cost = ec2_annual_cost + ebs_annual_cost

            click.echo(f"\nAnnual estimated cost (AWS, {region}):")
            click.echo(f"  EC2 (vCPU): ${ec2_annual_cost:,.2f} per year")
            click.echo(f"  EBS (Storage): ${ebs_annual_cost:,.2f} per year")
            click.echo(f"  Total Annual Cost: ${total_annual_cost:,.2f} per year")
        else:
            click.echo("\nPricing information not available for the specified region and instance type.")

        # Add a disclaimer
        click.echo("\nDisclaimer: This is just an estimate and actual costs may vary based on factors such as discounts, "
                   "reserved instances, and real-world usage patterns.")

    except Exception as e:
        click.echo(f"Error: {str(e)}")

if __name__ == '__main__':
    cli()
