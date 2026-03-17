"""HTTP client helpers for GA REST APIs.

All GA API calls use direct httpx REST requests rather than the gRPC-based
client libraries. This is more reliable with bare OAuth access tokens (no
refresh token / expiry) and avoids gRPC channel setup issues on Cloud Run.
"""

ADMIN_V1BETA = "https://analyticsadmin.googleapis.com/v1beta"
ADMIN_V1ALPHA = "https://analyticsadmin.googleapis.com/v1alpha"
DATA_V1BETA = "https://analyticsdata.googleapis.com/v1beta"


def auth_headers(token: str) -> dict[str, str]:
    """Returns the Authorization header dict for a bearer token."""
    return {"Authorization": f"Bearer {token}"}


def property_name(property_id: str) -> str:
    """Normalises a property ID to resource-name format."""
    if property_id.startswith("properties/"):
        return property_id
    return f"properties/{property_id}"
