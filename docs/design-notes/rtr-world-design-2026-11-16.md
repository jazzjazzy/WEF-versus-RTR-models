# Right to Repair world (RTR), design notes (started 16/11/2026)

The second world, to set beside the WEF world (`wef-world-model-design-2026-11-12.md`, beside this note, model in `~/Workspace/two-towns`; that folder was called `wef-world` until 18/11, so "wef-world" further down this note means the same folder. Since 17/11 the WEF world is run from its `wef/` folder and the RTR world from its `rtr/` folder, over one shared `engine/`).

## His brief, 16/11/2026, in his words
"Okay, so I think we've pretty much got what we need for The world economic forum version now, I want to do the right to repair one. So, this one runs pretty much the same rules as a WEF, but this one allows people the decision to either rent or buy. They can buy their own appliances. They can repair their own appliances. All products and manufacturing can be open-sourced with an MIT license agreement. So it covers things like ownership, rights to repair, and open source designs and software. In other words, giving people freedom to do whatever they want.. We'll call this one right to repair or RTR"

## What that settles (J)
- Name: Right to Repair, RTR.
- Same rules as the WEF world except where he says otherwise.
- People choose to rent or to buy.
- They can buy their own appliances and repair them themselves.
- Products and manufacturing can be open, under an MIT licence: ownership, right to repair, open designs and software.

## Already on record from 12/11 (docs/predictions.md in wef-world)
- Failure: the first week 90% of everyone is unhappy. Same measure in both worlds.
- His prediction: open source "would be more constructive for society, but if it is too open it may collapse as well".
- Mine: neither world collapses by itself.

## The conversation, 16/11/2026
- Asked: what does a newcomer do in the RTR town that they could not in the WEF town? His words: "The main thing that they can do is that they can own things so if they They can also make their own small businesses. So side hustles or actual small businesses themselves If a company creates something and gives the right to repair and actually open source it, then any person can actually take those open source designs and build it themselves or build it for other people who don't want to build it themselves. and so they can make a profit off it."
  - So (J): a person can own things; a person can run a side hustle or a small business; an open design can be built by anyone, for themselves or for others, at a profit.
  - Note his "if a company ... gives the right to repair and actually open source it": whether every company must, or each chooses, is not said. Asked next.

- Asked: must every company open its designs, or does each choose? His words: "Let's go for the most purest form, so if anyone creates anything, it's always open source. So if a company makes something it's open source if Someone comes along and creates a business out of that open source by making their own modifications Their modifications are open source and so on and so on."
  - So (J): the purest form. Everything anyone creates is open, always, and so is every modification of it, without end.
  - For the paper, not the model: that is a share-alike rule (as in the GPL), not the MIT licence he named on the first message; MIT lets a modifier keep changes closed. Told him once.
  - Builder's note: this puts his own "if it is too open it may collapse as well" to the test at its far end. An openness dial would let in-between towns be run later. Not discussed with him.

- Asked: if anyone can copy a new product the day it comes out, why would a company pay to create it? His words: "We need to work that out, that's not the issue. If companies are only making things to make money, then what's the point? Why don't I just leave it up to the people who are actually going to create things for fun?"
  - So (J): in RTR new things are created by people who create for the fun of it, not by companies for the money. How that works in the model is to be worked out ("We need to work that out").
  - Asked next: when does someone create for fun (my guess put to him: when their own needs are covered and they have time and security to spare).

- Asked: do people create only when their needs are covered, or also when struggling? His words: "I think people should still create while they're struggling. It gives them the opportunity to get out of the struggling."
  - So (J): anyone creates, whatever state they are in; creating is also a way out of struggling. (My guess that it needs spare security was wrong.)
  - Asked next: what someone needs to start making things for others (only their time, or money for materials and tools too).

- Asked: what does someone need to start making things for others? His words: "Time, I think, is the main thing to come up with an idea. Money is the way to expand it, and loans is to make it a business. Does that make sense? Some things may not require as much money as others, example would be if you work in an office job you already have a computer at home, so writing software isn't an expense to you. But if you need to host servers and stuff like that then you'll need to get a lot. But if you're building chairs, you need to buy table saws, drills, tools, all that sort of thing. So you'd need to be having an income that was reasonable in the beginning, or you could get a loan. if the bank thinks it's profitable."
  - So (J): three steps. Time gives the idea. Their own money expands it (a side hustle). A loan makes it a business. What it costs to start depends on the thing: software next to nothing, hosting a lot, furniture the price of the tools. A loan is given "if the bank thinks it's profitable".
  - Differs from the WEF bank, which lends to a person only against wages (eight weeks of them) and to a firm only against homes, appliance sets and land. A loan on the promise of profit is a new rule for RTR. Told him.
  - Asked next: does "rent or buy" cover homes as well as appliances and other things.

- Asked: does "rent or buy" cover homes too? His words: "that covers frames as well. Homes can also be borrowed against as well. but that also means it can also be foreclosed as well." ("frames" read as "homes": voice typing. Said so to him.)
  - So (J): homes can be bought as well as rented. A home can be borrowed against. A home borrowed against can be foreclosed.
  - Asked next: when the bank forecloses, who ends up owning the home.

- Asked: when the bank forecloses, who ends up owning the home? His words: "That's a very good question. I was thinking any landlord that wants to pay off the debt. Can own it, But then I was thinking renters may want to get up the ladder as well. So maybe renters and if no renters take it, then we offer it to the landlords. Or other owners can own it and become a landlord? Man, it starts getting complicated."
  - Not ruled: he was thinking aloud and found it getting complicated. His own words hold an order (renters first, then landlords; owners who become landlords as a third idea) and a price (the debt owed).
  - Put to him as one simple rule, for a yes or no: the bank sells a foreclosed home for the debt owed; first to a renter who can pay or borrow for it; if none, to a resident who already owns (they rent it out, a small landlord); if none, to a landlord firm.

- His answer: "Yes, I agree with you. That's an actual good order. The other option is The person that foreclosed on the house If they have enough money We'll always try and rent unless they don't have enough money to rent, then they become homeless. Is that already a consideration?"
  - So (J): a foreclosed home is sold for the debt owed, offered first to a renter who can pay or borrow, then to a resident who already owns (a small landlord), then to a landlord firm.
  - So (J): the person foreclosed on tries to rent if they have the money; if not, they are homeless. Already how the model treats anyone with no home (checked in `household._review_need`: each week someone with no home rents one if they can pay and one is free within reach; otherwise they stay homeless and are counted). Told him yes.
  - Asked next: who a buyer buys their home from.

- Asked: does a renter buy the home they live in from their landlord with a bank loan against it? His words: "So landlords can opt to rent or sell to a person. So, if their income allows for it, they will get a loan and buy. If they can't do that, then they'll rent. until their wages increase enough that they can buy."
  - So (J): the landlord chooses whether to rent a home or sell it. A person whose income allows gets a loan and buys; otherwise they rent until their wages rise enough to buy.
  - Asked next: when a landlord would choose to sell (its shareholders want the most profit and rent comes in for ever; if renting always pays more, nobody could ever buy and RTR would be the WEF town). My guess put to him: it sells when the price is worth more than the rent it would collect, or when it needs the cash.

- Asked: does a landlord sell when the price is worth more than the rent it would collect, or when it needs the cash, and otherwise keep renting? His words: "That is right. Also, another factor is if someone believes that they can rent they will initially Go to the bank and get a loan to build. So landlords can build and also rent people looking for housing can build as well"
  - So (J): the landlord's selling rule is as I guessed.
  - So (J): people can build homes too, with a loan from the bank: someone looking for housing can build their own, and (my reading of "if someone believes that they can rent", said back to him) someone who believes they can rent a home out can borrow to build one. Landlords still build and rent.
  - Asked next: what repairing your own appliance costs the owner, and whether a repair person can be paid instead (my guess: their time and parts at cost; or pay someone running a repair side hustle).

- Asked: does an owner keep their appliance going with their own time and parts at cost, or pay someone running a repair side hustle? His words: "Yes, that is correct."
  - So (J): repair your own with your time and parts at cost, or pay a repair person (a side hustle).
  - Asked next: prices. In WEF a company's price never falls (his decision 1). My guess put to him: in RTR companies still behave that way, but a person making things for others charges what it costs them plus a little and can undercut the company.

- Asked: do companies still never drop a price, while a person making for others charges cost plus a little and can undercut them? His words: "Yes, that is potentially true." (Tentative: record as his for now, open to change.)

## Played back to him 16/11 (the whole of it, for a yes or a correction)
1. Same town and rules as WEF, except what follows.
2. Everything anyone creates is open, always, and so is every change to it.
3. New things come from people creating for the fun of it, anyone, even while struggling; it is a way out.
4. Time gives the idea; their own money makes it a side hustle; a bank loan makes it a business, if the bank thinks it profitable. What it costs to start depends on the thing.
5. Anyone can make an open design for themselves or for others, at a profit.
6. Homes and appliances can be bought or rented. A landlord sells when the price beats the rent or it needs cash. A person buys with a loan when income allows, otherwise rents.
7. People can borrow to build a home, to live in or to rent out.
8. A home can be borrowed against and foreclosed. A foreclosed home is sold for the debt: renters first, then residents who own, then landlord firms. The person foreclosed on rents if they can, otherwise is homeless.
9. An owner repairs their own appliance with their time and parts at cost, or pays a repair person.
10. Companies still never drop a price; a person making for others charges cost plus a little and can undercut them (tentative).
11. Carried over unless he says otherwise (my assumption, put to him): no cap, 60 homes, fare before rent for work, the well-off spend more, the rich's unspent money sits, no tax or welfare, failure at 90% unhappy.

## The builder's to work out (told him; each will be marked as mine in the design)
- Time as something people have only so much of (creating, repairing and building all take it; the WEF model has no hours in the week except travel).
- What each kind of thing costs to start, and how the bank judges "profitable".
- The price of a home, the deposit and the loan; land for a home someone builds themselves.
- How his examples (software, chairs, hosting) map onto the town's needs.

## For the comparison
- The WEF world has no 100-town batch under its final rules yet (no cap was built after the second batch). One is needed on the same seeds before the two worlds are set side by side.

## Design document (16/11)
Written after his "Yes, write it up": wef-world `docs/superpowers/specs/2026-11-16-rtr-world-design.md`, branch `feature/rtr-world`. Awaiting the builder check and his approval. Nothing built.

## Builder check and his two answers (16/11)
A fresh reader asked eight questions. Six settled by me and marked (C) in the document: how owning enters wellbeing; the price of a let home (ten years of net rent); the least a maker's hour is worth (half the going wage); what a maker's business is (a small business with staff, working from home; a company only with the WEF capital); when anyone pays a repairer or builder (own hours valued at the model's hour, $25 at the start); no sale puts a tenant out, and a block with a privately owned home cannot be pulled down; building to let needs a sign a home is wanted.
Two put to him, by option:
- An empty home a landlord cannot let: **"Sells it cheap"** (J): after a year empty, sold at its value as a building.
- Borrowing against a home with no income, to pay bills: **"No, they need income"** (J): the bank lends against a home only when repayments fit income.
Document updated. Handed to him for approval. Nothing built.

## Stage 1a built (17/11)
Building and owning your own: spare time, own appliance sets, homes built on plots, the loan against a home, foreclosure and sale for the debt to renters. 773 tests; WEF unchanged. Three towns (not a finding): RTR 1a failed in years 23.0, 22.25, 22.02 against WEF 17.0, 18.0, 20.0 on the same seeds. Uncommitted, awaiting his word. Stage 1b, 2 and 3 not built.

## Stage 1b built (17/11)
Buying, selling and letting. Part A (buying from a landlord) committed `5f2c08e`; Part B (small landlords, the whole foreclosure order) committed `84fcb04` on his "Yes, commit", with the fresh review still running. 844 tests; WEF unchanged. Two calls of mine not yet put to him as questions: an owner buys an empty home to let only when a newcomer was turned away for want of a home in the last quarter; one landlord firm buys a let home from another only if it is worth a tenth more than the price. Three towns (not a finding): all of stage 1 failed in years 22.56, 23.75, 21.69 (1a alone 23.0, 22.25, 22.02; WEF 17.0, 18.0, 20.0). Two fifths to just over half owned the home they lived in at the most; up to 211 small landlords at once; one person let 76 to 100 homes by the end; the bank no longer holds unsold homes. Stages 2 and 3 not built.

## The review of stage 1b (17/11, after the commit)
One crash (about one full town in ten) and five rule faults, all fixed, tests first; not committed yet. The figures above are superseded. Three towns after the fixes (not a finding): failed in years 19.0, 24.25, 20.25 (WEF 17.0, 18.0, 20.0). A quarter to nearly half owned the home they lived in at the most; 112 to 164 small landlords at once; one person let 60 to 100 homes; the bank holds 146 to 382 homes unsold near the end. My call for him to confirm or overturn: an empty home is bought to let, by a person or a landlord firm, only when a newcomer was turned away for want of a home in the last quarter.
