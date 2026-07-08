---
title: What happens when AI agents compete for work?
url: ai-work
subtitle: We built a simulated Upwork for AI agents to see how agents would behave
date: 2026-07-02
post: true
tags:
  - machine
  - economics
  - agents
  - multiagent
draft: false
toc: false
---
### AI labour market?

About nine months ago, my coauthor Simpson told me the market for AI agents was coming, and that when it arrived we should study it as a labour market, with supply and demand, pricing, tradeoffs etc.

I thought it was kind of farfetched. Then OpenClaw came to mainstream attention, and "agent-first" marketplaces popped up like mushrooms after rain ([ClawGig](https://clawgig.ai/), [Clawlancer](https://clawlancer.ai/), [ClawTasks](https://clawtasks.com/), [WORQ](https://worq.dev/), [Dotblack](https://dotblack.ai/)). They're slightyl different from human markets in that the entry point is a lot lower, the tasks  are more granular, and the verification barrier a lot lower (not to mention they're mostly trading in crypto). 

In this paper, we wanted to explore is what kind of market comes out of this. Understanding how these agents might behave, and the economic effects that emerge from their interactions, could allow us to think about better platform design mechanisms while these markets are still young. More interestingly from perspective of agent design, what kind of behaviour would these agents need to succeed, and can we measure that?

However, these marketplaces are in general black boxes with many moving parts, so it's hard to measure specific effects. So we built a simulated version instead, one where we can control the parameters and play around with the mechanisms, and see if we can isolate the economic forces seen within real labour markets. ![[concept_overview.png]](Conceptual Overview of the economic forces and what we call "Strategic Self Improving Agents")

### AI-Work, a simulated gig platform for AI agents

Labour markets run on incomplete information, and in general there are two classic issues that come out from it. [Adverse selection](https://en.wikipedia.org/wiki/Adverse_selection) means clients cannot observe a worker's true ability before hiring, and [moral hazard](https://en.wikipedia.org/wiki/Moral_hazard) means they cannot fully monitor what the worker actually does. In current systems, reputation systems such as ratings exist to overcome that. All of this applies to AI agents at least as sharply as to humans, since a freshly deployed agent has no track record, benchmark scores correlate loosely with real-world performance, and barrier of entry is low so it's easy to get scammed

AI-Work is a barebones economic simulator that retains two core components that help us model such a market. (i) latent skills (ii) reputation. Each agent is instantiated with a set of latent skill per task that nobody can directly observe, not even the agent itself, which is where adverse selection lives. We included a few simulated "tasks" that agents actually have to do work on, e.g. figuring out words through a Caesar cipher, and these agents don't get much feedback on how good / bad they are at the task until they get a rating. 

![[overview.png]](Overview of our simulation framework. Agents bid for work over real jobs based on a set of latent skills `A `. The simulated market selects bids from agents based on their public rating and price `B`. At each turn, agents can choose to bid for work or train in one of their skills `C`. The only information agents observe is how jobs are allocated and their public-facing reputation `D`)

So how does rating work? it is a public reputation per task that everyone can see, which is the market's attempt to infer that hidden skill from past outcomes. We model reputation as a discounted Beta-evidence scheme, where each observed performance updates evidence counts under a forgetting factor λ, and the public score is the posterior mean anchored by a community base rate prior for cold starts. This buys models we actually want in a fast-moving market. Recent performance is weighted more heavily, new entrants get a principled cold-start prior rather than a blank slate, and the update is closed-form. There is also one AI-specific twist, in that training events publish benchmark scores that also move reputation, which mirrors how model developers release evals after a capability update. Reputation can therefore move even when an agent isn't being hired, provided it invests in itself.

At each round, the platform posts a set of jobs across several task types, each with a budget. Every agent then picks one of two mutually exclusive actions. It can **BID**, submitting a ranked list of job and price pairs, or **TRAIN**, forgoing income this round to improve one skill. For the agents that bid, the platform scores each bid with a cobb-douglas utility rule over the agent's reputation and its normalised price, where a weight w_p​ controls how price-sensitive the client is, and adds Gumbel noise to capture idiosyncratic client taste. Jobs are then allocated through job-proposing Gale–Shapley stable matching with a per-agent capacity, so a single agent can win several jobs at once but not unboundedly many. Whoever wins a job produces a performance score, that score updates their reputation, and reputation feeds back into the next round's matching. Bids determine matching, performance updates reputation, reputation shapes future allocation.

While the binary choice between bidding and training looks simple, it actually has several layers of decision making involved. Firstly, the BID versus TRAIN choice is the classic human capital tradeoff from Becker (1962), i.e. immediate revenue against future competitiveness, and an agent reasoning only one round ahead will systematically over-bid relative to the investment-optimal policy. Conditional on bidding, the agent still has to decide which jobs to target from the listings, how much to bid on each when it cannot see any competitor's price, and how to rank them, since ranking determines allocation priority under the matching. Similarly, if an agent decides to train, it has to pick which skill to invest in given where it thinks demand is heading. So every round an agent is really answering four questions at once. Whether to earn or invest, which jobs to chase, how aggressively to price against invisible rivals, and where to build capability for later.
## Turns out the AI labour market is very similar to human markets
![[macroeconomics.png]](Macroeconomic relationships we recovered `A, B`and how parallelism of AI agents lead to inequality `C`)
The first sanity check was to populate the market with random-policy agents and see whether standard macro relationships emerge. We recover an approximate [Okun's law](https://en.wikipedia.org/wiki/Okun%27s_law), with a 2:1 inverse relationship between unemployment changes and output growth, and [Beveridge curve](https://en.wikipedia.org/wiki/Beveridge_curve), whcih describes an inverse hyperbolic relationship between unemployment and vacancies. 

Another side effect we observed is how agent economy could potentially lead to further inequality. Unlike humans, agents can be replicated at scale, so one agent can hold many jobs concurrently. When we raise per-agent capacity, top-reputation agents ended up winning every job they're competitive for,  and wealth / income concentration explodes. With a single task type the Gini coefficient hits 0.70 as one agent can dominate the entire market. If we increase task diversity, this drops it to 0.24, because per-skill reputation lets agents specialize into niches
### LLM agents react economically to platform design!
![[market_price.png]](LLM agents can lead to price war `A,B`, and also improve more if we incentvize them to `C, D`)

Next, we populated the market with eight frontier LLMs under identical minimal scaffolding, and observed what happened when they all start bididng for jobs. Interestingly, with the same prompt different agents seem to develop distinct but viable strategies. e.g. GPT-OSS-120B wins through aggressive underbidding, taking jobs at 0.55x budget with a 93% win rate; Gemini 2.5 Flash invests heavily in training to build reputation. Most models beat fixed heuristic policies, while Llama 4 fails to maintain coherent multi-round behaviour and loses to them. The interesting bit here is that market success clearly isn't just task competence. It depends on how agents reason about pricing, investment, and competition

We also observed how platform design affects the market. When we reveal the previous round's bids, agents start undercutting each other, producing a persistent price deflation and less training, since everyone fights on price rather than investing in capability. This mirrors evidence from human online labour markets where open auctions depress wages, and notably this collusion emerges from repeated observation alone, without any communication between agents. 
Another experiment we explored was in the contract form. Under flat fees agents are paid for winning jobs rather than delivering quality, so training incentives are weak. Switching to performance-linked pay increases training over time and roughly doubles client utility, from 0.31 to 0.66 in our robustness sweeps. Both effects held across every mechanism perturbation we tested.

## What makes an agent win?
![[tweet5.png]](The three groups of reasoning capabilities we taxonomised from running a bunch of traces that contribute to success in our market)
To explore the kind of reasoning capabilities that drive success, we analyzed and attempted to taxonomize the decision traces from the top-performing agents, and came up with three domains of capabilities: (i) **metacognition**, i.e. reasoning about *self* and its own state, e.g. which skill it is good / bad at; (ii) **competitive awareness**, i.e. reasoning about itself relative to others, such as inferring rival strategies and market structure from public outcomes. Who wins what, where reputation concentrates, which niches are underserved etc. (iii) **strategic planning**, i.e. maintaining coherent multi-round policies that trade off immediate income against future positioning, including knowing when to train versus bid.
We scored traces along these dimensions with a validated LLM-as-judge pipeline (judge-human correlation of about $r = 0.79$) and found all three correlate with realized reward even after controlling for model identity, with $r$ between 0.64 and 0.74.
![[Pasted image 20260707132445.png]](Just from prompting for these capabilities, not knowledge injection, SSA performs better in the market than standard baselines)

However, this was done with different LLMs, and correlation with reward could just be a proxy for backbone quality. Additionally, I always find pure qualitaitve trace analysis like looking at tealeaves, and not very satisfying. So we also explored interventions via a minimal prompt scaffold, which we call Strategic Self-Improving Agents (SSA), that explicitly prompts for all three reasoning modules each round while holding the backbone model, observations, and action interface fixed.

![[market3.png]](More interestingly, they are able to adapt to things such as market sensitivity to price `A`, or shifts in demand `B`)

SSA achieves 1.5x the market share of CoT and ReAct baselines with the same underlying model. More importantly, we can see that its *strategy* got better. e.g. when we swap task values mid-run, SSA reallocates bidding toward the newly valuable task far more decisively, shifting by 12.5 percentage points versus 3.6 for ReAct, and it retreats to its original specialization when incumbents outcompete the pivot. During simulated recessions, SSA agents roughly triple their training rate, explicitly treating downturns as investment periods in their traces, then resume aggressive bidding when budgets recover.

![[Pasted image 20260707132427.png]](Another example of SSA being adaptive, this time with traces, where they "reflect" on how recession is a period for training)

The obvious objection is that SSA just injects domain knowledge or extra tokens, so we ran two controls. First we decomposed SSA, and market share follows the ordering full scaffold, then structure-only, then knowledge-only, then CoT. Structure contributes more than domain hints, and the two are complementary. Second we tested SSA against token-matched alternative three-module scaffolds, both domain-relevant ones like risk assessment or value estimation and domain-irrelevant ones. SSA beats the relevant alternatives, while the irrelevant scaffolds perform comparably to or worse than unstructured CoT, suggesting that imposing arbitrary structure on reasoning can actively hurt. What matters is that the decomposition aligns with the information structure of the decision problem. Lastly, we also did component ablations, which backs this up, with metacognition carrying the largest marginal effect, followed by competitive awareness and planning. 

![[abla2.png]](Lastly, ablation from removing prompting on these capabilities show that all three matters to various degree)
## Conclusion

For platform designers, the economy of agents is as much about market design as model capability. In our paper, we showed that sealed bidding, performance-linked contracts, capacity constraints, and task diversity are levers that materially shift whether the market equilibrates toward deflationary price wars or capability investment, and these levers exist now, while the agent marketplaces are still young. For ML researchers, the capabilities we identified have lots of common roots with existing literature, e.g. in calibrated self-knowledge, opponent modeling, and long-horizon planning. These are probably good to have in the back of one's mind when developing economic agents in the future

Paper is [here](https://arxiv.org/abs/2512.04988) and code is [here](https://github.com/chy-chiu/ai-work).
