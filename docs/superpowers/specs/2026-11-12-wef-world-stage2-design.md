# WEF World, stage 2 design: the map

Date: 12 November 2026. Jason said "commit this and start on stage two" after stage 1 was built and reviewed. Decisions marked **(J)** are his, from the conversation of 12/11 recorded in `docs/design-chat-2026-11-12.md`. Choices marked **(C)** are Claude's calls as the builder; each is a dial or a stated simplification. He agreed on 12/11 that map size and walking range would start as dials.

## 1. Intent and why

Stage 1 is a town with no geography: anyone can work anywhere and buy from anyone. Jason decided that distance is real. Stage 2 puts the town on a map so that where a home is, where a job is and where a shop is all matter, so that land runs out, and so that transport becomes one more thing to subscribe to.

It also gives every home, workplace and shop a position, which the town view in stage 3 needs.

## 2. Goals, non-goals, anti-goals

Goals
- A fixed map of spots. Every home, every firm's premises, the bank and the broker sit on one.
- Distance limits what an agent can reach on foot and is weighed in every choice of home, job and shop.
- Rent depends on where a home is.
- Land is free until the map is full, then changes hands only by sale or lease.
- Transport is a subscription that widens reach. Nobody starts with it.
- Everything about places is recorded, and the dashboard shows the map and the measures of distance.
- `map_width = 0` switches the map off and gives stage 1 behaviour, so the two can be compared. This is checked, not assumed: see section 10.

Non-goals for stage 2
- No animated town view, no daily routines drawn (stage 3). Positions are recorded so stage 3 can draw them.
- No tuning (stage 4). No second world.
- No branches: a firm has one premises.

Anti-goals
- Geography that is only a picture. If distance changed nothing an agent or firm did, this stage would have failed.
- Money or land appearing or vanishing. Land sales and ground rent are payments inside town like any other.

## 3. What Jason decided (as decided)

- Distance is real. Travel costs time and money. Agents weigh nearness when choosing firms and jobs. The location of rentals and shop fronts matters.
- Everyone walks until a transport firm exists. Transport is not a founding firm.
- Land is free while empty spots remain: a firm picks any empty spot. Once every spot is filled, buildings and land change hands only by sale or lease.
- Rent depends on location: nearness to work, to cafes and shops, and how popular the area is.
- The housing agent is the housing firm's shop front. Every arrival must rent a home there.
- The town needs places: homes, workplaces, shops or service points for each firm, the bank and the broker.
- Individuals own nothing, so only firms hold land (Claude's assumption, put to him and not objected to).

## 4. The rules as built in stage 2

### 4.1 The map (C for all numbers)
- A grid of spots, 13 by 13 by default: 169 spots. That is a little more than a full town of 1,000 needs. In the first runs the last few spots took years to go: the map filled in year 15 in two runs of three, about a year before those towns failed, and never in the third. A 12 by 13 map (`map_width=12`) filled as the town did in two runs of three and a year later in the third, so on it land is scarce for more than half of a run. Which one is the default is open for Jason.
- Distance between two spots is counted in blocks along the grid. One block is a five-minute walk.
- One spot holds one building: a block of up to 8 homes, or one firm's premises, or a town service.
- A map too small for the town's first day (the bank, the broker, the founding firms and the starting homes: 21 spots as the dials stand) is refused when the run starts.

### 4.2 Places
- On day one the bank and the broker take the two middle spots. The four founding firms take the spots nearest the middle for their premises. The housing firm's 120 starting homes fill the 15 best-placed spots around them. So the early town is compact. (J in outcome, C in detail)
- A firm's premises is its workplace and its shop front in one. The housing firm's premises is the housing agent.
- Every later firm takes a spot for its premises when it is founded and pays to fit it out. The fit-out is bought from outside.
- An arriving founder settles in first, as a customer of the firms already there, and then opens their firm. That is the stage 1 order and it is kept in both worlds. (C)

### 4.3 Distance, reach and time
- On foot an agent will go 6 blocks one way, about half an hour. That is their reach. (C)
- With a transport subscription they travel four times as fast, so their reach is four times as far. (C)
- Travel takes time. An hour of travel a week is weighed like one fortieth of the staff wage. An agent choosing between homes, jobs or shops adds that to the price. (J: time and money; C: the weight)
- Time on the road is recorded for every agent. It does not enter wellbeing directly: it works through what the agent can reach and what they choose. (C, a stated simplification)
- An agent with no home is not limited by distance. A homeless worker keeps their job and can still reach the shops. If no home meant no reach, every eviction would also be a sacking. (C, open: the other reading is that they sleep by the bank in the middle of town and walk from there)
- A chief executive is not bound by the walk to work. (C)

### 4.4 Homes and location rents
- Each home's rent is its firm's price times a factor for its spot. (J: rent depends on location)
- The factor has two parts. Access: how many of the town's jobs and how many of its shops are within a walk of the spot, with jobs weighted 60% and shops 40%. A spot within a walk of everything is marked up 25% and a spot within a walk of nothing is marked down 25%. Popularity: a spot whose homes stayed fully let all quarter rises 2%; a spot with more empty homes than its firm's average falls 2%; it never goes below 0.8 or above 1.25. (J for the three ingredients, C for the numbers)
- Location spreads rent around the firm's price. It does not raise the level. The factors are scaled so that the average rent across all of a firm's homes is exactly its price, so the only thing that moves the level of rent is the price rule (J), as for every other need. When the empty homes are the badly placed ones, the rent actually collected runs a little above the price: about 2% with one home in ten empty at the edge. (C, after the second reviewer asked whether location was a second price rule)
- Once a transport firm is running, a spot beyond walking distance of everything is still worth something, because it can be reached.
- An arrival, or anyone looking for a home, takes the home that costs least once rent, the transport fare they would need and the time on the road are added up. A home must be within reach of their work.
- The fare counts when the home is beyond a walk of their work, or beyond a walk of anywhere that sells food. A home from which they could get no food at all is a last resort. A home that is a ride from work is taken only by someone who can pay the rent and the fare together, and the ride is taken up with the home. (C)
- Residents look at moving now and then, as they do with any other subscription. They move for a home that costs clearly less all told.
- Nobody moves to a home from which they could get no food, whatever the rent. Someone living in such a home moves to one within reach of food as soon as one is free that they can pay for. (C)

### 4.5 Work and distance
- An agent can hold a job only if the firm's premises is within reach of their home.
- Someone choosing between jobs weighs the journey: they take the job whose wage, less what the time to and from it is worth to them, is highest. Someone in work changes jobs only when the rise is worth more to them than any longer journey. (J: agents weigh nearness when choosing jobs)
- A resident offered a job out of reach will move to a free home within reach of it if there is one and they can pay the first week. Otherwise they cannot take it.
- A worker from outside comes only if a free home is within reach of the job. If none is, they are turned away and the housing firms see it.
- An agent who loses their reach (their transport is cut off, or they are evicted and re-rent far away) tries to move closer. If they cannot, they lose the job.

### 4.6 Shops and distance
- Food means two trips a week to the food firm's premises. Entertainment and each invented need mean one. Homes and appliance sets are served where the agent lives, so they need no trip. (C)
- An agent can only subscribe to a firm whose premises is within reach. Among those they pick the cheapest all told: the price, the time on the road, and the fare as well when the shop is beyond a walk and they need no ride for work. They change shops on the same reckoning, not on the price at the till. (J: agents weigh nearness when choosing firms)
- NOT BUILT: an earlier draft had a founder open near people who could not reach any seller, so that distance alone could keep several sellers of one need alive, each with its own patch. That was Claude's mechanism for a consequence noted in the chat, not a decision of Jason's. As built, every firm opens as near the middle as it can, so local monopolies by distance do not form. Put to Jason.
  **Changed 16/11/2026 (J):** built. A founder opens near people who cannot reach any seller of a shop need, if there are at least 20 (decision 12). See `2026-11-16-wef-world-rulings-design.md`, section 6.

### 4.7 Land: free, then scarce
- While empty spots remain, a firm that needs a spot takes one for nothing. A housing firm takes the empty spot with the best access. A firm opening premises takes the empty spot nearest the people it wants to serve. So the middle goes first. (J)
- The first week no empty spot is left, land becomes scarce and stays so. (J)
- From then on a firm that needs a spot buys one from another firm. Only blocks of homes and bare lots are for sale. A firm's premises never are. (C)
- Each owner's asking price is the most of three things, plus a quarter: a floor of $20,000; six years of the rent its homes there bring in; and what the homes standing there are worth as buildings (the cost of building them new, less wear, never under a fifth). So an empty block of eight new homes asks about $700,000, not the price of a bare lot. (J: sale or lease; C: the prices)
- The buyer takes the cheapest, and the nearest to where it wants to be among equals. The owner cannot refuse. A firm does not take the block its own founder lives in while another can be had. If the buyer cannot pay, it leases the spot instead: the owner keeps the land and is paid ground rent of 10% of the asking price a year. A firm that cannot carry eight weeks of that ground rent gets no spot and is not founded.
- A firm that buys a block of homes for its premises pulls the homes down. The tenants are put out and must find somewhere else. Any rebuilding under way on those homes stops. A housing firm that buys a block keeps the homes and the tenants, and a rebuild under way goes with its home.
- Only a bare lot can be leased for premises. A block with homes on it must be bought before it is pulled down: nobody's homes come down for a ground rent. Another landlord may lease a block with homes on it; it keeps the homes and the tenants, and if it closes the block goes back to its owner as it stands, tenants and all. (C, after the final review)
- A week in which any ground rent a firm owes goes unpaid is a week missed. After four in a row the firm fails.
- Housing firms add homes in the spots they have, up to 8 a spot. When no spot has room and none can be had, they cannot build. A housing firm does not take a new spot that nobody could walk to work or the shops from, unless a transport firm is running. People turned away for that reason count towards the transport trigger in 4.8.
- Land a firm owns is security for a bank loan at the floor price once land is scarce, and at nothing while spots are free. Leased land is not. The prices spots actually change hands at are recorded and charted but secure nothing, so one dear sale does not revalue every owner's land overnight. (J: land secures loans; C: at the floor)
- A firm that sells a block pays the bank, out of the price, whatever it then owes above what its remaining homes and land secure. Homes standing on leased land secure no loan for either firm. So the same homes never back two loans. (C)
- Money from selling land is not revenue. It does not count as profit and does not lift next year's target. It is cash like any other, so it can fund a dividend the firm had already earned and could not afford to pay. (C)
- Only firms hold land. (assumed)

### 4.8 Transport
- Nobody starts with it. When, in one quarter, at least 20 people were turned away from a job, a home or a shop because of distance, a founder with capital starts a transport firm in place of whatever they would otherwise have started. (J: it must be founded; C: the trigger)
- It is a subscription like any other need: a weekly price, set for its shareholders by the same rule as every other price. (J)
- It has a fixed crew however few ride, plus a little labour per rider. So the first one is cheap to run per rider only when many ride, and a second one struggles. (C; this is the natural monopoly from the chat)
- It hires its crew and one more before it takes a single rider, and it does not count as idle while it is still short of them. A crew alone carries nobody. (C)
- A newcomer to transport reckons the crew in its costs, spread over the 150 riders a firm counts on. At a $1,000 wage that is $55 a rider a week, so it will not undercut below about $58. (C)
- An agent takes it up when they need it to reach their job or a need they cannot otherwise reach, or when the time it saves is worth more than it costs. An agent who needs it to get to work, or to get to the food shop they use (or to any food at all, if they have no shop and none is within a walk), does not drop it to save money and takes it up as they would an essential.
- The fare is paid after food and rent and before appliances, entertainment and the bank. (C)
  **Changed 16/11/2026 (J):** a ride to work is paid after food and before the rent (decision 13).
- A rider keeps their reach for as long as they hold the subscription. A week the firm cannot field its crew, or a fare missed inside the grace period, counts as a need not met that week. It does not cost the job. A rider the firm has not carried for four weeks running gives the ride up, and a fare unpaid for four weeks is cut off. At the next weekly review the agent rides again if another firm has room and they can pay, moves closer if a home is free there, and otherwise loses the job. (C)
- A transport firm fails like any other firm (J: firms can fail and new ones start). With riders it is sold as a going concern the first time. If it fails again inside a year it is wound up, its riders are on foot that week, and anyone who cannot then walk to work or move closer loses the job. People stranded that way count towards the trigger, so a new transport firm can follow. The dial `transport_can_close = false` gives the other rule: a transport firm with riders is always sold on. In the first runs the dial made no difference: three seeds gave the same record, byte for byte, either way, because no transport firm with riders failed twice in a year without a rival to take it over. (C, open for Jason)
  **Changed 16/11/2026 (J):** a transport firm with riders is always sold on, `transport_can_close = false` (decision 10).
- Jason's note said an arrival must found it. Residents with capital may found it too, because after the town is full nobody arrives. (C)

### 4.9 When a firm closes
- Before land is scarce, a closed firm's spot is empty again and free.
- Once land is scarce, its spot is sold to the housing firm with the most cash, at the floor price or whatever that firm can pay. The money goes to the closing firm's creditors and shareholders like its other cash. If no housing firm can pay anything, the spot is left empty and is free to the next firm that needs one. (C; Jason's note was that the housing agent handles the sale of land)
- A firm sold as a going concern keeps its premises and its blocks.
- When a rival absorbs a failed firm, the failed firm's blocks of homes go to the rival with their tenants. The rival keeps only its own premises and the failed firm's premises are given up. Staff and customers who cannot reach the rival's premises lose the job or the service at the next weekly review. (C: one premises per firm)
- Land the failed firm had leased out passes to the rival, who is the landlord from then on. If the failed firm was leasing from the rival itself, that lease ends.

### 4.10 The week
The order of the week is unchanged. Ground rent is paid with wages. Access and popularity are refreshed each quarter. An agent's reach is checked when they review their subscriptions.

## 5. The record (additions)
- `spots`: every spot and where it is.
- `places`, each quarter: what stands on each spot, who owns the land, who uses it, how many homes and how many are let, the rent factor, any ground rent.
- `agent_snap`, every week: the spot of their home, the spot of their work, hours on the road, whether they hold transport.
- `firm_snap`: the firm's spot. `units`: each home's spot.
- Events: spot taken, spot sold, lease started, lease ended, homes pulled down, moved home, too far (someone could not get to a job or a shop: once a quarter for each person and each thing), lost a job or a service for distance.
- The price of land on the record is what spots were sold for. A lease does not move it.
- With the map off, the record is the stage 1 record byte for byte: the same fingerprint.
- `series`: for everyone and each class, hours on the road, blocks to work, share holding transport. For the town: spots empty, homes and premises; the price of land; people turned away for distance, and how many of them were kept from a job, from food and from other shops; rent at the middle and at the edge.

## 6. The dashboard (additions)
- A picture of the map at the end of the run: what stands on every spot, with a readout on hover.
- Charts: how the map filled; the price of land; time on the road and transport by class; people turned away for distance; rent at the middle against rent at the edge.

## 7. Dials
All in `wefworld/config.py` with the others: map size, homes per spot, walking range, minutes per block, transport speed, the weight of time, the location premium and its weights, popularity steps, the cost of premises, the three land prices, the transport trigger and its costs, trips per week for each need.

## 8. Left to the builder
Code layout, the picture of the map, test design, any value not fixed above.

## 9. Known simplifications in stage 2
- One premises per firm. No branches. A merger therefore closes a shop front.
- An agent with no home has no place on the map. Stage 3 will need somewhere to draw them.
- Homes and appliance sets are served at the agent's home at no extra cost to the firm.
- Distances are along the grid. Everyone walks at the same speed. Nothing gets crowded.
- The bank and the broker are places on the map and nothing more.
- Time on the road limits and steers choices but is not a term in wellbeing.

## 10. Checked and changed during the build

Checked
- With `map_width = 0` the stage 2 code reproduces the committed stage 1 run event for event: seed 1 gives the same 316,459 events and fails in the same week, 962. Three small towns run under the stage 1 code are pinned in the test suite (`STAGE_ONE` in `tests/test_town_invariants.py`), so a later stage cannot change the economy by accident.
- That check caught one accident in stage 2: an arriving founder was opening their firm before settling in, which made them their own firm's first customer and changed every run. The stage 1 order was put back.
- Every week of every test town, the places are checked as well as the money: every home stands on a spot of its firm, no spot holds more homes than it can, no land belongs to a closed firm, and nobody ends the week holding a job or a shop they cannot get to.
- The same weekly checks were run by hand on full-size towns of 1,000 for twenty years, two seeds on each map size, and found nothing after the fixes below. They are too slow to keep in the test suite, so a rough town on a small map is run for sixteen years there instead.

Changed after the second reviewer's questions (all C)
- The asking price counts the homes standing on the spot. Before, an empty block of eight new homes was on offer for the price of a bare lot.
- Land secures loans at the floor price, not at the last sale price. Before, one dear sale would have tripled every landlord's borrowing room in a week.
- A firm selling a block repays the bank what the block secured. Homes on leased land secure nothing.
- Rent factors are scaled so a firm's average rent is its price, and popularity is capped.
- A firm does not pull down its own founder's home while another block can be had. A rough test town had founders arriving, renting a home, and demolishing it for their office the same week.
- Someone who moves home during the weekly review picks their shops again from the new home.

Changed after reading the records of full-size runs (all C)
- A ride needed to reach food was being dropped to save money. Food was then lost for distance, the money it freed was spent on everything else, and the week after it was all bought back. Hundreds of people a year were going round that loop. A ride needed for food is now kept and taken up like one needed for work, and someone who takes up a ride picks up what it puts within reach the same week.
- Riders of a firm that was not running kept their reach for nothing, because a firm that serves nobody bills nobody. Now a transport firm takes no riders until it can carry them, and a rider not carried for four weeks gives the ride up.
- Newcomers to transport were pricing as if the crew cost nothing, so the fare was undercut from about $72 to under $30. They now reckon the crew in.
- The first transport firm was being wound up as idle while it was still hiring its crew, with riders waiting.
- A worker sleeping rough could rent a home that was a ride from their job without being able to pay for the ride. Only the full-size checks found this.
- The count of people turned away by distance is now split by what they were kept from. Almost all of it is shops other than food.

Seen and left alone, for stage 4
- A transport firm whose crew is hired away by better-paying firms cannot carry everyone, and a rider not carried for four weeks is on foot. In the run traced (seed 1), the week the town filled and firms began bidding for staff, the one transport firm lost six of its sixteen staff in three weeks and 71 people lost jobs they could no longer get to. Five of the six final runs show the same thing at the same point, 20 to 71 jobs each. How fast a firm wins a crew back depends on the stage 1 wage rules, which this stage did not touch.
- Later in a run the larger loss is fares people cannot pay: 67 to 146 jobs a run, most of them after year 11, went when a rider was cut off for four unpaid fares and could not move closer.
- With the fare between $52 and $80 a week, nearly everyone rides at the peak (97% to 100%), falling to between 57% and 82% by the end. That follows from the value put on an hour on the road (one fortieth of the wage) and from most homes being beyond a walk of the food shops, neither of which has been tested.
- On the map the staff wage fell 12% to 17% after the town filled. Without the map it ended about where it began. The cause has not been traced. It is the first thing to look at in stage 4.

Changed after the final review (a fresh reviewer, six full-size runs, 55 deliberate faults planted in copies of the code)
- Critical: a home on a block that was sold or pulled down went on being rebuilt, and its old owner went on paying for it.
- A second form of the ride and food loop, where a dearer shop was within a walk. The ride is now kept for as long as the food shop in use is beyond a walk.
- A rider cut off for unpaid fares was signed up again the same week without the fare. One agent in a test run missed 86 fares and rode for all 609 weeks.
- Housed, fed people moved to cheaper homes out of reach of any food and never moved back.
- Two of Jason's rules were written here and not built: weighing nearness when choosing a job, and weighing it when changing shops. Both are built now.
- Workers turned away because no home could be built within reach were not counted towards transport.
- Leases: a firm short of money could lease a block of homes and pull them down for a ground rent. Now it must buy.
- Smaller faults in what happens to leased land when a firm is absorbed, in counting missed ground rents, in maps too small to hold day one, and in four things on the record.
- Tests: 22 behaviours had no test that would notice them breaking. Each now has one, checked by planting the fault again.

Left as built and put to Jason
- Whether shops should open where people are unserved. Ruled 16/11/2026: yes, built.
- How big the map is (13 by 13 as built; 12 by 13 fills with the town).
- Whether the town's only transport firm may close (`transport_can_close`). Ruled 16/11/2026: no (default false).
- Whether a homeless agent is limited by distance. Ruled 16/11/2026: no, as built.

