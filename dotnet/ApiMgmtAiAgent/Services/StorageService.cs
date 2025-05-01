using System;
using System.Collections.Generic;
using ApiMgmtAiAgent.Models;

namespace ApiMgmtAiAgent.Services
{
    /// <summary>
    /// Service for storing and retrieving API information
    /// </summary>
    public class StorageService
    {
        private readonly Dictionary<string, string> _apiInfoStore = new Dictionary<string, string>();

        /// <summary>
        /// Store API details for retrieval by the AI
        /// </summary>
        public void StoreApiInformation(List<ApiInfo> apiDetails)
        {
            Console.WriteLine("Storing API information...");
            
            foreach (var api in apiDetails)
            {
                // Create a detailed description for the API
                string apiText = $"API Name: {api.Name}\nDisplay Name: {api.DisplayName}\nDescription: {api.Description}\nPath: {api.Path}\n";
                
                // Add details about operations
                foreach (var op in api.Operations)
                {
                    apiText += $"\nOperation: {op.DisplayName}\nMethod: {op.Method}\nURL: {op.UrlTemplate}\nDescription: {op.Description}\n";
                    
                    // Add parameter information
                    if (op.Parameters.Count > 0)
                    {
                        apiText += "Parameters:\n";
                        
                        foreach (var param in op.Parameters)
                        {
                            apiText += $"- {param.Name} ({param.Type}): {param.Description}, Required: {param.Required}\n";
                        }
                    }
                }
                
                // Store the API information with its name as key
                _apiInfoStore[api.Name] = apiText;
                Console.WriteLine($"Stored API information for: {api.Name}");
            }
        }

        /// <summary>
        /// Get all stored API information
        /// </summary>
        public Dictionary<string, string> GetAllApiInfo()
        {
            return _apiInfoStore;
        }

        /// <summary>
        /// Get API information for a specific API
        /// </summary>
        public string GetApiInfo(string apiName)
        {
            return _apiInfoStore.TryGetValue(apiName, out var info) 
                ? info 
                : $"API '{apiName}' not found.";
        }

        /// <summary>
        /// Check if there's any stored API information
        /// </summary>
        public bool HasStoredApis()
        {
            return _apiInfoStore.Count > 0;
        }
    }
}