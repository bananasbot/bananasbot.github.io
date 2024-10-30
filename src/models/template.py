from models.setup import *


class Template:
    def __init__(
        self,
        begin: str,
        end: str,
    ):
        """The template for scheduling"""

        self.begin = begin
        """the first part"""

        self.end = end
        """the last part"""

    @staticmethod
    def from_string(data: str):
        parts = data.split("/*### DATA ###*/")

        return Template(
            begin=parts[0],
            end=parts[2],
        )

    def instantiate(
        self,
        maxPreference: int,
        specs: list[Spec],
        raids: list[str],
        player_specs: dict[str, list[str]],
        timezones: list[str],
        preferences: list[Preference],
    ):
        res = ";"
        res += f"const maxPreference = {maxPreference+1};"
        res += f"const specs = {specs};"
        res += f"const raids = {raids};"
        res += f"const timezones = {timezones};"
        res += f"const player_preferences = [{preferences}];"
        res += f"const player_specs = {player_specs}"

        return " ".join([self.begin, res, self.end])
