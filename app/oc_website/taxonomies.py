from enum import Enum


class StringChoiceEnum(Enum):
    @classmethod
    def get_choices(cls) -> list[tuple[str, str]]:
        return [(item.value, item.value.replace("_", " ")) for item in cls]


class ProjectStatus(StringChoiceEnum):
    ACTIVE = "active"
    FINISHED = "finished"
