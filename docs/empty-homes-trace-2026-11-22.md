# Empty homes: a trace (22 November 2026)

## The question

Decision 17 (13 November 2026): should a landlord build while homes elsewhere in town stand empty? Without
the map, WEF towns built 1,099 to 2,283 homes for about 1,000 people. Jason ruled it a fault: "Most likely
your fault" (J). The rule to replace it was left to Claude to propose and was never built.

On 22 November, asked whether there was enough for the paper, Claude listed this fault as one of the gaps.
His words: "ok, fix the empty homes fault first".

## What the towns show now

The hundred towns of each world run that afternoon (`wef/batches/shared-wef`, `rtr/batches/shared-rtr`,
both on the 13 by 13 map), middle town of the hundred:

| Year | WEF people | WEF homes | WEF empty | WEF homeless | RTR people | RTR homes | RTR empty |
|---|---|---|---|---|---|---|---|
| 5 | 342 | 344 | 1 | 0 | 788 | 1,036 | 318 |
| 10 | 1,113 | 1,113 | 5 | 0 | 798 | 1,237 | 442 |
| 14 | 1,168 | 1,152 | 232 | 242 | 805 | 1,238 | 430 |
| 18 | 1,171 | 1,112 | 319 | 364 | 812 | 1,238 | 419 |

**The WEF world.** The fault does not happen. Homes keep pace with people until the land runs out, about
year 10. Homes stand empty after that only as people who cannot pay are put out of them: the empty homes
rise with the homeless, and fewer homes stand as old ones are pulled down. No landlord builds into empty
homes. Without the map it would (the trace of 13 November), but the WEF world as it ships has the map.

**The RTR world.** A town of about 800 has about 1,240 homes, and a third stand empty from year 5. Traced in
seed 1:

- Week 208 (year 4): 758 people, 480 homes being built at once, by residents for themselves and to let.
  The town filled that same week and grew very little after.
- One newcomer turned away for want of a home in a quarter was the sign for every resident who could afford
  it to start a home to let, all in the same quarter: 203 were started in year 3.
- Year 8, with no homes built to let at all (the fix below), 283 homes stood empty: 271 were residents'
  homes offered to let, 9 a landlord firm's, 3 held by the bank. About nine in ten residents had built a home
  of their own and left the home they rented; landlords sold those homes on to residents, who offered them to
  let; nobody needed them. The town had stopped growing for want of jobs, not homes.

## A fix tried and dropped

Claude built a rule (C): a resident starts a home to let only while more newcomers were turned away (the most
in any one week of the last quarter) than homes stand empty and are being built in town, and a landlord
builds for those turned away only past the homes empty and being built by everyone else. Tests first; it
passed them. Full RTR towns of 10 years, with and without it:

| RTR town, year 10 | Seed 1 before | Seed 1 with it | Seed 2 before | Seed 2 with it |
|---|---|---|---|---|
| people | 797 | 657 | 823 | 909 |
| homes standing empty | 336 | 291 | 363 | 448 |
| homes started to let | 331 | 0 | 261 | 0 |

It stopped building to let altogether (landlord firms' own building always covered those turned away), and
it did not touch the empty homes: fewer in one town, more in the other. Jason's rule that a resident builds
to let when they "believe that they can rent" (J) would never have happened again. Put to him; his words:
"Yes, drop it and write it up". The code was not committed.

## Where it stands

- Decision 17's fault, as he ruled it, does not happen in either world as they ship: the WEF world's land
  stops it, and in the RTR world landlord firms all but stop building once the town is full (in seed 1, 18
  homes over years 7 to 11 against 135 in year 3).
- The RTR world's empty homes are homes people left when they moved into homes they built, after a fast
  early boom. That is the RTR world's own rule (own, build or rent, whichever is cheapest), not a landlord
  building into empty homes.
- A known oddity, not fixed: residents start homes to let as a herd, all in the quarter after one newcomer
  is turned away. It adds to the boom of years 3 to 5.
- Rents of empty homes still rise (in seed 1 with the dropped fix, the cheapest landlord's rent went from $340 to
  $459 a week between years 4 and 8 with hundreds of homes empty): under his decision 1 a price never falls.

## To check it yourself

The scripts, the four towns' results, the dropped code (`dropped-fix.diff`) and its tests are in
`rtr/batches/empty-homes-trace-2026-11-22/` (not in git). From the top folder:

```
python3 rtr/batches/empty-homes-trace-2026-11-22/whoempty.py 1 8 homes_built_for_those_wanted=true
```

needs the dropped code applied (`git apply rtr/batches/empty-homes-trace-2026-11-22/dropped-fix.diff`) in a
scratch copy; without it, run `whoempty.py 1 8` for the town as it ships. Each takes a few minutes.
