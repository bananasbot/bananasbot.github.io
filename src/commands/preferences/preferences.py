from collections import defaultdict
import logging
import io
from os.path import join

import discord
from discord import app_commands
from discord import File
from minify_html import minify

import config
import state as state

from commands.preferences.preferencesUx import *


@app_commands.command(
    name="preferences",
    description="update your preferences with time scheduling",
)
async def preferences(interaction: discord.Interaction):
    userId = interaction.user.id
    __logger.info(f"{userId} ({interaction.user.name})")

    player = state.players[userId]

    player_specs = defaultdict(list[str])
    for spec, raid in player.specs:
        if player.specs[(spec, raid)]:
            player_specs[spec].append(raid)

    instance = state.template.instantiate(
        maxPreference=config.maxPreference,
        specs=state.setup.SPECS,
        raids=list(state.raids.keys()),
        player_specs=dict(player_specs),
        timezones=config.timezones,
        preferences=list(player.preference.values()),
    )
    instance = minify(instance, minify_js=True, minify_css=True)
    buf = io.BytesIO(bytes(instance, "ascii"))
    f = discord.File(buf, filename=f"{interaction.user.name}.html")

    await interaction.response.send_message(
        content=None,
        embed=PreferencesEmbed(),
        ephemeral=True,
        view=PreferencesButtons(),
        file=f,
    )


__logger = logging.getLogger(preferences.name)
