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
        "name": "text-summarizer-model",
        "container": "123456789012.dkr.ecr.us-east-1.amazonaws.com/text-summarizer:latest",
        "data_url": "s3://test-bucket/model.tar.gz"
    },
    "endpoint": {
        "name": "text-summarizer-endpoint",
        "config_name": "text-summarizer-config",
        "variant_name": "text-summarizer-variant",
        "instance_count": 1,
        "instance_type": "ml.m5.xlarge"
    }
}

class TextFrame:
    """Helper class for text data processing"""
    def __init__(self, text: str):
        self.text = text
    
    def to_dict(self) -> Dict[str, Any]:
        return {"text": self.text}

class Preprocessing:
    """Handles input preprocessing"""
    @staticmethod
    def process_input(data: Dict[str, Any]) -> 'TextFrame':
        try:
            if isinstance(data, dict) and "text" in data:
                return TextFrame(data["text"])
            raise ValueError("Invalid input format")
        except Exception as e:
            logger.error(f"Preprocessing error: {str(e)}")
            raise

class Postprocessing:
    """Handles output postprocessing"""
    @staticmethod
    def process_output(response: Dict[str, Any]) -> Dict[str, Any]:
        try:
            if isinstance(response, dict) and "summary" in response:
                return {
                    "statusCode": 200,
                    "body": json.dumps({
                        "summary": response["summary"],
                        "message": "Successfully processed summary"
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

def convert_parsed_response_to_ndarray(response: Dict[str, Any]) -> List[str]:
    """Convert parsed response to a list of summary sentences"""
    try:
        if isinstance(response, dict) and "summary" in response:
            return [response["summary"]]
        raise ValueError("Invalid response format")
    except Exception as e:
        logger.error(f"Conversion error: {str(e)}")
        raise

# WARP templates for different model types
WARP_TEMPLATES = {
    "text": {
        "input_template": {
            "text": "{{input_text}}"
        },
        "output_template": {
            "summary": "{{summary}}"
        }
    }
}

def lambda_handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    """
    Lambda function handler for text summarization model inference
    """
    try:
        # Log the incoming event
        logger.info(f"Received event: {json.dumps(event)}")
        
        # Parse the input data with better error handling
        try:
            body = json.loads(event.get('body', '{}'))
        except json.JSONDecodeError:
            body = {}
            
        # Use default test data if input is empty or missing 'text'
        if not body or 'text' not in body:
            body = {"text": "This is a long text that needs to be summarized."}
            logger.info(f"Using default test data: {body}")
        
        # Preprocess the input
        preprocessor = Preprocessing()
        text_frame = preprocessor.process_input(body)
        
        # Prepare the request payload
        payload = json.dumps(text_frame.to_dict())
        
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