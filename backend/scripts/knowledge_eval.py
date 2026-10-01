"""Read the grounded replies with your own eyes: prints each realistic buyer question and the answer for a sample home, an agent listing (with `about`)
and an area, once with the real default LLM (when a key is configured) and once with the deterministic fallback only. Nothing is written or posted.
  docker compose exec -T -e PYTHONPATH=. backend python scripts/knowledge_eval.py [--channel facebook|instagram|chat] [--only S|L|A] [--no-llm]
What to look for: the answer uses the fact that matches the question; a detail we do not have is said plainly (never 'we will forward');
nothing appears that is not in the facts printed under each heading.
"""
import argparse
import asyncio

from app.modules.ai_listing.llm import default_llm
from app.modules.knowledge import Ref, answer, facts_for
from app.modules.knowledge.grounding import listing_grounding

LISTING = {"_id": "L1", "agent_id": "A1", "title": "2 BHK in Kharadi", "transaction": "sale", "property_type": "apartment", "price_inr": 8_500_000, "city": "Pune",
           "locality": "Kharadi", "bhk": 2, "carpet_sqft": 1100, "floor": 7, "total_floors": 20, "furnishing": "semi", "possession": "ready", "rera_no": "P52100012345",
           "amenities": ["Gym", "Lift"], "status": "live",
           "about": {"project_name": "Green Park", "amenities": ["Clubhouse"], "water": "Municipal supply with a storage tank", "power_backup": "Lifts and common areas",
                     "parking": "One covered slot", "nearby": [{"type": "school", "name": "City School", "minutes": 8}, {"type": "office", "name": "EON IT Park", "minutes": 15}],
                     "faq": [{"q": "Is the price negotiable?", "a": "The final price is discussed with the agent."}]}}

QUESTIONS = [
    "What is the carpet area?", "carpet area kitna hai", "is it ready to move?", "possession kab hai", "which school is nearby?", "nearby school?", "parking milegi?",
    "is there parking?", "maintenance kitna", "what is the maintenance?", "how far from the office park?", "can I visit on Sunday", "price negotiable?", "is it available?",
    "what is the price?", "किंमत किती आहे?", "कार्पेट एरिया कितना है?", "metro kab chalu hogi?", "is there a swimming pool?", "which floor?", "RERA number?",
    "home loan milega kya?", "water supply kaisa hai", "kuthe aahe ha flat?", "is it a good investment?", "is the area safe for kids?",
]


async def main(a) -> None:
    llm = None if a.no_llm else default_llm()
    print("LLM:", "default LLM (real network calls)" if llm else "none (deterministic fallback only)")
    groundings = {"S": await facts_for(Ref.sample("kharadi-2bhk-ready")), "L": listing_grounding(LISTING), "A": await facts_for(Ref.area("Wagholi"))}
    for key, g in groundings.items():
        if a.only and key != a.only:
            continue
        print(f"\n{'=' * 100}\n[{key}] {g.subject}  (kind={g.kind}, sample={g.sample})")
        for f in g.facts:
            print("   fact:", f)
        for q in QUESTIONS:
            for label, use in (("rules", None), ("llm  ", llm)) if llm else (("rules", None),):
                r = await answer(q, g, a.channel, use)
                text = r.text.replace("{interest_url}", "https://site.example/i/abc123")
                flag = "ok     " if r.confident else "MISSING"
                print(f"\nQ: {q}\n  [{label}|{flag}|{r.language}|{r.via}] {text}" + (f"\n  missing: {r.missing}" if r.missing else "") + (f"\n  basis: {r.basis}" if r.basis else ""))


if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("--channel", default="facebook", choices=["facebook", "instagram", "chat"])
    p.add_argument("--only", choices=["S", "L", "A"])
    p.add_argument("--no-llm", action="store_true")
    asyncio.run(main(p.parse_args()))
