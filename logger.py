import logging
import os

def get_logger(logger_name: str = "DolapScraper") -> logging.Logger:
    """
    Creates and configures a custom logger with both file and stream handlers.
    """
    # Ensure the 'logs' directory exists
    os.makedirs("logs", exist_ok=True)

    # Create a custom logger
    logger = logging.getLogger(logger_name)
    
    # Set the default log level
    logger.setLevel(logging.INFO)
    
    # Prevent adding multiple handlers if the logger is called multiple times
    if not logger.handlers:
        # Define the format for the logs
        log_format = logging.Formatter(
            "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
        )
        
        # 1. Console Handler (Outputs to terminal)
        console_handler = logging.StreamHandler()
        console_handler.setFormatter(log_format)
        
        # 2. File Handler (Outputs to file)
        file_handler = logging.FileHandler("logs/scraper.log", encoding="utf-8")
        file_handler.setFormatter(log_format)
        
        # Add both handlers to the logger
        logger.addHandler(console_handler)
        logger.addHandler(file_handler)
        
    return logger