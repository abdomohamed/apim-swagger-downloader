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
            # Use Markitdown to convert the swagger file
            result = self.markitdown.convert(swagger_file_path)
            markdown_content = result.text_content
            
            # Extract API info for additional metadata
            with open(swagger_file_path, 'r') as f:
                swagger_data = json.load(f)
            
            # Extract API info
            info = swagger_data.get('info', {})
            api_title = info.get('title', 'API Documentation')
            api_version = info.get('version', '')
            api_description = info.get('description', '')
            
            # Add custom header with additional metadata
            header = f"# {api_title}\n\n"
            if api_version:
                header += f"**Version**: {api_version}\n\n"
            if api_description:
                header += f"{api_description}\n\n"
                
            # Add download timestamp if available
            if 'x-downloaded-timestamp' in info:
                header += f"*Last updated: {info['x-downloaded-timestamp']}*\n\n"
            
            # Combine header with the generated markdown
            enhanced_markdown = header + markdown_content
                
        except Exception as e:
            logger.error(f"Error converting with Markitdown: {str(e)}")
            logger.info("Falling back to basic Python-based conversion")
            enhanced_markdown = self._python_based_conversion(swagger_file_path)
        
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
        
        # Add API information
        info = swagger.get('info', {})
        title = info.get('title', 'API Documentation')
        version = info.get('version', '')
        description = info.get('description', '')
        
        markdown.append(f"# {title}\n")
        if version:
            markdown.append(f"**Version:** {version}\n")
        if description:
            markdown.append(f"{description}\n")
        
        # Add base URL information
        if 'servers' in swagger and swagger['servers']:
            markdown.append("## Servers\n")
            for server in swagger['servers']:
                url = server.get('url', '')
                description = server.get('description', '')
                markdown.append(f"* {url} - {description}\n")
        
        # Add paths (endpoints)
        if 'paths' in swagger:
            markdown.append("## Endpoints\n")
            
            for path, path_item in swagger['paths'].items():
                markdown.append(f"### {path}\n")
                
                for method, operation in path_item.items():
                    if method in ['get', 'post', 'put', 'delete', 'patch']:
                        summary = operation.get('summary', '')
                        op_description = operation.get('description', '')
                        
                        markdown.append(f"#### {method.upper()}\n")
                        if summary:
                            markdown.append(f"**Summary:** {summary}\n")
                        if op_description:
                            markdown.append(f"{op_description}\n")
                        
                        # Add request parameters
                        if 'parameters' in operation and operation['parameters']:
                            markdown.append("**Parameters:**\n")
                            for param in operation['parameters']:
                                param_name = param.get('name', '')
                                param_in = param.get('in', '')
                                required = 'Required' if param.get('required', False) else 'Optional'
                                param_description = param.get('description', '')
                                
                                markdown.append(f"* `{param_name}` ({param_in}, {required}) - {param_description}\n")
                        
                        # Add request body
                        if 'requestBody' in operation:
                            markdown.append("**Request Body:**\n")
                            content = operation['requestBody'].get('content', {})
                            for content_type, content_schema in content.items():
                                markdown.append(f"Content Type: `{content_type}`\n")
                                # Add example if available
                                if 'example' in content_schema:
                                    markdown.append("Example:\n```json\n")
                                    markdown.append(json.dumps(content_schema['example'], indent=2))
                                    markdown.append("\n```\n")
                        
                        # Add responses
                        if 'responses' in operation:
                            markdown.append("**Responses:**\n")
                            for status_code, response in operation['responses'].items():
                                response_description = response.get('description', '')
                                markdown.append(f"* `{status_code}` - {response_description}\n")
                                
                                # Add example response if available
                                content = response.get('content', {})
                                for content_type, content_schema in content.items():
                                    if 'example' in content_schema:
                                        markdown.append(f"  Example ({content_type}):\n  ```json\n")
                                        markdown.append(json.dumps(content_schema['example'], indent=2))
                                        markdown.append("\n  ```\n")
                
                markdown.append("\n")
        
        # Add components/schemas (data models)
        if 'components' in swagger and 'schemas' in swagger['components']:
            markdown.append("## Models\n")
            
            for schema_name, schema in swagger['components']['schemas'].items():
                markdown.append(f"### {schema_name}\n")
                
                schema_type = schema.get('type', '')
                if schema_type:
                    markdown.append(f"**Type:** {schema_type}\n")
                
                if 'properties' in schema:
                    markdown.append("**Properties:**\n")
                    for prop_name, prop in schema['properties'].items():
                        prop_type = prop.get('type', 'object')
                        prop_description = prop.get('description', '')
                        markdown.append(f"* `{prop_name}` ({prop_type}) - {prop_description}\n")
        
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