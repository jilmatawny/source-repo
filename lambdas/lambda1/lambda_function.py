# Valid lambda with all required elements
config = {}
sagemaker_runtime = {}
WARP_TEMPLATES = {}

class VisionFrame:
    def __init__(self):
        pass

class Preprocessing:
    def __init__(self):
        pass

class Postprocessing:
    def __init__(self):
        pass

def convert_parsed_response_to_ndarray():
    pass

def lambda_handler(event, context):
    return {
        'statusCode': 200,
        'body': 'Hello from Lambda!'
    }
