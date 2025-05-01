import os
import re
import logging
import hashlib
from datetime import datetime
from azure.identity import DefaultAzureCredential, ClientSecretCredential
from azure.core.credentials import AzureKeyCredential
from azure.search.documents import SearchClient
from azure.search.documents.indexes import SearchIndexClient
from azure.search.documents.indexes.models import (
    SearchIndex, SimpleField, SearchableField, 
    SearchFieldDataType, TextWeights
)
from src.config import Config

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class AzureSearchIndexer:
    def __init__(self, config=None):
        """
        Initialize the Azure AI Search Indexer
        
        Args:
            config (Config, optional): Configuration object
        """
        # Load configuration
        self.config = config if config else Config()
        self.search_settings = self.config.get_search_settings()
        self.creds = self.config.get_azure_credentials()
        self.output_dirs = self.config.get_output_dirs()
        
        # Initialize Azure clients
        self._initialize_clients()
    
    def _initialize_clients(self):
        """Initialize Azure AI Search clients"""
        # Initialize search clients
        endpoint = self.search_settings['endpoint']
        key = self.search_settings['key']
        index_name = self.search_settings['index_name']
        
        # Create Azure credential based on configuration
        if self.config.should_use_default_credential():
            logger.info("Using DefaultAzureCredential (current logged-in user via Azure CLI)")
            credential = DefaultAzureCredential()
        else:
            logger.info("Using ClientSecretCredential with provided service principal")
            credential = AzureKeyCredential(key)
        
        # For managing indexes
        self.index_client = SearchIndexClient(
            endpoint=endpoint,
            credential= credential
        )
        
        # For uploading documents
        self.search_client = SearchClient(
            endpoint=endpoint,
            index_name=index_name,
            credential= credential
        )
    
    def create_search_index(self):
        """
        Create or update the search index
        
        Returns:
            bool: True if successful, False otherwise
        """
        index_name = self.search_settings['index_name']
        logger.info(f"Creating/updating search index: {index_name}")
        
        try:
            # Define the index fields
            fields = [
                SimpleField(name="id", type=SearchFieldDataType.String, key=True),
                SearchableField(name="title", type=SearchFieldDataType.String, 
                                searchable=True, retrievable=True, analyzer_name="en.microsoft"),
                SearchableField(name="content", type=SearchFieldDataType.String, 
                                searchable=True, retrievable=True, analyzer_name="en.microsoft"),
                SimpleField(name="apiName", type=SearchFieldDataType.String, 
                            filterable=True, facetable=True, retrievable=True),
                SimpleField(name="apiVersion", type=SearchFieldDataType.String, 
                            filterable=True, facetable=True, retrievable=True),
                SimpleField(name="documentType", type=SearchFieldDataType.String, 
                            filterable=True, facetable=True, retrievable=True),
                SimpleField(name="lastUpdated", type=SearchFieldDataType.DateTimeOffset, 
                            filterable=True, sortable=True, retrievable=True),
                SimpleField(name="fileName", type=SearchFieldDataType.String, retrievable=True),
                SimpleField(name="fileUrl", type=SearchFieldDataType.String, retrievable=True)
            ]
            
            # Create the index definition
            index = SearchIndex(name=index_name, fields=fields)
            
            # Create or update the index
            result = self.index_client.create_or_update_index(index)
            logger.info(f"Index {result.name} created or updated")
            return True
            
        except Exception as e:
            logger.error(f"Error creating search index: {str(e)}")
            return False
    
    def parse_markdown_file(self, markdown_file_path):
        """
        Parse a markdown file to extract API documentation information
        
        Args:
            markdown_file_path (str): Path to the markdown file
            
        Returns:
            dict: Parsed information from the markdown file
        """
        logger.info(f"Parsing markdown file: {os.path.basename(markdown_file_path)}")
        
        # Read the markdown file
        with open(markdown_file_path, 'r') as f:
            content = f.read()
        
        # Extract title (first level-1 heading)
        title_match = re.search(r'^# (.+)$', content, re.MULTILINE)
        title = title_match.group(1) if title_match else os.path.basename(markdown_file_path)
        
        # Extract API version
        version_match = re.search(r'\*\*Version[:\s]*\*\*\s*(.+)', content)
        version = version_match.group(1) if version_match else ""
        
        # Extract last updated timestamp
        timestamp_match = re.search(r'\*Last updated: ([^*]+)\*', content)
        last_updated = timestamp_match.group(1) if timestamp_match else datetime.now().isoformat()
        
        # Regular expression to match ISO 8601 datetime format
        iso_datetime_match = re.search(r'\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(?:\.\d{3}+)?', last_updated)
        iso_datetime = iso_datetime_match.group(0) + 'Z' if iso_datetime_match else None
        
        # Create a unique ID based on the file content
        file_id = hashlib.md5(content.encode()).hexdigest()
        
        return {
            "id": file_id,
            "title": title,
            "content": content,
            "apiName": title,
            "apiVersion": version,
            "documentType": "API Documentation",
            "lastUpdated": iso_datetime,
            "fileName": os.path.basename(markdown_file_path),
            "fileUrl": f"/{os.path.relpath(markdown_file_path)}"
        }
    
    def index_markdown_files(self, markdown_files=None):
        """
        Index markdown files into Azure AI Search
        
        Args:
            markdown_files (list, optional): List of markdown file paths to index.
                                           If None, will scan the markdown directory.
        
        Returns:
            int: Number of files successfully indexed
        """
        # Create or update the search index
        if not self.create_search_index():
            logger.error("Failed to create search index. Aborting indexing operation.")
            return 0
        
        # If no markdown files provided, scan the directory
        if not markdown_files:
            markdown_dir = self.output_dirs['markdown_dir']
            markdown_files = [
                os.path.join(markdown_dir, f) 
                for f in os.listdir(markdown_dir) 
                if f.endswith('.md')
            ]
        
        # Parse and index each markdown file
        documents = []
        for markdown_file in markdown_files:
            try:
                # Parse the markdown file
                doc = self.parse_markdown_file(markdown_file)
                documents.append(doc)
                
                # Index in batches of 10
                if len(documents) >= 10:
                    self.search_client.upload_documents(documents)
                    logger.info(f"Indexed batch of {len(documents)} documents")
                    documents = []
                    
            except Exception as e:
                logger.error(f"Error indexing {os.path.basename(markdown_file)}: {str(e)}")
        
        # Upload any remaining documents
        if documents:
            self.search_client.upload_documents(documents)
            logger.info(f"Indexed final batch of {len(documents)} documents")
        
        logger.info(f"Indexed {len(markdown_files)} markdown files")
        return len(markdown_files)

if __name__ == "__main__":
    # Create indexer and run
    indexer = AzureSearchIndexer()
    num_indexed = indexer.index_markdown_files()
    
    print(f"\nIndexed {num_indexed} markdown files to Azure AI Search index: {indexer.search_settings['index_name']}")
    print(f"Search endpoint: {indexer.search_settings['endpoint']}")