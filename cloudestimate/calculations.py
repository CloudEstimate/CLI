import json
import os

# Function to load pricing data from JSON files
def load_pricing(cloud_provider):
    """Load pricing data from a JSON file based on the cloud provider."""
    pricing_file = os.path.join(os.getcwd(), 'cloudestimate', 'cloud_pricing', f'{cloud_provider}_pricing.json')

    if not os.path.exists(pricing_file):
        raise FileNotFoundError(f"Pricing file for {cloud_provider} not found at {pricing_file}.")

    with open(pricing_file, 'r') as file:
        return json.load(file)

# Function to calculate resources for fixed components
def calculate_fixed_components(software_config):
    """Calculate fixed components (vCPU, memory, storage)."""
    total_vcpu = 0
    total_memory = 0
    total_storage = 0

    # Loop through fixed components
    for component in software_config['software'].get('fixed_components', []):
        total_vcpu += component['compute_requirements'].get('vcpu', 0)
        total_memory += component['compute_requirements'].get('memory_gb', 0)
        total_storage += component['compute_requirements'].get('storage_gb', 0)

    print(f"Fixed components - vCPU: {total_vcpu}, Memory: {total_memory} GB, Storage: {total_storage} GB")  # Debugging
    return total_vcpu, total_memory, total_storage


# Function to calculate resources for variable components
def calculate_variable_components(software_config, users, workload, activity):
    """Calculate variable components (vCPU, memory, storage) based on users, workload, and activity."""
    total_vcpu = 0
    total_memory = 0
    total_storage = 0

    # Loop through variable components
    for component in software_config['software'].get('variable_components', []):
        usage_profile = component['usage_profiles'].get(workload, {}).get(activity, {})
        total_vcpu += users * usage_profile.get('average_vcpu_per_user', 0)
        total_memory += users * usage_profile.get('average_memory_per_user_gb', 0)
        total_storage += users * usage_profile.get('storage_per_user_gb', 0)

    print(f"Variable components - vCPU: {total_vcpu}, Memory: {total_memory} GB, Storage: {total_storage} GB")  # Debugging
    return total_vcpu, total_memory, total_storage


# Function to combine fixed and variable resource calculations
def calculate_total_resources(software_config, users, workload, activity):
    """Combine fixed and variable resources."""
    fixed_vcpu, fixed_memory, fixed_storage = calculate_fixed_components(software_config)
    variable_vcpu, variable_memory, variable_storage = calculate_variable_components(software_config, users, workload, activity)

    total_vcpu = fixed_vcpu + variable_vcpu
    total_memory = fixed_memory + variable_memory
    total_storage = fixed_storage + variable_storage

    return total_vcpu, total_memory, total_storage

# Function to calculate cloud costs for AWS, GCP, and Azure
def calculate_cloud_costs(total_vcpu, total_storage_gb, cloud_provider):
    """Calculate the cloud cost for a given provider (AWS, GCP, or Azure)."""
    pricing_data = load_pricing(cloud_provider)

    if cloud_provider == 'aws':
        price_per_vcpu_hour = pricing_data['ec2']['c5.2xlarge']
        price_per_gb_month = pricing_data['ebs']['general_purpose_ssd']
    elif cloud_provider == 'gcp':
        price_per_vcpu_hour = pricing_data['compute']['n1-standard-8']
        price_per_gb_month = pricing_data['storage']['persistent_ssd']
    elif cloud_provider == 'azure':
        price_per_vcpu_hour = pricing_data['compute']['F8s_v2']
        price_per_gb_month = pricing_data['storage']['ssd']
    else:
        raise ValueError(f"Unsupported cloud provider: {cloud_provider}")

    # Calculate costs
    compute_cost = total_vcpu * price_per_vcpu_hour * 24 * 365
    storage_cost = total_storage_gb * price_per_gb_month * 12
    total_cost = compute_cost + storage_cost

    return {
        'compute_cost': compute_cost,
        'storage_cost': storage_cost,
        'total_cost': total_cost
    }
