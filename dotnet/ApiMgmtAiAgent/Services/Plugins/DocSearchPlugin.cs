using Azure.Search.Documents;
using Azure.Search.Documents.Indexes;
using Azure.Search.Documents.Models;
using Microsoft.Extensions.VectorData;
using Microsoft.SemanticKernel;
using System;
using System.Collections.Generic;
using System.ComponentModel;
using System.Text.Json.Serialization;
using System.Threading.Tasks;

namespace ApiMgmtAiAgent.Services.Plugins
{
    /// <summary>
    /// Plugin for searching documentation in Azure AI Search
    /// </summary>
    public class DocSearchPlugin
    {
        private readonly Kernel _kernel;
        private readonly string _collectionName;
        private readonly SearchClient _searchClient;

        public DocSearchPlugin(Kernel kernel, string collectionName, SearchClient searchClient)
        {
            _kernel = kernel;
            _collectionName = collectionName;
            _searchClient = searchClient;
        }

        [KernelFunction("Search")]
        [Description("Search for documentation in the API wiki information")]
        public async Task<IEnumerable<string>> SearchAsync(string query)
        {
            try
            {
                var options = new SearchOptions()
                {
                    IncludeTotalCount = true,
                    Filter = ""
                };

                options = new SearchOptions()
                {
                    QueryType = Azure.Search.Documents.Models.SearchQueryType.Semantic,
                    SemanticSearch = new()
                    {
                        SemanticConfigurationName = "my-semantic-config",
                        QueryCaption = new(QueryCaptionType.Extractive)
                    }
                };

                options.Select.Add("apiContent");
                options.Select.Add("reference");
                options.Select.Add("id");


                var searchResult = await _searchClient.SearchAsync<IndexSchema>(query, options);

                var results = new List<string>();

                await foreach (var record in searchResult.Value.GetResultsAsync())
                {
                    var content = $"Content:{record.Document.ApiContent}, Reference: {record.Document.Reference}";

                    results.Add(content);
                }

                return results;
            }
            catch (Exception ex)
            {
                // Log or handle the exception as needed
                Console.WriteLine($"An error occurred during documentation search: {ex.Message}");
                return Enumerable.Empty<string>();
            }
        }

        public class IndexSchema
        {

            [JsonPropertyName("id")]
            [VectorStoreRecordKey]
            public string Id { get; set; }

            [JsonPropertyName("apiContent")]
            [VectorStoreRecordData]
            public string ApiContent { get; set; }

            [JsonPropertyName("apiContentVector")]
            [VectorStoreRecordVector(Dimensions: 1536)]
            public ReadOnlyMemory<float> ApiContentVector { get; set; }

            [JsonPropertyName("reference")]
            public string Reference { get; set; }

        }
    }
}