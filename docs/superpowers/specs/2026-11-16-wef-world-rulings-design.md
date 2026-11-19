# Jason's rulings of 16 November 2026: what changes and how it is built

On 16 November 2026 Jason ruled on decisions 1 to 16 (README, "Decisions"). Seven
differ from what was built: 2, 5, 8, 10, 12 and 13 change the model, 14 changes the
town view. He said "Yes, build them". For decision 8 he then chose "Bigger plan and
better home" from three designs put to him. This document says how each is built.
**(J)** is his ruling, **(C)** the builder's call.

## 1. The principle: every ruling is a dial

Each ruling is a dial whose default is his ruling and whose other value is the model
as it was built before 16 November. `config.OLD_RULES` is the list of settings that
gives the old model. With them, a town must give the same record, byte for byte, as
before (the stage one fingerprints in `tests/test_town_invariants.py`, and a town of the
first batch of 13 November). So the first batch can always be made again, and every
change can be measured one dial at a time. (C)

## 2. Decision 2: a lost luxury fades after a year (J)

`habit_weeks` defaults to 52. Old value 0.

## 3. Decision 5: the town starts with 60 homes (J)

`needs.housing.initial_units` defaults to 60. Old value 120. Appliance sets stay at
120: he named homes only. (C)

## 4. Decision 10: a transport firm with riders is always sold on (J)

`transport_can_close` defaults to false. Old value true.

## 5. Decision 13: the fare before the rent when the ride is for work (J)

`fare_first_for_work`, default true. A resident who rides and whose job is beyond a
walk of home pays the fare after food and before rent. A ride needed only for food
keeps its old place, after rent (C: the ruling is about work). A chief executive is not
bound by the walk to work, so their fare keeps its old place (C). The fare is still not
essential: a calm resident still does not borrow for it (C, unchanged).

## 6. Decision 12: a shop opens where people are unserved (J)

`shops_near_unserved`, default true. `unserved_entry_min`, 20 (C: the same as the
transport trigger).

- A resident is unserved for a need when they have a home, do not hold the need, would
  want it (everyone wants a base need; an invented need suits some tastes), and no
  seller of it is within their reach (walking, or riding if they ride). Only needs a
  customer travels to count: food, entertainment and invented needs. Not housing, not
  transport. (C)
- A founder choosing what to start looks first for the transport gap (as before), then
  for the shop need with the most unserved residents, if at least `unserved_entry_min`.
  If there is one they enter it. Only then do they invent a need or enter the most
  profitable one, as before. (C)
- Price: the cheapest seller's price, never below cost plus the usual floor margin. They
  need not undercut a rival their customers cannot reach. (C)
- Premises: as near as can be to the home spot with the most unserved residents within
  a walk of it (ties: the lowest spot id). (C)
- Event `unserved_entry`: the need, how many were unserved, the spot aimed for.
- With no map nobody is unserved by distance, so nothing changes.

## 7. Decision 8: the well-off spend more (J: bigger plan and better home)

- **Well-off.** Income at least `well_off_income` (1.5) times their weekly bills at
  standard size (the basket of the four base needs, held or not, the luxuries and the ride
  they hold, and the loan payment), with their savings cushion full (C, put to him with
  the design). They
  stop being well-off when income falls below `well_off_drop` (1.2) times those bills or
  their cash below half the cushion (C: so a plan does not flip every week).
  `well_off_income = 0` switches decision 8 off.
- **Bigger plan.** Food, entertainment and invented needs, not transport (C: a ride is
  a ride). A well-off resident's plan is `bigger_plan` (2) times the standard: they pay
  twice the price, and the firm needs twice the staff and goods for them and counts
  them twice when it decides whether it has room and how many staff it needs (J). Each
  week, at the review of what they buy, a well-off resident moves up, need by need in
  order of need, but only while income stays at least `well_off_drop` times the bills with
  the bigger plan; one who is no longer well-off moves back. A well-off resident short of
  cash steps bigger plans back to standard, least needed first, before dropping anything
  (C, after the review). Event `plan_change` with the need and the size.
- **Better home.** A home is standard or better. A better home costs `better_home`
  (1.5) times as much to build, to keep up and to rent, and is worth that much more
  as security for a loan (C: the factor). A well-off resident looking for a home (when
  signing up, on becoming well-off, and when they look at moving) looks at better homes
  first and takes the one that costs least all told, within reach of work and within what
  they can pay, leaving income at least `well_off_drop` times the bills. If none is free
  they wait for one, and look again each week; only someone who could pay for one at the
  cheapest landlord's price waits. The biggest landlord starts better homes for those
  waiting, less the better homes free or being built anywhere in town, after and on top of
  its usual building (which counts standard homes only), under the same test of what it
  can pay for (C). (First
  built as noted demand, the way people turned away are noted: that counted looks, not
  people, and built 178 better homes for a peak of 44 well-off in seed 1, over 100 of them
  standing empty from year 11. Changed the same day.) Anyone else may rent a
  free better home if it is their cheapest choice; a resident who is no longer well-off
  moves out of one by the usual test of cost. Event `unit_built` carries `grade` for a
  better home; `moved_home` has reason `better`.
- **The yardstick.** The basket, and with it security and the cushion, is measured at
  standard sizes and standard rents, as it already leaves out luxuries, so moving up does
  not make anyone feel poorer. The bills actually due, and the test for destitution, use
  what is really paid. (C)
- **The record.** The units table gains a grade column. Without a map, homes have no
  place, and a well-off resident simply takes a better home when a landlord has one free.

## 8. Decision 14: class as the dot's shape (J)

The colour stays as it is (wellbeing, or class when switched). The shape shows class:
working a circle, owner a square, out of work a triangle (C). The key shows the
shapes. A rider on the road used to be a square; now a square is an owner, so a rider on
the road has a dark outline instead (C).

## 8a. No cap on people (J, later the same day)

`population_cap` defaults to 0, no cap; above 0 it is a cap as before, and
`OLD_RULES` sets 1,000. A newcomer, worker or founder, still needs a free home
(J). With no cap the town is full (`town_full`, reason "no home, no land") the
first week a newcomer is turned away for want of a home while no block of land is
empty (C). Without a map there is no land to run out, so a town with no map and no
cap is never marked full; arrivals stop only when no home is free or the wage is
under the outside wage.

## 9. Not in this build

The rule that replaces decision 17 (a landlord building while homes stand empty) is
not designed. Better homes already follow the rule it may want: none is built while
better homes stand empty. The rules documents of stages 1, 2 and 3 have a note under
each changed rule.

## 10. Build order

Settings (2, 5, 10), then 13, 12, 8 and 14, each tests first. Then the whole suite, the
old-rules records checked, a fresh reviewer, one fix pass.
