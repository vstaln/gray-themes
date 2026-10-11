# gray-themes

A 29-palette theme pack for [gray](https://github.com/vstaln/gray) —
color schemes converted from upstream `colors.toml` files (each theme
file names its source).

## Install

```sh
cargo build --release
gray plugin install /path/to/gray-themes    # or `gray plugin register` the binary
```

## Use

Inside gray:

```
/palettes                # list all 29 palettes (● active, ✓ installed)
/palettes use saga       # writes ~/.gray/themes/saga.json
/theme saga              # built-in: switch the live palette
```

(`/palettes` rather than `/themes` — that's a built-in alias of `/theme`.)

From the shell (`gray <name> <verb>` forwards to this binary):

```sh
gray themes list                 # same table
gray themes use velvetnight      # install + set "theme" in config.json (next launch)
gray themes install              # install all 29
gray themes show oxocarbon       # dump a palette
gray themes path                 # the themes dir
```

GRAY_HOME is respected. Install never overwrites a theme file that
didn't come from this pack (pack files carry a `_source` marker).

## Themes

25 dark + 4 light: aamis, banish, batou, blackgold, blackmoney, blackturq,
demon, dos-moos, greek-noir, **harbor** (light), harbordark, inkypinky,
kanso, labra, lasthorizon, mechanoonna, moodpeak, oxford, oxocarbon,
**roseofdune** (light), ryu, saga, sapphire, shadesofjade, solitude,
**thegreek** (light), turbonite, velvetnight, **whitegold** (light).

## How it works

`themes/*.json` are gray theme files (`{vars, colors}` overriding the
built-in palette's 38 semantic roles). `scripts/sync.py` fetches each
upstream `colors.toml` and regenerates them — palette keys map onto gray's
roles (bg/fg→surfaces+text ramp, accent→accent, red/green/blue→status,
named colors→tool/diff slots, muted→dim ramp) with luminance blends
filling the derived roles. Run `python3 scripts/sync.py` to refresh from
upstream, then rebuild.

Sidecar: NDJSON wire per the gray plugin contract — `plugin/manifest`,
`command/run` (`/palettes`), `plugin/shutdown`. No tools, no hooks, no
capabilities.
