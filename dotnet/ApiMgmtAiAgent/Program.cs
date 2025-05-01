using System;
using System.Threading.Tasks;
using ApiMgmtAiAgent.Config;
using ApiMgmtAiAgent.Services;


Console.WriteLine("Starting API Management AI Agent...");

try
{
    // Initialize configuration
    var config = new ConfigurationManager();

    // Initialize services
    var aiService = new AIService(config);

    var chatService = new ChatService(aiService);

    // Run chat loop
    await chatService.RunChatLoopAsync();
}
catch (Exception ex)
{
    Console.WriteLine($"Error: {ex.Message}");
    Console.WriteLine(ex.StackTrace);
}
