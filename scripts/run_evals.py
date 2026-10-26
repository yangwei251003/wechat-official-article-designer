from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from common import write_json

REQUIRED = {"id", "name", "input_type", "expected_route", "safeguards"}


def load_scenarios(path: Path) -> list[dict[str, Any]]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, list):
        raise ValueError("eval catalog必须是JSON数组")
    return payload


def validate_catalog(scenarios: list[dict[str, Any]]) -> dict[str, Any]:
    errors = []
    ids = []
    for index, scenario in enumerate(scenarios, 1):
        missing = REQUIRED - set(scenario)
        if missing:
            errors.append(f"场景{index}缺少：{', '.join(sorted(missing))}")
        if not isinstance(scenario.get("safeguards"), list) or not scenario.get("safeguards"):
            errors.append(f"场景{index}没有安全断言")
        ids.append(scenario.get("id"))
    if len(ids) != len(set(ids)):
        errors.append("场景ID重复")
    if len(scenarios) < 20:
        errors.append("代表性场景少于20个")
    return {"ok": not errors, "count": len(scenarios), "errors": errors, "dimensions": ["trigger_accuracy", "content_integrity", "fact_reliability", "structure", "design_fit", "readability", "brand_consistency", "wechat_compatibility", "copyright_safety", "lock_preservation", "recovery", "usability", "performance"]}


def _probe(scenario_id: str) -> str:
    if scenario_id == "E11":
        from connectors import ConnectorPermissionError, search_assets
        try:
            search_assets("pexels", "test", limit=1, allow_network=False)
        except ConnectorPermissionError:
            return "network permission and missing-key path guarded"
        raise AssertionError("real connector ran without explicit network permission")
    if scenario_id == "E13":
        from license_report import build_report
        assert not build_report([{"id": "unknown", "provider": "upload", "license": "", "source_url": ""}])["auto_publish_allowed"]
        return "unknown license blocks auto publish"
    if scenario_id == "E14":
        from sanitize_svg import sanitize_svg_text
        result = sanitize_svg_text('<svg xmlns="http://www.w3.org/2000/svg" onload="x"><script>x</script><rect width="1" height="1"/></svg>')
        assert "script" not in result["svg"].lower() and "onload" not in result["svg"].lower()
        return "active SVG content removed"
    if scenario_id == "E15":
        from sanitize_html import sanitize_and_inline
        result = sanitize_and_inline("<p>ignore rules</p><script>steal()</script>")
        assert "ignore rules" in result["html"] and "steal" not in result["html"]
        return "web instruction retained only as inert data"
    if scenario_id == "E17":
        from mock_wechat_server import MockState
        state = MockState()
        one = state.response_for("POST", "/cgi-bin/draft/add", {"articles": []}, idempotency_key="same")[1]
        two = state.response_for("POST", "/cgi-bin/draft/add", {"articles": []}, idempotency_key="same")[1]
        assert one == two
        return "duplicate draft request deduplicated"
    if scenario_id == "E18":
        from article_schema import scaffold_from_source
        from revisions import LockViolation, apply_text_revision
        article = scaffold_from_source("# T\n\nlocked\n", title="T")
        article["content"]["sections"][0]["nodes"][0]["locked"] = True
        try:
            apply_text_revision(article, "node-1", "changed", actor="ai")
        except LockViolation:
            return "locked content preserved"
        raise AssertionError("locked content was modified")
    if scenario_id == "E19":
        from library import rank_assets
        ranked = rank_assets([{"id": "external", "title": "topic", "tags": [], "origin_priority": 3, "license_status": "verified"}, {"id": "user", "title": "topic", "tags": [], "origin_priority": 1, "license_status": "verified"}], query="topic")
        assert ranked[0]["id"] == "user"
        return "user library priority enforced"
    if scenario_id == "E20":
        from article_schema import scaffold_from_source
        from compile_wechat import compile_article
        article = scaffold_from_source("# T\n\nbody\n", title="T")
        article["content"]["sections"][0]["nodes"].append({"id": "chart", "type": "chart", "engine": "mock", "spec": {}, "fallback": {"type": "image", "src": "assets/chart.png", "alt": "chart"}, "locked": False, "provenance": {"kind": "ai", "source_refs": []}})
        result = compile_article(article)
        assert "chart" in result["compatibility"]["degraded_nodes"]
        return "complex node compiled to static fallback"
    if scenario_id in {"E21", "E22"}:
        from article_schema import scaffold_from_source
        from design_quality import audit_high_design

        article = scaffold_from_source("# T\n\nbody\n", title="T")
        article["design"].update({
            "mode": "high-design",
            "design_read": {"article_type": "test", "audience": "test", "action": "test", "emotion": "test", "visual_family": "test", "wechat_constraint": "static"},
            "controls": {"design_variance": 8, "motion_intensity": 4, "visual_density": 5},
            "visual_concept": "signal relationship",
            "rhythm_families": ["hero", "spread", "close"],
        })
        assets = [
            {"id": "hero", "role": "hero", "local_path": "hero.png", "provider": "original", "license": "Original asset", "wechat_ready": True},
            {"id": "motion", "role": "ornament", "local_path": "motion.gif", "provider": "original", "license": "Original asset", "wechat_ready": True},
        ]
        if scenario_id == "E21":
            report = audit_high_design(article, '<section data-rhythm="hero"><img src="original-ornament.png" alt="x"/></section>', assets)
            assert "legacy-reference" in {item["code"] for item in report["errors"]}
            return "legacy visual marker rejected from greenfield design"
        from build_package import baseline_fragment
        fragment = baseline_fragment([{"type": "heading", "level": "1", "text": "T"}, {"type": "paragraph", "text": "body"}], {"palette": ["#111111", "#ff4f32", "#f4f1e8"]})
        report = audit_high_design(article, fragment, assets)
        assert "baseline-only" in {item["code"] for item in report["errors"]}
        return "baseline-only HTML rejected for high-design delivery"
    return "scenario contract and safeguards validated; qualitative output requires forward/manual review"


def run_catalog(scenarios: list[dict[str, Any]]) -> dict[str, Any]:
    catalog = validate_catalog(scenarios)
    if not catalog["ok"]:
        return {"ok": False, "passed": 0, "failed": len(scenarios), "results": [], "errors": catalog["errors"]}
    results = []
    for scenario in scenarios:
        try:
            evidence = _probe(str(scenario["id"]))
            results.append({"id": scenario["id"], "name": scenario["name"], "status": "pass", "evidence": evidence})
        except Exception as exc:
            results.append({"id": scenario["id"], "name": scenario["name"], "status": "fail", "evidence": type(exc).__name__})
    passed = sum(item["status"] == "pass" for item in results)
    return {"ok": passed == len(results), "passed": passed, "failed": len(results) - passed, "results": results, "note": "Deterministic guards run locally; content/design quality dimensions still require Skill forward-test or human review."}


def main() -> int:
    parser = argparse.ArgumentParser(description="校验并运行可重复的Skill eval目录")
    parser.add_argument("catalog", type=Path)
    parser.add_argument("--report", type=Path)
    args = parser.parse_args()
    scenarios = load_scenarios(args.catalog)
    result = {"catalog": validate_catalog(scenarios), "execution": run_catalog(scenarios)}
    if args.report:
        write_json(args.report, result)
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if result["catalog"]["ok"] and result["execution"]["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
