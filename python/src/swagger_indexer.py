#!/usr/bin/env python3
import os
import re
import json
import logging
import hashlib
from datetime import datetime
from azure.identity import DefaultAzureCredential, ClientSecretCredential
from azure.core.credentials import AzureKeyCredential
from azure.search.documents import SearchClient
from azure.search.documents.indexes import SearchIndexClient
from azure.search.documents.indexes.models import (
    SearchIndex, SimpleField, SearchableField, 
    SearchFieldDataType, SearchableField, SearchField,
    VectorSearch,
    VectorSearchProfile,
    HnswAlgorithmConfiguration,
    AzureOpenAIVectorizer,
    AzureOpenAIVectorizerParameters,
    SemanticConfiguration,
    SemanticPrioritizedFields,
    SemanticField,
    SemanticSearch
)
from openai import AzureOpenAI
from config import Config

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class AzureSearchIndexerV2:
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
        
        # Get OpenAI settings if available
        try:
            self.openai_settings = self.config.get_openai_settings()
        except AttributeError:
            logger.warning("OpenAI settings not found in configuration. LLM features will be disabled.")
            self.openai_settings = None
        
        # Initialize Azure clients
        self._initialize_clients()
    
    def _initialize_clients(self):
        """Initialize Azure AI Search and OpenAI clients"""
        # Initialize search clients
        endpoint = self.search_settings['endpoint']
        key = self.search_settings['key']
        index_name = self.search_settings['index_name']
        
        logger.info("Using AzureKeyCredential for Azure Search")
        credential = AzureKeyCredential(key)
        
        # For managing indexes
        self.index_client = SearchIndexClient(
            endpoint=endpoint,
            credential=credential
        )
        
        # For uploading documents
        self.search_client = SearchClient(
            endpoint=endpoint,
            index_name=index_name,
            credential=credential
        )
        
        # Initialize Azure OpenAI client if settings are available
        self.openai_client = None
        if self.openai_settings:
            try:
                self.openai_client = AzureOpenAI(
                    api_key=self.openai_settings['api_key'],
                    api_version=self.openai_settings['api_version'],
                    azure_endpoint=self.openai_settings['endpoint'],
                    
                    azure_deployment=self.openai_settings.get('model', ''),
                )
                logger.info("Azure OpenAI client initialized successfully")
            except Exception as e:
                logger.error(f"Failed to initialize Azure OpenAI client: {str(e)}")
    
    def create_search_index(self):
        """
        Create or update the search index with fields for API information
        
        Returns:
            bool: True if successful, False otherwise
        """
        index_name = self.search_settings['index_name']
        logger.info(f"Creating/updating search index: {index_name}")
        
        try:
            # Define the index fields
            fields = [
                SimpleField(name="id", type=SearchFieldDataType.String, key=True),
                SearchableField(name="apiName", type=SearchFieldDataType.String, searchable=True, retrievable=True, analyzer_name="en.microsoft"),
                SearchableField(name="apiContent", type=SearchFieldDataType.String, searchable=True, retrievable=True, analyzer_name="en.microsoft"),
                SearchField(
                    name="apiContentVector",
                    type=SearchFieldDataType.Collection(SearchFieldDataType.Single),
                    searchable=True,
                    vector_search_dimensions=1536,
                    vector_search_profile_name="myHnswProfile",
                ),
                SimpleField(name="reference", type=SearchFieldDataType.String, retrievable=True),
                SimpleField(name="lastUpdated", type=SearchFieldDataType.DateTimeOffset, 
                            filterable=True, sortable=True, retrievable=True),
                
            ]
            
            vector_search = VectorSearch(
                 algorithms=[HnswAlgorithmConfiguration(name="myHnsw")],
                 profiles=[VectorSearchProfile(name="myHnswProfile", algorithm_configuration_name="myHnsw", vectorizer_name="myVectorizer")],
                 vectorizers=[
                    AzureOpenAIVectorizer(
                        vectorizer_name="myVectorizer",
                        parameters=AzureOpenAIVectorizerParameters(
                            resource_url=self.openai_settings['endpoint'],
                            deployment_name=self.openai_settings['embeedding_model_deployment_name'],
                            model_name=self.openai_settings['embedding_model_name'],
                            api_key=self.openai_settings['api_key']
                        )
                    )
                ]
            )
            
            semantic_config = SemanticConfiguration(
                name="my-semantic-config",
                prioritized_fields=SemanticPrioritizedFields(
                    title_field=SemanticField(field_name="apiName"), 
                    content_fields=[SemanticField(field_name="apiContent")]
                )
           )

            # Create the semantic settings with the configuration
            semantic_search = SemanticSearch(configurations=[semantic_config])

            # Create the index definition
            index = SearchIndex(name=index_name, fields=fields, vector_search=vector_search, semantic_search=semantic_search)
            
            # Create or update the index
            result = self.index_client.create_or_update_index(index)
            logger.info(f"Index {result.name} created or updated")
            return True
            
        except Exception as e:
            logger.error(f"Error creating search index: {str(e)}")
            return False

    def extract_api_info_with_llm(self, swagger_content, file_name):
        """
        Extract API information from a Swagger file using Azure OpenAI
        
        Args:
            swagger_content (str): Content of the Swagger file
            file_name (str): Name of the swagger file for reference
            
        Returns:
            dict: Extracted API information
        """
        if not self.openai_client:
            logger.warning(f"OpenAI client not initialized. Cannot extract API information from {file_name}.")
            return {}
        
        logger.info(f"Extracting API information from {file_name} using LLM")
        
        # Calculate approximate token count (rough estimation: ~4 chars per token)
        estimated_tokens = len(swagger_content) / 4
        max_swagger_tokens = 80000  # Conservative limit to leave room for prompt and completion
        
        # Truncate the content if it's likely to exceed the token limit
        if estimated_tokens > max_swagger_tokens:
            logger.warning(f"Swagger file {file_name} is too large ({estimated_tokens:.0f} estimated tokens). Truncating content.")
            # Try to find a valid JSON structure in the truncated content
            try:
                # Load and extract the most important parts of the swagger file
                swagger_json = json.loads(swagger_content)
                
                # Extract key information for processing
                extracted_parts = {
                    "info": swagger_json.get("info", {}),
                    "paths": {}
                }
                
                # Get a sample of paths (first 50)
                paths = swagger_json.get("paths", {})
                path_items = list(paths.items())[:50]  # Take first 50 paths
                
                for path, methods in path_items:
                    extracted_parts["paths"][path] = methods
                
                # Add definitions/components for key schemas (limited)
                if "definitions" in swagger_json:
                    # Get just a sample of definitions
                    extracted_parts["definitions"] = dict(list(swagger_json["definitions"].items())[:20])
                elif "components" in swagger_json and "schemas" in swagger_json["components"]:
                    extracted_parts["components"] = {"schemas": {}}
                    schemas = list(swagger_json["components"]["schemas"].items())[:20]
                    extracted_parts["components"]["schemas"] = dict(schemas)
                
                # Convert back to a smaller JSON string
                swagger_content = json.dumps(extracted_parts, indent=2)
                logger.info(f"Successfully truncated {file_name} to focus on key API information")
                
            except json.JSONDecodeError:
                # If not valid JSON, just truncate the string
                logger.warning(f"Could not parse {file_name} as JSON. Using simple truncation.")
                swagger_content = swagger_content[:max_swagger_tokens * 4]  # Simple truncation
        
        # Prepare the prompt for OpenAI
        prompt = f"""
        Analyze the following Swagger/OpenAPI definition (which may be truncated) and extract the following information:
        1. The API name
        2. The purpose and description of the API
        3. The business context in which this API is used
        4. A list of all operations with their names and descriptions
        
        Format your response as a JSON object with the following structure:
        {{
            "apiName": "Name of the API",
            "apiPurpose": "Detailed purpose and description of the API",
            "apiDescription": "A brief description of the API",
            "apiContext": "The business context where this API is used",
            "operations": [
                {{
                    "operationName": "Name of operation 1",
                    "operationDescription": "Description of operation 1"
                }},
                {{
                    "operationName": "Name of operation 2",
                    "operationDescription": "Description of operation 2"
                }}
            ]
        }}
        
        Only return the valid JSON object, nothing else.
        
        Here's the Swagger definition (possibly truncated):
        {swagger_content}  
        """
        
        try:
            response = self.openai_client.chat.completions.create(
                model=self.openai_settings.get('model', 'gpt-4'),
                messages=[
                    {"role": "system", "content": "You are an AI assistant that extracts structured information from API specifications."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.1,  # Low temperature for more deterministic output
                response_format={"type": "json_object"}
            )
            
            # Extract the JSON response
            result_text = response.choices[0].message.content
            
            try:
                # Parse the JSON response
                result = json.loads(result_text)
                logger.info(f"Successfully extracted API information from {file_name}")
                return result
            except json.JSONDecodeError as e:
                logger.error(f"Failed to parse LLM response as JSON for {file_name}: {str(e)}")
                logger.debug(f"Raw response: {result_text[:500]}...")
                return {}
                
        except Exception as e:
            logger.error(f"Error calling OpenAI for {file_name}: {str(e)}")
            return {}
    
    def extract_api_info_with_llm_v1(self, swagger_content, file_name):
        """
        Extract API information from a Swagger file using Azure OpenAI
        
        Args:
            swagger_content (str): Content of the Swagger file
            file_name (str): Name of the swagger file for reference
            
        Returns:
            dict: Extracted API information
        """
        if not self.openai_client:
            logger.warning(f"OpenAI client not initialized. Cannot extract API information from {file_name}.")
            return {}
        
        logger.info(f"Extracting API information from {file_name} using LLM")
        
        # Prepare the prompt for OpenAI
        prompt = f"""
        Analyze the following Swagger/OpenAPI definition and extract the following information:
        1. The API name
        2. The purpose and description of the API
        3. The business context in which this API is used
        4. A list of all operations with their names and descriptions
        
        Format your response as a JSON object with the following structure:
        {{
            "apiName": "Name of the API",
            "apiPurpose": "Detailed purpose and description of the API",
            "apiDescription": "A brief description of the API",
            "apiContext": "The business context where this API is used",
            "operations": [
                {{
                    "operationName": "Name of operation 1",
                    "operationDescription": "Description of operation 1"
                }},
                {{
                    "operationName": "Name of operation 2",
                    "operationDescription": "Description of operation 2"
                }}
            ]
        }}
        
        Only return the valid JSON object, nothing else.
        
        Here's the Swagger definition:
        {swagger_content}  
        """
        
        try:
            response = self.openai_client.chat.completions.create(
                model=self.openai_settings.get('model', 'gpt-4'),
                messages=[
                    {"role": "system", "content": "You are an AI assistant that extracts structured information from API specifications."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.1,  # Low temperature for more deterministic output
                response_format={"type": "json_object"}
            )
            
            # Extract the JSON response
            result_text = response.choices[0].message.content
            
            try:
                # Parse the JSON response
                result = json.loads(result_text)
                logger.info(f"Successfully extracted API information from {file_name}")
                return result
            except json.JSONDecodeError as e:
                logger.error(f"Failed to parse LLM response as JSON for {file_name}: {str(e)}")
                logger.debug(f"Raw response: {result_text[:500]}...")
                return {}
                
        except Exception as e:
            logger.error(f"Error calling OpenAI for {file_name}: {str(e)}")
            return {}
    
    def process_swagger_file(self, swagger_file_path):
        """
        Process a Swagger file to extract API information using LLM
        
        Args:
            swagger_file_path (str): Path to the Swagger file
            
        Returns:
            dict: Processed information ready for indexing
        """
        file_name = os.path.basename(swagger_file_path)
        logger.info(f"Processing Swagger file: {file_name}")
        
        # Read the Swagger file
        try:
            with open(swagger_file_path, 'r', encoding='utf-8') as f:
                raw_content = f.read()
        except Exception as e:
            logger.error(f"Error reading swagger file {file_name}: {str(e)}")
            return None
        
        # Extract API information using LLM
        api_info = self.extract_api_info_with_llm(raw_content, file_name)
        
        llm_dir = self.output_dirs.get('llm_dir', '')
        
        # Check if llm_dir exists, if not, create it
        if llm_dir and not os.path.exists(llm_dir):
            os.makedirs(llm_dir)
            logger.info(f"Created directory: {llm_dir}")
        
        # Save the extracted API information to a file
        llm_file_path = os.path.join(llm_dir, file_name)
        try:
            with open(llm_file_path, 'w', encoding='utf-8') as llm_file:
                json.dump(api_info, llm_file, indent=2)
                logger.info(f"Saved extracted API information to {llm_file_path}")
        except Exception as e:
            logger.error(f"Error saving API information to {llm_file_path}: {str(e)}")
        
        # Create a unique ID based on the file content
        file_id = hashlib.md5(raw_content.encode()).hexdigest()
        
        # Format operations for search index if available
        operations_list = []
        if api_info and 'operations' in api_info:
            for op in api_info.get('operations', []):
                operation_text = f"{op.get('operationName', '')}: {op.get('operationDescription', '')}"
                operations_list.append(operation_text)
        
        # Extract version information if present in the filename
        version_match = re.search(r'v\d+(\.\d+)*', file_name)
        api_version = version_match.group(0) if version_match else ""
        
        # If LLM extraction failed, build a minimal document
        if not api_info or not api_info.get('apiName'):
           raise ValueError(f"Failed to extract API information using LLM from {file_name}")
        
        # Create document with extracted information
        json_content = json.dumps(api_info)
        return {
            "id": file_id,
            "apiName": api_info.get("apiName", ""),
            "apiContent": json_content,
            "apiContentVector": json_content,
            "lastUpdated": datetime.now().isoformat() + 'Z',
            "reference": swagger_file_path,
        }
    
    def index_swagger_files(self, swagger_files=None):
        """
        Index Swagger files into Azure AI Search
        
        Args:
            swagger_files (list, optional): List of Swagger file paths to index.
                                           If None, will scan the swagger directory.
        
        Returns:
            int: Number of files successfully indexed
        """
        # Create or update the search index
        if not self.create_search_index():
            logger.error("Failed to create search index. Aborting indexing operation.")
            return 0
        
        # If no swagger files provided, scan the directory
        if not swagger_files:
            swagger_dir = self.output_dirs.get('swagger_dir', '')
            if not swagger_dir or not os.path.exists(swagger_dir):
                logger.error("Swagger directory not found or not specified")
                return 0
                
            swagger_files = []
            for root, _, files in os.walk(swagger_dir):
                for file in files:
                    if file.endswith(('.json', '.yaml', '.yml')):
                        swagger_files.append(os.path.join(root, file))
        
        logger.info(f"Found {len(swagger_files)} Swagger files to process")
        
        # Process and index each Swagger file
        documents = []
        processed_count = 0
        
        for swagger_file in swagger_files:
            try:
                # Process the swagger file
                doc = self.process_swagger_file(swagger_file)
                if doc:
                    documents.append(doc)
                    processed_count += 1
                    logger.info(f"Processed {os.path.basename(swagger_file)}")
                
                # Index in batches of 10
                if len(documents) >= 10:
                    self.search_client.upload_documents(documents)
                    logger.info(f"Indexed batch of {len(documents)} documents")
                    documents = []
                    
            except Exception as e:
                logger.error(f"Error processing {os.path.basename(swagger_file)}: {str(e)}")
        
        # Upload any remaining documents
        if documents:
            try:
                self.search_client.upload_documents(documents)
                logger.info(f"Indexed final batch of {len(documents)} documents")
            except Exception as e:
                logger.error(f"Error uploading final batch: {str(e)}")
        
        logger.info(f"Indexed {processed_count} Swagger files")
        return processed_count

if __name__ == "__main__":
    # Create indexer and run
    indexer = AzureSearchIndexerV2(config=Config(config_path='/workspaces/apim-swagger-downloader/config/config.yaml'))
    num_indexed = indexer.index_swagger_files()
    
    print(f"\nIndexed {num_indexed} Swagger files to Azure AI Search index: {indexer.search_settings['index_name']}")
    print(f"Search endpoint: {indexer.search_settings['endpoint']}")