using Azure.Search.Documents;
using Azure.Search.Documents.Indexes;
using Azure.Search.Documents.Models;
using Microsoft.Extensions.VectorData;
using Microsoft.SemanticKernel;
using System.ComponentModel;
using System.ComponentModel.Design;
using System.Net;
using System.Text.Json.Serialization;

public class ApiSearchPlugin
{
    private readonly Kernel _kernel;
    private readonly string _collectionName;
    private readonly SearchClient _searchClient;

    public ApiSearchPlugin(Kernel kernel, string collectionName, SearchClient searchClient)
    {
        _kernel = kernel;
        _collectionName = collectionName;
        _searchClient = searchClient;   
    }

    [KernelFunction("Search")]
    [Description("Search for apis in the API Management service catalogue")]
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

            //var vectorStore = _kernel.GetRequiredService<IVectorStore>();

            //var collection = vectorStore.GetCollection<string, IndexSchema>(_collectionName);

            //var vectorSearchOptions = new VectorSearchOptions<IndexSchema>
            //{
            //    VectorProperty = r => r.ApiContentVector,
            //};

            //// Perform search request
            //var searchResult = collection.SearchAsync(query, top: 5, vectorSearchOptions);

            var searchResult = await _searchClient.SearchAsync<IndexSchema>(options);

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
            Console.WriteLine($"An error occurred during search: {ex.Message}");
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