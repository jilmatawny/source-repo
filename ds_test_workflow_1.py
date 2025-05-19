#!/usr/bin/env python3
import click
import ast
import sys
from pathlib import Path
from rich.console import Console
from rich.table import Table
from rich.panel import Panel

class LambdaStructureChecker:
    def __init__(self):
        self.console = Console()
        self.required_elements = [
            'config',
            'sagemaker_runtime',
            'VisionFrame',
            'WARP_TEMPLATES',
            'convert_parsed_response_to_ndarray',
            'Preprocessing',
            'Postprocessing',
            'lambda_handler'
        ]

    def check_structure(self, lambda_file: Path) -> dict:
        """Check if lambda function follows required structure"""
        result = {
            'status': 'success',
            'missing': [],
            'found': [],
            'imports': set()
        }

        try:
            with open(lambda_file, 'r') as f:
                tree = ast.parse(f.read())

            found_elements = set()
            for node in ast.walk(tree):
                if isinstance(node, (ast.FunctionDef, ast.ClassDef)):
                    found_elements.add(node.name)
                elif isinstance(node, ast.Assign):
                    for target in node.targets:
                        if isinstance(target, ast.Name):
                            found_elements.add(target.id)
                elif isinstance(node, ast.Import):
                    for name in node.names:
                        result['imports'].add(name.name)
                elif isinstance(node, ast.ImportFrom):
                    if node.module:
                        result['imports'].add(node.module)

            result['found'] = list(found_elements)
            result['missing'] = list(set(self.required_elements) - found_elements)

            if result['missing']:
                result['status'] = 'warning'

        except Exception as e:
            result['status'] = 'error'
            result['missing'].append(f'Error: {str(e)}')

        return result

def scan_lambda_directories(root_dir: Path) -> dict:
    """Scan for lambda functions in subdirectories"""
    results = {}

    for path in root_dir.iterdir():
        if path.is_dir():
            lambda_file = path.joinpath('lambda_function.py')
            if lambda_file.exists():
                results[path.name] = lambda_file

    return results

@click.command()
@click.argument('root_dir', type=click.Path(exists=True))
@click.option('--strict', is_flag=True, default=False, help='Exit with error if checks fail')
@click.option('--json', 'json_output', is_flag=True, default=False, help='Output in JSON format')
def main(root_dir: str, strict: bool, json_output: bool):
    """Check Lambda functions structure in the given directory"""
    console = Console()
    checker = LambdaStructureChecker()
    root_path = Path(root_dir)

    console.print(Panel.fit("🔍 Checking Lambda Functions Structure", style="bold blue"))

    # Find all lambda functions
    lambda_files = scan_lambda_directories(root_path)

    if not lambda_files:
        console.print(f"[red]No lambda functions found in {root_dir}[/red]")
        sys.exit(1)

    # Create results table
    table = Table(show_header=True)
    table.add_column("Lambda Function", style="cyan")
    table.add_column("Status", style="bold")
    table.add_column("Missing Elements", style="yellow")
    table.add_column("Found Elements", style="green")
    table.add_column("Imports", style="blue")

    has_warnings = False
    has_errors = False

    for lambda_name, lambda_file in lambda_files.items():
        result = checker.check_structure(lambda_file)

        status_style = {
            'success': '[green]✓[/green]',
            'warning': '[yellow]⚠[/yellow]',
            'error': '[red]✗[/red]'
        }.get(result['status'], '')

        table.add_row(
            lambda_name,
            status_style,
            '\n'.join(result['missing']) if result['missing'] else '-',
            '\n'.join(result['found']) if result['found'] else '-',
            '\n'.join(result['imports']) if result['imports'] else '-'
        )

        if result['status'] == 'warning':
            has_warnings = True
        elif result['status'] == 'error':
            has_errors = True

    console.print(table)

    if has_errors:
        console.print("[red]❌ Some lambdas have errors![/red]")
        sys.exit(1)
    elif has_warnings and strict:
        console.print("[yellow]⚠ Some lambdas are missing required elements![/yellow]")
        sys.exit(1)
    else:
        console.print("[green]✅ All checks completed![/green]")
        sys.exit(0)

if __name__ == '__main__':
    main()
