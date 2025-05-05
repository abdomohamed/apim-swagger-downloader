using System;
using System.Collections.Generic;
using System.ComponentModel;
using System.Text.Json.Serialization;
using System.Threading.Tasks;
using Azure.Search.Documents.Indexes;
using Microsoft.Extensions.VectorData;
using Microsoft.SemanticKernel;

namespace ApiMgmtAiAgent.Services.Plugins
{
    /// <summary>
    /// Plugin for searching documentation in Azure AI Search
    /// </summary>
    public class DocSearchPlugin
    {
        private readonly Kernel _kernel;
        private readonly string _collectionName;

        public DocSearchPlugin(Kernel kernel, string collectionName)
        {
            _kernel = kernel;
            _collectionName = collectionName;
        }

        [KernelFunction("Search")]
        [Description("Search for documentation in the API Management patterns and integrations")]
        public async Task<IEnumerable<string>> SearchAsync(string query)
        {
            try
            {
                var vectorStore = _kernel.GetRequiredService<IVectorStore>();

                var collection = vectorStore.GetCollection<string, IndexSchema>(_collectionName);

                var vectorSearchOptions = new VectorSearchOptions<IndexSchema>
                {
                    VectorProperty = r => r.Vector,
                };

                // Perform search request
                var searchResult = collection.SearchAsync(query, top: 5, vectorSearchOptions);

                var results = new List<string>();

                await foreach (var record in searchResult)
                {
                    var content = record.Record.Content;
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

            [JsonPropertyName("title")]
            [VectorStoreRecordData]
            public string Title { get; set; }

            [JsonPropertyName("content")]
            [VectorStoreRecordData]
            public string Content { get; set; }

            [JsonPropertyName("documentType")]
            public string DocumentType { get; set; }

            [JsonPropertyName("lastUpdated")]
            public string LastUpdated { get; set; }

            [JsonPropertyName("vector")]
            [VectorStoreRecordVector(Dimensions: 1536)]
            public ReadOnlyMemory<float> Vector { get; set; }
        }
    }
}