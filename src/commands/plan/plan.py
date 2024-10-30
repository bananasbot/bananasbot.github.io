import logging
import asyncio
import time
from collections import defaultdict

import discord
from discord import app_commands

import state
from models.raid import Raid

from commands.plan.planner import *

from math import ceil


def raid_to_choice(raidId: str, raid: Raid):
    return app_commands.Choice(name=raid.name, value=raidId)


@app_commands.command(
    name="plan",
    description="Helps with finding the best timeslot for the raid.",
)
@app_commands.describe(raid="the raid")
@app_commands.describe(timeout="timeout for the calculation")
@app_commands.choices(
    raid=[raid_to_choice(id, raid) for id, raid in state.raids.items()]
)
async def plan(interaction: discord.Interaction, raid: str, timeout: int = 60):
    __logger.info(f"{interaction.user.id} ({interaction.user.name})")

    notify_period = 2
    await interaction.response.send_message("this could take a while...")

    planner = asyncio.create_task(
        Planner.plan(
            state.setup,
            state.raids[raid],
            state.players,
        )
    )

    async def try_planning(ttl: int = 0) -> list:
        try:
            return await asyncio.wait_for(planner, timeout=notify_period)
        except asyncio.TimeoutError:
            if ttl <= 0:
                planner.cancel()
                await interaction.edit_original_response(content="timeout.")
                return None
            else:
                await interaction.edit_original_response(
                    content=f"im still working on it, wait for up to {ttl*notify_period})s ..."
                )
                return try_planning(ttl - 1)

    planned = await try_planning(ceil(timeout / notify_period))
    await interaction.edit_original_response(content="done, preparing results...")

    if planned and any(planned):
        spec_to_players = defaultdict(list[PlayerId])
        for pid, spec in planned:
            spec_to_players[spec].append(pid)

        emb = discord.Embed(title=state.raids[raid].name)
        for spec in spec_to_players:
            emb.add_field(
                name=spec,
                value=" ".join([f"<@{pid}>" for pid in spec_to_players[spec]]),
                inline=False,
            )

        await interaction.edit_original_response(content=None, embed=emb)


__logger = logging.getLogger(plan.name)
