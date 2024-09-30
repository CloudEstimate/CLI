import json
import os
import traceback
import math

# Function to load pricing data from JSON files
def load_pricing(cloud_provider):
    """Load pricing data from a JSON file based on the cloud provider."""
    try:
        pricing_file = os.path.join(
            os.getcwd(),
            'cloudestimate',
            'cloud_pricing',
            f'{cloud_provider}_pricing.json'
        )
        if not os.path.exists(pricing_file):
            raise FileNotFoundError(f"Pricing file for {cloud_provider} not found at {pricing_file}.")

        with open(pricing_file, 'r') as file:
            return json.load(file)
    except Exception as e:
        print(f"Error loading pricing data for {cloud_provider}: {e}")
        traceback.print_exc()

# Function to calculate resources for fixed components
def calculate_fixed_components(software_config):
    """Calculate fixed components (vCPU, memory, storage)."""
    total_vcpu = 0
    total_memory = 0
    total_storage = 0

    try:
        for component in software_config['software'].get('fixed_components', []):
            if component['type'] == 'compute':
                total_vcpu += component['compute_requirements'].get('vcpu', 0)
                total_memory += component['compute_requirements'].get('memory_gb', 0)
                total_storage += component['compute_requirements'].get('storage_gb', 0)
            elif component['type'] == 'storage':
                total_storage += component['storage_requirements'].get('storage_gb', 0)
    except Exception as e:
        print(f"Error calculating fixed components: {e}")
        traceback.print_exc()

    return total_vcpu, total_memory, total_storage

# Function to calculate variable components
def calculate_variable_components(software_config, users):
    """Calculate variable components based on users and growth nature."""
    total_vcpu = 0
    total_memory = 0
    total_storage = 0

    if users == 0:
        return total_vcpu, total_memory, total_storage  # Return zero for all components if no users

    try:
        growth_nature = software_config['software'].get('variable_growth', 'linear')
        scaling_factor = software_config['software'].get('scaling_factor', 1)

        # Calculate variable growth
        if growth_nature == 'linear':
            user_factor = users * scaling_factor
        elif growth_nature == 'superlinear':
            user_factor = users ** scaling_factor
        elif growth_nature == 'sublinear':
            user_factor = math.sqrt(users) * scaling_factor
        elif growth_nature == 'power':
            user_factor = users ** scaling_factor
        else:
            user_factor = users  # Default to linear if growth type is unknown

        # Loop through variable components
        for component in software_config['software'].get('variable_components', []):
            total_vcpu += user_factor * component.get('average_vcpu_per_user', 0)
            total_memory += user_factor * component.get('average_memory_per_user_gb', 0)
            total_storage += user_factor * component.get('storage_per_user_gb', 0)

    except Exception as e:
        print(f"Error calculating variable components: {e}")
        traceback.print_exc()

    return total_vcpu, total_memory, total_storage

# Function to calculate GPU components (if applicable)
def calculate_gpu_components(software_config):
    """Calculate GPU requirements (number of GPUs and memory)."""
    total_gpus = 0
    total_gpu_memory = 0

    try:
        for component in software_config['software'].get('gpu_requirements', []):
            total_gpus += component['gpu_requirements'].get('gpu_count', 0)
            total_gpu_memory += component['gpu_requirements'].get('gpu_memory_gb', 0)
    except Exception as e:
        print(f"Error calculating GPU components: {e}")
        traceback.print_exc()

    return total_gpus, total_gpu_memory

# Function to combine fixed, variable, and GPU resource calculations
def calculate_total_resources(software_config, users):
    """Combine fixed, variable, and GPU resources."""
    fixed_vcpu, fixed_memory, fixed_storage = calculate_fixed_components(software_config)
    variable_vcpu, variable_memory, variable_storage = calculate_variable_components(software_config, users)
    total_gpus, total_gpu_memory = calculate_gpu_components(software_config)

    total_vcpu = fixed_vcpu + variable_vcpu
    total_memory = fixed_memory + variable_memory
    total_storage = fixed_storage + variable_storage

    return total_vcpu, total_memory, total_storage, total_gpus, total_gpu_memory

# Function to calculate cloud costs including GPU pricing
def calculate_cloud_costs(total_vcpu, total_memory_gb, total_storage_gb, total_gpus, software_config, cloud_provider, users):
    """Calculate the cloud cost for a given provider (AWS, GCP, or Azure)."""
    try:
        pricing_data = load_pricing(cloud_provider)

        # Get compute SKU, storage SKU, and GPU SKU from the YAML config
        compute_sku = next(
            (comp['cloud_skus'][cloud_provider]
             for comp in software_config['software']['fixed_components']
             if comp['type'] == 'compute'),
            None
        )
        storage_sku = next(
            (comp['cloud_skus'][cloud_provider]
             for comp in software_config['software']['fixed_components']
             if comp['type'] == 'storage'),
            None
        )
        gpu_sku = None
        if total_gpus > 0 and 'gpu_requirements' in software_config['software']:
            gpu_sku = software_config['software']['gpu_requirements'][0]['cloud_skus'][cloud_provider]

        # Retrieve pricing and specs from JSON
        price_per_instance_hour = pricing_data['compute'][compute_sku]
        instance_specs = pricing_data['compute_specs'][compute_sku]
        instance_vcpu = instance_specs['vcpu']
        instance_memory = instance_specs['memory_gb']

        price_per_storage_gb_month = pricing_data['storage'][storage_sku]

        # Calculate number of compute instances required
        num_instances_vcpu = math.ceil(total_vcpu / instance_vcpu)
        num_instances_memory = math.ceil(total_memory_gb / instance_memory)
        num_instances = max(num_instances_vcpu, num_instances_memory)

        compute_cost = num_instances * price_per_instance_hour * 24 * 365

        # Calculate storage cost
        storage_cost = total_storage_gb * price_per_storage_gb_month * 12

        # Calculate GPU cost if applicable
        gpu_cost = 0
        if gpu_sku:
            price_per_gpu_hour = pricing_data['gpu'][gpu_sku]
            gpu_instance_specs = pricing_data['compute_specs'][compute_sku]
            gpu_instance_gpu_count = gpu_instance_specs.get('gpu_count', 0)

            if gpu_instance_gpu_count > 0:
                num_gpu_instances = math.ceil(total_gpus / gpu_instance_gpu_count)
                gpu_cost = num_gpu_instances * price_per_gpu_hour * 24 * 365
            else:
                # If the compute instance does not include GPUs, assume GPU pricing is separate
                gpu_cost = total_gpus * price_per_gpu_hour * 24 * 365

        total_cost = compute_cost + storage_cost + gpu_cost

        return {
            'compute_cost': compute_cost,
            'storage_cost': storage_cost,
            'gpu_cost': gpu_cost,
            'total_cost': total_cost
        }

    except Exception as e:
        print(f"Error calculating cloud costs for {cloud_provider}: {e}")
        traceback.print_exc()
        return None

# Function to display cloud costs for AWS, GCP, and Azure
def display_cloud_costs(software_config, total_vcpu, total_memory_gb, total_storage_gb, total_gpus, users):
    """Display cloud costs for each provider."""
    try:
        for cloud_provider in ['aws', 'gcp', 'azure']:
            cloud_costs = calculate_cloud_costs(
                total_vcpu,
                total_memory_gb,
                total_storage_gb,
                total_gpus,
                software_config,
                cloud_provider,
                users
            )

            if cloud_costs:
                print(f"Estimated Annual Cloud Costs for {software_config['software']['name']} ({cloud_provider.upper()}):")
                print(f"  Compute: ${cloud_costs['compute_cost']:.2f} USD per year")
                print(f"  Storage: ${cloud_costs['storage_cost']:.2f} USD per year")
                if cloud_costs['gpu_cost']:
                    print(f"  GPU: ${cloud_costs['gpu_cost']:.2f} USD per year")
                print(f"  Total: ${cloud_costs['total_cost']:.2f} USD per year\n")
            else:
                print(f"Failed to calculate costs for {cloud_provider}.")
    except Exception as e:
        print(f"Error displaying cloud costs: {e}")
        traceback.print_exc()
