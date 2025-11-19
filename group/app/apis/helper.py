import sys
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
import logging
from fastmcp.exceptions import ToolError


def setup_logger(name, tool_name: str = "Google Groups MCP server"):
    """Setup a logger that writes to sys.stderr. This will eventually show up in GPTScript's debugging logs.

    Args:
        name (str): The name of the logger.

    Returns:
        logging.Logger: The logger.
    """
    # Create a logger
    logger = logging.getLogger(name)
    logger.setLevel(logging.DEBUG)  # Set the logging level

    # Create a stream handler that writes to sys.stderr
    stderr_handler = logging.StreamHandler(sys.stderr)

    # Create a log formatter
    formatter = logging.Formatter(
        f"[{tool_name} Debugging Log]: %(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )
    stderr_handler.setFormatter(formatter)

    # Add the handler to the logger
    logger.addHandler(stderr_handler)

    return logger


logger = setup_logger(__name__)


def get_client(cred_token: str):
    """Build Google Directory API client for Groups management.
    
    Args:
        cred_token: OAuth access token
        
    Returns:
        Google Directory API service client
    """
    creds = Credentials(token=cred_token)
    try:
        # Google Groups are managed via the Directory API
        service = build(serviceName="admin", version="directory_v1", credentials=creds)
        return service
    except HttpError as err:
        raise ToolError(f"Failed to build Google Directory API client. HttpError: {err}")

