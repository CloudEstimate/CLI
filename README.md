# CloudEstimate CLI

**CloudEstimate** is an open-source CLI tool that helps you estimate the annual cloud costs for self-managed/hosted software, like GitLab, based on variable workloads and user activity. The CLI retrieves pricing data from major cloud providers (**AWS**, **Google Cloud**, and **Azure**) and generates an estimate based on the number of users, workload complexity, and activity levels.

## Features

-   Estimate annual cloud infrastructure costs for self-managed software like GitLab.
-   Supports AWS, Google Cloud, and Azure cloud providers.
-   Customizable for variable workloads and user activity.
-   Pricing data is regularly updated via JSON files, avoiding the need for static credentials.

## Target Supported Cloud Providers

-   **AWS**
-   **Google Cloud**
-   **Azure**

## Contributing

Contributions are welcome! Please feel free to submit a pull request or open an issue if you encounter any problems or have suggestions for improvements.

## License

This project is licensed under the **MIT License**. See the [LICENSE](LICENSE) file for more details.

## Disclaimer

This tool provides **cost estimates** based on publicly available cloud pricing data. Actual costs may vary depending on factors like:

-   Reserved instances
-   Discounts
-   Usage patterns not covered by the estimation model
-   Cloud provider pricing changes