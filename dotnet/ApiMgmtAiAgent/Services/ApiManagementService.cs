using System;
using System.Collections.Generic;
using System.Threading.Tasks;
using ApiMgmtAiAgent.Config;
using ApiMgmtAiAgent.Models;
using Microsoft.Azure.Management.ApiManagement;
using Microsoft.Rest;

namespace ApiMgmtAiAgent.Services
{
    /// <summary>
    /// Service for interacting with Azure API Management
    /// </summary>
    public class ApiManagementService
    {
        private readonly ConfigurationManager _config;
        private readonly ApiManagementClient _client;

        public ApiManagementService(ConfigurationManager config)
        {
            _config = config;
            
            // Create credentials with Azure access token
            var credentials = new TokenCredentials(_config.AzureAccessToken);
            
            // Create API Management client
            _client = new ApiManagementClient(credentials)
            {
                SubscriptionId = _config.ApiManagementSubscriptionId
            };
        }

        /// <summary>
        /// Extract API details from API Management catalog
        /// </summary>
        public async Task<List<ApiInfo>> ExtractApiDetailsAsync()
        {
            Console.WriteLine("Extracting API information from API Management...");
            
            var apiDetailsList = new List<ApiInfo>();
            
            try 
            {
                // Get all APIs in the service
                var apis = await _client.Api.ListByServiceAsync(
                    _config.ApiManagementResourceGroup, 
                    _config.ApiManagementServiceName
                );
                
                foreach (var api in apis)
                {
                    Console.WriteLine($"Processing API: {api.Name}");
                    
                    var apiInfo = new ApiInfo
                    {
                        Name = api.Name ?? "Unknown",
                        DisplayName = api.DisplayName ?? api.Name ?? "Unknown",
                        Description = api.Description ?? "No description available",
                        Path = api.Path ?? "/",
                        Operations = new List<OperationInfo>()
                    };
                    
                    // Get all operations (endpoints) for this API
                    var operations = await _client.ApiOperation.ListByApiAsync(
                        _config.ApiManagementResourceGroup, 
                        _config.ApiManagementServiceName,
                        api.Name
                    );
                    
                    foreach (var operation in operations)
                    {
                        var opInfo = new OperationInfo
                        {
                            Name = operation.Name ?? "Unknown",
                            DisplayName = operation.DisplayName ?? operation.Name ?? "Unknown",
                            Method = operation.Method ?? "GET",
                            UrlTemplate = operation.UrlTemplate ?? "/",
                            Description = operation.Description ?? "No description available",
                            Parameters = new List<ParameterInfo>()
                        };
                        
                        // Get details about request parameters from template parameters
                        if (operation.TemplateParameters != null)
                        {
                            foreach (var param in operation.TemplateParameters)
                            {
                                opInfo.Parameters.Add(new ParameterInfo
                                {
                                    Name = param.Name ?? "Unknown",
                                    Description = param.Description ?? "No description available", 
                                    Type = param.Type ?? "string",
                                    Required = param.Required ?? true
                                });
                            }
                        }
                        
                        // Add parameters from request if available
                        if (operation.Request?.QueryParameters != null)
                        {
                            foreach (var param in operation.Request.QueryParameters)
                            {
                                opInfo.Parameters.Add(new ParameterInfo
                                {
                                    Name = param.Name ?? "Unknown",
                                    Description = param.Description ?? "No description available",
                                    Type = param.Type ?? "string",
                                    Required = param.Required ?? false
                                });
                            }
                        }
                        
                        apiInfo.Operations.Add(opInfo);
                    }
                    
                    apiDetailsList.Add(apiInfo);
                }
            }
            catch (Exception ex) 
            {
                Console.WriteLine($"Error while extracting API details: {ex.Message}");
                // Adding a sample API for testing if real APIs can't be accessed
                apiDetailsList.Add(CreateSampleApi());
            }
            
            Console.WriteLine($"Extracted information for {apiDetailsList.Count} APIs.");
            return apiDetailsList;
        }
        
        /// <summary>
        /// Creates a sample API for testing when actual APIM connection fails
        /// </summary>
        private static ApiInfo CreateSampleApi()
        {
            return new ApiInfo
            {
                Name = "sample-api",
                DisplayName = "Sample API",
                Description = "This is a sample API for demonstration purposes",
                Path = "/sample",
                Operations = new List<OperationInfo>
                {
                    new OperationInfo
                    {
                        Name = "get-users",
                        DisplayName = "Get Users",
                        Method = "GET",
                        UrlTemplate = "/users",
                        Description = "Returns a list of users",
                        Parameters = new List<ParameterInfo>
                        {
                            new ParameterInfo
                            {
                                Name = "limit",
                                Description = "Maximum number of results to return",
                                Type = "integer",
                                Required = false
                            },
                            new ParameterInfo
                            {
                                Name = "offset",
                                Description = "Number of results to skip",
                                Type = "integer",
                                Required = false
                            }
                        }
                    },
                    new OperationInfo
                    {
                        Name = "get-user-by-id", 
                        DisplayName = "Get User by ID",
                        Method = "GET",
                        UrlTemplate = "/users/{userId}",
                        Description = "Returns details for a specific user",
                        Parameters = new List<ParameterInfo>
                        {
                            new ParameterInfo
                            {
                                Name = "userId",
                                Description = "The ID of the user to retrieve",
                                Type = "string",
                                Required = true
                            }
                        }
                    },
                    new OperationInfo
                    {
                        Name = "create-user",
                        DisplayName = "Create User",
                        Method = "POST",
                        UrlTemplate = "/users",
                        Description = "Creates a new user",
                        Parameters = new List<ParameterInfo>()
                    }
                }
            };
        }
    }
}