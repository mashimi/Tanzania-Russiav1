"""End-to-end test: verifies real Exa data flows through scanner."""
import sys
sys.path.insert(0, 'tz-radar-saas/backend')

import asyncio
from scanner import (
    run_exa_search, _parse_exa_output,
    analyze_russia_posts, analyze_china_posts,
    build_executive_summary, build_pdf_report_text,
    _get_mcporter_path
)


async def main():
    lines = []

    path = _get_mcporter_path()
    lines.append(f"mcporter path: {path}")

    # Test Russian search - use keyword that matches analysis patterns
    out_ru = await run_exa_search("прямые рейсы Танзания", 2)
    ru_parsed = _parse_exa_output(out_ru) if out_ru else []
    lines.append(f"Russian articles: {len(ru_parsed)}")
    for r in ru_parsed:
        lines.append(f"  [{r.get('published','')}] {r.get('title','')}")
        lines.append(f"  snippet: {r.get('text','')[:150]}")

    # Test Chinese search
    out_cn = await run_exa_search("坦桑尼亚 投资 机遇", 2)
    cn_parsed = _parse_exa_output(out_cn) if out_cn else []
    lines.append(f"Chinese articles: {len(cn_parsed)}")
    for c in cn_parsed:
        lines.append(f"  [{c.get('published','')}] {c.get('title','')}")
        lines.append(f"  snippet: {c.get('text','')[:150]}")

    # Analyze
    ri, rc = analyze_russia_posts(ru_parsed)
    ci, cc = analyze_china_posts(cn_parsed)
    crisis = rc + cc

    summary = build_executive_summary(ru_parsed, cn_parsed, ri, ci, crisis)
    lines.append(f"Russia insights: {len(ri)}")
    lines.append(f"China insights: {len(ci)}")
    lines.append(f"Crisis alerts: {len(crisis)}")
    lines.append("")
    lines.append("EXECUTIVE SUMMARY:")
    lines.append(summary)
    lines.append("")
    lines.append("PDF REPORT:")
    lines.append(build_pdf_report_text(ri, ci, crisis, summary))

    result = "\n".join(lines)
    with open("e2e_scan_proof.txt", "w", encoding="utf-8") as f:
        f.write(result)
    print(f"OK - wrote {len(result)} bytes")


if __name__ == "__main__":
    asyncio.run(main())