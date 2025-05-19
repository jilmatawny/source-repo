import json
import boto3
import sagemaker
from sagemaker import get_execution_role
from sagemaker.model import Model
from sagemaker.predictor import Predictor
from sagemaker.serializers import JSONSerializer
from sagemaker.deserializers import JSONDeserializer
import numpy as np
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
        "name": "test-model",
        "container": "123456789012.dkr.ecr.us-east-1.amazonaws.com/test-image:latest",
        "data_url": "s3://test-bucket/model.tar.gz"
    },
    "endpoint": {
        "name": "test-endpoint",
        "config_name": "test-config",
        "variant_name": "test-variant",
        "instance_count": 1,
        "instance_type": "ml.m5.xlarge"
    }
}

class VisionFrame:
    """Helper class for vision data processing"""
    def __init__(self, data: np.ndarray):
        self.data = data
    
    def to_dict(self) -> Dict[str, Any]:
        return {"data": self.data.tolist()}

class Preprocessing:
    """Handles input preprocessing"""
    @staticmethod
    def process_input(data: Dict[str, Any]) -> VisionFrame:
        try:
            # Convert input data to numpy array
            if isinstance(data, dict) and "data" in data:
                array_data = np.array(data["data"])
                return VisionFrame(array_data)
            raise ValueError("Invalid input format")
        except Exception as e:
            logger.error(f"Preprocessing error: {str(e)}")
            raise

class Postprocessing:
    """Handles output postprocessing"""
    @staticmethod
    def process_output(response: Dict[str, Any]) -> Dict[str, Any]:
        try:
            # Process the model response
            if isinstance(response, dict) and "predictions" in response:
                return {
                    "statusCode": 200,
                    "body": json.dumps({
                        "predictions": response["predictions"],
                        "message": "Successfully processed predictions"
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

def convert_parsed_response_to_ndarray(response: Dict[str, Any]) -> np.ndarray:
    """Convert parsed response to numpy array"""
    try:
        if isinstance(response, dict) and "predictions" in response:
            return np.array(response["predictions"])
        raise ValueError("Invalid response format")
    except Exception as e:
        logger.error(f"Conversion error: {str(e)}")
        raise

# WARP templates for different model types
WARP_TEMPLATES = {
    "vision": {
        "input_template": {
            "data": "{{input_data}}"
        },
        "output_template": {
            "predictions": "{{predictions}}"
        }
    }
}

def lambda_handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    """
    Lambda function handler for SageMaker model inference
    """
    try:
        # Log the incoming event
        logger.info(f"Received event: {json.dumps(event)}")
        
        # Parse the input data with better error handling
        try:
            body = json.loads(event.get('body', '{}'))
        except json.JSONDecodeError:
            body = {}
            
        # Use default test data if input is empty or missing 'data'
        if not body or 'data' not in body:
            body = {"data": [[1, 2, 3], [4, 5, 6]]}
            logger.info(f"Using default test data: {body}")
        
        # Preprocess the input
        preprocessor = Preprocessing()
        vision_frame = preprocessor.process_input(body)
        
        # Prepare the request payload
        payload = json.dumps(vision_frame.to_dict())
        
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