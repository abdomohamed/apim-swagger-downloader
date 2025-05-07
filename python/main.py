#!/usr/bin/env python3
import os
import sys
import argparse
import logging
from src.config import Config
from src.apim_swagger_downloader import APIMSwaggerDownloader
from src.swagger_to_markdown import SwaggerToMarkdownConverter
from src.azure_search_indexer import AzureSearchIndexer
from src.wiki_document_processor import WikiDocumentProcessor

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def parse_arguments():
    """Parse command line arguments"""
    parser = argparse.ArgumentParser(description='APIM Swagger Downloader and Processor')
    
    parser.add_argument('--config', type=str, help='Path to config file')
    parser.add_argument('--download-only', action='store_true', help='Only download swagger files, don\'t convert')
    parser.add_argument('--convert-only', action='store_true', help='Only convert swagger to markdown, don\'t download')
    parser.add_argument('--index-only', action='store_true', help='Only index markdown files to Azure Search')
    parser.add_argument('--wiki-only', action='store_true', help='Only process wiki documents, don\'t download or convert swagger')

    return parser.parse_args()

def main():
    """Main function that runs the APIM Swagger processing pipeline"""
    # Parse command-line arguments
    args = parse_arguments()
    
    # Load configuration
    try:
        config = Config(args.config)
    except Exception as e:
        logger.error(f"Error loading configuration: {str(e)}")
        return 1
    
    # Get processing settings
    processing_settings = config.get_processing_settings()
    
    # Track results for reporting
    downloaded_files = []
    converted_files = []
    indexed_count = 0
    
    # Step 1: Download swagger files
    if not args.convert_only and not args.index_only:
        try:
            logger.info("=== STEP 1: Downloading Swagger files from APIM ===")
            downloader = APIMSwaggerDownloader(config)
            downloaded_files = downloader.download_all_swaggers()
            
            if not downloaded_files:
                logger.warning("No swagger files were downloaded.")
        except Exception as e:
            logger.error(f"Error downloading swagger files: {str(e)}")
            return 1
    
    # Step 2: Convert swagger to markdown
    if (not args.download_only and not args.index_only and processing_settings.get('convert_to_markdown', True)) or args.convert_only:
        try:
            logger.info("=== STEP 2: Converting Swagger files to Markdown ===")
            converter = SwaggerToMarkdownConverter(config)
            
            # If we're only converting, use all available swagger files
            if args.convert_only:
                downloaded_files = None
                
            converted_files = converter.convert_all_swagger_files(downloaded_files)
            
            if not converted_files:
                logger.warning("No markdown files were generated.")
        except Exception as e:
            logger.error(f"Error converting swagger to markdown: {str(e)}")
            if not args.convert_only:  # Only exit if this isn't a convert-only run
                return 1

    # Step 2.5: Process wiki documents
    if (not args.download_only and not args.convert_only and not args.index_only and
        processing_settings.get('process_wiki', True)) or args.wiki_only:
        try:
            logger.info("=== STEP 2.5: Processing Wiki Documents ===")
            wiki_processor = WikiDocumentProcessor(config)
            wiki_processed = wiki_processor.process_wiki_documents()
            
            logger.info(f"Processed {wiki_processed} wiki documents")
        except Exception as e:
            logger.error(f"Error processing wiki documents: {str(e)}")
            if args.wiki_only:  # Only exit if this is a wiki-only run
                return 1
            
    # Step 3: Index markdown in Azure AI Search
    if (not args.download_only and not args.convert_only and processing_settings.get('upload_to_search', True)) or args.index_only:
        try:
            logger.info("=== STEP 3: Indexing Markdown files in Azure AI Search ===")
            indexer = AzureSearchIndexer(config)
            
            # If we're only indexing, use all available markdown files
            if args.index_only:
                converted_files = None
                
            indexed_count = indexer.index_markdown_files(converted_files)
            
            if indexed_count == 0:
                logger.warning("No files were indexed in Azure AI Search.")
        except Exception as e:
            logger.error(f"Error indexing markdown files: {str(e)}")
            return 1
    
    # Print summary
    logger.info("\n=== Processing Complete ===")
    logger.info(f"Downloaded: {len(downloaded_files) if downloaded_files else 0} swagger files")
    logger.info(f"Converted: {len(converted_files) if converted_files else 0} markdown files")
    logger.info(f"Indexed: {indexed_count} files in Azure AI Search")
    
    return 0

if __name__ == "__main__":
    sys.exit(main())