# CloudEstimate

**CloudEstimate** is an open-source CLI tool designed to help you estimate cloud costs for self-hosted software deployments. Whether you're managing your own GitLab, Nvidia, or other software setups on AWS, GCP, or Azure, CloudEstimate provides a fast and straightforward way to calculate potential cloud expenses.

## Key Features

-   Supports multiple cloud providers (AWS, GCP, Azure).
-   Estimates cloud costs based on CPU, memory, storage, and GPU usage.
-   Built-in configurations for common software like GitLab, Nvidia, and more.
-   Extensible through custom YAML configurations for other software.

## Installation

To get started with CloudEstimate, clone the repository and set up a virtual environment:

    git clone https://github.com/CloudEstimate/CLI.git
    cd CLI
    python3 -m venv .venv
    source .venv/bin/activate
    pip install -r requirements.txt 

## Usage

You can estimate cloud costs using a simple CLI command. For example, to estimate the cost for deploying GitLab for 1000 users with a medium workload:

    cloudestimate gitlab --users 1000 --workload medium --activity moderate 

### Example Output

    Estimated Annual Cloud Costs for GitLab (AWS):
      Compute: $80,732.16 USD per year
      Storage: $13,200.00 USD per year
      Total: $93,932.16 USD per year 

## Supported Software

-   **GitLab** – Fully configurable for CI/CD runners.
-   **Nvidia** – Includes GPU and memory pricing for high-performance workloads.
-   **Ubuntu, RHEL, Debian, Windows Server** – Default configurations for common OS deployments.

## How It Works

CloudEstimate leverages YAML configuration files for each software package, making it easy to update or extend the tool for new software. The tool supports fixed and variable resource requirements, as well as GPU pricing.

### Pricing Sources

-   AWS: Uses on-demand pricing for compute, storage, and GPU resources.
-   GCP: Reflects current prices for standard and GPU-enabled instances.
-   Azure: Includes pricing for standard and specialized VM instances.

## Contributing

Contributions are welcome! If you’d like to add new software configurations, improve cloud pricing, or refine the tool, please check out the `CONTRIBUTING.md` for guidelines.

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Maintainer

CloudEstimate was created and is maintained by [Regnard Raquedan](https://github.com/regnardraquedan). Feel free to reach out if you have any questions or feedback.