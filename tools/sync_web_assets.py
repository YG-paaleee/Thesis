#!/usr/bin/env python3
"""Generate ESP32 PROGMEM headers from the canonical standalone web pages."""

from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent
ASSETS = (
    (ROOT / "index.html", ROOT / "include" / "captive_portal.h",
     "CAPTIVE_PORTAL_H", "CAPTIVE_PORTAL_HTML", "CAPTIVEPORTAL"),
    (ROOT / "admin.html", ROOT / "include" / "admin_dashboard.h",
     "ADMIN_DASHBOARD_H", "ADMIN_DASHBOARD_HTML", "ADMINDASHBOARD"),
)


def render_header(source: Path, guard: str, symbol: str, delimiter: str) -> str:
    html = source.read_text(encoding="utf-8").replace("\r\n", "\n").rstrip("\n")
    closing_token = f"){delimiter}\""
    if closing_token in html:
        raise ValueError(f"Raw string delimiter {delimiter!r} conflicts with {source.name}")
    return (
        f"// Generated from {source.name} by tools/sync_web_assets.py. Do not edit directly.\n"
        f"#ifndef {guard}\n#define {guard}\n\n"
        "#include <pgmspace.h>\n\n"
        f"const char {symbol}[] PROGMEM = R\"{delimiter}(\n"
        f"{html}\n"
        f"){delimiter}\";\n\n"
        "#endif\n"
    )


def main() -> None:
    for source, destination, guard, symbol, delimiter in ASSETS:
        destination.write_text(
            render_header(source, guard, symbol, delimiter), encoding="utf-8", newline="\n"
        )
        print(f"Generated {destination.relative_to(ROOT)} from {source.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
