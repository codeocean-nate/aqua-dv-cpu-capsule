# aqua-dv-cpu-capsule

A tiny, dependency-free capsule used by the **deployment-verification** Aqua skill
([aqua-dv-skill](https://github.com/codeocean-nate/aqua-dv-skill)) to check a Code Ocean
deployment after an install or upgrade.

It needs only Python 3 (any Code Ocean Python starter environment works) and no network access.

## What a run does

`code/run` calls `code/dv_check.py`, which:

1. prints a banner with the four Code Ocean identity variables
   (`CO_CAPSULE_ID`, `CO_COMPUTATION_ID`, `CO_CPUS`, `CO_MEMORY`) and basic machine facts;
2. reads **every** file under `/data`, printing its size and SHA-256, so attached data
   assets (internal or external) are proven readable, not just listed;
3. writes `/results/result.txt`, `/results/data_manifest.tsv` and `/results/summary.json`.

It prints no other environment variables and contacts no external service.

| Exit code | Meaning |
|---|---|
| 0 | `DV-CHECK OK` |
| 2 | `DV-CHECK FAIL`: a file under `/data` couldn't be read, or fewer files than `--require-data N` |

## Used for

- Reproducible Runs on Flex and on a dedicated machine.
- Result data assets, and attaching internal and external data assets.
- Cloud workstation checks. The workstation commands are in the skill.
- A one-step pipeline. Run it with `--require-data 1` so a pipeline with no data fails.

## Make a capsule from it

In Code Ocean: **New Capsule > Copy from Git**, paste
`https://github.com/codeocean-nate/aqua-dv-cpu-capsule`, then choose a Python starter environment.
Or ask Aqua, with the deployment-verification skill enabled, to do it for you.
