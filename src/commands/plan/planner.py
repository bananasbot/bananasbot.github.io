from ortools.init.python import init
from ortools.linear_solver.pywraplp import Objective, Solver

from math import cos, pi

from models.player import Player
from models.raid import Raid
from models.setup import *


class Planner:
    """The actual planner"""

    async def plan(setup: Setup, raid: Raid, players: dict[int, Player]) -> list[int]:
        solver: Solver = Solver.CreateSolver("SAT")
        if not solver:
            raise "Could not create solver"

        ########
        # VARS #
        ########

        # is this spec gonna be played by this player?
        selected: dict[(PlayerId, Spec), bool] = {}
        for pid in players:
            for s in setup.SPECS:
                selected[(pid, s)] = solver.BoolVar(f"selected_{pid}_{s}")

        # will this hour be played?
        playhours: dict[Timepoint, bool] = {}
        for h in setup.TIMEPOINTS:
            playhours[h] = solver.BoolVar(f"playhours_{h}")

        # is the raid gonna start at this time?
        start: dict[Timepoint, bool] = {}
        for h in setup.TIMEPOINTS:
            start[h] = solver.BoolVar(f"start_{h}")

        # has this player been chosen to play?
        plays: dict[(PlayerId, Timepoint), bool] = {}
        for pid in players:
            for h in setup.TIMEPOINTS:
                plays[(pid, h)] = solver.BoolVar(f"plays_{pid}_{h}")

        #############
        # OBJECTIVE #
        #############

        # non linear function, to skew toward high preferences: https://www.desmos.com/calculator/lacz4qr29u (curve in green)
        objective: Objective = solver.Objective()
        for pid in players:
            for h in setup.TIMEPOINTS:
                objective.SetCoefficient(
                    plays[(pid, h)],
                    (1 - cos(pi * players[pid].preference[h])) / 2,
                )
        objective.SetMaximization()

        ###############
        # CONSTRAINTS #
        ###############

        # select_implies_existing_chars
        for pid in players:
            for s in setup.SPECS:
                solver.Add(selected[(pid, s)] <= players[pid].specs[s])

        # at_most_one_char_per_player_selected
        for pid in players:
            solver.Add(solver.Sum(selected[(pid, s)] for s in setup.SPECS) <= 1)

        # fulfill_all_raid_requirements
        for c in setup.CAPABILITIES:
            solver.Add(
                solver.Sum(
                    selected[(pid, s)] * setup.SPEC_CAN[(s, c)]
                    for pid in players
                    for s in setup.SPECS
                )
                >= raid.requirements[c]
            )

        # people amount bounds
        solver.Add(
            raid.min_people
            <= solver.Sum(selected[(pid, s)] for pid in players for s in setup.SPECS)
        )
        solver.Add(
            solver.Sum(selected[(pid, s)] for pid in players for s in setup.SPECS)
            <= raid.max_people
        )

        # single_start_1
        for h in setup.TIMEPOINTS:
            solver.Add(
                playhours[(h + 1) % setup.T] - playhours[h] <= start[(h + 1) % setup.T]
            )

        # single_start_2
        solver.Add(solver.Sum(start[h] for h in setup.TIMEPOINTS) == 1)

        # suppress_play
        for pid in players:
            for h in setup.TIMEPOINTS:
                solver.Add(
                    plays[(pid, h)]
                    <= solver.Sum(selected[(pid, c)] for c in setup.SPECS)
                )
                solver.Add(plays[(pid, h)] <= playhours[h])
                solver.Add(plays[(pid, h)] <= players[pid].preference[h] * 10)

        #######
        # END #
        #######

        status = solver.Solve()

        if status == Solver.OPTIMAL:
            res = []
            for s in setup.SPECS:
                for pid in players:
                    val = selected[(pid, s)].solution_value()
                    if val:
                        res.append((pid, s))
            return res
        else:
            return []
