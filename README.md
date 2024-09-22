# CloudEstimate CLI

**CloudEstimate** is an open-source CLI tool designed to estimate the annual cloud cost for self-managed/hosted software across multiple cloud service providers (CSPs), including AWS, GCP, and Azure. The tool helps users calculate cloud infrastructure costs based on the number of users, workload complexity, and activity level.

## Features

-   **Cloud Service Providers Supported**:
    
    -   **AWS**
    -   **Google Cloud (GCP)**
    -   **Microsoft Azure**
-   **Supported Software in this Version**:
    
    -   **GitLab**
    -   **Ubuntu**
    -   **Debian**
    -   **Red Hat Enterprise Linux (RHEL)**
    -   **Windows Server**
-   **Key Features**:
    
    -   Provides cloud cost estimates based on user count, workload complexity, and activity level.
    -   Optionally shows detailed resource usage (vCPU, memory, and storage).
    -   Cost estimates include compute (vCPU) and storage across AWS, GCP, and Azure.
    -   Flexible YAML configurations for each software, easily extendable for additional software.

## Installation

Clone the repository and install the required dependencies:

    git clone https://github.com/CloudEstimate/CLI.git
    cd CLI
    pip install -r requirements.txt 

## Usage

Run the CLI tool to estimate cloud costs:

    cloudestimate <software_name> --users <number_of_users> --workload <workload_type> --activity <activity_level>

### Example:

    cloudestimate gitlab --users 1000 --workload medium --activity moderate

### Options:

-   `--users`: The number of users or agents (default: 1000).
-   `--workload`: The type of workload: `simple`, `medium`, or `complex`.
-   `--activity`: The activity level: `light`, `moderate`, or `heavy`.
-   `--show-resources`: Option to display detailed resource usage (vCPU, memory, storage).

### Example with resource display:

    cloudestimate ubuntu --users 500 --workload medium --activity moderate --show-resources

## YAML Configurations

Each supported software has its own YAML file defining its resource requirements. These YAML files are stored in the `config/software` directory.

Example `gitlab.yaml` configuration:

    software:
      name: "GitLab"
      description: "Self-managed GitLab instance with CI/CD capabilities."
      fixed_components:
        - name: "Primary Compute Unit"
          type: "compute"
          compute_requirements:
            vcpu: 8
            memory_gb: 16
            storage_gb: 500
      variable_components:
        - name: "CI/CD Runners"
          type: "variable-compute"
          user_inputs:
            users: 1000
            workload: "medium"
            activity: "moderate"
          usage_profiles:
            medium:
              moderate:
                average_vcpu_per_user: 0.05
                average_memory_per_user_gb: 0.2
                storage_per_user_gb: 10

You can modify these YAML files or create new ones to support additional software.

## License

CloudEstimate is licensed under the **MIT License**.

## Contributing

Contributions are welcome! Please check the `CONTRIBUTING.md` file for guidelines.

## Disclaimer

This is just an estimate, and actual costs may vary based on factors such as discounts, reserved instances, and real-world usage patterns.