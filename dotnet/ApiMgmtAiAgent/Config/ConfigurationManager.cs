using System;
using DotNetEnv;

namespace ApiMgmtAiAgent.Config
{
    /// <summary>
    /// Manages application configuration settings from environment variables
    /// </summary>
    public class ConfigurationManager
    {
        // API Management settings
        public string ApiManagementSubscriptionId { get; }
        public string ApiManagementResourceGroup { get; }
        public string ApiManagementServiceName { get; }
        public string AzureAccessToken { get; }

        // AI service settings
        public string OpenAIApiKey { get; }
        public string AzureOpenAIEndpoint { get; }
        public string AzureOpenAIApiKey { get; }
        public string AzureOpenAIDeploymentName { get; }
        public string AzureAISearchUri { get; }
        public string AzureAISearchKey { get; }
        public string AzureAISearchApiCollectionName { get; }
        public string AzureAISearchDocCollectionName { get; }

        public ConfigurationManager()
        {
            // Load environment variables from .env file if it exists
            Env.Load();

            // Load settings from environment variables with fallbacks
            // ApiManagementSubscriptionId = Environment.GetEnvironmentVariable("APIM_SUBSCRIPTION_ID") ?? "your_subscription_id";
            // ApiManagementResourceGroup = Environment.GetEnvironmentVariable("APIM_RESOURCE_GROUP") ?? "your_resource_group";
            // ApiManagementServiceName = Environment.GetEnvironmentVariable("APIM_SERVICE_NAME") ?? "your_apim_service_name";
            // AzureAccessToken = Environment.GetEnvironmentVariable("AZURE_ACCESS_TOKEN") ?? "your_azure_token";

            // OpenAI or Azure OpenAI settings
            OpenAIApiKey = Environment.GetEnvironmentVariable("OPENAI_API_KEY") ?? "your_openai_api_key";
            AzureOpenAIEndpoint = Environment.GetEnvironmentVariable("AZURE_OPENAI_ENDPOINT") ?? "your_azure_openai_endpoint";
            AzureOpenAIApiKey = Environment.GetEnvironmentVariable("AZURE_OPENAI_API_KEY") ?? "your_azure_openai_api_key";
            AzureOpenAIDeploymentName = Environment.GetEnvironmentVariable("AZURE_OPENAI_DEPLOYMENT_NAME") ?? "your_azure_openai_deployment";

            // Ai Search 
            AzureAISearchUri = Environment.GetEnvironmentVariable("AZURE_SEARCH_ENDPOINT") ?? "";
            AzureAISearchKey = Environment.GetEnvironmentVariable("AZURE_SEARCH_API_KEY") ?? "";
            AzureAISearchApiCollectionName = Environment.GetEnvironmentVariable("AZURE_SEARCH_API_COLLECTION_NAME") ?? "";
            AzureAISearchDocCollectionName = Environment.GetEnvironmentVariable("AZURE_SEARCH_DOC_COLLECTION_NAME") ?? "";
        }

        /// <summary>
        /// Determines if Azure OpenAI should be used instead of OpenAI
        /// </summary>
        public bool ShouldUseAzureOpenAI()
        {
            return !string.IsNullOrEmpty(AzureOpenAIEndpoint) && !string.IsNullOrEmpty(AzureOpenAIApiKey);
        }
    }
}