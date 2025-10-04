"""
Habit Template Definitions.

This module contains pre-configured habit templates that users can select
during onboarding to quickly set up their challenge without typing.
"""

from typing import List, Dict, Optional
from enum import Enum


class HabitCategory(str, Enum):
    """Habit template categories."""
    SOBER_OCTOBER = "sober_october"
    PHYSICAL_HEALTH = "physical_health"
    MENTAL_WELLNESS = "mental_wellness"
    DAILY_ROUTINES = "daily_routines"


class HabitTemplate:
    """
    Represents a pre-configured habit template.
    
    Attributes:
        id: Unique template identifier
        name: Habit name
        description: Brief description of the habit
        type: Habit type (binary or counted)
        preferred_time: Suggested time of day
        target_count: Target count for counted habits
        category: Template category
        icon: Emoji or icon identifier
    """
    
    def __init__(
        self,
        id: str,
        name: str,
        description: str,
        type: str,
        preferred_time: str,
        category: HabitCategory,
        icon: str,
        target_count: Optional[int] = None
    ):
        self.id = id
        self.name = name
        self.description = description
        self.type = type
        self.preferred_time = preferred_time
        self.target_count = target_count
        self.category = category
        self.icon = icon
    
    def to_dict(self) -> Dict:
        """Convert template to dictionary."""
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "type": self.type,
            "preferred_time": self.preferred_time,
            "target_count": self.target_count,
            "category": self.category.value,
            "icon": self.icon
        }


# Define all available habit templates
HABIT_TEMPLATES = [
    # Sober October Essentials
    HabitTemplate(
        id="no_alcohol",
        name="No Alcohol",
        description="Stay alcohol-free for the entire challenge",
        type="binary",
        preferred_time="all_day",
        category=HabitCategory.SOBER_OCTOBER,
        icon="🚫🍺"
    ),
    HabitTemplate(
        id="no_sugar",
        name="No Added Sugar",
        description="Avoid added sugars and sweeteners",
        type="binary",
        preferred_time="all_day",
        category=HabitCategory.SOBER_OCTOBER,
        icon="🚫🍰"
    ),
    HabitTemplate(
        id="no_caffeine",
        name="No Caffeine After 2pm",
        description="Cut off caffeine intake after 2pm",
        type="binary",
        preferred_time="afternoon",
        category=HabitCategory.SOBER_OCTOBER,
        icon="☕"
    ),
    HabitTemplate(
        id="no_social_media",
        name="No Social Media",
        description="Stay off social media platforms",
        type="binary",
        preferred_time="all_day",
        category=HabitCategory.SOBER_OCTOBER,
        icon="📱"
    ),
    
    # Physical Health
    HabitTemplate(
        id="exercise",
        name="Exercise",
        description="Complete a workout session",
        type="binary",
        preferred_time="morning",
        category=HabitCategory.PHYSICAL_HEALTH,
        icon="💪"
    ),
    HabitTemplate(
        id="pushups",
        name="Pushups",
        description="Do your daily pushups",
        type="counted",
        preferred_time="morning",
        target_count=20,
        category=HabitCategory.PHYSICAL_HEALTH,
        icon="🏋️"
    ),
    HabitTemplate(
        id="walk_10k",
        name="Walk 10,000 Steps",
        description="Hit your daily step goal",
        type="binary",
        preferred_time="all_day",
        category=HabitCategory.PHYSICAL_HEALTH,
        icon="🚶"
    ),
    HabitTemplate(
        id="vitamins",
        name="Take Vitamins",
        description="Take your daily vitamins and supplements",
        type="binary",
        preferred_time="morning",
        category=HabitCategory.PHYSICAL_HEALTH,
        icon="💊"
    ),
    HabitTemplate(
        id="cold_shower",
        name="Cold Shower",
        description="Take a cold shower for alertness and recovery",
        type="binary",
        preferred_time="morning",
        category=HabitCategory.PHYSICAL_HEALTH,
        icon="🚿"
    ),
    HabitTemplate(
        id="yoga",
        name="Yoga Practice",
        description="Complete a yoga session",
        type="binary",
        preferred_time="morning",
        category=HabitCategory.PHYSICAL_HEALTH,
        icon="🧘"
    ),
    HabitTemplate(
        id="drink_water",
        name="Drink 8 Glasses of Water",
        description="Stay hydrated throughout the day",
        type="counted",
        preferred_time="all_day",
        target_count=8,
        category=HabitCategory.PHYSICAL_HEALTH,
        icon="💧"
    ),
    
    # Mental Wellness
    HabitTemplate(
        id="meditate",
        name="Meditate",
        description="Practice mindfulness meditation",
        type="binary",
        preferred_time="morning",
        category=HabitCategory.MENTAL_WELLNESS,
        icon="🧘‍♀️"
    ),
    HabitTemplate(
        id="journal",
        name="Journal",
        description="Write in your journal",
        type="binary",
        preferred_time="evening",
        category=HabitCategory.MENTAL_WELLNESS,
        icon="📓"
    ),
    HabitTemplate(
        id="read",
        name="Read",
        description="Read for pleasure or learning",
        type="binary",
        preferred_time="evening",
        category=HabitCategory.MENTAL_WELLNESS,
        icon="📚"
    ),
    HabitTemplate(
        id="gratitude",
        name="Practice Gratitude",
        description="Write down three things you're grateful for",
        type="binary",
        preferred_time="evening",
        category=HabitCategory.MENTAL_WELLNESS,
        icon="🙏"
    ),
    
    # Daily Routines
    HabitTemplate(
        id="sleep_8hrs",
        name="Sleep 8 Hours",
        description="Get a full night's rest",
        type="binary",
        preferred_time="evening",
        category=HabitCategory.DAILY_ROUTINES,
        icon="😴"
    ),
    HabitTemplate(
        id="make_bed",
        name="Make Your Bed",
        description="Start the day by making your bed",
        type="binary",
        preferred_time="morning",
        category=HabitCategory.DAILY_ROUTINES,
        icon="🛏️"
    ),
    HabitTemplate(
        id="floss",
        name="Floss Teeth",
        description="Floss your teeth daily",
        type="binary",
        preferred_time="evening",
        category=HabitCategory.DAILY_ROUTINES,
        icon="🦷"
    ),
]


def get_all_templates() -> List[Dict]:
    """
    Get all habit templates.
    
    Returns:
        List[Dict]: List of all habit templates as dictionaries
    """
    return [template.to_dict() for template in HABIT_TEMPLATES]


def get_template_by_id(template_id: str) -> Optional[Dict]:
    """
    Get a specific habit template by ID.
    
    Args:
        template_id: Template identifier
        
    Returns:
        Optional[Dict]: Template dictionary if found, None otherwise
    """
    for template in HABIT_TEMPLATES:
        if template.id == template_id:
            return template.to_dict()
    return None


def get_templates_by_category(category: HabitCategory) -> List[Dict]:
    """
    Get habit templates filtered by category.
    
    Args:
        category: Category to filter by
        
    Returns:
        List[Dict]: List of templates in the specified category
    """
    return [
        template.to_dict()
        for template in HABIT_TEMPLATES
        if template.category == category
    ]

