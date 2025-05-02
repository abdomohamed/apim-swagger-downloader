using System.ComponentModel;
using System.Text.Json.Serialization;
using Azure.Search.Documents.Indexes;
using Microsoft.Extensions.VectorData;
using Microsoft.SemanticKernel;

public class ApiSearchPlugin
{
    private readonly Kernel _kernel;
    private readonly string _collectionName;

    public ApiSearchPlugin(Kernel kernel, string collectionName )
    {
        _kernel = kernel;
        _collectionName = collectionName;
    }

    [KernelFunction("Search")]
    [Description("Search for apis in the API Management service catalogue")]
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
            Console.WriteLine($"An error occurred during search: {ex.Message}");
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

        [JsonPropertyName("apiName")]
        public string ApiName { get; set; }

        [JsonPropertyName("apiVersion")]
        public string ApiVersion { get; set; }

        [JsonPropertyName("vector")]
        [VectorStoreRecordVector(Dimensions: 1536)]
        public ReadOnlyMemory<float> Vector { get; set; }
    }
}