"""Routing constants (owner: B). Values from the PRD constants table."""

WALK_MPS = 1.3            # m/s walking speed
DETOUR = 1.3              # straight-line distance multiplier for campus paths
BOARD_RADIUS_M = 600      # max walk to a boarding stop
ALIGHT_RADIUS_M = 400     # max walk from an alighting stop
CATCH_MARGIN_S = 45       # bus must reach the stop this long after you do
TIGHT_WINDOW_S = 180      # verdict band around the deadline
MAX_WAIT_S = 1800         # ignore buses more than 30 min out

WALK_ONLY_UNDER_M = 250   # origin/dest closer than this: walk-only, no bus lookup
CAMPUS_CENTER = (33.7756, -84.3963)
CAMPUS_RADIUS_M = 3000    # origin farther than this from campus center: ask to confirm
