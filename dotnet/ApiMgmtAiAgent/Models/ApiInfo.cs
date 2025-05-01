using System.Collections.Generic;

namespace ApiMgmtAiAgent.Models
{
    /// <summary>
    /// Represents an API in Azure API Management
    /// </summary>
    public class ApiInfo
    {
        /// <summary>
        /// Internal name of the API
        /// </summary>
        public string Name { get; set; }

        /// <summary>
        /// Display name of the API shown in the developer portal
        /// </summary>
        public string DisplayName { get; set; }

        /// <summary>
        /// Description of the API
        /// </summary>
        public string Description { get; set; }

        /// <summary>
        /// Base URL path for the API
        /// </summary>
        public string Path { get; set; }

        /// <summary>
        /// Collection of operations (endpoints) available in this API
        /// </summary>
        public List<OperationInfo> Operations { get; set; } = new List<OperationInfo>();
    }
}