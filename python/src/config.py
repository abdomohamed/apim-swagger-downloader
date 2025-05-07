import os
import yaml
from dotenv import load_dotenv

class Config:
    def __init__(self, config_path=None):
        """
        Initialize configuration from YAML file and environment variables
        
        Args:
            config_path (str, optional): Path to the config YAML file
        """
        # Load environment variables from .env file if it exists
        load_dotenv()
        
        # Default config path
        if config_path is None:
            config_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 
                                      'config', 'config.yaml')
        
        # Load configuration from YAML
        with open(config_path, 'r') as config_file:
            self.config = yaml.safe_load(config_file)
            
        # Override with environment variables if present
        self._override_with_env_vars()
        
        # Set default values for use_default_credential if not present
        if 'azure' in self.config and 'auth' not in self.config['azure']:
            self.config['azure']['auth'] = {'use_default_credential': True}
        
    def _override_with_env_vars(self):
        """Override configuration with environment variables"""
        # Azure auth settings
        if os.getenv('AZURE_USE_DEFAULT_CREDENTIAL'):
            self.config['azure']['auth'] = {
                'use_default_credential': os.getenv('AZURE_USE_DEFAULT_CREDENTIAL').lower() in ('true', 'yes', '1')
            }
        
        # Azure credentials (only needed if not using default credential)
        if os.getenv('AZURE_TENANT_ID'):
            self.config['azure']['tenant_id'] = os.getenv('AZURE_TENANT_ID')
        if os.getenv('AZURE_CLIENT_ID'):
            self.config['azure']['client_id'] = os.getenv('AZURE_CLIENT_ID')
        if os.getenv('AZURE_CLIENT_SECRET'):
            self.config['azure']['client_secret'] = os.getenv('AZURE_CLIENT_SECRET')
        
        # APIM settings
        if os.getenv('AZURE_SUBSCRIPTION_ID'):
            self.config['azure']['subscription_id'] = os.getenv('AZURE_SUBSCRIPTION_ID')
        if os.getenv('AZURE_RESOURCE_GROUP'):
            self.config['azure']['resource_group'] = os.getenv('AZURE_RESOURCE_GROUP')
        if os.getenv('AZURE_APIM_SERVICE_NAME'):
            self.config['azure']['service_name'] = os.getenv('AZURE_APIM_SERVICE_NAME')
        
        # Azure AI Search settings
        if os.getenv('AZURE_SEARCH_ENDPOINT'):
            self.config['azure']['search']['endpoint'] = os.getenv('AZURE_SEARCH_ENDPOINT')
        if os.getenv('AZURE_SEARCH_KEY'):
            self.config['azure']['search']['key'] = os.getenv('AZURE_SEARCH_KEY')
        if os.getenv('AZURE_SEARCH_INDEX_NAME'):
            self.config['azure']['search']['index_name'] = os.getenv('AZURE_SEARCH_INDEX_NAME')
            
          # API filter settings
        if os.getenv('AZURE_APIM_INCLUDE_APIS'):
            if 'api_filter' not in self.config['azure']:
                self.config['azure']['api_filter'] = {}
            include_apis = os.getenv('AZURE_APIM_INCLUDE_APIS').split(',')
            self.config['azure']['api_filter']['include_apis'] = [api.strip() for api in include_apis]
    
        if os.getenv('AZURE_APIM_INCLUDE_TAGS'):
            if 'api_filter' not in self.config['azure']:
                self.config['azure']['api_filter'] = {}
            include_tags = os.getenv('AZURE_APIM_INCLUDE_TAGS').split(',')
            self.config['azure']['api_filter']['include_tags'] = [tag.strip() for tag in include_tags]
    
    def should_use_default_credential(self):
        """Check if DefaultAzureCredential should be used"""
        if 'azure' in self.config and 'auth' in self.config['azure']:
            return self.config['azure']['auth'].get('use_default_credential', True)
        return True  # Default to using DefaultAzureCredential if not specified
    
    def get_azure_credentials(self):
        """Get Azure credentials for authentication"""
        if not self.should_use_default_credential():
            return {
                'tenant_id': self.config['azure']['tenant_id'],
                'client_id': self.config['azure']['client_id'],
                'client_secret': self.config['azure']['client_secret']
            }
        return {}  # Empty dict since we're using DefaultAzureCredential
    
    def get_apim_settings(self):
        """Get APIM-related settings"""
        settings = {
            'subscription_id': self.config['azure']['subscription_id'],
            'resource_group': self.config['azure']['resource_group'],
            'service_name': self.config['azure']['service_name']
        }
        
        # Add API filter settings if they exist
        if 'api_filter' in self.config['azure']:
            settings['api_filter'] = self.config['azure']['api_filter']
        else:
            settings['api_filter'] = {'include_apis': [], 'include_tags': []}
        
        return settings
    
    def get_search_settings(self):
        """Get Azure Search settings"""
        return self.config['azure']['search']
    
    def get_output_dirs(self):
        """Get output directory settings"""
        return self.config['output']
    
    def get_processing_settings(self):
        """Get processing settings"""
        return self.config['processing']
    
    # Add this method to the Config class
    def get_wiki_settings(self):
        """Get wiki-related settings"""
        if 'wiki' not in self.config:
            self.config['wiki'] = {
                'wiki_dir': 'wiki_documents',
                'wiki_base_url': ''
            }
        return self.config['wiki']