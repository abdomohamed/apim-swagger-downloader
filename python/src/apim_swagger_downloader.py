import os
import json
import logging
from datetime import datetime
from azure.identity import DefaultAzureCredential, ClientSecretCredential
from azure.mgmt.apimanagement import ApiManagementClient
from azure.mgmt.apimanagement.models import ExportApi, ExportFormat
from src.config import Config
import requests

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class APIMSwaggerDownloader:
    def __init__(self, config=None):
        """
        Initialize the APIM Swagger Downloader
        
        Args:
            config (Config, optional): Configuration object
        """
        # Load configuration
        self.config = config if config else Config()
        self.apim_settings = self.config.get_apim_settings()
        self.creds = self.config.get_azure_credentials()
        self.output_dirs = self.config.get_output_dirs()
        
        # Ensure output directory exists
        os.makedirs(self.output_dirs['swagger_dir'], exist_ok=True)
        
        # Initialize Azure clients
        self._initialize_clients()
    
    def _initialize_clients(self):
        """Initialize Azure clients for API Management"""
        # Create Azure credential based on configuration
        if self.config.should_use_default_credential():
            logger.info("Using DefaultAzureCredential (current logged-in user via Azure CLI)")
            credential = DefaultAzureCredential()
        else:
            logger.info("Using ClientSecretCredential with provided service principal")
            credential = ClientSecretCredential(
                tenant_id=self.creds['tenant_id'],
                client_id=self.creds['client_id'],
                client_secret=self.creds['client_secret']
            )
        
        # Initialize API Management client
        self.apim_client = ApiManagementClient(
            credential=credential,
            subscription_id=self.apim_settings['subscription_id']
        )
    
    def get_all_apis(self):
        """
        Get all APIs from the APIM instance
        
        Returns:
            list: List of API objects
        """
        logger.info(f"Retrieving APIs from service: {self.apim_settings['service_name']}")
        apis = list(self.apim_client.api.list_by_service(
            resource_group_name=self.apim_settings['resource_group'],
            service_name=self.apim_settings['service_name']
        ))
        logger.info(f"Found {len(apis)} APIs")
        return apis
    
    def download_swagger(self, api):
        """
        Download OpenAPI/Swagger specification for a given API
        
        Args:
            api: The API object
            
        Returns:
            str: Path to the saved swagger file
        """
        api_id = api.name
        api_name = api.display_name or api.name
        
        logger.info(f"Downloading OpenAPI specification for API: {api_name} (ID: {api_id})")
        
        # Get the API's export details in OpenAPI format
        export_result = self.apim_client.api_export.get(
            resource_group_name=self.apim_settings['resource_group'],
            service_name=self.apim_settings['service_name'],
            api_id=api_id,
            format=ExportFormat.SWAGGER,
            export=ExportApi.TRUE
        )
        
        
        
        print(f"Export result: {export_result.additional_properties}")
        
        # Convert response content to dictionary
        if hasattr(export_result, 'additional_properties'):
            swagger_link = export_result.additional_properties['properties']['value']['link']
            response = requests.get(swagger_link)
            response.raise_for_status()
            swagger_content = response.json()
        else:
            raise ValueError("Failed to retrieve swagger content from export result")
        
        # Create clean filename
        safe_name = ''.join(c if c.isalnum() or c in ['-', '_'] else '_' for c in api_name)
        filename = f"{safe_name}_{api_id}.json"
        filepath = os.path.join(self.output_dirs['swagger_dir'], filename)
        
        # Add metadata to the swagger
        if isinstance(swagger_content, dict):
            swagger_content['info'] = swagger_content.get('info', {})
            swagger_content['info']['x-api-id'] = api_id
            swagger_content['info']['x-api-name'] = api_name
            swagger_content['info']['x-downloaded-timestamp'] = datetime.now().isoformat()
            
            # Add API URL information if available
            if hasattr(api, 'service_url') and api.service_url:
                swagger_content['info']['x-api-service-url'] = api.service_url
                
            # Add description if available
            if hasattr(api, 'description') and api.description:
                swagger_content['info']['description'] = api.description
        
        # Save swagger to file
        with open(filepath, 'w') as f:
            json.dump(swagger_content, f, indent=2)
        
        logger.info(f"Saved swagger to {filepath}")
        return filepath
    
    def download_all_swaggers(self):
        """
        Download OpenAPI/Swagger specifications for all APIs
        
        Returns:
            list: Paths to the saved swagger files
        """
        # Get all APIs
        apis = self.get_all_apis()
        
        # Download swagger for each API
        swagger_files = []
        for api in apis:
            try:
                swagger_file = self.download_swagger(api)
                swagger_files.append(swagger_file)
            except Exception as e:
                logger.error(f"Error downloading swagger for API {api.name}: {str(e)}")
        
        logger.info(f"Downloaded {len(swagger_files)} swagger files")
        return swagger_files

if __name__ == "__main__":
    # Create downloader and run
    downloader = APIMSwaggerDownloader()
    swagger_files = downloader.download_all_swaggers()
    
    print(f"\nDownloaded {len(swagger_files)} swagger files to {downloader.output_dirs['swagger_dir']}")
    for file in swagger_files:
        print(f"  - {os.path.basename(file)}")