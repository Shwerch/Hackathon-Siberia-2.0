import asyncio
import json
import xml.etree.ElementTree as ET
from pathlib import Path
import httpx

API_URL = "http://localhost:8000"
BENCHMARKS_PATH = Path("../../data/04_benchmarks.json")


async def run_all() -> None:
    data = json.loads(BENCHMARKS_PATH.read_text(encoding="utf-8"))
    items = data["items"]

    async with httpx.AsyncClient(base_url=API_URL, timeout=30.0) as client:
        for item in items:
            sid = (await client.post("/api/sessions")).json()["session_id"]
            res = (await client.post(f"/api/sessions/{sid}/turn", json={"message": item["query"]})).json()

            # Если сценарий с доуточнением (N05)
            if "follow_up" in item:
                res = (
                    await client.post(
                        f"/api/sessions/{sid}/turn",
                        json={"message": item["follow_up"]["user_answer"]},
                    )
                ).json()

            exp = item.get("expected") or item.get("follow_up", {}).get("expected")
            rules_ok = True
            if exp:
                rules_ok = res["rules_count"] == exp["rules_count"]

            xml_ok = True
            if res.get("drawio_xml"):
                root = ET.fromstring(res["drawio_xml"])
                xml_ok = root.tag == "mxfile" and root.find(".//mxGraphModel") is not None

            mean_t = res["timing"]["mean_turn_seconds"]
            cost = res["usage"]["evaluation_cost_usd"]
            print(
                f"[{item['id']}] status={res['status']} | rules={res['rules_count']} "
                f"(ok={rules_ok}) | xml_ok={xml_ok} | mean_t={mean_t}s | cost=${cost:.6f}"
            )


if __name__ == "__main__":
    asyncio.run(run_all())
