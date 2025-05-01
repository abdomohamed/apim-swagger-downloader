using System.Collections.Generic;

namespace ApiMgmtAiAgent.Models
{
    /// <summary>
    /// Represents an operation (endpoint) in an Azure API Management API
    /// </summary>
    public class OperationInfo
    {
        /// <summary>
        /// Internal name of the operation
        /// </summary>
        public string Name { get; set; }

        /// <summary>
        /// Display name shown in the developer portal
        /// </summary>
        public string DisplayName { get; set; }

        /// <summary>
        /// HTTP method (GET, POST, PUT, DELETE, etc.)
        /// </summary>
        public string Method { get; set; }

        /// <summary>
        /// URL template pattern for the operation (e.g., /users/{userId})
        /// </summary>
        public string UrlTemplate { get; set; }

        /// <summary>
        /// Description of the operation
        /// </summary>
        public string Description { get; set; }

        /// <summary>
        /// Collection of parameters for this operation
        /// </summary>
        public List<ParameterInfo> Parameters { get; set; } = new List<ParameterInfo>();
    }
}