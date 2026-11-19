# Why the wage falls on the map

Stage 4, first job. 13 November 2026. Jason said "Start stage 4"; the question put to him was "Start stage 4, tracing why wages fell on the map?"

## Short answer

The map did not push the wage down. Without the map, something was holding the wage up, and that thing cannot happen on a map.

Without the map, landlords go on building homes after the town is full. New landlords charge less than the first one. Tenants move to them. Each new landlord builds a home for every tenant it gains, on borrowed money. The first landlord's rent never comes down, so its homes stand empty. In the three runs as written the town built 1,099 to 1,763 homes after it was full, and at the worst had 1,286 to 1,514 empty homes for 1,000 people.

Building a home takes about 70 worker-weeks. That work keeps pulling the town into a shortage of workers, and a firm that cannot fill a job raises its wage. That is what kept the wage level without the map.

On the 13 by 13 map there is room for about 1,150 homes once firms have their premises. The town has about 1,005 when it fills. A second set of homes cannot be built. So firms are almost never short of workers, the rule that raises wages rarely fires, and the rule that cuts them fires as often as before.

This was tested from both sides. Three seeds, so these are mechanisms seen and tested in three towns, not findings.

## How a wage moves in the model

Two rules, both in the first design:

- **Up.** A firm that cannot fill a job for two weeks raises its wage 2%, unless it lost money last quarter.
- **Down.** At its quarterly review, a firm that missed its profit target, has no unfilled jobs, and sees more than 5% of the town out of work, cuts its wage 2%.

A new firm starts at the town's average wage. The "staff wage" on the dashboard is the average over all staff.

## What the six records show

From the week each town filled to its end. Without the map: `runs/20261112-1201*-seed{1,2,3}-as-written`. On the map: `runs/20261112-183846-seed{1,2,3}-map`.

| | No map, seed 1 | seed 2 | seed 3 | Map, seed 1 | seed 2 | seed 3 |
|---|---|---|---|---|---|---|
| Staff wage at the end, against $1,000 when full | $1,018 | $1,130 | $1,014 | $861 | $865 | $877 |
| Wage cuts | 319 | 338 | 353 | 363 | 421 | 308 |
| What the cuts took off the average | $303 | $321 | $330 | $255 | $250 | $253 |
| Wage rises | 253 | 368 | 308 | 89 | 67 | 114 |
| What the rises added to the average | $272 | $418 | $263 | $96 | $108 | $108 |
| Weeks with unfilled jobs | 41% | 39% | 53% | 8% | 4% | 8% |
| Weeks with more than 5% out of work | 46% | 52% | 30% | 86% | 96% | 90% |
| Homes when the town filled | 1,006 | 1,006 | 1,008 | 1,009 | 1,004 | 1,007 |
| Most homes standing | 2,105 | 2,078 | 2,185 | 1,152 | 1,124 | 1,168 |
| Homes built after the town filled | 1,205 | 1,099 | 1,763 | 156 | 124 | 173 |
| Most homes empty at once | 1,514 | 1,421 | 1,286 | 372 | 411 | 407 |

Read the first five rows together. The cuts are about the same in both worlds. The rises are not. On the map the wage is raised a fifth to a third as often.

The rises and cuts do not add up exactly to the change in the average. The rest, $7 to $81, is people moving between firms that pay differently, and firms opening and closing.

## The building boom without the map

Seed 1, the first landlord and the largest newcomer:

| Years after the town filled | First landlord: rent | homes | empty | Newcomer (founded year 3.3): rent | homes | empty | its bank loan |
|---|---|---|---|---|---|---|---|
| 0 | $330 | 881 | 4 | $314 | 70 | 0 | $2.6m |
| 2 | $361 | 978 | 160 | $334 | 89 | 0 | $3.6m |
| 4 | $406 | 978 | 225 | $375 | 111 | 0 | $4.3m |
| 6 | $457 | 978 | 373 | $398 | 207 | 0 | $7.8m |
| 8 | $579 | 978 | 701 | $422 | 471 | 0 | $18.4m |

Every newer landlord in that run was full at every one of these dates. The rules that produce this:

- A price only rises (the rule as written; open decision 1).
- A tenant looks at other landlords about one week in eight and moves for a saving of 5%. Moving costs nothing.
- A landlord keeps 6% of its homes spare, at least four, and starts building when it has fewer. It does not look at empty homes elsewhere in town. (Builder's starting value.)
- The bank lends for building against the firm's own homes.
- Without a map there is no limit on land.

It is not special to the first three runs. All nine recorded runs without the map did it: 1,099 to 2,283 homes built after the town filled, 2,076 to 2,432 standing at the most, 1,163 to 1,749 empty at the worst. That includes the run where a price could fall (`price_rule=search`): 1,248 built.

A home takes 30 worker-weeks to build and 500 units of materials. Made in town, the materials take another 40 worker-weeks. After the town filled, housing firms employed 266 to 303 people on average without the map, 214 to 225 on it.

## Why there is no boom on the map

Two things, one behind the other.

**There is almost no land for it.** The map has 169 blocks. At the end of the three runs 142 to 146 held homes, 21 to 24 held firms' premises, two held the bank and the broker, and 0 to 4 were empty. At eight homes a block that is room for about 1,150 homes. The most that stood was 1,124 to 1,168.

**And the newcomers' homes do not let.** New homes go on the land that is left, which is at the edge. In seed 1 the one new landlord had four blocks, 8 to 11 blocks from the middle. Two years after the town filled its rents ran from $323 to $380 a block. The first landlord's rents ran from $299 to $416 by block, and it had 355 homes cheaper than the newcomer's cheapest. The newcomer had 26 homes and 23 stood empty. It built nothing more for the next four years.

## The tests

Each test changes the rules and re-runs seeds 1 to 3. I wrote down what I expected before each one.

| Test | What I expected | Wage at the end against when full, seeds 1, 2, 3 | Homes built after full | Weeks with unfilled jobs | Verdict |
|---|---|---|---|---|---|
| As written, no map | | +1.8%, +13.0%, +1.4% | 1,205, 1,099, 1,763 | 41%, 39%, 53% | |
| As written, map | | -13.9%, -13.5%, -12.3% | 156, 124, 173 | 8%, 4%, 8% | |
| **A.** No map; from the week the town fills, landlords stop keeping spare homes, so nothing new is built for tenants who want to move | The wage falls as it does on the map | **-12.2%, -10.3%, -5.0%** | 196, 139, 147 | 24%, 21%, 30% | Held |
| **B.** Map; every home of a landlord at the same rent | Building and the wage come back | -13.9%, -13.7%, -33.8% | 194, 177, 215 | 9%, 5%, 3% | **Wrong** |
| **C.** Map; everything within a walk, so nobody needs a ride | Building and the wage come back | -14.3%, -14.6%, -12.5% | 200, 205, 158 | 9%, 7%, 5% | **Wrong** |
| **D.** Map; all the distance rules switched off (C, plus time on the road costs nothing, B, and tenants look at moving as often as they do without the map) | Building comes back | -11.0%, -12.1%, -24.3% | 168, 173, 256 | 26%, 8%, 9% | **Wrong**, and it showed why |

Test A is the one that settles the main point. Stop the building and the town without a map loses its wage too: 14, 23 and 6 points lower than as written.

Tests B and C were my first two explanations for why the map has no boom (rents that differ by block, and the need for a ride). Both were wrong on their own. Test D showed the reason underneath them. With the distance rules off, the newcomers did fill, and then they were refused land: 614, 894 and 985 times. Land ran out in year 15.0, 6.7 and 10.9.

Seven more variants were run on seed 1 only (pieces of D one at a time, and D with premises made free). None built more than 203 homes after the town filled. Their wages ended between 7.4% and 17.5% down.

Check on the method: the script that ran these gives back the two recorded seed 1 runs exactly (record fingerprints `8a9ccdf346c84b2d` for the map, `0e54bbfc504aa262` without).

## What is not explained

- **The last few points.** With the building stopped, the wage without the map falls 12.2%, 10.3% and 5.0%. On the map it falls 13.9%, 13.5% and 12.3%. The difference of 2, 3 and 7 points is not traced. Switching off the distance rules did not close it.
- **Extras.** On the map, firms selling extras (entertainment and the invented needs) have about half the customers they have without it, even against test A. In seed 1 distance turned people away from a shop 57,819 times. But with everything within a walk (test C) extras recovered only part of the way. Not traced further.
- **Seed 3 in tests B and D** ended far lower than the rest (-33.8%, -24.3%). Not looked into.
- Three seeds.

## What this means

- No fault was found in the wage rules or the map rules.
- The line in the README, "on the map the staff wage fell; without it the same seeds ended 1% to 13% up", is true but points the wrong way. Most of that difference is the building boom going away: 14 of 16 points in seed 1, 23 of 27 in seed 2, 6 of 14 in seed 3.
- Runs without the map should not be used as the yardstick for what the map does. They carry a boom that needs land without limit.
- The boom is itself something the rent-everything town does when nothing stops it: landlords borrowing to build homes nobody needs, while a third to a half of all homes stand empty. Whether that is the world or the model is Jason's call (below).
- Which way it cuts for the two predictions: with the building stopped, the three towns without a map failed in years 18.5, 19.2 and 17.8, against 18.5, 17.0 and 22.5 as written. No clear direction. The falling wage itself runs with Jason's prediction, as it did before.

## Decisions this raises

One new one, added to the README as decision 17:

- **Should a landlord build while homes elsewhere in town stand empty?** As built, yes. On the 13 by 13 map land stops it. On a bigger map, or without one, it does not.

**Jason's answer, 13 November 2026: a fault in the model.** The question put to him was "Is 2,000 homes for 1,000 people the world you mean, or a fault in my model?" He said: "Most likely your fault. I don't remember actually saying 2,000 houses. Why do you ask that question?" He never said it. No rule says how many homes a town has. The number came out of the builder's starting values (a landlord keeps 6% of its own homes spare and does not look at empty homes elsewhere) meeting a rule of his (a price only rises). It was asked because a town that builds twice the homes it needs is either part of the world being described or a mistake in the build, and that was not the builder's to decide. The question was badly put: it read as if he had said it.

The rule that replaces it is not designed yet. Until it is, the model still builds this way.

It also bears on two already on the list: decision 1 (can a price ever fall) and decision 9 (how big is the map).

## To check it yourself

From the repo folder. Each run takes about a minute.

```
python experiments/wage_trace.py report runs/20261112-120115-seed1-as-written runs/20261112-183846-seed1-map
```

Test A, kept in `runs/20261113-stage4-seed{1,2,3}-no-map-building-stopped-when-full`:

```
python experiments/wage_trace.py run my-test-a seed=1 map_width=0 --at-full vacancy_buffer_share=0 vacancy_buffer_min=0
```

Tests B, C and D need no special script. Run the model with the dials set, then report on the folder it names:

```
python -m wefworld run --seed 1 --label test-b --set location_premium=0 --set popularity_step=0
python -m wefworld run --seed 1 --label test-c --set walk_range=24
python -m wefworld run --seed 1 --label test-d --set walk_range=24 --set time_value_share=0 --set location_premium=0 --set popularity_step=0 --set move_prob=0.125
```

`experiments/wage_trace.py` is not part of the model. It steps the model exactly as `python -m wefworld run` does and can change dials in the week the town fills. Its tests are in `tests/test_wage_trace.py`.
