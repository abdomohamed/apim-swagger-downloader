import os
import json
import logging
import tempfile
from markitdown import MarkItDown
from src.config import Config

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class SwaggerToMarkdownConverter:
    def __init__(self, config=None):
        """
        Initialize the Swagger to Markdown converter
        
        Args:
            config (Config, optional): Configuration object
        """
        # Load configuration
        self.config = config if config else Config()
        self.output_dirs = self.config.get_output_dirs()
        
        # Ensure output directory exists
        os.makedirs(self.output_dirs['markdown_dir'], exist_ok=True)
        
        # Initialize Markitdown converter
        self.markitdown = MarkItDown(enable_plugins=False)
    
    def convert_swagger_to_markdown(self, swagger_file_path):
        """
        Convert a Swagger/OpenAPI file to Markdown using Markitdown
        
        Args:
            swagger_file_path (str): Path to the swagger file
            
        Returns:
            str: Path to the generated markdown file
        """
        file_basename = os.path.basename(swagger_file_path)
        api_name = os.path.splitext(file_basename)[0]
        markdown_file = os.path.join(self.output_dirs['markdown_dir'], f"{api_name}.md")
        
        logger.info(f"Converting {file_basename} to Markdown using Markitdown")
        
        try:
            # # Use Markitdown to convert the swagger file
            # result = self.markitdown.convert(swagger_file_path)
            # markdown_content = result.text_content
            
            # # Extract API info for additional metadata
            # with open(swagger_file_path, 'r') as f:
            #     swagger_data = json.load(f)
            
            # # Extract API info
            # info = swagger_data.get('info', {})
            # api_title = info.get('title', 'API Documentation')
            # api_version = info.get('version', '')
            # api_description = info.get('description', '')
            
            # # Add custom header with additional metadata
            # header = f"# {api_title}\n\n"
            # if api_version:
            #     header += f"**Version**: {api_version}\n\n"
            # if api_description:
            #     header += f"{api_description}\n\n"
                
            # # Add download timestamp if available
            # if 'x-downloaded-timestamp' in info:
            #     header += f"*Last updated: {info['x-downloaded-timestamp']}*\n\n"
            
            # # Combine header with the generated markdown
            # enhanced_markdown = header + markdown_content
            enhanced_markdown = self._python_based_conversion(swagger_file_path)
        except Exception as e:
            logger.error(f"Error converting with Markitdown: {str(e)}")
            logger.info("Falling back to basic Python-based conversion")
            
        
        # Save the enhanced markdown
        with open(markdown_file, 'w') as f:
            f.write(enhanced_markdown)
        
        logger.info(f"Saved markdown to {markdown_file}")
        return markdown_file
    
    def _python_based_conversion(self, swagger_file_path):
        """
        Basic Python-based conversion of Swagger to Markdown as a fallback
        
        Args:
            swagger_file_path (str): Path to the swagger file
            
        Returns:
            str: Markdown content
        """
        # Load the swagger file
        with open(swagger_file_path, 'r') as f:
            swagger = json.load(f)
        
        # Create basic markdown content
        markdown = []
        
        # Title
        title = swagger.get('info', {}).get('title', 'API Documentation')
        markdown.append(f"# {title}")
        markdown.append("")
        
        # Description
        description = swagger.get('info', {}).get('description', '')
        if description:
            markdown.append(description)
            markdown.append("")
        
        # Add version information
        version = swagger.get('info', {}).get('version', '')
        if version:
            markdown.append(f"**Version:** {version}")
            markdown.append("")
        
        # Base URL
        servers = swagger.get('servers', [])
        if servers:
            markdown.append("## Base URL")
            for server in servers:
                markdown.append(f"* {server.get('url', '')}")
                if server.get('description'):
                    markdown.append(f"  * {server.get('description')}")
            markdown.append("")
        
        # Authentication
        security_schemes = swagger.get('components', {}).get('securitySchemes', {})
        if security_schemes:
            markdown.append("## Authentication")
            for name, scheme in security_schemes.items():
                markdown.append(f"### {name}")
                markdown.append(f"**Type:** {scheme.get('type', '')}")
                
                if scheme.get('description'):
                    markdown.append(f"\n{scheme.get('description')}")
                    
                if scheme.get('type') == 'http':
                    markdown.append(f"**Scheme:** {scheme.get('scheme', '')}")
                    
                if scheme.get('bearerFormat'):
                    markdown.append(f"**Bearer Format:** {scheme.get('bearerFormat', '')}")
                    
                markdown.append("")
        
        # Endpoints by tag
        tags = {}
        
        # Group operations by tags
        for path, path_item in swagger.get('paths', {}).items():
            for method, operation in path_item.items():
                if method in ['get', 'post', 'put', 'delete', 'patch']:
                    operation_tags = operation.get('tags', ['default'])
                    for tag in operation_tags:
                        if tag not in tags:
                            tags[tag] = []
                        tags[tag].append((path, method, operation))
        
        # Generate markdown for each tag
        for tag_name, operations in tags.items():
            markdown.append(f"## {tag_name}")
            
            # Find tag description if available
            tag_description = ""
            for tag in swagger.get('tags', []):
                if tag.get('name') == tag_name and tag.get('description'):
                    tag_description = tag.get('description')
                    break
            
            if tag_description:
                markdown.append(f"{tag_description}")
                markdown.append("")
            
            # Generate documentation for each endpoint
            for path, method, operation in operations:
                operation_id = operation.get('operationId', f"{method} {path}")
                summary = operation.get('summary', operation_id)
                
                markdown.append(f"### {summary}")
                markdown.append("")
                
                if operation.get('description'):
                    markdown.append(operation.get('description'))
                    markdown.append("")
                
                # Endpoint information
                markdown.append("```")
                markdown.append(f"{method.upper()} {path}")
                markdown.append("```")
                markdown.append("")
                
                # Parameters
                parameters = operation.get('parameters', [])
                if parameters:
                    markdown.append("#### Parameters")
                    markdown.append("")
                    markdown.append("| Name | In | Type | Required | Description |")
                    markdown.append("|------|----|----|----------|-------------|")
                    
                    for param in parameters:
                        name = param.get('name', '')
                        param_in = param.get('in', '')
                        required = "Yes" if param.get('required', False) else "No"
                        
                        # Get the type
                        param_type = "object"
                        if 'schema' in param:
                            param_type = param['schema'].get('type', 'object')
                            if param_type == 'array' and 'items' in param['schema']:
                                items_type = param['schema']['items'].get('type', 'object')
                                param_type = f"array of {items_type}"
                        
                        description = param.get('description', '').replace('\n', '<br>')
                        
                        markdown.append(f"| {name} | {param_in} | {param_type} | {required} | {description} |")
                    
                    markdown.append("")
                
                # Request Body
                if 'requestBody' in operation:
                    markdown.append("#### Request Body")
                    markdown.append("")
                    
                    request_body = operation['requestBody']
                    if request_body.get('description'):
                        markdown.append(request_body.get('description'))
                        markdown.append("")
                    
                    content = request_body.get('content', {})
                    for content_type, content_schema in content.items():
                        markdown.append(f"**Content Type:** `{content_type}`")
                        markdown.append("")
                        
                        schema = content_schema.get('schema', {})
                        if '$ref' in schema:
                            ref_name = schema['$ref'].split('/')[-1]
                            markdown.append(f"Schema: {ref_name}")
                            
                            # Try to find the schema definition
                            component_schema = swagger.get('components', {}).get('schemas', {}).get(ref_name, {})
                            if component_schema:
                                # Add example if available
                                if 'example' in content_schema:
                                    markdown.append("**Example:**")
                                    markdown.append("```json")
                                    markdown.append(json.dumps(content_schema['example'], indent=2))
                                    markdown.append("```")
                                elif 'example' in component_schema:
                                    markdown.append("**Example:**")
                                    markdown.append("```json")
                                    markdown.append(json.dumps(component_schema['example'], indent=2))
                                    markdown.append("```")
                        
                        # Add example if available at content level
                        elif 'example' in content_schema:
                            markdown.append("**Example:**")
                            markdown.append("```json")
                            markdown.append(json.dumps(content_schema['example'], indent=2))
                            markdown.append("```")
                    
                    markdown.append("")
                
                # Responses
                markdown.append("#### Responses")
                markdown.append("")
                
                responses = operation.get('responses', {})
                for status_code, response in responses.items():
                    markdown.append(f"**Status Code:** {status_code}")
                    
                    if response.get('description'):
                        markdown.append(f"**Description:** {response.get('description')}")
                    
                    content = response.get('content', {})
                    for content_type, content_schema in content.items():
                        markdown.append(f"**Content Type:** `{content_type}`")
                        
                        schema = content_schema.get('schema', {})
                        if '$ref' in schema:
                            ref_name = schema['$ref'].split('/')[-1]
                            markdown.append(f"Schema: {ref_name}")
                            
                            # Add example if available
                            if 'example' in content_schema:
                                markdown.append("**Example:**")
                                markdown.append("```json")
                                markdown.append(json.dumps(content_schema['example'], indent=2))
                                markdown.append("```")
                    
                    markdown.append("")
        
        return "\n".join(markdown)
    
    def convert_all_swagger_files(self, swagger_files=None):
        """
        Convert all swagger files to markdown
        
        Args:
            swagger_files (list, optional): List of swagger file paths to convert.
                                           If None, will scan the swagger directory.
        
        Returns:
            list: Paths to the generated markdown files
        """
        # If no swagger files provided, scan the directory
        if not swagger_files:
            swagger_dir = self.output_dirs['swagger_dir']
            swagger_files = [
                os.path.join(swagger_dir, f) 
                for f in os.listdir(swagger_dir) 
                if f.endswith('.json') or f.endswith('.yaml') or f.endswith('.yml')
            ]
        
        # Convert each swagger file
        markdown_files = []
        for swagger_file in swagger_files:
            try:
                markdown_file = self.convert_swagger_to_markdown(swagger_file)
                markdown_files.append(markdown_file)
            except Exception as e:
                logger.error(f"Error converting {os.path.basename(swagger_file)} to markdown: {str(e)}")
        
        logger.info(f"Generated {len(markdown_files)} markdown files")
        return markdown_files

if __name__ == "__main__":
    # Create converter and run
    converter = SwaggerToMarkdownConverter()
    markdown_files = converter.convert_all_swagger_files()
    
    print(f"\nConverted {len(markdown_files)} swagger files to markdown in {converter.output_dirs['markdown_dir']}")
    for file in markdown_files:
        print(f"  - {os.path.basename(file)}")