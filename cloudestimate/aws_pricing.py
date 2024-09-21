import boto3
import json

def get_aws_pricing(region, instance_type):
    """
    Fetches the pricing for EC2 instances and EBS volumes from AWS Pricing API.
    
    :param region: AWS region (e.g., 'us-east-1')
    :param instance_type: EC2 instance type (e.g., 'c5.2xlarge')
    :return: Pricing details as a dictionary.
    """
    pricing_client = boto3.client('pricing', region_name='us-east-1')  # Pricing is global, but 'us-east-1' is used for API
    pricing_info = {}

    # Get EC2 instance pricing
    ec2_filter = [
        {'Field': 'serviceCode', 'Type': 'TERM_MATCH', 'Value': 'AmazonEC2'},
        {'Field': 'instanceType', 'Type': 'TERM_MATCH', 'Value': instance_type},
        {'Field': 'location', 'Type': 'TERM_MATCH', 'Value': get_aws_region_name(region)},  # Convert region code to name
    ]

    ec2_prices = pricing_client.get_products(ServiceCode='AmazonEC2', Filters=ec2_filter)
    ec2_price = extract_price_from_response(ec2_prices, 'OnDemand')
    pricing_info['ec2'] = ec2_price

    # Get EBS pricing
    ebs_filter = [
        {'Field': 'serviceCode', 'Type': 'TERM_MATCH', 'Value': 'AmazonEC2'},
        {'Field': 'productFamily', 'Type': 'TERM_MATCH', 'Value': 'Storage'},
        {'Field': 'location', 'Type': 'TERM_MATCH', 'Value': get_aws_region_name(region)},
        {'Field': 'volumeType', 'Type': 'TERM_MATCH', 'Value': 'General Purpose'}  # You can specify other volume types here
    ]

    ebs_prices = pricing_client.get_products(ServiceCode='AmazonEC2', Filters=ebs_filter)
    ebs_price = extract_price_from_response(ebs_prices, 'OnDemand')
    pricing_info['ebs'] = ebs_price

    return pricing_info


def get_aws_region_name(region_code):
    """
    Converts AWS region code (e.g., 'us-east-1') to region name (e.g., 'US East (N. Virginia)').
    
    :param region_code: AWS region code
    :return: Human-readable region name
    """
    region_mapping = {
        'us-east-1': 'US East (N. Virginia)',
        'us-west-1': 'US West (N. California)',
        'us-west-2': 'US West (Oregon)',
        # Add more mappings as needed
    }
    return region_mapping.get(region_code, region_code)


def extract_price_from_response(response, term_type):
    """
    Extracts the price from the AWS Pricing API response.
    
    :param response: The response from the AWS Pricing API.
    :param term_type: Pricing term type (e.g., 'OnDemand', 'Reserved').
    :return: Price in USD.
    """
    for price_item in response['PriceList']:
        price_details = json.loads(price_item)
        if term_type in price_details['terms']:
            price_dimension = list(price_details['terms'][term_type].values())[0]['priceDimensions']
            for dimension in price_dimension.values():
                return float(dimension['pricePerUnit']['USD'])  # Returning price in USD
    return None