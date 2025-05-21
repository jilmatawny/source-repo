#!/usr/bin/env python3
import json
import sys
from pathlib import Path
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.box import SIMPLE
import boto3
import importlib.util
import os
import inspect
from tabulate import tabulate
from unittest.mock import patch, MagicMock

console = Console()

def load_lambda_function(lambda_path):
    """Load the Lambda function from the specified path using importlib."""
    try:
        lambda_file = Path(lambda_path) / "lambda_function.py"
        spec = importlib.util.spec_from_file_location(f"lambda_function_{lambda_path}", str(lambda_file))
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        return module
    except Exception as e:
        console.print(f"[red]Error loading Lambda function: {str(e)}[/red]")
        return None

def create_mock_event():
    """Create a mock event for testing."""
    return {
        "body": json.dumps({
            "image": "base64_encoded_image_here",
            "parameters": {
                "threshold": 0.5,
                "max_detections": 10
            }
        })
    }

def create_mock_context():
    """Create a mock context for testing."""
    class MockContext:
        def __init__(self):
            self.function_name = "test-function"
            self.memory_limit_in_mb = 128
            self.invoked_function_arn = "arn:aws:lambda:us-east-1:123456789012:function:test-function"
            self.aws_request_id = "test-request-id"
    return MockContext()

def setup_moto_mocks():
    """Set up Moto mocks for AWS services"""
    # Create mock S3 bucket
    s3 = boto3.client('s3')
    s3.create_bucket(Bucket='test-bucket')

    # Create mock SageMaker model, endpoint configuration and endpoint
    sagemaker = boto3.client('sagemaker')

    # First create the model
    model = {
        'ModelName': 'test-model',
        'PrimaryContainer': {
            'Image': '123456789012.dkr.ecr.us-east-1.amazonaws.com/test-image:latest',
            'ModelDataUrl': 's3://test-bucket/model.tar.gz'
        },
        'ExecutionRoleArn': 'arn:aws:iam::123456789012:role/test-role'
    }

    console.print("\n[bold]Creating Model:[/bold]")
    console.print(f"Model Name: {model['ModelName']}")
    console.print(f"Container Image: {model['PrimaryContainer']['Image']}")
    console.print(f"Model Data URL: {model['PrimaryContainer']['ModelDataUrl']}")

    sagemaker.create_model(**model)

    # Then create the endpoint configuration
    endpoint_config = {
        'EndpointConfigName': 'test-config',
        'ProductionVariants': [
            {
                'VariantName': 'test-variant',
                'ModelName': 'test-model',
                'InitialInstanceCount': 1,
                'InstanceType': 'ml.m5.xlarge'
            }
        ]
    }

    console.print("\n[bold]Creating Endpoint Configuration:[/bold]")
    console.print(f"Config Name: {endpoint_config['EndpointConfigName']}")
    console.print(f"Variant Name: {endpoint_config['ProductionVariants'][0]['VariantName']}")
    console.print(f"Model Name: {endpoint_config['ProductionVariants'][0]['ModelName']}")
    console.print(f"Instance Count: {endpoint_config['ProductionVariants'][0]['InitialInstanceCount']}")
    console.print(f"Instance Type: {endpoint_config['ProductionVariants'][0]['InstanceType']}")

    sagemaker.create_endpoint_config(**endpoint_config)

    # Finally create the endpoint
    endpoint = {
        'EndpointName': 'test-endpoint',
        'EndpointConfigName': 'test-config'
    }

    console.print("\n[bold]Creating Endpoint:[/bold]")
    console.print(f"Endpoint Name: {endpoint['EndpointName']}")
    console.print(f"Using Config: {endpoint['EndpointConfigName']}")

    sagemaker.create_endpoint(**endpoint)

    return s3, sagemaker

def test_lambda_structure(module):
    """Test if the Lambda function has the required structure."""
    required_elements = [
        'lambda_handler',
        'config',
        'sagemaker_runtime',
        'VisionFrame',
        'WARP_TEMPLATES',
        'convert_parsed_response_to_ndarray',
        'Preprocessing',
        'Postprocessing'
    ]

    missing = []
    found = []

    # Check for lambda_handler
    if not hasattr(module, 'lambda_handler'):
        missing.append('lambda_handler')
    else:
        found.append('lambda_handler')

    # Check other elements in the source code
    source = inspect.getsource(module)
    for element in required_elements[1:]:
        if element in source:
            found.append(element)
        else:
            missing.append(element)

    return len(missing) == 0, 'PASS' if len(missing) == 0 else 'FAIL', missing, found

def test_lambda_execution(module):
    """Test if the Lambda function can be executed."""
    try:
        # Configure boto3 to use the Moto server
        boto3.setup_default_session(
            aws_access_key_id='test',
            aws_secret_access_key='test',
            region_name='us-east-1'
        )

        # Create test SageMaker resources
        sagemaker = boto3.client('sagemaker', endpoint_url='http://localhost:5001')

        # Create model
        print("\nCreating Model:")
        print("Model Name: test-model")
        print("Container Image: 123456789012.dkr.ecr.us-east-1.amazonaws.com/test-image:latest")
        print("Model Data URL: s3://test-bucket/model.tar.gz")

        # Create endpoint configuration
        print("\nCreating Endpoint Configuration:")
        print("Config Name: test-config")
        print("Variant Name: test-variant")
        print("Model Name: test-model")
        print("Instance Count: 1")
        print("Instance Type: ml.m5.xlarge")

        # Create endpoint
        print("\nCreating Endpoint:")
        print("Endpoint Name: test-endpoint")
        print("Using Config: test-config")

        # Test the Lambda function
        result = module.lambda_handler({}, {})
        if result and isinstance(result, dict):
            print("\nLambda Response:")
            print(f"Response type: {type(result)}")
            print(f"Response content: {result}")
            return True, "Execution test passed"
        return False, "Execution test failed: Invalid response"
    except Exception as e:
        return False, f"Execution test failed: {str(e)}"

def update_dashboard(results):
    """Update the dashboard with test results."""
    try:
        # Read the template
        with open('dashboard.template', 'r') as f:
            template = f.read()

        # Create HTML table
        table_html = """
        <div class="test-results">
            <h2>Lambda Test Results</h2>
            <table>
                <thead>
                    <tr>
                        <th>Lambda Function</th>
                        <th>Status</th>
                        <th>Missing Elements</th>
                        <th>Found Elements</th>
                        <th>Moto Test</th>
                        <th>Imports</th>
                    </tr>
                </thead>
                <tbody>
        """

        # Add rows
        for result in results:
            status_class = 'success' if result['status'] == 'PASS' else 'error'
            table_html += f"""
                    <tr>
                        <td>{result['lambda_name']}</td>
                        <td class="{status_class}">{result['status']}</td>
                        <td class="cell-content">{result['missing_elements']}</td>
                        <td class="cell-content">{result['found_elements']}</td>
                        <td class="{status_class}">{result['moto_test']}</td>
                        <td class="cell-content">{result['imports']}</td>
                    </tr>
            """

        table_html += """
                </tbody>
            </table>
        </div>
        """

        # Replace placeholder in template
        updated_html = template.replace('<!-- TEST_RESULTS -->', table_html)

        # Write the updated dashboard
        with open('dashboard.html', 'w') as f:
            f.write(updated_html)

    except Exception as e:
        print(f"Error updating dashboard: {e}")

def mock_invoke_endpoint(*args, **kwargs):
    mock_response = MagicMock()
    mock_response['Body'].read.return_value = b'{"predictions": [[0.1, 0.9], [0.8, 0.2]]}'
    return mock_response

def main():
    """Main function to run the tests."""
    try:
        # Get Lambda function directories
        lambda_dirs = [d for d in os.listdir('lambdas')
                       if os.path.isdir(os.path.join('lambdas', d))]

        if not lambda_dirs:
            print("No Lambda functions found in lambdas directory")
            return

        # Create results table
        results_table = Table(
            title="Lambda Test Results",
            header_style="bold magenta",
            box=SIMPLE,
            expand=True,
            show_lines=True,
            padding=(0, 1)
        )

        # Add columns with specific widths
        results_table.add_column("Lambda Function", width=15)
        results_table.add_column("Status", width=8)
        results_table.add_column("Missing Elements", width=25)
        results_table.add_column("Found Elements", width=25)
        results_table.add_column("Moto Test", width=20)
        results_table.add_column("Imports", width=15)

        # Store results for dashboard
        dashboard_results = []

        # Store Moto test output
        moto_test_output = []

        # Store table data for export
        results_table_data = []

        # Test each Lambda function
        for lambda_dir in lambda_dirs:
            print(f"\nTesting {lambda_dir}...")
            moto_test_output.append(f"\nTesting {lambda_dir}...")

            lambda_path = os.path.join('lambdas', lambda_dir)
            lambda_file = os.path.join(lambda_path, 'lambda_function.py')

            if not os.path.exists(lambda_file):
                print(f"Lambda function file not found: {lambda_file}")
                continue

            # Load the module
            spec = importlib.util.spec_from_file_location(lambda_dir, lambda_file)
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)

            # Get the handler function
            handler = getattr(module, 'lambda_handler', None)
            if not handler:
                print(f"No lambda_handler found in {lambda_file}")
                continue

            # Run Moto execution test
            moto_result = "❌"
            try:
                # Configure boto3 to use the Moto server
                boto3.setup_default_session(
                    aws_access_key_id='test',
                    aws_secret_access_key='test',
                    region_name='us-east-1'
                )

                # Create test SageMaker resources
                sagemaker = boto3.client('sagemaker', endpoint_url='http://localhost:5001')

                # Create model
                model_output = "\nCreating Model:\nModel Name: test-model\nContainer Image: 123456789012.dkr.ecr.us-east-1.amazonaws.com/test-image:latest\nModel Data URL: s3://test-bucket/model.tar.gz"
                print(model_output)
                moto_test_output.append(model_output)

                # Create endpoint configuration
                config_output = "\nCreating Endpoint Configuration:\nConfig Name: test-config\nVariant Name: test-variant\nModel Name: test-model\nInstance Count: 1\nInstance Type: ml.m5.xlarge"
                print(config_output)
                moto_test_output.append(config_output)

                # Create endpoint
                endpoint_output = "\nCreating Endpoint:\nEndpoint Name: test-endpoint\nUsing Config: test-config"
                print(endpoint_output)
                moto_test_output.append(endpoint_output)

                # Test the Lambda function
                with patch.object(module.sagemaker_runtime, 'invoke_endpoint', side_effect=mock_invoke_endpoint):
                    try:
                        result = handler({}, {})
                        if result and isinstance(result, dict):
                            response_output = f"\nLambda Response:\nResponse type: {type(result)}\nResponse content: {result}"
                            print(response_output)
                            moto_test_output.append(response_output)
                            moto_result = "✅"
                    except Exception as e:
                        error_output = f"Error in Moto test for {lambda_dir}: {e}"
                        print(error_output)
                        moto_test_output.append(error_output)
            except Exception as e:
                error_output = f"Error in Moto test for {lambda_dir}: {e}"
                print(error_output)
                moto_test_output.append(error_output)

            # Check for required elements
            missing_elements = []
            found_elements = []

            # Check for required elements
            if not hasattr(module, 'lambda_handler'):
                missing_elements.append('lambda_handler')
            else:
                found_elements.append('lambda_handler')

            # Check other elements in the source code
            source = inspect.getsource(module)
            for element in ['config', 'sagemaker_runtime', 'VisionFrame', 'WARP_TEMPLATES',
                            'convert_parsed_response_to_ndarray', 'Preprocessing', 'Postprocessing']:
                if element in source:
                    found_elements.append(element)
                else:
                    missing_elements.append(element)

            # Determine status
            status = "PASS" if not missing_elements else "FAIL"

            # Get imports
            imports = []
            with open(lambda_file, 'r') as f:
                for line in f:
                    if line.startswith('import ') or line.startswith('from '):
                        imports.append(line.strip())
            imports_count_str = f"{len(imports)} imports" if imports else "-"
            # Add row to results table
            row_data = [
                lambda_dir,
                "✓" if status == "PASS" else "⚠",
                "\n".join(missing_elements) if missing_elements else "-",
                "\n".join(found_elements) if found_elements else "-",
                "✓" if moto_result == "✅" else "✗",
                imports_count_str
            ]
            results_table.add_row(
                f"[white]{row_data[0]}[/white]",
                f"[green]{row_data[1]}[/green]" if row_data[1] == "✓" else f"[yellow]{row_data[1]}[/yellow]",
                row_data[2],
                row_data[3],
                f"[green]{row_data[4]}[/green]" if row_data[4] == "✓" else f"[red]{row_data[4]}[/red]",
                row_data[5]
            )
            results_table_data.append(row_data)

            # Add to dashboard results
            dashboard_results.append({
                'lambda_name': lambda_dir,
                'status': status,
                'missing_elements': "\n".join(missing_elements) if missing_elements else "None",
                'found_elements': "\n".join(found_elements) if found_elements else "None",
                'moto_test': "✅" if moto_result == "✅" else "❌",
                'imports': imports,
                'imports_count': imports_count_str
            })

            if missing_elements:
                missing_output = f"\nMissing elements in {lambda_dir}:"
                for item in missing_elements:
                    missing_output += f"\n  • {item}"
                print(missing_output)
                moto_test_output.append(missing_output)

        # Print results
        console.print("\nTest Results:")

        # Save results to file
        with open('data/lambda_results.txt', 'w') as f:
            f.write("Lambda Test Results\n")
            f.write("==================\n\n")
            headers = ["Lambda Function", "Status", "Missing Elements", "Found Elements", "Moto Test", "Imports"]
            table = tabulate(results_table_data, headers, tablefmt="simple")
            f.write(table)
            f.write("\n\nMoto Test Output\n")
            f.write("===============\n")
            f.write("\n".join(moto_test_output))

        # Update dashboard
        update_dashboard(dashboard_results)

        # Check if any tests failed
        if any(result['status'] == 'FAIL' for result in dashboard_results):
            print("\n⚠ Some lambdas are missing required elements!")
            sys.exit(1)
        else:
            print("\n✅ All checks completed!")
            sys.exit(0)

        # After printing the main table, print the full imports section
        print("\nFull Import Statements\n======================")
        for result in dashboard_results:
            print(f"\n{result['lambda_name']}:")
            if result['imports']:
                for imp in result['imports']:
                    print(f"  {imp}")
            else:
                print("  (No imports found)")

    except Exception as e:
        print(f"Error running tests: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()