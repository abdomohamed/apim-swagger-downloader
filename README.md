# Azure APIM Swagger Downloader

This tool helps you:
1. Download OpenAPI/Swagger definitions from Azure API Management (APIM)
2. Convert these Swagger files to readable Markdown documentation
3. Index the documentation in Azure AI Search for easy discovery

## Features

- Authenticate with Azure and enumerate all APIs in an APIM instance
- Download OpenAPI/Swagger specifications for each API
- Convert Swagger to Markdown with detailed API documentation using Markitdown
- Index API documentation in Azure AI Search for full-text search
- Configurable via YAML file or environment variables
- Run specific steps independently (download, convert, or index)

## Prerequisites

- Python 3.7+
- An Azure account with:
  - API Management instance containing APIs
  - Azure AI Search service (optional, for indexing)
- Either:
  - Azure CLI login (`az login`) for DefaultAzureCredential authentication (recommended)
  - Service Principal with proper permissions for Azure resources

## Installation

1. Clone this repository:
   ```
   git clone https://github.com/yourusername/apim-swagger-downloader.git
   cd apim-swagger-downloader
   ```

2. Install Python dependencies:
   ```
   pip install -r requirements.txt
   ```

## Configuration

You can configure the tool in two ways:

1. **YAML Configuration File** (preferred): Edit `config/config.yaml`
2. **Environment Variables**: Set the proper environment variables

### Configuration File

The default configuration file is located at `config/config.yaml`:

```yaml
# Azure API Management Configuration
azure:
  # Authentication settings
  auth:
    use_default_credential: true  # Set to true to use Azure CLI login, false to use service principal
  
  # Azure credentials (only needed if use_default_credential is false)
  tenant_id: "<your-tenant-id>"
  client_id: "<your-client-id>"
  client_secret: "<your-client-secret>"
  
  # APIM details
  subscription_id: "<your-subscription-id>"
  resource_group: "<your-resource-group>"
  service_name: "<your-apim-service-name>"
  
  # Azure AI Search settings
  search:
    endpoint: "<your-search-service-endpoint>"
    key: "<your-search-admin-key>"
    index_name: "apim-swagger-docs"

# Output settings
output:
  swagger_dir: "output/swagger"
  markdown_dir: "output/markdown"

# Processing settings
processing:
  # Set to true to convert swagger to markdown
  convert_to_markdown: true
  # Set to true to upload markdown to Azure AI Search
  upload_to_search: true
```

### API Filtering

You can limit the APIs that are processed using the following configuration options:

```yaml
azure:
  # API filter settings
  api_filter:
    include_apis: ["api1", "api2"]  # Process only these specific API IDs
    include_tags: ["public", "v1"]  # Process only APIs with these tags


You can limit the APIs that are processed using the following configuration options:

```yaml
azure:
  # API filter settings
  api_filter:
    include_apis: ["api1", "api2"]  # Process only these specific API IDs
    include_tags: ["public", "v1"]  # Process only APIs with these tags


With these changes, the APIM swagger downloader will:
1. By default, continue to enumerate all APIs in the APIM instance
2. If `include_apis` is specified, only process the listed APIs
3. If `include_tags` is specified, only process APIs that have at least one of the specified tags
4. If both filters are specified, it will include APIs that match either condition

This gives you the flexibility to limit the scope of APIs being processed while maintaining the original behavior when no filters are specified.With these changes, the APIM swagger downloader will:
1. By default, continue to enumerate all APIs in the APIM instance
2. If `include_apis` is specified, only process the listed APIs
3. If `include_tags` is specified, only process APIs that have at least one of the specified tags
4. If both filters are specified, it will include APIs that match either condition

This gives you the flexibility to limit the scope of APIs being processed while maintaining the original behavior when no filters are specified.
```

### Authentication Options

The tool supports two authentication methods:

1. **DefaultAzureCredential** (recommended): Uses your current Azure CLI login credentials
   - Make sure you've logged in with `az login`
   - Set `use_default_credential: true` in the config file
   - No need to provide tenant_id, client_id, or client_secret

2. **Service Principal**: Uses a service principal for authentication
   - Set `use_default_credential: false` in the config file
   - Provide `tenant_id`, `client_id`, and `client_secret` values

### Environment Variables

You can also use environment variables to override settings in the config file:

```
# Azure Authentication
AZURE_USE_DEFAULT_CREDENTIAL=true  # Set to "true" to use Azure CLI login, "false" to use service principal
AZURE_TENANT_ID=your-tenant-id     # Only needed if not using default credential
AZURE_CLIENT_ID=your-client-id     # Only needed if not using default credential
AZURE_CLIENT_SECRET=your-client-secret  # Only needed if not using default credential

# APIM Settings
AZURE_SUBSCRIPTION_ID=your-subscription-id
AZURE_RESOURCE_GROUP=your-resource-group
AZURE_APIM_SERVICE_NAME=your-apim-service-name

# Azure Search Settings
AZURE_SEARCH_ENDPOINT=your-search-endpoint
AZURE_SEARCH_KEY=your-search-key
AZURE_SEARCH_INDEX_NAME=your-index-name
```

## Usage

### Running All Steps

To run the entire pipeline (download, convert, and index):

```
./main.py
```

### Running Specific Steps

You can run specific steps individually:

```
# Download only
./main.py --download-only

# Convert only
./main.py --convert-only

# Index only
./main.py --index-only
```

### Using a Different Configuration File

You can specify a different configuration file:

```
./main.py --config /path/to/your/config.yaml
```

## Output

The tool produces the following outputs:

1. **Swagger Files**: JSON files in OpenAPI format in `output/swagger/`
2. **Markdown Documentation**: Human-readable API docs in `output/markdown/`
3. **Search Index**: API documentation indexed in Azure AI Search for full-text search

## Search Schema

The Azure AI Search index includes the following fields:

- **id**: Unique identifier for the document
- **title**: API title (searchable)
- **content**: Full markdown content (searchable)
- **apiName**: Name of the API (filterable, facetable)
- **apiVersion**: API version (filterable, facetable)
- **documentType**: Type of documentation (filterable, facetable)
- **lastUpdated**: Timestamp when the document was last updated (filterable, sortable)
- **fileName**: Original markdown filename
- **fileUrl**: Relative path to the markdown file

## Development

The project has the following structure:

```
apim-swagger-downloader/
├── main.py                      # Main runner script
├── requirements.txt             # Python dependencies
├── config/
│   └── config.yaml              # Configuration file
├── output/
│   ├── swagger/                 # Generated swagger files
│   └── markdown/                # Generated markdown files
└── src/
    ├── apim_swagger_downloader.py    # APIM API enumeration and swagger downloading
    ├── azure_search_indexer.py       # Azure AI Search indexing
    ├── config.py                     # Configuration handling
    └── swagger_to_markdown.py        # Swagger to markdown conversion
```

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

This project is licensed under the MIT License - see the LICENSE file for details.