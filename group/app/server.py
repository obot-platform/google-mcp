from fastmcp import FastMCP
from pydantic import Field
from typing import Annotated, Literal
import os
from .apis.helper import setup_logger, get_client
from googleapiclient.errors import HttpError
from fastmcp.exceptions import ToolError
from fastmcp.server.dependencies import get_http_headers
from .apis.groups import (
    list_groups,
    get_group,
    create_group,
    update_group,
    delete_group,
)
from .apis.members import (
    list_members,
    get_member,
    add_member,
    update_member,
    remove_member,
    has_member,
)
from .apis.domains import (
    list_domains,
    get_domain,
)
from starlette.requests import Request
from starlette.responses import JSONResponse

logger = setup_logger(__name__)

# Configure server-specific settings
PORT = int(os.getenv("PORT", 9000))
MCP_PATH = os.getenv("MCP_PATH", "/")

mcp = FastMCP(
    name="GoogleGroupsMCPServer",
    on_duplicate_tools="error",
    on_duplicate_resources="warn",
    on_duplicate_prompts="replace",
)


def _get_access_token() -> str:
    headers = get_http_headers()
    access_token = headers.get("x-forwarded-access-token", None)
    if not access_token:
        raise ToolError(
            "No access token found in headers, available headers: " + str(headers)
        )
    return access_token


@mcp.custom_route("/health", methods=["GET"])
async def health_check(request: Request):
    return JSONResponse({"status": "healthy"})


@mcp.tool(
    annotations={
        "readOnlyHint": True,
        "destructiveHint": False,
    },
)
def list_google_groups(
    max_results: Annotated[
        int,
        Field(description="Maximum number of groups to return", ge=1, le=200)
    ] = 50,
    domain: Annotated[
        str | None,
        Field(description="Optional domain to filter groups by")
    ] = None,
    page_token: Annotated[
        str | None,
        Field(description="Optional token for pagination")
    ] = None,
) -> dict:
    """Lists all Google Groups in the domain. Returns a list of groups and a nextPageToken for pagination if available."""
    try:
        service = get_client(_get_access_token())
        result = list_groups(
            service, 
            max_results=max_results, 
            domain=domain, 
            page_token=page_token
        )
        return result
    except HttpError as err:
        raise ToolError(f"Failed to list Google Groups. HttpError: {err}")


@mcp.tool(
    annotations={
        "readOnlyHint": True,
        "destructiveHint": False,
    },
)
def get_google_group(
    group_email: Annotated[str, Field(description="Email address of the group to get")],
) -> dict:
    """Get details of a specific Google Group by its email address."""
    if group_email == "":
        raise ValueError("argument `group_email` can't be empty")
    service = get_client(_get_access_token())
    try:
        group = get_group(service, group_email)
        return group
    except HttpError as err:
        raise ToolError(f"Failed to get Google Group. HttpError: {err}")
    except Exception as e:
        raise ToolError(f"Failed to get Google Group. Exception: {e}")


@mcp.tool()
def create_google_group(
    email: Annotated[str, Field(description="Email address for the new group")],
    name: Annotated[str, Field(description="Display name for the new group")],
    description: Annotated[
        str,
        Field(description="Description for the new group")
    ] = "",
) -> dict:
    """Creates a new Google Group."""
    if email == "":
        raise ValueError("argument `email` can't be empty")
    if name == "":
        raise ValueError("argument `name` can't be empty")
    service = get_client(_get_access_token())
    try:
        group = create_group(service, email, name, description)
        return group
    except HttpError as err:
        raise ToolError(f"Failed to create Google Group. HttpError: {err}")
    except Exception as e:
        raise ToolError(f"Failed to create Google Group. Exception: {e}")


@mcp.tool()
def update_google_group(
    group_email: Annotated[str, Field(description="Email address of the group to update")],
    name: Annotated[
        str | None,
        Field(description="New display name for the group")
    ] = None,
    description: Annotated[
        str | None,
        Field(description="New description for the group")
    ] = None,
) -> dict:
    """Updates an existing Google Group."""
    if group_email == "":
        raise ValueError("argument `group_email` can't be empty")
    service = get_client(_get_access_token())
    try:
        group = update_group(service, group_email, name, description)
        return group
    except HttpError as err:
        raise ToolError(f"Failed to update Google Group. HttpError: {err}")
    except Exception as e:
        raise ToolError(f"Failed to update Google Group. Exception: {e}")


@mcp.tool()
def delete_google_group(
    group_email: Annotated[str, Field(description="Email address of the group to delete")],
) -> str:
    """Deletes a Google Group"""
    if group_email == "":
        raise ValueError("argument `group_email` can't be empty")
    service = get_client(_get_access_token())
    try:
        result = delete_group(service, group_email)
        return result
    except HttpError as err:
        raise ToolError(f"Failed to delete Google Group. HttpError: {err}")
    except Exception as e:
        raise ToolError(f"Failed to delete Google Group. Exception: {e}")


@mcp.tool(
    annotations={
        "readOnlyHint": True,
        "destructiveHint": False,
    },
)
def list_group_members(
    group_email: Annotated[str, Field(description="Email address of the group")],
    max_results: Annotated[
        int,
        Field(description="Maximum number of members to return", ge=1, le=200)
    ] = 50,
    page_token: Annotated[
        str | None,
        Field(description="Optional token for pagination")
    ] = None,
) -> dict:
    """Lists all members in a Google Group. Returns a list of members and a nextPageToken for pagination if available."""
    if group_email == "":
        raise ValueError("argument `group_email` can't be empty")
    service = get_client(_get_access_token())
    try:
        result = list_members(service, group_email, max_results, page_token)
        return result
    except HttpError as err:
        raise ToolError(
            f"Failed to list members from group {group_email}. HttpError: {err}"
        )
    except Exception as e:
        raise ToolError(
            f"Failed to list members from group {group_email}. Exception: {e}"
        )


@mcp.tool(
    annotations={
        "readOnlyHint": True,
        "destructiveHint": False,
    },
)
def get_group_member(
    group_email: Annotated[str, Field(description="Email address of the group")],
    member_email: Annotated[str, Field(description="Email address of the member")],
) -> dict:
    """Gets details of a specific member in a Google Group."""
    if group_email == "":
        raise ValueError("argument `group_email` can't be empty")
    if member_email == "":
        raise ValueError("argument `member_email` can't be empty")
    service = get_client(_get_access_token())
    try:
        member = get_member(service, group_email, member_email)
        return member
    except HttpError as err:
        raise ToolError(
            f"Failed to get member {member_email} from group {group_email}. HttpError: {err}"
        )
    except Exception as e:
        raise ToolError(
            f"Failed to get member {member_email} from group {group_email}. Exception: {e}"
        )


@mcp.tool()
def add_group_member(
    group_email: Annotated[str, Field(description="Email address of the group")],
    member_email: Annotated[str, Field(description="Email address of the member to add")],
    role: Annotated[
        Literal["OWNER", "MANAGER", "MEMBER"],
        Field(description="Role of the member in the group")
    ] = "MEMBER",
) -> dict:
    """Adds a member to a Google Group."""
    if group_email == "":
        raise ValueError("argument `group_email` can't be empty")
    if member_email == "":
        raise ValueError("argument `member_email` can't be empty")
    service = get_client(_get_access_token())
    try:
        member = add_member(service, group_email, member_email, role)
        return member
    except HttpError as err:
        raise ToolError(
            f"Failed to add member {member_email} to group {group_email}. HttpError: {err}"
        )
    except Exception as e:
        raise ToolError(
            f"Failed to add member {member_email} to group {group_email}. Exception: {e}"
        )


@mcp.tool()
def update_group_member(
    group_email: Annotated[str, Field(description="Email address of the group")],
    member_email: Annotated[str, Field(description="Email address of the member to update")],
    role: Annotated[
        Literal["OWNER", "MANAGER", "MEMBER"],
        Field(description="New role for the member")
    ],
) -> dict:
    """Updates a member's role in a Google Group."""
    if group_email == "":
        raise ValueError("argument `group_email` can't be empty")
    if member_email == "":
        raise ValueError("argument `member_email` can't be empty")
    service = get_client(_get_access_token())
    try:
        member = update_member(service, group_email, member_email, role)
        return member
    except HttpError as err:
        raise ToolError(
            f"Failed to update member {member_email} in group {group_email}. HttpError: {err}"
        )
    except Exception as e:
        raise ToolError(
            f"Failed to update member {member_email} in group {group_email}. Exception: {e}"
        )


@mcp.tool()
def remove_group_member(
    group_email: Annotated[str, Field(description="Email address of the group")],
    member_email: Annotated[str, Field(description="Email address of the member to remove")],
) -> str:
    """Removes a member from a Google Group."""
    if group_email == "":
        raise ValueError("argument `group_email` can't be empty")
    if member_email == "":
        raise ValueError("argument `member_email` can't be empty")
    service = get_client(_get_access_token())
    try:
        result = remove_member(service, group_email, member_email)
        return result
    except HttpError as err:
        raise ToolError(
            f"Failed to remove member {member_email} from group {group_email}. HttpError: {err}"
        )
    except Exception as e:
        raise ToolError(
            f"Failed to remove member {member_email} from group {group_email}. Exception: {e}"
        )


@mcp.tool(
    annotations={
        "readOnlyHint": True,
        "destructiveHint": False,
    },
)
def check_group_membership(
    group_email: Annotated[str, Field(description="Email address of the group")],
    member_email: Annotated[str, Field(description="Email address to check")],
) -> dict:
    """Checks if a user is a member of a Google Group."""
    if group_email == "":
        raise ValueError("argument `group_email` can't be empty")
    if member_email == "":
        raise ValueError("argument `member_email` can't be empty")
    service = get_client(_get_access_token())
    try:
        result = has_member(service, group_email, member_email)
        return result
    except HttpError as err:
        raise ToolError(
            f"Failed to check membership of {member_email} in group {group_email}. HttpError: {err}"
        )
    except Exception as e:
        raise ToolError(
            f"Failed to check membership of {member_email} in group {group_email}. Exception: {e}"
        )


@mcp.tool(
    annotations={
        "readOnlyHint": True,
        "destructiveHint": False,
    },
)
def list_google_domains() -> dict:
    """Lists all domains in the Google Workspace account. This is useful to see which domains are available for creating groups."""
    try:
        service = get_client(_get_access_token())
        result = list_domains(service)
        return result
    except HttpError as err:
        raise ToolError(f"Failed to list domains. HttpError: {err}")


@mcp.tool(
    annotations={
        "readOnlyHint": True,
        "destructiveHint": False,
    },
)
def get_google_domain(
    domain_name: Annotated[str, Field(description="The domain name to retrieve details for")],
) -> dict:
    """Get details of a specific domain in the Google Workspace account."""
    if domain_name == "":
        raise ToolError("domain_name cannot be empty")
    
    try:
        service = get_client(_get_access_token())
        result = get_domain(service, domain_name)
        return result
    except HttpError as err:
        raise ToolError(f"Failed to get domain {domain_name}. HttpError: {err}")


def streamable_http_server():
    """Main entry point for the Google Groups MCP server."""
    mcp.run(
        transport="streamable-http",  # fixed to streamable-http
        host="0.0.0.0",
        port=PORT,
        path=MCP_PATH,
    )


def stdio_server():
    """Main entry point for the Google Groups MCP server."""
    mcp.run()


if __name__ == "__main__":
    streamable_http_server()

