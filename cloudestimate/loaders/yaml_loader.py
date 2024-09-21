import yaml
import os

def load_software_config(software_name):
    """
    Loads the YAML configuration file for the given software.

    :param software_name: Name of the software (used as the file name).
    :return: Parsed YAML configuration as a dictionary.
    :raises FileNotFoundError: If the configuration file is not found.
    :raises ValueError: If the YAML file contains syntax errors.
    """
    # Construct the file path relative to the current working directory
    base_path = os.path.join(os.getcwd(), 'cloudestimate', 'config', 'software')
    file_path = os.path.join(base_path, f"{software_name}.yaml")

    # Check if the file exists
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"Configuration file for {software_name} not found at {file_path}.")

    # Load and parse the YAML file
    try:
        with open(file_path, 'r') as file:
            config = yaml.safe_load(file)
        return config
    except yaml.YAMLError as e:
        raise ValueError(f"Error parsing YAML file for {software_name}: {e}")
