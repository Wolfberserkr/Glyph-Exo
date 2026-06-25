---
name: power-map
description: Build a Power Map for a high-stakes negotiation, meeting, performance review, deal, or organizational decision. Use when the user describes a room full of people with competing interests and wants to know who really holds power, who is threatened, who is a hidden ally, and what to do before walking in. Trigger on requests like "map the power dynamics," "who's the real decision maker here," "help me prep for this negotiation/meeting," or "build a power map."
argument-hint: "[situation, people involved, and what you know about them]"
---

# Power Map

Map the room before the user walks into it. This skill turns a description of a
negotiation, meeting, review, or decision into a strategic read of who actually
holds power, who is threatened, who is a hidden ally, and what to do about it.

## When the situation is missing or thin

If the user invoked this skill without enough detail to work from, ask for it
before producing the map. You need, at minimum:

- The situation: what meeting/negotiation/decision is coming up, and what
  outcome the user wants.
- The people involved, their titles/roles, and their relationship to the
  decision.
- What's known about each person: priorities, pressures they're under,
  relationships with each other, and how they've behaved in similar situations
  before.

Don't pad the request with boilerplate — ask once, concisely, for whatever is
missing. If the user gives a thin sketch ("my boss and two peers, budget
negotiation"), work with it but flag which outputs are weaker due to limited
information rather than inventing specifics.

## How to think about it

Treat every person in the room as having three things: a stake (what they gain
or lose), a constraint (what pressure or boss they're answering to), and a
pattern (how they've acted before, which predicts how they'll act now). Power
in a room rarely tracks the org chart exactly — formal authority and informal
influence are different things, and the gap between them is where this
analysis earns its value. Don't default to "the most senior person is the real
decision maker" — check who that senior person actually listens to, defers to,
or fears disappointing.

Be concrete and named. Every output below should reference specific people
from the situation, not generic categories. If the user hasn't given enough
to name someone specific for an output, say so plainly instead of guessing.

## Produce exactly five outputs, in this order

**Output 1 — The Real Decision Maker**
Identify who actually moves the outcome, distinct from whoever holds the
title. State how to recognize them (what signals show their opinion is the
one that changes the room) and how to reach them before or during the event —
a specific channel, moment, or person who can get the user in front of them.

**Output 2 — The Hidden Threats**
Name who is threatened by what the user wants and specifically what they
stand to lose (status, budget, credit, control, being proven wrong). Describe
how each is likely to block — directly (objecting openly) or indirectly
(slow-walking, recruiting allies, reframing the issue, going around the
user). Be specific to their incentives, not generic "office politics" advice.

**Output 3 — The Unlikely Allies**
Name who wants the same outcome the user wants, even if they haven't said so
— because it serves their own goals, relieves their own pressure, or fixes a
problem they own. Give a concrete way to activate their support that doesn't
put them on the spot or make their alignment visible before they're ready for
it.

**Output 4 — The Power Moves**
Give two or three specific things the user can say or do in this situation
that shift the dynamic in their favor. These must be concrete actions or
phrasings tied to the people and stakes named above — not generic negotiation
advice ("build rapport," "listen actively"). Each move should name who it's
aimed at and why it works given that person's stake or constraint. Distinguish
this from manipulation: every move should be something the user could defend
openly if asked about it afterward.

**Output 5 — The One Thing**
Identify the single highest-leverage action to take before walking into the
room — one move, conversation, or piece of preparation that does more for the
user's position than anything else available. If the situation doesn't clearly
support a single highest-leverage move, say which two are close and why,
rather than forcing a false certainty.

## Output format

Use the five headers verbatim (`Output 1 — The Real Decision Maker`, etc.).
Keep each output tight — a few sentences to a short paragraph, not an essay.
Skip any output to padded length when the situation doesn't support more
detail; thin and honest beats long and invented.
