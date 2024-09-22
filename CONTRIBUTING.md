# Contributing to CloudEstimate

Hi! 👋 I’m **Regnard Raquedan**, and I’m thrilled that you’re interested in contributing to **CloudEstimate**. This project is open source, and we encourage contributions from the community. Whether you want to improve existing software configs or add new ones, your help is greatly appreciated!

## How to Contribute

### 1. Fork the Repository

-   First, fork this repository to your own GitHub account and clone the project to your local machine.

    `git clone https://github.com/<your-username>/CLI.git` 

### 2. Work on Software Configs

We're specifically looking for contributions to the software YAML configuration files for different self-managed/hosted applications. Each software’s resource usage (vCPU, memory, storage) should reflect real-world deployment scenarios across cloud platforms (AWS, GCP, Azure).

#### Steps:

-   Navigate to the `config/software/` directory.
-   Create or modify YAML files for software you'd like to contribute to.
-   Make sure to define **fixed** and **variable** resource components as seen in the existing configurations (e.g., `gitlab.yaml`, `ubuntu.yaml`).

### 3. Submit a Pull Request

Once you're satisfied with your changes, submit a pull request (PR) to the **main** branch. We’ll review it as soon as possible!

### YAML Contribution Example:

    software:
      name: "YourSoftware"
      description: "Brief description of the software."
      fixed_components:
        - name: "Primary Compute Unit"
          type: "compute"
          compute_requirements:
            vcpu: 4
            memory_gb: 16
            storage_gb: 200
      variable_components:
        - name: "Additional Load"
          type: "variable-compute"
          user_inputs:
            users: 1000
            workload: "medium"
            activity: "moderate"
          usage_profiles:
            medium:
              light:
                average_vcpu_per_user: 0.02
                average_memory_per_user_gb: 0.1
                storage_per_user_gb: 5 

### Code of Conduct

Be kind, collaborative, and respectful. All contributions are welcome, regardless of skill level.

## Questions?

You are welcome to open an issue if you have any questions. Thanks for your interest, and happy coding! 🚀