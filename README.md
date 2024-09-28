# CloudEstimate CLI

CloudEstimate CLI is a command-line tool that estimates annual cloud costs across major providers (AWS, GCP, Azure) based on specified software resource requirements and user counts. It helps you plan and budget for cloud deployments by providing detailed cost breakdowns.

Features:

-   Estimates compute, storage, and GPU costs.
-   Supports fixed and variable resource components.
-   Allows customization through YAML configuration files.
-   Includes up-to-date pricing data for AWS, GCP, and Azure.

## Installation

1.  **Clone the Repository:**
    
    `git clone https://www.github.com/CloudEstimate/CLI.git` 
    
2.  **Navigate to the Project Directory and Set Up a Virtual Environment:**
    
    `cd CLI
    python3 -m venv .venv
    source .venv/bin/activate` 
    
3.  **Install the Package:**
    
    `pip install -e .` 
    

## Usage

Run the `cloudestimate` command with the software name and desired options.

**Syntax:**

`cloudestimate <software> [--users <number>] [--show-resources]` 

**Options:**

-   `--users`: Specifies the number of users to calculate variable components. Defaults to 0.
-   `--show-resources`: Displays a detailed breakdown of the estimated resources.

**Examples:**

-   Estimate costs for GitLab with 0 users:
    
    `cloudestimate gitlab --users 0 --show-resources` 
    
-   Estimate costs for GitLab with 1000 users:

    `cloudestimate gitlab --users 1000 --show-resources` 
    

## Adding Software Configurations

To estimate costs for additional software, create a YAML configuration file:

1.  **Create the YAML File:**
    
    Place a new YAML file in the `cloudestimate/config/software/` directory. Name it after your software, e.g., `my_software.yaml`.
    
2.  **Define Software Specifications:**
    
    Include the following sections in your YAML file:
    
    -   `fixed_components`: Define fixed resources like compute and storage.
    -   `variable_components`: Specify per-user resource requirements.
    -   `gpu_requirements` (optional): Include if your software requires GPUs.
    -   `variable_growth`: Set to `linear`, `superlinear`, `sublinear`, or `power`.
    -   `scaling_factor`: A number that influences how variable components scale with users.

## Updating Pricing Data

Pricing data is stored in JSON files within `cloudestimate/cloud_pricing/`:

-   `aws_pricing.json`
-   `gcp_pricing.json`
-   `azure_pricing.json`

**To Update Pricing:**

1.  Open the relevant JSON file.
2.  Update the `compute`, `compute_specs`, `gpu`, and `storage` sections with current pricing and instance specifications.

## Contributing

Contributions are welcome! If you’d like to add new software configurations, improve cloud pricing, or refine the tool, please check out the `CONTRIBUTING.md` for guidelines.

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Maintainer

CloudEstimate was created and is maintained by [Regnard Raquedan](https://github.com/regnard). Feel free to reach out if you have any questions or feedback.