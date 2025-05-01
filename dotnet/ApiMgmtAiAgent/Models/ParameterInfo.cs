namespace ApiMgmtAiAgent.Models
{
    /// <summary>
    /// Represents a parameter for an API operation
    /// </summary>
    public class ParameterInfo
    {
        /// <summary>
        /// Name of the parameter
        /// </summary>
        public string Name { get; set; }

        /// <summary>
        /// Description of the parameter
        /// </summary>
        public string Description { get; set; }

        /// <summary>
        /// Data type of the parameter (string, integer, boolean, etc.)
        /// </summary>
        public string Type { get; set; }

        /// <summary>
        /// Whether the parameter is required for the operation
        /// </summary>
        public bool Required { get; set; }
    }
}