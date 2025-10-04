"""
Base Pydantic configuration for response models.
Provides automatic snake_case to camelCase conversion for API responses.
"""

from pydantic import ConfigDict


def to_camel(string: str) -> str:
    """
    Convert snake_case to camelCase.
    
    Args:
        string: A snake_case string
        
    Returns:
        The same string in camelCase format
        
    Examples:
        >>> to_camel("habit_id")
        "habitId"
        >>> to_camel("created_at")
        "createdAt"
    """
    components = string.split('_')
    return components[0] + ''.join(x.title() for x in components[1:])


# Base configuration for all response models
# Automatically converts snake_case Python fields to camelCase JSON
base_response_config = ConfigDict(
    alias_generator=to_camel,
    populate_by_name=True,  # Accept both snake_case and camelCase on input
    from_attributes=True,
    serialize_by_alias=True  # Use camelCase aliases when serializing to JSON
)

