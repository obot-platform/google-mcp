"""Google Groups Members API operations"""
from googleapiclient.errors import HttpError
from fastmcp.exceptions import ToolError
from .helper import logger


def list_members(service, group_email: str, max_results: int = 50, page_token: str | None = None):
    """List all members in a group.
    
    Args:
        service: Google Directory API service client
        group_email: Email address of the group
        max_results: Maximum number of results to return (1-200)
        page_token: Optional token for pagination
        
    Returns:
        Dictionary with members list and nextPageToken if available
    """
    try:
        params = {
            "groupKey": group_email,
            "maxResults": max_results,
        }
        
        if page_token:
            params["pageToken"] = page_token
            
        result = service.members().list(**params).execute()
        
        return {
            "members": result.get("members", []),
            "nextPageToken": result.get("nextPageToken")
        }
    except HttpError as err:
        logger.error(f"Failed to list members for group {group_email}. HttpError: {err}")
        raise ToolError(f"Failed to list members for group {group_email}. HttpError: {err}")
    except Exception as e:
        logger.error(f"Failed to list members for group {group_email}. Exception: {e}")
        raise ToolError(f"Failed to list members for group {group_email}. Exception: {e}")


def get_member(service, group_email: str, member_email: str):
    """Get details of a specific member in a group.
    
    Args:
        service: Google Directory API service client
        group_email: Email address of the group
        member_email: Email address of the member
        
    Returns:
        Dictionary with member details
    """
    try:
        member = service.members().get(groupKey=group_email, memberKey=member_email).execute()
        return member
    except HttpError as err:
        logger.error(f"Failed to get member {member_email} in group {group_email}. HttpError: {err}")
        raise ToolError(f"Failed to get member {member_email} in group {group_email}. HttpError: {err}")
    except Exception as e:
        logger.error(f"Failed to get member {member_email} in group {group_email}. Exception: {e}")
        raise ToolError(f"Failed to get member {member_email} in group {group_email}. Exception: {e}")


def add_member(service, group_email: str, member_email: str, role: str = "MEMBER"):
    """Add a member to a group.
    
    Args:
        service: Google Directory API service client
        group_email: Email address of the group
        member_email: Email address of the member to add
        role: Role of the member (OWNER, MANAGER, MEMBER)
        
    Returns:
        Dictionary with added member details
    """
    try:
        member_body = {
            "email": member_email,
            "role": role
        }
        
        member = service.members().insert(groupKey=group_email, body=member_body).execute()
        return member
    except HttpError as err:
        logger.error(f"Failed to add member {member_email} to group {group_email}. HttpError: {err}")
        raise ToolError(f"Failed to add member {member_email} to group {group_email}. HttpError: {err}")
    except Exception as e:
        logger.error(f"Failed to add member {member_email} to group {group_email}. Exception: {e}")
        raise ToolError(f"Failed to add member {member_email} to group {group_email}. Exception: {e}")


def update_member(service, group_email: str, member_email: str, role: str):
    """Update a member's role in a group.
    
    Args:
        service: Google Directory API service client
        group_email: Email address of the group
        member_email: Email address of the member to update
        role: New role for the member (OWNER, MANAGER, MEMBER)
        
    Returns:
        Dictionary with updated member details
    """
    try:
        member_body = {
            "email": member_email,
            "role": role
        }
        
        member = service.members().update(
            groupKey=group_email, 
            memberKey=member_email, 
            body=member_body
        ).execute()
        return member
    except HttpError as err:
        logger.error(f"Failed to update member {member_email} in group {group_email}. HttpError: {err}")
        raise ToolError(f"Failed to update member {member_email} in group {group_email}. HttpError: {err}")
    except Exception as e:
        logger.error(f"Failed to update member {member_email} in group {group_email}. Exception: {e}")
        raise ToolError(f"Failed to update member {member_email} in group {group_email}. Exception: {e}")


def remove_member(service, group_email: str, member_email: str):
    """Remove a member from a group.
    
    Args:
        service: Google Directory API service client
        group_email: Email address of the group
        member_email: Email address of the member to remove
        
    Returns:
        Success message
    """
    try:
        service.members().delete(groupKey=group_email, memberKey=member_email).execute()
        return f"Member {member_email} removed from group {group_email} successfully."
    except HttpError as err:
        logger.error(f"Failed to remove member {member_email} from group {group_email}. HttpError: {err}")
        raise ToolError(f"Failed to remove member {member_email} from group {group_email}. HttpError: {err}")
    except Exception as e:
        logger.error(f"Failed to remove member {member_email} from group {group_email}. Exception: {e}")
        raise ToolError(f"Failed to remove member {member_email} from group {group_email}. Exception: {e}")


def has_member(service, group_email: str, member_email: str):
    """Check if a user is a member of a group.
    
    Args:
        service: Google Directory API service client
        group_email: Email address of the group
        member_email: Email address to check
        
    Returns:
        Dictionary with membership status
    """
    try:
        result = service.members().hasMember(
            groupKey=group_email, 
            memberKey=member_email
        ).execute()
        return result
    except HttpError as err:
        logger.error(f"Failed to check membership of {member_email} in group {group_email}. HttpError: {err}")
        raise ToolError(f"Failed to check membership of {member_email} in group {group_email}. HttpError: {err}")
    except Exception as e:
        logger.error(f"Failed to check membership of {member_email} in group {group_email}. Exception: {e}")
        raise ToolError(f"Failed to check membership of {member_email} in group {group_email}. Exception: {e}")

