from typing import List, NewType

from bs4.element import Tag
from galaxy.api.types import Achievement

PoeSessionId = NewType("PoeSessionId", str)
ProfileName = NewType("ProfileName", str)
Achievements = List[Achievement]
HtmlPage = NewType("HtmlPage", str)

Timestamp = NewType("Timestamp", int)
AchievementName = NewType("AchievementName", str)
AchievementTag = NewType("AchievementTag", Tag)
AchievementTagSet = List[AchievementTag]
