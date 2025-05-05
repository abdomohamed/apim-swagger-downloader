# Repository Overview

This repository contains two main folders, `python` and `dotnet`, each serving a different purpose in the project.

## Python Folder

Is a data ingeestion tool responsible for downloading api(s) swagger definition and convert them to a human readable markdown format, and then ingest them to an azure AI search index. 

The `python` folder includes the following files and subdirectories:

1. **[README.md](https://github.com/abdomohamed/apim-swagger-downloader/blob/main/python/README.md)**: Documentation specific to the Python-related components.
2. **[main.py](https://github.com/abdomohamed/apim-swagger-downloader/blob/main/python/main.py)**: The main Python script for executing the functionalities of this project.
3. **[requirements.txt](https://github.com/abdomohamed/apim-swagger-downloader/blob/main/python/requirements.txt)**: A file listing the dependencies required to run the Python script.
4. **[src](https://github.com/abdomohamed/apim-swagger-downloader/tree/main/python/src)**: A directory containing the source code for the apim apis swagger data ingestion tool. 

## Dotnet Folder

Is an AI Agent built on top Semantic Kernel library, it acts as an expert on answering questions about the ingested API(s) swagger definitions. 

The `dotnet` folder includes the following:

1. **[README.md](https://github.com/abdomohamed/apim-swagger-downloader/blob/main/dotnet/README.md)**: Documentation explaining what the ApiMgmtAiAgent project is and how to run it.
2. **[ApiMgmtAiAgent](https://github.com/abdomohamed/apim-swagger-downloader/tree/main/dotnet/ApiMgmtAiAgent)**: This folder contains the .NET implementation for the project including the AI Agent for answering API-related questions.

Feel free to explore the respective folders to understand the components better.
