# gray-themes

The [HANCORE-linux](https://github.com/HANCORE-linux) palette pack for
[gray](https://github.com/vstaln/gray) — 29 `omarchy-*-theme` color schemes
converted to gray theme files.

## Install

```sh
cargo build --release
gray plugin install /path/to/gray-themes    # or `gray plugin register` the binary
```

## Use

Inside gray:

```
/themes                  # list all 29 palettes (● active, ✓ installed)
/themes use saga         # writes ~/.gray/themes/hancore-saga.json
/theme hancore-saga      # built-in: switch the live palette
```

From the shell (`gray <name> <verb>` forwards to this binary):

```sh
gray themes list                 # same table
gray themes use velvetnight      # install + set "theme" in config.json (next launch)
gray themes install              # install all 29
gray themes show oxocarbon       # dump a palette
gray themes path                 # the themes dir
```

Names resolve with or without the `hancore-` prefix (`use saga` ≡
`use hancore-saga`). GRAY_HOME is respected.

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
`command/run` (`/themes`), `plugin/shutdown`. No tools, no hooks, no
capabilities.
