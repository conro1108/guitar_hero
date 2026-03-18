"""
Song data for terminal Guitar Hero.

Each song is a dictionary with note patterns expressed as (time_in_seconds, lane)
tuples. Lanes: 0=D, 1=F, 2=J, 3=K.
"""

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

LANE_KEYS = ["d", "f", "j", "k"]
LANE_NAMES = ["D", "F", "J", "K"]

PERFECT_WINDOW = 0.05  # +/- 50ms
GOOD_WINDOW = 0.10     # +/- 100ms
OK_WINDOW = 0.15       # +/- 150ms


# ---------------------------------------------------------------------------
# Pattern helpers
# ---------------------------------------------------------------------------

def _beat(bpm: int) -> float:
    """Duration of one beat (quarter note) in seconds."""
    return 60.0 / bpm


def _scale_run(start: float, bpm: int, lanes: list[int],
               subdivisions: int = 1) -> list[tuple[float, int]]:
    """Play through *lanes* in order, one note per subdivision."""
    dt = _beat(bpm) / subdivisions
    return [(round(start + i * dt, 4), lane) for i, lane in enumerate(lanes)]


def _arpeggio(start: float, bpm: int, pattern: list[int],
              cycles: int = 1, subdivisions: int = 1) -> list[tuple[float, int]]:
    """Cycle through a lane pattern for *cycles* repetitions."""
    dt = _beat(bpm) / subdivisions
    notes: list[tuple[float, int]] = []
    idx = 0
    for _ in range(cycles):
        for lane in pattern:
            notes.append((round(start + idx * dt, 4), lane))
            idx += 1
    return notes


def _repeat(start: float, bpm: int, pattern: list[tuple[float, int]],
            repeats: int, gap_beats: float = 0) -> list[tuple[float, int]]:
    """Repeat a pattern *repeats* times, each offset by pattern length + gap."""
    if not pattern:
        return []
    duration = pattern[-1][0] - pattern[0][0] + _beat(bpm) + gap_beats * _beat(bpm)
    notes: list[tuple[float, int]] = []
    for r in range(repeats):
        offset = r * duration
        for t, lane in pattern:
            notes.append((round(start + offset + (t - pattern[0][0]), 4), lane))
    return notes


def _chord(time: float, lanes: list[int]) -> list[tuple[float, int]]:
    """Simultaneous notes on multiple lanes."""
    return [(time, lane) for lane in lanes]


def _measure_end(notes: list[tuple[float, int]], bpm: int,
                 extra_beats: float = 0) -> float:
    """Return the time one beat after the last note, plus optional extra."""
    return notes[-1][0] + _beat(bpm) * (1 + extra_beats)


# ---------------------------------------------------------------------------
# Song 1 - "First Steps"
# Easy (1), 100 BPM, ~45 seconds
# Single lane at a time, gentle quarter-note introduction.
# Teaches each finger individually, then simple combinations.
# ---------------------------------------------------------------------------

def _build_first_steps() -> dict:
    bpm = 100
    b = _beat(bpm)  # 0.6s
    notes: list[tuple[float, int]] = []

    # -- Section A: Meet each finger (16 beats = 9.6s) --
    t = 1.0

    # Lane 0 solo (4 beats)
    for i in range(4):
        notes.append((round(t + i * b, 4), 0))
    t += 4 * b

    # Lane 1 solo (4 beats)
    for i in range(4):
        notes.append((round(t + i * b, 4), 1))
    t += 4 * b

    # Lane 2 solo (4 beats)
    for i in range(4):
        notes.append((round(t + i * b, 4), 2))
    t += 4 * b

    # Lane 3 solo (4 beats)
    for i in range(4):
        notes.append((round(t + i * b, 4), 3))
    t += 4 * b

    # -- Section B: Simple scales (16 beats = 9.6s) --
    # Ascending 0-1-2-3 x2
    for _ in range(2):
        notes += _scale_run(t, bpm, [0, 1, 2, 3])
        t += 4 * b

    # Descending 3-2-1-0 x2
    for _ in range(2):
        notes += _scale_run(t, bpm, [3, 2, 1, 0])
        t += 4 * b

    # -- Section C: Neighbor pairs (16 beats = 9.6s) --
    # Alternating 0-1 (4 beats)
    for i in range(4):
        notes.append((round(t + i * b, 4), i % 2))
    t += 4 * b

    # Alternating 2-3 (4 beats)
    for i in range(4):
        notes.append((round(t + i * b, 4), 2 + i % 2))
    t += 4 * b

    # Alternating 0-2 (wide, 4 beats)
    for i in range(4):
        notes.append((round(t + i * b, 4), 0 if i % 2 == 0 else 2))
    t += 4 * b

    # Alternating 1-3 (wide, 4 beats)
    for i in range(4):
        notes.append((round(t + i * b, 4), 1 if i % 2 == 0 else 3))
    t += 4 * b

    # -- Section D: Call and response (16 beats = 9.6s) --
    # Left hand phrase (0-1-0), then right hand echoes (2-3-2)
    for _ in range(2):
        for lane in [0, 1, 0]:
            notes.append((round(t, 4), lane))
            t += b
        t += b  # rest beat
        for lane in [2, 3, 2]:
            notes.append((round(t, 4), lane))
            t += b
        t += b  # rest beat

    # -- Section E: Full ascending/descending with rests (12 beats = 7.2s) --
    # Up the full scale
    notes += _scale_run(t, bpm, [0, 1, 2, 3])
    t += 4 * b
    t += 2 * b  # 2-beat rest

    # Down the full scale
    notes += _scale_run(t, bpm, [3, 2, 1, 0])
    t += 4 * b
    t += 2 * b  # rest

    # -- Ending: whole notes on each lane --
    for lane in [0, 1, 2, 3]:
        notes.append((round(t, 4), lane))
        t += b

    return {
        "name": "First Steps",
        "artist": "The Beginners",
        "difficulty": 1,
        "bpm": bpm,
        "notes": sorted(notes, key=lambda n: (n[0], n[1])),
    }


# ---------------------------------------------------------------------------
# Song 2 - "Steady Groove"
# Easy-Medium (2), 110 BPM, ~50 seconds
# Two-lane patterns, some eighth notes, groove-oriented.
# ---------------------------------------------------------------------------

def _build_steady_groove() -> dict:
    bpm = 110
    b = _beat(bpm)  # ~0.545s
    notes: list[tuple[float, int]] = []

    t = 0.8

    # -- Section A: Driving beat - lane 0 on beats, lane 1 on off-beats (8 beats) --
    for i in range(8):
        notes.append((round(t + i * b, 4), 0))
        notes.append((round(t + i * b + b / 2, 4), 1))
    t += 8 * b

    # -- Section B: Call and response (16 beats) --
    call = [(0, 0), (b, 1), (2 * b, 0), (3 * b, 1)]
    resp = [(0, 2), (b, 3), (2 * b, 2), (3 * b, 3)]
    for _ in range(2):
        for dt, lane in call:
            notes.append((round(t + dt, 4), lane))
        t += 4 * b
        for dt, lane in resp:
            notes.append((round(t + dt, 4), lane))
        t += 4 * b

    # -- Section C: Eighth-note lane pairs (12 beats) --
    for pair in [(0, 1), (2, 3), (1, 2)]:
        notes += _arpeggio(t, bpm, list(pair), cycles=4, subdivisions=2)
        t += 4 * b

    # -- Section D: Bass + melody groove (16 beats) --
    # Lane 0 steady quarter, lanes 1-2 alternating eighth-note melody
    for i in range(16):
        notes.append((round(t + i * b, 4), 0))
        if i % 2 == 0:
            notes.append((round(t + i * b + b / 2, 4), 1))
        else:
            notes.append((round(t + i * b + b / 2, 4), 2))
    t += 16 * b

    # -- Section E: Build-up - adding lanes gradually (12 beats) --
    # 4 beats: just lane 0
    for i in range(4):
        notes.append((round(t + i * b, 4), 0))
    t += 4 * b
    # 4 beats: lanes 0 + 1
    for i in range(4):
        notes.append((round(t + i * b, 4), 0))
        notes.append((round(t + i * b + b / 2, 4), 1))
    t += 4 * b
    # 4 beats: lanes 0 + 1 + 2 cycling eighths
    for i in range(8):
        notes.append((round(t + i * b / 2, 4), i % 3))
    t += 4 * b

    # -- Section F: Swing feel - dotted quarter + eighth (16 beats) --
    for i in range(8):
        notes.append((round(t, 4), i % 2))            # dotted quarter
        notes.append((round(t + 3 * b / 4, 4), 2 + i % 2))  # eighth
        t += b

    # Repeat with roles swapped
    for i in range(8):
        notes.append((round(t, 4), 2 + i % 2))
        notes.append((round(t + 3 * b / 4, 4), i % 2))
        t += b

    # -- Ending: chord stabs --
    notes += _chord(round(t, 4), [0, 1])
    t += b
    notes += _chord(round(t, 4), [2, 3])
    t += b
    t += b  # rest
    notes += _chord(round(t, 4), [0, 1, 2, 3])

    return {
        "name": "Steady Groove",
        "artist": "Rhythm Section",
        "difficulty": 2,
        "bpm": bpm,
        "notes": sorted(notes, key=lambda n: (n[0], n[1])),
    }


# ---------------------------------------------------------------------------
# Song 3 - "Neon Nights"
# Medium (3), 120 BPM, ~55 seconds
# All four lanes, syncopation, moderate density.
# ---------------------------------------------------------------------------

def _build_neon_nights() -> dict:
    bpm = 120
    b = _beat(bpm)  # 0.5s
    notes: list[tuple[float, int]] = []

    t = 0.5

    # -- Section A: Synth arpeggio intro (8 beats = 4s) --
    notes += _arpeggio(t, bpm, [0, 2, 1, 3], cycles=4, subdivisions=2)
    t += 8 * b

    # -- Section B: Syncopated melody (8 beats = 4s) --
    # Notes land on the "and" of each beat
    for i in range(8):
        lane = [1, 3, 2, 0][i % 4]
        notes.append((round(t + i * b + b / 2, 4), lane))
    t += 8 * b

    # -- Section C: Call & response with syncopation (12 beats = 6s) --
    call_pattern = [(0, 0), (b / 2, 1), (b, 2), (2 * b, 3)]
    resp_pattern = [(0, 3), (b / 2, 2), (b, 1), (2 * b, 0)]
    for _ in range(2):
        for dt, lane in call_pattern:
            notes.append((round(t + dt, 4), lane))
        t += 3 * b
        for dt, lane in resp_pattern:
            notes.append((round(t + dt, 4), lane))
        t += 3 * b

    # -- Section D: Rhythmic groove - bass on beat, melody off-beat (16 beats = 8s) --
    for i in range(16):
        notes.append((round(t + i * b, 4), 0))  # bass on beat
        melody_lane = [1, 2, 3, 2][i % 4]
        notes.append((round(t + i * b + b / 2, 4), melody_lane))  # melody off-beat
    t += 16 * b

    # -- Section E: Ascending density build-up (8 beats = 4s) --
    lanes_cycle = [0, 1, 2, 3]
    idx = 0
    for section, subdiv in [(2, 1), (2, 2), (2, 3), (2, 4)]:
        dt_sub = b / subdiv
        count = section * subdiv
        for i in range(count):
            notes.append((round(t + i * dt_sub, 4), lanes_cycle[idx % 4]))
            idx += 1
        t += section * b

    # -- 2-beat break (silence) --
    t += 2 * b

    # -- Section F: Post-break burst (8 beats = 4s) --
    # Fast descending runs
    notes += _scale_run(t, bpm, [3, 2, 1, 0, 3, 2, 1, 0], subdivisions=2)
    t += 4 * b
    notes += _scale_run(t, bpm, [0, 1, 2, 3, 0, 1, 2, 3], subdivisions=2)
    t += 4 * b

    # -- Section G: Syncopated chord hits (12 beats = 6s) --
    for i in range(6):
        # Chord on the "and"
        notes += _chord(round(t + b / 2, 4), [0, 3] if i % 2 == 0 else [1, 2])
        # Single note on the next beat
        notes.append((round(t + b, 4), (i + 1) % 4))
        t += 2 * b

    # -- Section H: Wide arpeggios with rests (12 beats = 6s) --
    for _ in range(4):
        notes += _arpeggio(t, bpm, [0, 3, 1, 2], cycles=1, subdivisions=2)
        t += 3 * b  # pattern + rest

    # -- Section I: Driving verse reprise (16 beats = 8s) --
    # Bass on lane 0 every beat, syncopated melody across 1-2-3
    melody_seq = [1, 3, 2, 1, 3, 2, 3, 1, 2, 3, 1, 2, 1, 3, 2, 1]
    for i in range(16):
        notes.append((round(t + i * b, 4), 0))
        notes.append((round(t + i * b + b / 2, 4), melody_seq[i]))
    t += 16 * b

    # -- Section J: Outro build + final chord (8 beats = 4s) --
    # Accelerating single notes
    for i, lane in enumerate([0, 1, 2, 3, 0, 1, 2, 3]):
        notes.append((round(t + i * b / 2, 4), lane))
    t += 4 * b

    # Double-time arpeggio
    notes += _arpeggio(t, bpm, [3, 1, 2, 0], cycles=2, subdivisions=2)
    t += 2 * b

    # Final chord
    t += b
    notes += _chord(round(t, 4), [0, 1, 2, 3])

    return {
        "name": "Neon Nights",
        "artist": "Synthwave Collective",
        "difficulty": 3,
        "bpm": bpm,
        "notes": sorted(notes, key=lambda n: (n[0], n[1])),
    }


# ---------------------------------------------------------------------------
# Song 4 - "Thunder Road"
# Hard (4), 140 BPM, ~50 seconds
# Fast runs, chord-like simultaneous notes, complex patterns.
# ---------------------------------------------------------------------------

def _build_thunder_road() -> dict:
    bpm = 140
    b = _beat(bpm)  # ~0.4286s
    notes: list[tuple[float, int]] = []

    t = 0.4

    # -- Section A: Driving eighth-note riff (8 beats) --
    riff = [0, 1, 0, 1, 0, 0, 1, 1, 0, 1, 1, 0, 0, 1, 0, 1]
    for i, lane in enumerate(riff):
        notes.append((round(t + i * b / 2, 4), lane))
    t += len(riff) * b / 2

    # -- Section B: Power chords with pickups (16 beats) --
    for i in range(8):
        notes += _chord(round(t, 4), [0, 1])
        notes.append((round(t + b / 2, 4), 2 + i % 2))
        t += b

    # -- Section C: 16th-note scalar runs (8 beats) --
    notes += _scale_run(t, bpm, [0, 1, 2, 3] * 4, subdivisions=4)
    t += 4 * b
    notes += _scale_run(t, bpm, [3, 2, 1, 0] * 4, subdivisions=4)
    t += 4 * b

    # -- Section D: Gallop triplets (8 beats) --
    for i in range(8):
        base_lane = i % 4
        notes.append((round(t, 4), base_lane))
        notes.append((round(t + b / 3, 4), (base_lane + 1) % 4))
        notes.append((round(t + 2 * b / 3, 4), (base_lane + 2) % 4))
        t += b

    # -- 2-beat break --
    t += 2 * b

    # -- Section E: Chord stabs (4 beats) --
    for i in range(8):
        notes += _chord(round(t, 4), [0, 1, 2, 3])
        t += b / 2
    t += b  # breath

    # -- Section F: Syncopated cross-lane (16 beats) --
    for i in range(16):
        # Off-beat melody cycling through all lanes backwards
        notes.append((round(t + b / 2, 4), (3 - i) % 4))
        if i % 2 == 0:
            notes += _chord(round(t, 4), [0, 3])
        else:
            notes.append((round(t, 4), 1 + i % 2))
        t += b

    # -- Section G: Mixed meter feel (8 beats) --
    # Groups of 3+3+2 eighth notes
    group_pattern = [0, 1, 2, 0, 1, 2, 0, 3]
    for rep in range(4):
        for i, lane in enumerate(group_pattern):
            notes.append((round(t + i * b / 2, 4), lane))
        t += 4 * b

    # -- Ending: Triple slam --
    notes += _chord(round(t, 4), [0, 1, 2, 3])
    t += b / 2
    notes += _chord(round(t, 4), [0, 1, 2, 3])
    t += b / 2
    notes += _chord(round(t, 4), [0, 1, 2, 3])

    return {
        "name": "Thunder Road",
        "artist": "The Shredders",
        "difficulty": 4,
        "bpm": bpm,
        "notes": sorted(notes, key=lambda n: (n[0], n[1])),
    }


# ---------------------------------------------------------------------------
# Song 5 - "Final Boss"
# Expert (5), 160 BPM, ~55 seconds
# Extremely dense, rapid lane switching, four-finger independence.
# ---------------------------------------------------------------------------

def _build_final_boss() -> dict:
    bpm = 160
    b = _beat(bpm)  # 0.375s
    notes: list[tuple[float, int]] = []

    t = 0.3

    # -- Phase 1: Relentless 16th-note zigzag (16 beats = 6s) --
    zigzag = [0, 3, 1, 2] * 16
    for i, lane in enumerate(zigzag):
        notes.append((round(t + i * b / 4, 4), lane))
    t += 16 * b

    # -- Phase 2: Hand independence drill (16 beats = 6s) --
    # Left hand (0,1) on eighth notes, right hand (2,3) on off-16ths
    for i in range(32):
        notes.append((round(t + i * b / 2, 4), i % 2))
        notes.append((round(t + i * b / 2 + b / 4, 4), 2 + (i + 1) % 2))
    t += 16 * b

    # -- Phase 3: Polyrhythm 3-against-4 (16 beats = 6s) --
    poly_bar = 4 * b
    for bar in range(4):
        bar_start = t + bar * poly_bar
        # 3-feel on lane 0
        for j in range(3):
            notes.append((round(bar_start + j * poly_bar / 3, 4), 0))
        # 4-feel cycling lanes 1-2-3
        for j in range(4):
            notes.append((round(bar_start + j * b, 4), 1 + (j % 3)))
        # Extra: 6-feel on lane chosen by position
        for j in range(6):
            notes.append((round(bar_start + j * poly_bar / 6, 4), (j + 2) % 4))
    t += 4 * poly_bar

    # -- Phase 4: Burst patterns with micro-rests (16 beats = 6s) --
    bursts = [
        [0, 1, 2, 3, 3, 2, 1, 0],         # palindrome
        [0, 2, 1, 3, 0, 2, 1, 3],         # interleaved
        [3, 3, 1, 1, 2, 2, 0, 0],         # doubles
        [0, 3, 0, 3, 1, 2, 1, 2],         # ping-pong
        [0, 1, 0, 2, 0, 3, 0, 3],         # anchor + walk
        [3, 0, 2, 1, 3, 0, 2, 1],         # reverse interleave
    ]
    for burst in bursts:
        for i, lane in enumerate(burst):
            notes.append((round(t + i * b / 4, 4), lane))
        t += len(burst) * b / 4 + b  # burst + one beat rest

    # -- Phase 5: Chord flurry (8 beats = 3s) --
    chord_seq = [
        [0, 1], [2, 3], [1, 2], [0, 3],
        [0, 2], [1, 3], [0, 1, 2, 3],
        [0, 3], [1, 2], [0, 1], [2, 3],
        [0, 1, 2, 3], [1, 3], [0, 2],
        [0, 1, 2, 3], [0, 1, 2, 3],
    ]
    for chord_lanes in chord_seq:
        notes += _chord(round(t, 4), chord_lanes)
        t += b / 2

    t += b  # breath

    # -- Phase 6: The gauntlet - all permutations in 16ths (8 beats = 3s) --
    perms = [
        [0, 1, 2, 3], [1, 0, 3, 2], [2, 3, 0, 1], [3, 2, 1, 0],
        [0, 2, 3, 1], [3, 1, 0, 2], [1, 3, 2, 0], [2, 0, 1, 3],
    ]
    for perm in perms:
        for i, lane in enumerate(perm):
            notes.append((round(t + i * b / 4, 4), lane))
        t += b

    # -- Phase 7: Double-time independence (16 beats = 6s) --
    # Left hand pattern: 0-1-1-0, right hand pattern: 3-2-2-3, interlocked
    lh = [0, 1, 1, 0] * 8
    rh = [3, 2, 2, 3] * 8
    for i in range(32):
        notes.append((round(t + i * b / 4, 4), lh[i]))
        notes.append((round(t + i * b / 4 + b / 8, 4), rh[i]))
    t += 8 * b

    # -- Phase 8: Accelerating chaos (8 beats = 3s) --
    intervals = [b, b * 3 / 4, b / 2, b / 2, b / 3, b / 3,
                 b / 4, b / 4, b / 4, b / 4, b / 4, b / 4]
    chord_cycle = [[0, 3], [1, 2], [0, 1, 2, 3]]
    for i, interval in enumerate(intervals):
        notes += _chord(round(t, 4), chord_cycle[i % len(chord_cycle)])
        t += interval

    # -- Phase 9: Final 16th-note flurry (8 beats = 3s) --
    # All lanes in wild patterns
    wild = [
        0, 3, 1, 2, 3, 0, 2, 1,
        1, 2, 0, 3, 2, 1, 3, 0,
        0, 2, 3, 1, 1, 3, 0, 2,
        3, 1, 2, 0, 2, 0, 1, 3,
    ]
    for i, lane in enumerate(wild):
        notes.append((round(t + i * b / 4, 4), lane))
    t += 8 * b

    # -- Finale: Quad slams --
    for _ in range(4):
        notes += _chord(round(t, 4), [0, 1, 2, 3])
        t += b / 4
    t += b / 2
    # One last hit
    notes += _chord(round(t, 4), [0, 1, 2, 3])

    return {
        "name": "Final Boss",
        "artist": "\u221e",
        "difficulty": 5,
        "bpm": bpm,
        "notes": sorted(notes, key=lambda n: (n[0], n[1])),
    }


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

SONGS: list[dict] = [
    _build_first_steps(),
    _build_steady_groove(),
    _build_neon_nights(),
    _build_thunder_road(),
    _build_final_boss(),
]


def get_song(index: int) -> dict:
    """Return a song dict by index. Raises IndexError if out of range."""
    return SONGS[index]
