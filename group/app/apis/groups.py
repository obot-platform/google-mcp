"""Google Groups API operations"""
from googleapiclient.errors import HttpError
from fastmcp.exceptions import ToolError
from .helper import logger


def list_groups(service, max_results: int = 50, customer: str = "my_customer", domain: str | None = None, page_token: str | None = None):
    """List all groups in the domain.
    
    Args:
        service: Google Directory API service client
        max_results: Maximum number of results to return (1-200)
        customer: Customer ID (use 'my_customer' for current account)
        domain: Optional domain to filter groups by
        page_token: Optional token for pagination
        
    Returns:
        Dictionary with groups list and nextPageToken if available
    """
    try:
        params = {
            "customer": customer,
            "maxResults": max_results,
        }
        
        if domain:
            params["domain"] = domain
            
        if page_token:
            params["pageToken"] = page_token
            
        result = service.groups().list(**params).execute()
        
        return {
            "groups": result.get("groups", []),
            "nextPageToken": result.get("nextPageToken")
        }
    except HttpError as err:
        logger.error(f"Failed to list groups. HttpError: {err}")
        raise ToolError(f"Failed to list groups. HttpError: {err}")
    except Exception as e:
        logger.error(f"Failed to list groups. Exception: {e}")
        raise ToolError(f"Failed to list groups. Exception: {e}")


def get_group(service, group_email: str):
    """Get details of a specific group.
    
    Args:
        service: Google Directory API service client
        group_email: Email address of the group
        
    Returns:
        Dictionary with group details
    """
    try:
        group = service.groups().get(groupKey=group_email).execute()
        return group
    except HttpError as err:
        logger.error(f"Failed to get group {group_email}. HttpError: {err}")
        raise ToolError(f"Failed to get group {group_email}. HttpError: {err}")
    except Exception as e:
        logger.error(f"Failed to get group {group_email}. Exception: {e}")
        raise ToolError(f"Failed to get group {group_email}. Exception: {e}")


def create_group(service, email: str, name: str, description: str = ""):
    """Create a new group.
    
    Args:
        service: Google Directory API service client
        email: Email address for the group
        name: Display name for the group
        description: Optional description
        
    Returns:
        Dictionary with created group details
    """
    try:
        group_body = {
            "email": email,
            "name": name,
            "description": description
        }
        
        group = service.groups().insert(body=group_body).execute()
        return group
    except HttpError as err:
        logger.error(f"Failed to create group. HttpError: {err}")
        raise ToolError(f"Failed to create group. HttpError: {err}")
    except Exception as e:
        logger.error(f"Failed to create group. Exception: {e}")
        raise ToolError(f"Failed to create group. Exception: {e}")


def update_group(service, group_email: str, name: str | None = None, description: str | None = None):
    """Update an existing group.
    
    Args:
        service: Google Directory API service client
        group_email: Email address of the group to update
        name: Optional new display name
        description: Optional new description
        
    Returns:
        Dictionary with updated group details
    """
    try:
        # First get the current group
        group = service.groups().get(groupKey=group_email).execute()
        
        # Update only the fields that are provided
        if name:
            group["name"] = name
        if description is not None:  # Allow empty string
            group["description"] = description
            
        updated_group = service.groups().update(groupKey=group_email, body=group).execute()
        return updated_group
    except HttpError as err:
        logger.error(f"Failed to update group {group_email}. HttpError: {err}")
        raise ToolError(f"Failed to update group {group_email}. HttpError: {err}")
    except Exception as e:
        logger.error(f"Failed to update group {group_email}. Exception: {e}")
        raise ToolError(f"Failed to update group {group_email}. Exception: {e}")


def delete_group(service, group_email: str):
    """Delete a group.
    
    Args:
        service: Google Directory API service client
        group_email: Email address of the group to delete
        
    Returns:
        Success message
    """
    try:
        service.groups().delete(groupKey=group_email).execute()
        return f"Group {group_email} deleted successfully."
    except HttpError as err:
        logger.error(f"Failed to delete group {group_email}. HttpError: {err}")
        raise ToolError(f"Failed to delete group {group_email}. HttpError: {err}")
    except Exception as e:
        logger.error(f"Failed to delete group {group_email}. Exception: {e}")
        raise ToolError(f"Failed to delete group {group_email}. Exception: {e}")

