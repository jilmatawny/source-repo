import json
import boto3
import sagemaker
from sagemaker import get_execution_role
from sagemaker.model import Model
from sagemaker.predictor import Predictor
from sagemaker.serializers import JSONSerializer
from sagemaker.deserializers import JSONDeserializer
from typing import Dict, Any, List, Union
import logging

# Configure logging
logger = logging.getLogger()
logger.setLevel(logging.INFO)

# Initialize AWS clients
sagemaker_runtime = boto3.client('sagemaker-runtime')
sagemaker_client = boto3.client('sagemaker')

# Configuration dictionary
config = {
    "model": {
        "name": "number-doubler-model",
        "container": "123456789012.dkr.ecr.us-east-1.amazonaws.com/number-doubler:latest",
        "data_url": "s3://test-bucket/model.tar.gz"
    },
    "endpoint": {
        "name": "number-doubler-endpoint",
        "config_name": "number-doubler-config",
        "variant_name": "number-doubler-variant",
        "instance_count": 1,
        "instance_type": "ml.m5.xlarge"
    }
}

class NumberFrame:
    """Helper class for number data processing"""
    def __init__(self, number: float):
        self.number = number
    
    def to_dict(self) -> Dict[str, Any]:
        return {"number": self.number}

class Preprocessing:
    """Handles input preprocessing"""
    @staticmethod
    def process_input(data: Dict[str, Any]) -> 'NumberFrame':
        try:
            if isinstance(data, dict) and "number" in data:
                return NumberFrame(float(data["number"]))
            raise ValueError("Invalid input format")
        except Exception as e:
            logger.error(f"Preprocessing error: {str(e)}")
            raise

class Postprocessing:
    """Handles output postprocessing"""
    @staticmethod
    def process_output(response: Dict[str, Any]) -> Dict[str, Any]:
        try:
            if isinstance(response, dict) and "doubled" in response:
                return {
                    "statusCode": 200,
                    "body": json.dumps({
                        "doubled": response["doubled"],
                        "message": "Successfully doubled the number"
                    })
                }
            raise ValueError("Invalid response format")
        except Exception as e:
            logger.error(f"Postprocessing error: {str(e)}")
            return {
                "statusCode": 500,
                "body": json.dumps({
                    "error": f"Postprocessing error: {str(e)}"
                })
            }

def convert_parsed_response_to_ndarray(response: Dict[str, Any]) -> List[float]:
    """Convert parsed response to a list containing the doubled number"""
    try:
        if isinstance(response, dict) and "doubled" in response:
            return [response["doubled"]]
        raise ValueError("Invalid response format")
    except Exception as e:
        logger.error(f"Conversion error: {str(e)}")
        raise

# WARP templates for different model types
WARP_TEMPLATES = {
    "number": {
        "input_template": {
            "number": "{{input_number}}"
        },
        "output_template": {
            "doubled": "{{doubled}}"
        }
    }
}

def lambda_handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    """
    Lambda function handler for number doubling model inference
    """
    try:
        # Log the incoming event
        logger.info(f"Received event: {json.dumps(event)}")
        
        # Parse the input data with better error handling
        try:
            body = json.loads(event.get('body', '{}'))
        except json.JSONDecodeError:
            body = {}
            
        # Use default test data if input is empty or missing 'number'
        if not body or 'number' not in body:
            body = {"number": 21}
            logger.info(f"Using default test data: {body}")
        
        # Preprocess the input
        preprocessor = Preprocessing()
        number_frame = preprocessor.process_input(body)
        
        # Prepare the request payload
        payload = json.dumps(number_frame.to_dict())
        
        # Get the endpoint name from config
        endpoint_name = config["endpoint"]["name"]
        
        # Invoke the SageMaker endpoint
        response = sagemaker_runtime.invoke_endpoint(
            EndpointName=endpoint_name,
            ContentType='application/json',
            Body=payload
        )
        
        # Parse the response
        response_body = json.loads(response['Body'].read().decode())
        
        # Postprocess the response
        postprocessor = Postprocessing()
        result = postprocessor.process_output(response_body)
        
        return result
        
    except Exception as e:
        logger.error(f"Error in lambda_handler: {str(e)}")
        return {
            "statusCode": 500,
            "body": json.dumps({
                "error": f"Internal server error: {str(e)}"
            })
        } 