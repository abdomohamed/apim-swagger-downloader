using System;
using System.Threading.Tasks;
using ApiMgmtAiAgent.Config;
using ApiMgmtAiAgent.Services.Plugins;
using Microsoft.Extensions.DependencyInjection;
using Microsoft.SemanticKernel;
using Microsoft.SemanticKernel.ChatCompletion;
using Microsoft.SemanticKernel.Connectors.OpenAI;
using Microsoft.SemanticKernel.Connectors.AzureOpenAI;
using Microsoft.SemanticKernel.Agents;
using Azure;

namespace ApiMgmtAiAgent.Services
{
    /// <summary>
    /// Service for AI operations using Semantic Kernel
    /// </summary>
    public class AIService
    {
        private readonly ConfigurationManager _config;
        private readonly Kernel _kernel;
        private readonly ChatCompletionAgent _agent ;

        public AIService(ConfigurationManager config)
        {
            _config = config;
            _kernel = InitializeSemanticKernel();
            
            // Register API search plugin
            _kernel.Plugins.AddFromObject(new ApiSearchPlugin(_kernel,_config.AzureAISearchApiCollectionName), "ApiSearchPlugin");
            
            // Register documentation search plugin if collection name is provided
            if (!string.IsNullOrEmpty(_config.AzureAISearchDocCollectionName))
            {
                _kernel.Plugins.AddFromObject(new DocSearchPlugin(_kernel, _config.AzureAISearchDocCollectionName), "DocSearchPlugin");
                Console.WriteLine($"DocSearchPlugin registered with collection: {_config.AzureAISearchDocCollectionName}");
            }

            _agent = new()
            {
                Name = "apim-ai-assistant",
                Instructions = instructions,
                Kernel = _kernel,
                Arguments = // Specify the service-identifier via the KernelArguments
                new KernelArguments(
                    new AzureOpenAIPromptExecutionSettings { FunctionChoiceBehavior = FunctionChoiceBehavior.Auto()})
            };

        }

        /// <summary>
        /// Initialize the Semantic Kernel with appropriate settings
        /// </summary>
        private Kernel InitializeSemanticKernel()
        {
            Console.WriteLine("Initializing Semantic Kernel...");
            
            var builder = Kernel.CreateBuilder();

            var handler = new HttpClientHandler();
            handler.ServerCertificateCustomValidationCallback = (httpRequestMessage, cert, cetChain, policyErrors) => true;

            var client = new HttpClient(handler);

            // Configure AI service - either Azure OpenAI or OpenAI
            if (_config.ShouldUseAzureOpenAI())
            {
                // Use Azure OpenAI
                builder.AddAzureOpenAIChatCompletion(
                    deploymentName: _config.AzureOpenAIDeploymentName,
                    endpoint: _config.AzureOpenAIEndpoint,
                    apiKey: _config.AzureOpenAIApiKey,
                    serviceId: "AzureOpenAIChatCompletion",
                    httpClient: client
                );
            }
            else
            {
                // Use OpenAI
                builder.AddOpenAIChatCompletion(
                    modelId: "gpt-4",
                    apiKey: _config.OpenAIApiKey
                );
            }

            builder.Services.AddAzureAISearchVectorStore(new Uri(_config.AzureAISearchUri), new AzureKeyCredential(_config.AzureAISearchKey));

            return builder.Build();
        }

        const string instructions = "You are an expert API assistant that helps users understand and work with APIs. " +
                            "Provide accurate, concise answers based on the API documentation and related patterns documentation. " +
                            "You can search both API specifications and implementation patterns documentation to provide comprehensive answers. " +
                            "If you don't have enough information to answer a question, say so clearly.\n\n" +
                            "Based on the following information, answer the user's question:\n\n";

        /// <summary>
        /// Gets the response from the AI model for a given prompt
        /// </summary>
        public async Task<string> GetAIResponseAsync(string userInput)
        {
            try
            {

                var result = "";
                await foreach (ChatMessageContent response in _agent.InvokeAsync(new ChatMessageContent(AuthorRole.User, userInput)))
                {
                    result += response.Content;
                }

                return result;
            }
            catch (Exception ex)
            {
                Console.WriteLine($"Error generating AI response: {ex.Message}");
                return $"Error: {ex.Message}";
            }
        }

        /// <summary>
        /// Check if the AI service is properly configured
        /// </summary>
        public bool IsConfigured()
        {
            try
            {
                var openAIClient = _kernel.GetRequiredService<IChatCompletionService>();
                return openAIClient != null;
            }
            catch
            {
                return false;
            }
        }
    }
}