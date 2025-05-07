import os
import re
import logging
import json
import hashlib
from datetime import datetime
from pathlib import Path
from azure.identity import DefaultAzureCredential, ClientSecretCredential
from azure.search.documents import SearchClient
from src.config import Config

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class WikiDocumentProcessor:
    def __init__(self, config=None):
        """
        Initialize the Wiki Document Processor
        
        Args:
            config (Config, optional): Configuration object
        """
        # Load configuration
        self.config = config if config else Config()
        self.search_settings = self.config.get_search_settings()
        self.wiki_settings = self.config.get_wiki_settings()
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
            credential = ClientSecretCredential(
                tenant_id=self.config.get_azure_credentials()['tenant_id'],
                client_id=self.config.get_azure_credentials()['client_id'],
                client_secret=self.config.get_azure_credentials()['client_secret']
            )
        
        # For uploading documents
        self.search_client = SearchClient(
            endpoint=endpoint,
            index_name=index_name,
            credential=credential,
            api_key=key
        )
    
    def process_wiki_documents(self, wiki_root_dir=None):
        """
        Process wiki documents and upload them to Azure AI Search
        
        Args:
            wiki_root_dir (str, optional): Root directory containing wiki documents
                                          If None, uses the configured directory
        
        Returns:
            int: Number of documents processed
        """
        # Use configured wiki directory if not provided
        if not wiki_root_dir:
            wiki_root_dir = self.wiki_settings.get('wiki_dir', 'wiki_documents')
        
        if not os.path.exists(wiki_root_dir):
            logger.error(f"Wiki directory not found: {wiki_root_dir}")
            return 0
        
        logger.info(f"Processing wiki documents from: {wiki_root_dir}")
        
        # Track all processed documents
        processed_docs = []
        
        # Walk through the directory structure
        api_designs = {}
        api_builds = {}
        
        # First pass: identify and categorize design and build documents
        for root, _, files in os.walk(wiki_root_dir):
            for file in files:
                if not file.lower().endswith('.md'):
                    continue
                
                file_path = os.path.join(root, file)
                rel_path = os.path.relpath(file_path, wiki_root_dir)
                
                # Extract service name from the path
                path_parts = Path(rel_path).parts
                if len(path_parts) < 1:
                    continue
                
                service_name = self._extract_service_name(file_path, path_parts)
                
                # Categorize as design or build document
                if 'design' in file.lower() or 'design' in rel_path.lower():
                    if service_name not in api_designs:
                        api_designs[service_name] = []
                    api_designs[service_name].append(file_path)
                    
                if 'build' in file.lower() or 'build' in rel_path.lower():
                    if service_name not in api_builds:
                        api_builds[service_name] = []
                    api_builds[service_name].append(file_path)
        
        # Second pass: combine design and build documents for each service
        for service_name in set(list(api_designs.keys()) + list(api_builds.keys())):
            design_docs = api_designs.get(service_name, [])
            build_docs = api_builds.get(service_name, [])
            
            # Process this service's documents
            doc = self._process_service_documents(service_name, design_docs, build_docs)
            if doc:
                processed_docs.append(doc)
        
        # Upload documents in batches
        if processed_docs:
            self._upload_documents_to_search(processed_docs)
            
        logger.info(f"Processed {len(processed_docs)} wiki documents")
        return len(processed_docs)
    
    def _extract_service_name(self, file_path, path_parts):
        """
        Extract service name from file path or content
        
        Args:
            file_path (str): Path to the markdown file
            path_parts (list): Parts of the relative path
            
        Returns:
            str: Service name
        """
        # First try to extract from path
        if len(path_parts) > 1:
            # The first directory usually contains the service name
            service_name = path_parts[0]
            
            # Clean up service name
            service_name = service_name.replace('-', ' ').replace('_', ' ')
            return service_name
        
        # If couldn't extract from path, try to find in content
        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
            content = f.read()
            
            # Look for "Service: NAME" or "API: NAME" patterns
            service_match = re.search(r'[Ss]ervice:\s*([^\n]+)', content)
            if service_match:
                return service_match.group(1).strip()
                
            api_match = re.search(r'[Aa][Pp][Ii]:\s*([^\n]+)', content)
            if api_match:
                return api_match.group(1).strip()
            
            # Try to use the title as a fallback
            title_match = re.search(r'^#\s+(.+)$', content, re.MULTILINE)
            if title_match:
                return title_match.group(1).strip()
        
        # Use filename as last resort
        return os.path.splitext(os.path.basename(file_path))[0]
    
    def _process_service_documents(self, service_name, design_docs, build_docs):
        """
        Process and combine design and build documents for a service
        
        Args:
            service_name (str): Service name
            design_docs (list): List of design document paths
            build_docs (list): List of build document paths
            
        Returns:
            dict: Document to be indexed
        """
        logger.info(f"Processing documents for service: {service_name}")
        
        combined_content = f"# {service_name}\n\n"
        document_url = ""
        
        # Process design documents
        if design_docs:
            combined_content += "## Design Documentation\n\n"
            for doc_path in design_docs:
                with open(doc_path, 'r', encoding='utf-8', errors='ignore') as f:
                    content = f.read()
                    
                    # Extract content without the title (we've already added it)
                    lines = content.split('\n')
                    if lines and lines[0].startswith('# '):
                        lines = lines[1:]
                    doc_content = '\n'.join(lines)
                    combined_content += doc_content + "\n\n"
                
                # Use the path of the first design document for the URL
                if not document_url:
                    rel_path = os.path.relpath(doc_path, self.wiki_settings.get('wiki_dir', 'wiki_documents'))
                    document_url = self._construct_document_url(rel_path)
        
        # Process build documents
        if build_docs:
            combined_content += "## Build Documentation\n\n"
            for doc_path in build_docs:
                with open(doc_path, 'r', encoding='utf-8', errors='ignore') as f:
                    content = f.read()
                    
                    # Extract content without the title
                    lines = content.split('\n')
                    if lines and lines[0].startswith('# '):
                        lines = lines[1:]
                    doc_content = '\n'.join(lines)
                    combined_content += doc_content + "\n\n"
        
        # If no design docs (for URL), use the first build doc
        if not document_url and build_docs:
            rel_path = os.path.relpath(build_docs[0], self.wiki_settings.get('wiki_dir', 'wiki_documents'))
            document_url = self._construct_document_url(rel_path)
        
        # Create a unique ID based on service name
        doc_id = f"wiki-{hashlib.md5(service_name.encode()).hexdigest()}"
        
        # Create the document
        return {
            "id": doc_id,
            "title": service_name,
            "content": combined_content,
            "apiName": service_name,
            "documentType": "Wiki",
            "lastUpdated": datetime.now().isoformat(),
            "documentUrl": document_url,
            "sourceType": "Wiki"
        }
    
    def _construct_document_url(self, relative_path):
        """
        Construct a document URL based on the folder structure
        
        Args:
            relative_path (str): Relative path to the document
            
        Returns:
            str: Document URL
        """
        # Get base URL from configuration
        base_url = self.wiki_settings.get('wiki_base_url', '')
        if not base_url:
            return relative_path  # Return relative path if no base URL configured
        
        # Normalize path separators and ensure the URL uses forward slashes
        path = relative_path.replace('\\', '/')
        
        # Remove file extension
        if path.endswith('.md'):
            path = path[:-3]
        
        # Combine base URL with path
        if base_url.endswith('/'):
            url = base_url + path
        else:
            url = base_url + '/' + path
            
        return url
    
    def _upload_documents_to_search(self, documents):
        """
        Upload documents to Azure AI Search
        
        Args:
            documents (list): List of documents to upload
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            # Upload in batches of 10
            batch_size = 10
            for i in range(0, len(documents), batch_size):
                batch = documents[i:i+batch_size]
                self.search_client.upload_documents(batch)
                logger.info(f"Uploaded batch of {len(batch)} documents to search index")
                
            return True
        except Exception as e:
            logger.error(f"Error uploading documents to search index: {str(e)}")
            return False

if __name__ == "__main__":
    # Test running the wiki document processor
    processor = WikiDocumentProcessor()
    num_processed = processor.process_wiki_documents()
    print(f"Processed {num_processed} wiki documents")