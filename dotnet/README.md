# API Management AI Agent

## Overview

The ApiMgmtAiAgent is an intelligent, AI-powered assistant that helps users understand and work with APIs defined in Azure API Management. This application leverages Microsoft's Semantic Kernel and Azure OpenAI to create a natural language interface for querying API documentation.

## Features

- Interactive chat interface for asking questions about APIs
- Integration with Azure AI Search for retrieving API information
- Support for both OpenAI and Azure OpenAI models
- Semantic search capabilities for finding relevant API documentation
- Vector-based similarity search for accurate information retrieval

## Architecture

The ApiMgmtAiAgent consists of several core components:

1. **ChatService**: Manages the interactive chat interface with the user
2. **AIService**: Handles AI model integration with Semantic Kernel
3. **ApiSearchPlugin**: Enables semantic search against indexed API documentation
4. **ConfigurationManager**: Manages application configuration settings

## Prerequisites

- .NET 8.0 SDK or later
- Azure OpenAI service (or OpenAI API access)
- Azure AI Search service with indexed API documentation
- Environment variables or .env file for configuration

## Configuration

The ApiMgmtAiAgent can be configured using environment variables or a .env file. The following settings are available:

### OpenAI Configuration

```
# OpenAI settings (if using OpenAI instead of Azure OpenAI)
OPENAI_API_KEY="your_openai_api_key"
```

### Azure OpenAI Configuration

```
# Azure OpenAI settings
AZURE_OPENAI_ENDPOINT="https://your-azure-openai-service.openai.azure.com/"
AZURE_OPENAI_API_KEY="your_azure_openai_api_key"
AZURE_OPENAI_DEPLOYMENT_NAME="your_deployment_name"
```

### Azure AI Search Configuration

```
# Azure AI Search settings
AZURE_SEARCH_ENDPOINT="https://your-search-service.search.windows.net"
AZURE_SEARCH_API_KEY="your_search_api_key"
AZURE_SEARCH_API_COLLECTION_NAME="apim-swagger-docs"
```

## How to Run

1. Clone the repository
2. Configure environment variables (see Configuration section)
3. Build the project:

```bash
cd dotnet/ApiMgmtAiAgent
dotnet build
```

4. Run the application:

```bash
dotnet run
```

## Using the Chat Interface

Once the application is running, you can interact with the AI assistant through the console:

1. Type your question about APIs and press Enter
2. The AI will process your question and provide a response based on available API documentation
3. Continue asking questions or type 'exit' to quit

Example questions you can ask:
- "What APIs are available?"
- "How do I authenticate with the User API?"
- "What parameters does the GET /users endpoint accept?"
- "Show me an example of calling the Create Product API"

## Integration with API Documentation

This tool works best when paired with the Python-based API documentation ingestion pipeline found in the `../python` directory. The ingestion pipeline:

1. Downloads API definitions from Azure API Management
2. Converts them to markdown documentation
3. Indexes them in Azure AI Search

The ApiMgmtAiAgent then uses this indexed documentation to provide accurate answers to user queries.

## Security Considerations

- API keys and endpoints are stored in environment variables or a .env file (not included in version control)
- The application is designed to work with appropriate authentication mechanisms for Azure services
- Consider using Azure Managed Identities in production environments

## Development

### Project Structure

- `Program.cs`: Application entry point
- `Config/`: Configuration management
- `Models/`: Data models for API information
- `Services/`: Core services including AI and chat functionality
- `Services/Plugins/`: Semantic Kernel plugins like ApiSearchPlugin

### Adding New Features

To extend the agent with additional capabilities:

1. Create new plugins by implementing classes with the `[KernelFunction]` attribute
2. Register plugins with the kernel using `_kernel.Plugins.AddFromObject()`
3. Update the AI instructions as needed in the `AIService` class

## Troubleshooting

If you encounter issues:

- Verify your Azure OpenAI and Azure AI Search services are properly configured
- Check that your API documentation has been indexed correctly
- Ensure all required environment variables are set
- Look for error messages in the console output