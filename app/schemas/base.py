"""
Base Pydantic configuration for response models.
Provides automatic snake_case to camelCase conversion for API responses.
"""

from pydantic import ConfigDict
from pydantic.alias_generators import to_camel as pydantic_to_camel


# Base configuration for all response models
# Automatically converts snake_case Python fields to camelCase JSON
base_response_config = ConfigDict(
    alias_generator=pydantic_to_camel,
    populate_by_name=True,  # Accept both snake_case and camelCase on input
    from_attributes=True,
    use_enum_values=True
)

