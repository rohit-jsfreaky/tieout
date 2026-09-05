# CLAUDE.md — desk/ (the one screen)

The demo. A judge who has won 22 hackathons said presentation is scored. This screen has one
job: make the loop visible — evidence lands, a human approves once, the rule appears with a
name on it, the next exception clears itself citing that name, the counter drops.

Phase 4. Read `PLAN.md`, then `PROGRESS.md`. Root rules in `../CLAUDE.md` apply. Depends on
`api/`. The API is the only data source.

## Stack

Next.js 16 (App Router) · TypeScript strict · Tailwind v4 · fonts via @fontsource:
**Shantell Sans** (display) + **Hanken Grotesk** (body) · icons **@phosphor-icons/react** ·
no chart library, no state library.

⚠️ **Next 16 differs from training data.** After the first `next dev`, a block appears in this
file pointing at `node_modules/next/dist/docs/`. Read it before writing app code. Check the
`next` version `create-next-app` writes into `package.json` — last time it pinned an
unpublished one and had to be set to 16.3.3 by hand.

## Rohit's locked design rules

- NO Inter, NO generic SaaS fonts. NO Lucide, NO Material icons.
- Depth via layered INSET shadows, not drop shadows. Squircle corners where supported.
- One accent colour only. Headings in Shantell Sans at 450–500 weight, never bold.
- Opinionated and finished beats neutral and safe. A finance desk can still have taste.

## The one architecture rule

Thin client. No logic, no engine imports, no OpenRouter, no Playwright. `lib/api.ts` is the
only place that fetches or opens an SSE stream. Types mirrored from `api/schemas.py` in one
file, `lib/api-types.ts`.

## The screen (one page — do not add pages)

```
┌───────────────────────────────────────────────────────────────────────┐
│  counters: human touches · auto-cleared · refused · evidence items    │
├─────────────────┬─────────────────────────────┬───────────────────────┤
│ QUEUE           │ EVIDENCE PACK               │ POLICIES              │
│ 5 exceptions,   │ facts land live, each with  │ rule cards:           │
│ class + status  │ source · time · screenshot  │ SHORT-SHIP-01 v1      │
│ badge; the one  │ thumb; proposed decision +  │ approved by Chris,    │
│ being worked    │ confidence; or the REFUSAL  │ Controller · Sep 6    │
│ is highlighted  │ with "where I looked"       │ learned from E1       │
│                 │ [Approve] [Reject] [Edit]   │ cited by: E2          │
├─────────────────┴─────────────────────────────┴───────────────────────┤
│  controls: WORK NEXT · RESET (back to the seed) · approver name field │
└───────────────────────────────────────────────────────────────────────┘
```

When E2 auto-clears, its row in the queue must visibly say **"cleared by SHORT-SHIP-01 ·
Chris, Controller"** — that sentence is the whole product, on screen.

## Clean code rules

TypeScript strict, no `any`. Small components, one per file. No leftover create-next-app
boilerplate. No unused deps.

## Definition of done

Renders correctly during a REAL run against the API (no mock mode) + typecheck clean +
PROGRESS.md updated.
