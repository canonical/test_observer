#!/usr/bin/env python3
"""
QA Agent Visual Comparison Tool
=================================
Stitches two screenshots (reference + candidate) into a labelled side-by-side
composite image, then optionally submits it to Gemini for a structured review.

Usage:
    python3 compare.py REFERENCE CANDIDATE [OUTPUT] [--page-name NAME] [--call-gemini]

Arguments:
    REFERENCE       Path to the reference screenshot (e.g. Flutter).
    CANDIDATE       Path to the candidate screenshot (e.g. Vue).
    OUTPUT          Output composite PNG (default: /tmp/compare-output.png).
    --page-name     Human-readable name for the page being compared (default: "page").
    --ref-label     Label for the left image (default: "Flutter (Reference)").
    --cand-label    Label for the right image (default: "Vue (Candidate)").
    --call-gemini   Send the composite to Gemini and print its review.
                    Requires GEMINI_API_KEY environment variable.
    --model         Gemini model to use (default: gemini-2.0-flash).

Examples:
    # Just produce the composite image:
    python3 compare.py /tmp/flutter-home.png /tmp/vue-home.png /tmp/compare-home.png

    # Produce composite AND get Gemini review:
    GEMINI_API_KEY=your_key python3 compare.py \\
        /tmp/flutter-home.png /tmp/vue-home.png /tmp/compare-home.png \\
        --page-name "Snaps Dashboard" --call-gemini
"""

import argparse
import os
import sys
from pathlib import Path


REVIEW_PROMPT_TEMPLATE = """\
You are a senior front-end QA engineer reviewing a UI migration from Flutter to {candidate_label}.

The attached image shows two screenshots of the **same page** ({page_name}) placed side-by-side:
- **LEFT**: {ref_label} — this is the reference implementation.
- **RIGHT**: {candidate_label} — this is the new implementation being reviewed.

Please provide a structured review covering:

1. **Layout & Structure**: Are the overall page layout, sections, and component hierarchy consistent? Note any missing sections, incorrect ordering, or alignment issues.

2. **Visual Elements**: Are all UI elements present? (buttons, inputs, tables, cards, navigation, icons, badges). Flag anything missing or misplaced.

3. **Typography & Colour**: Are fonts, sizes, weights, and colours consistent? Note any brand/theme deviations.

4. **Spacing & Density**: Is whitespace, padding, and information density comparable?

5. **Functional Concerns**: Are there any obvious interactive elements (dropdowns, links, tooltips) that appear broken or inaccessible in the candidate?

6. **Overall Assessment**: Rate similarity on a scale of 1–10 and summarise the most important issues to fix.

Be concise and actionable. Reference positions as (top-left, centre, etc.) where helpful.
"""


def build_composite(ref_path: Path, cand_path: Path, output_path: Path,
                    ref_label: str, cand_label: str) -> Path:
    from PIL import Image, ImageDraw, ImageFont

    ref_img = Image.open(ref_path).convert("RGB")
    cand_img = Image.open(cand_path).convert("RGB")

    # Normalise heights to the taller of the two
    max_h = max(ref_img.height, cand_img.height)
    if ref_img.height < max_h:
        padded = Image.new("RGB", (ref_img.width, max_h), (240, 240, 240))
        padded.paste(ref_img, (0, 0))
        ref_img = padded
    if cand_img.height < max_h:
        padded = Image.new("RGB", (cand_img.width, max_h), (240, 240, 240))
        padded.paste(cand_img, (0, 0))
        cand_img = padded

    # Header bar height for labels
    header_h = 40
    gap = 6  # gap between images

    total_w = ref_img.width + gap + cand_img.width
    total_h = header_h + max_h

    composite = Image.new("RGB", (total_w, total_h), (30, 30, 30))

    # Paste images below header
    composite.paste(ref_img, (0, header_h))
    composite.paste(cand_img, (ref_img.width + gap, header_h))

    draw = ImageDraw.Draw(composite)

    # Try to use a system font, fall back to default
    try:
        font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 18)
    except Exception:
        font = ImageFont.load_default()

    # Draw label backgrounds and text
    draw.rectangle([0, 0, ref_img.width, header_h], fill=(60, 60, 180))
    draw.rectangle([ref_img.width + gap, 0, total_w, header_h], fill=(40, 140, 60))

    # Centre the label text
    for text, x_start, x_end, colour in [
        (ref_label,  0,                       ref_img.width,  (255, 255, 255)),
        (cand_label, ref_img.width + gap,     total_w,        (255, 255, 255)),
    ]:
        bbox = draw.textbbox((0, 0), text, font=font)
        text_w = bbox[2] - bbox[0]
        text_h = bbox[3] - bbox[1]
        tx = x_start + (x_end - x_start - text_w) // 2
        ty = (header_h - text_h) // 2
        draw.text((tx, ty), text, fill=colour, font=font)

    output_path.parent.mkdir(parents=True, exist_ok=True)
    composite.save(str(output_path), format="PNG")
    return output_path


def call_gemini(composite_path: Path, prompt: str, model: str) -> str:
    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        print("ERROR: GEMINI_API_KEY environment variable is not set.", file=sys.stderr)
        sys.exit(1)

    try:
        import google.generativeai as genai
        from PIL import Image
    except ImportError:
        print("ERROR: google-generativeai or Pillow not installed.", file=sys.stderr)
        sys.exit(1)

    genai.configure(api_key=api_key)
    gemini = genai.GenerativeModel(model)

    img = Image.open(composite_path)
    print(f"Sending composite ({composite_path.stat().st_size // 1024}KB) to {model}...")
    response = gemini.generate_content([prompt, img])
    return response.text


def parse_args():
    parser = argparse.ArgumentParser(
        description="Compare two UI screenshots and optionally get a Gemini review."
    )
    parser.add_argument("reference", help="Path to the reference screenshot (Flutter).")
    parser.add_argument("candidate", help="Path to the candidate screenshot (Vue).")
    parser.add_argument(
        "output", nargs="?", default="/tmp/compare-output.png",
        help="Output composite PNG path (default: /tmp/compare-output.png).",
    )
    parser.add_argument("--page-name", default="page", help="Page name for the review prompt.")
    parser.add_argument("--ref-label", default="Flutter (Reference)", help="Label for the left image.")
    parser.add_argument("--cand-label", default="Vue (Candidate)", help="Label for the right image.")
    parser.add_argument("--call-gemini", action="store_true", help="Send to Gemini for review.")
    parser.add_argument("--model", default="gemini-2.0-flash", help="Gemini model (default: gemini-2.0-flash).")
    return parser.parse_args()


def main():
    args = parse_args()

    ref_path = Path(args.reference)
    cand_path = Path(args.candidate)
    output_path = Path(args.output)

    for p in (ref_path, cand_path):
        if not p.exists():
            print(f"ERROR: File not found: {p}", file=sys.stderr)
            sys.exit(1)

    print(f"Building composite: {ref_path.name} | {cand_path.name}")
    composite = build_composite(ref_path, cand_path, output_path, args.ref_label, args.cand_label)
    print(f"Composite saved:    {composite.resolve()}")

    prompt = REVIEW_PROMPT_TEMPLATE.format(
        page_name=args.page_name,
        ref_label=args.ref_label,
        candidate_label=args.cand_label,
    )

    if args.call_gemini:
        review = call_gemini(composite, prompt, args.model)
        print("\n" + "=" * 72)
        print("GEMINI REVIEW")
        print("=" * 72)
        print(review)
    else:
        print("\n" + "=" * 72)
        print("READY-TO-PASTE PROMPT (for manual Gemini/ChatGPT submission)")
        print("=" * 72)
        print(prompt)
        print(f"\nAttach: {composite.resolve()}")


if __name__ == "__main__":
    main()
