# AutoSOC Command Center — Monetization Strategy

> **Disclaimer:** All prices, limits, and packaging in this document are **illustrative**. They are intended to guide product and go-to-market planning, not to represent committed pricing. Final numbers should be validated against cost-to-serve (especially AI inference), competitive benchmarks, and customer willingness-to-pay research.

AutoSOC Command Center is a **local-first, defensive, AI-powered SOC automation platform**. It automates alert triage, investigation, IOC enrichment, case correlation, incident reporting, and safe response guidance. It supports multiple AI providers (OpenAI, Azure OpenAI, Anthropic, Gemini, Mistral, Cohere, Groq, OpenRouter, Ollama, LM Studio, vLLM, and a deterministic Mock provider) with **per-customer AI policy** and **local-only / private deployment** options, and ships as a Docker Compose stack.

---

## Market Positioning

AutoSOC is positioned as a **defensive security operations force-multiplier** — it does not perform offensive actions; it triages, investigates, correlates, and *recommends* safe response steps for human analysts. This framing matters for both buyer trust and provider AI-use policies.

Three primary buyer segments:

- **SMBs and lean IT/security teams.** Organizations that receive more alerts than they can investigate, often without a dedicated SOC. AutoSOC reduces alert fatigue and gives non-specialists structured, explainable triage. Local-first deployment removes the "our data goes to a vendor cloud" objection.
- **Internal SOC / SecOps teams (mid-market & enterprise).** Teams drowning in alert volume that want to cut mean-time-to-triage (MTTT) and standardize investigation quality across analysts of varying seniority. AutoSOC acts as a tier-1 accelerator and a consistent investigation co-pilot.
- **MSSPs / MDR providers (the highest-value segment).** Managed security service providers running detection and response for *many* client organizations. AutoSOC's multi-tenant isolation, per-customer AI policy, white-label reporting, and consolidated cross-tenant dashboards let an MSSP scale analyst capacity, differentiate their offering, and sell **AutoSOC-powered managed detection & response (MDR)** as a productized service.

**Core value proposition:** more alerts investigated per analyst-hour, consistent and explainable triage, and a privacy posture (local-first + local-only mode) that cloud-only competitors cannot match for regulated and privacy-sensitive buyers.

---

## SaaS Pricing Tiers

Four tiers span the journey from evaluation to multi-tenant managed service. Volumes are stated per month unless noted.

| | **Free / Community** | **Starter** | **Professional** | **Enterprise / MSSP** |
|---|---|---|---|---|
| **Target user** | Evaluators, homelab, small internal teams | Single SMB / small internal SOC | Mid-market SOC team | MSSP / MDR provider, large enterprise |
| **Price (USD/mo)** | $0 | $299 | $1,499 | Custom (from ~$5,000) |
| **Alerts ingested / triaged** | Up to 1,000 | Up to 15,000 | Up to 100,000 | Unlimited / negotiated |
| **AI investigations** | Up to 250 | Up to 3,000 | Up to 25,000 | Negotiated / metered |
| **Customers / tenants** | 1 | 1 | Up to 5 | Unlimited (multi-tenant) |
| **Analyst seats** | 2 | 5 | 25 | Custom (per-seat or pooled) |
| **AI providers** | Mock + bring-your-own **local LLM** (Ollama / LM Studio / vLLM) | Local LLM + 1 hosted provider (BYO API key) | All hosted + local providers, per-policy | All providers + hosted-inference option + per-tenant AI policy |
| **local_only_mode** | Yes | Yes | Yes | Yes (+ air-gapped / on-prem license) |
| **Case correlation** | Basic | Standard | Advanced cross-case | Advanced + cross-tenant |
| **Reporting** | Markdown export | PDF incident reports | Scheduled + branded reports | **White-label** reports |
| **Connectors / integrations** | Community | Core SIEM/EDR | Extended catalog | Full catalog + custom |
| **Dashboards** | Single-tenant | Single-tenant | Single-tenant | **Consolidated cross-tenant** |
| **SSO / RBAC** | — | Basic RBAC | SSO (SAML/OIDC) + RBAC | SSO + granular RBAC + tenant scoping |
| **Support** | Community (docs, forum) | Email (next business day) | Priority email + chat | Dedicated CSM + SLA |
| **Deployment** | Self-host (Docker Compose) | Self-host or managed | Self-host or managed | Self-host, managed, or **on-prem/air-gapped license** |

### Free / Community
For evaluators, homelabs, and very small internal teams who want to prove value with zero spend and zero data egress. Runs entirely on Docker Compose with the deterministic **Mock provider** for repeatable demos or a **bring-your-own local LLM** (Ollama, LM Studio, vLLM) so no data ever leaves the environment. Capped volumes and a single tenant make it a true entry point and a low-friction lead source — not a production MSSP tool.

### Starter — $299/mo
For a single SMB or small internal SOC moving from "trying it" to "running it." Adds PDF incident reporting, core SIEM/EDR connectors, basic RBAC, and one **hosted AI provider** via bring-your-own API key, while still supporting full local-only operation. Sized for teams that need real triage throughput without enterprise overhead.

### Professional — $1,499/mo
For mid-market SOC teams standardizing investigation quality across many analysts. Unlocks **all AI providers** under per-customer AI policy, advanced cross-case correlation, scheduled and branded reporting, the extended connector catalog, SSO, and priority support. Supports up to 5 tenants — a natural fit for a company with subsidiaries or a small managed-service experiment.

### Enterprise / MSSP — Custom (from ~$5,000/mo)
For MSSPs, MDR providers, and large enterprises. Adds **unlimited multi-tenant** operation, per-tenant AI policy, **white-label reports**, **consolidated cross-tenant dashboards**, optional **hosted inference**, air-gapped / on-prem licensing, a dedicated customer success manager, and contractual SLAs. Priced via flexible models (per-seat, per-tenant, per-alert-volume, or flat on-prem license) — see [Billing Models](#pricing-ideas--billing-models-summary).

---

## MSSP Multi-Tenant Angle

The MSSP segment is where AutoSOC's architecture compounds into a defensible business. A single MSSP analyst pool can serve dozens of client organizations from one deployment while keeping each client cleanly separated.

- **Per-customer isolation.** Each client is a first-class tenant (`Customer`) with isolated alerts, cases, and data. The tenancy layer scopes every query so analysts and reports never bleed across clients.
- **Per-customer AI policy.** Each tenant carries its own `CustomerAIPolicy` — a `preferred_provider` and a `local_only_mode` flag — so one client can run fully local (privacy-sensitive or regulated) while another uses a hosted model for richer enrichment. The MSSP honors each client's contractual data-handling requirements without running separate deployments.
- **White-label reports.** Incident and investigation reports can carry the MSSP's branding (or co-branding), so the managed service feels like the MSSP's own product, not a third-party tool.
- **Consolidated cross-tenant dashboards.** SOC managers see aggregated posture, alert load, and SLA status across all clients in one view, then drill into any single tenant. This is the operational backbone for running MDR at scale.
- **Flexible billing for resale.** MSSPs can be billed (and can in turn bill *their* clients) **per-seat**, **per-tenant**, or **per-alert-volume**, letting them match AutoSOC's cost to their own pricing model and protect margin.

**The business case for the MSSP:** AutoSOC lets an MSSP productize **AutoSOC-powered managed detection & response**. Analyst capacity scales with automation rather than headcount, triage quality is consistent across clients, onboarding a new client is a new tenant (not a new stack), and white-label reporting plus cross-tenant dashboards turn the platform into the MSSP's delivery engine. The MSSP captures the recurring MDR revenue; AutoSOC captures a per-tenant / per-seat / volume share of it.

---

## Local-First / Private Deployment Value Proposition

For privacy-sensitive and regulated buyers, AutoSOC's biggest differentiator is that **sensitive security data never has to leave the customer environment.**

- **Data stays local.** With a local LLM (Ollama, LM Studio, or vLLM) and `local_only_mode` enabled, alerts, logs, and investigation context are processed in-environment. No alert content, IOC, or case detail is sent to an external AI provider.
- **Compliance posture.** Keeping data in-region and in-environment directly supports **GDPR** (data residency / minimized processing), **HIPAA** (PHI handling for healthcare SOCs), and the requirements of regulated industries such as **finance, government, defense, and critical infrastructure**. Per-customer `local_only_mode` lets a single MSSP deployment satisfy strict clients and flexible clients simultaneously.
- **Air-gapped / on-prem licensing.** For environments with no outbound internet (classified, OT/ICS, certain government and defense networks), AutoSOC offers a **self-hosted / on-prem enterprise license**: a flat annual fee for a fully air-gapped deployment with local inference, with no usage data or telemetry leaving the boundary.
- **Why this beats cloud-only competitors.** Cloud-only SOC-automation tools require routing security telemetry through the vendor's infrastructure — a non-starter for many regulated and security-conscious buyers, and a recurring procurement and audit obstacle. AutoSOC inverts the default: **private by design, with hosted AI as an opt-in convenience**, not a mandatory dependency. This removes the single biggest objection in privacy-sensitive deals and shortens security review cycles.

The **self-hosted / on-prem enterprise license** is also a distinct revenue line: a flat, high-value annual license (optionally with a support/maintenance contract) for buyers who will not operate in a SaaS model at all.

---

## Add-Ons / Expansion Revenue

Add-ons drive net revenue retention by letting accounts grow beyond their base tier without re-tiering.

- **Hosted inference credits.** For customers who don't want to manage their own AI keys or local models, sell prepaid inference credits with a margin over upstream token cost (see metering below). Natural upsell for Starter/Professional.
- **Premium threat-intel enrichment feeds.** Paid IOC enrichment from premium commercial feeds (reputation, malware family, actor attribution) layered onto investigations — billed per feed or as an enrichment bundle.
- **Additional connectors / integrations.** Connectors beyond the tier's included catalog (additional SIEMs, EDR/XDR, ticketing, SOAR, identity providers), sold individually or as integration packs.
- **Managed onboarding.** Paid onboarding and tuning engagements — connector setup, detection mapping, AI-policy configuration, and analyst enablement. High-touch, high-margin, and a strong fit for Enterprise/MSSP.
- **Custom detection content packs.** Curated, maintained detection and correlation content (industry-specific, threat-specific, or compliance-aligned), sold as a subscription with ongoing updates.
- **Priority support / SLAs.** Upgraded support tiers and contractual response/uptime SLAs, including 24x7 coverage and a named technical contact — particularly relevant for MSSPs whose own clients expect SLAs.

---

## Pricing Ideas / Billing Models Summary

AutoSOC supports several billing models so packaging can match each segment's economics:

- **Per-seat.** Bill per analyst seat. Predictable for internal SOC teams; aligns cost with team size. Best for Starter/Professional.
- **Per-tenant.** Bill per managed client organization. The natural model for MSSPs, where each client is a tenant and the MSSP can mark up per-client.
- **Per-alert-volume.** Bill on alerts ingested/triaged per month, with tiered brackets. Aligns cost with actual workload and scales with the value delivered; good for high-throughput environments and as an MSSP wholesale model.
- **Flat on-prem / air-gapped license.** A fixed annual license for self-hosted or air-gapped deployments, decoupled from usage. Suits regulated, classified, and procurement-driven buyers.
- **Usage-based AI metering.** For hosted inference, meter actual token / cost consumption and bill as **upstream cost passthrough plus margin**. This keeps AI a profit center rather than a cost risk and isolates the business from provider price changes. Customers using their own keys or local models avoid this entirely (and pay a lower base).
- **Annual discounts.** Offer roughly **15–20% off** for annual prepayment versus monthly to improve cash flow and retention. Multi-year and multi-tenant volume commitments can stack additional discounts at the Enterprise/MSSP level.

These models are not mutually exclusive: a typical Enterprise/MSSP contract combines a **per-tenant or per-seat base**, **per-alert-volume brackets** for overage, and **metered hosted-inference passthrough** for any tenants not running local-only.

---

## Go-to-Market / ICP Note

**Primary ICP:** MSSPs and MDR providers (10–500+ managed clients) seeking to scale analyst capacity and differentiate with a private, white-labelable, AI-driven SOC platform. **Secondary ICP:** mid-market internal SOC teams (alert volume outpacing headcount) and privacy-/compliance-driven organizations in regulated industries.

**Motion:** product-led entry via the Free/Community tier (self-hosted, zero data egress) to seed evaluation and homelab adoption, converting to Starter/Professional as volume and team needs grow; **sales-led** for Enterprise/MSSP and on-prem/air-gapped licenses, led by the multi-tenant, white-label, and compliance value props. Lead with the **local-first privacy story** in regulated verticals — it is the fastest path through security review and the clearest differentiator against cloud-only competitors.

---

*Reminder: the figures in this document are illustrative and provided for planning purposes only.*
