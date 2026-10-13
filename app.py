"""ReceiptOwl · Gradio entry point (UI only; no backend yet).

Run:  python app.py
"""

from __future__ import annotations

import gradio as gr

from config import APP_NAME
from ui.components.blocks import header_left, header_status
from ui.tabs import hunt, nest, perch, settings, treasure
from ui.theme import get_launch_kwargs

NAV = [
    ("nest", "Nest", "home"),
    ("hunt", "Hunt", "radar"),
    ("perch", "Perch", "table"),
    ("treasure", "Treasure", "wallet"),
    ("settings", "Settings", "cog"),
]


def build_app() -> gr.Blocks:
    with gr.Blocks(title=APP_NAME) as demo:
        with gr.Column(elem_id="owl-app"):
            # ---- Titlebar ----
            with gr.Row(elem_classes="owl-header"):
                gr.HTML(header_left())
                with gr.Row(elem_classes="owl-header-right"):
                    gr.HTML(header_status())
                    quick = gr.Button(
                        "Settings", elem_classes=["owl-quick", "owl-ic-cog"]
                    )

            with gr.Row(elem_classes="owl-nav"):
                nav_buttons = {
                    key: gr.Button(
                        label,
                        variant="primary" if key == "nest" else "secondary",
                        elem_classes=["owl-tab", f"owl-ic-{icon_name}"],
                    )
                    for key, label, icon_name in NAV
                }

            screens = {
                "nest": nest.build(),
                "hunt": hunt.build(),
                "perch": perch.build(),
                "treasure": treasure.build(),
                "settings": settings.build(),
            }

        screen_cols = [screens[k]["screen"] for k, _, _ in NAV]
        nav_btns = [nav_buttons[k] for k, _, _ in NAV]

        def go(target: str):
            return [gr.update(visible=k == target) for k, _, _ in NAV] + [
                gr.update(variant="primary" if k == target else "secondary")
                for k, _, _ in NAV
            ]

        def route(component, target: str):
            component.click(
                lambda: go(target),
                outputs=screen_cols + nav_btns,
                show_progress="hidden",
            )

        for key, btn in nav_buttons.items():
            route(btn, key)
        route(quick, "settings")
        route(screens["nest"]["start"], "hunt")
        route(screens["hunt"]["cancel"], "nest")
        route(screens["perch"]["to_treasure"], "treasure")

    return demo


demo = build_app()

if __name__ == "__main__":
    demo.launch(**get_launch_kwargs())
