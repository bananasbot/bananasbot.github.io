from .setup import *


class Raid:
    def __init__(
        self,
        setup: Setup,
        id: RaidId,
        name: str,
        length: int,
        min_people: int,
        max_people: int,
        requirements: dict[Capability, int],
    ):
        """Planner params for raid"""
        self.id = id
        """the raid id"""

        self.name = name
        """expanded raid name"""

        self.length = length
        """expected raid duration, in hours"""

        self.min_people = min_people
        """min amount of people"""

        self.max_people = max_people
        """max amount of people"""

        self.requirements = {c: 0 for c in setup.CAPABILITIES}
        self.requirements.update(requirements)
        """the capabilities required by the raid """

    @staticmethod
    def from_json(setup: Setup, id: RaidId, data: dict):
        return Raid(
            setup,
            id=id,
            name=data.get("name"),
            length=int(data.get("length")),
            min_people=int(data.get("min_people")),
            max_people=int(data.get("max_people")),
            requirements=data.get("requirements"),
        )
