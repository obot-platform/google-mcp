"""Google Workspace Domains API operations"""
from googleapiclient.errors import HttpError
from fastmcp.exceptions import ToolError
from .helper import logger


def list_domains(service, customer: str = "my_customer"):
    """List all domains in the Google Workspace account.
    
    Args:
        service: Google Directory API service client
        customer: Customer ID (use 'my_customer' for current account)
        
    Returns:
        Dictionary with domains list
    """
    try:
        result = service.domains().list(customer=customer).execute()
        
        return {
            "domains": result.get("domains", [])
        }
    except HttpError as err:
        logger.error(f"Failed to list domains. HttpError: {err}")
        raise ToolError(f"Failed to list domains. HttpError: {err}")
    except Exception as e:
        logger.error(f"Failed to list domains. Exception: {e}")
        raise ToolError(f"Failed to list domains. Exception: {e}")


def get_domain(service, domain_name: str, customer: str = "my_customer"):
    """Get details of a specific domain.
    
    Args:
        service: Google Directory API service client
        domain_name: The domain name to retrieve
        customer: Customer ID (use 'my_customer' for current account)
        
    Returns:
        Dictionary with domain details
    """
    try:
        result = service.domains().get(
            customer=customer,
            domainName=domain_name
        ).execute()
        
        return result
    except HttpError as err:
        logger.error(f"Failed to get domain. HttpError: {err}")
        raise ToolError(f"Failed to get domain. HttpError: {err}")
    except Exception as e:
        logger.error(f"Failed to get domain. Exception: {e}")
        raise ToolError(f"Failed to get domain. Exception: {e}")
