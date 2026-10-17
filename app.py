# ReceiptOwl — entry point
from __future__ import annotations

import gradio as gr

import config
from ui.components.blocks import header_left
from ui.tabs import hunt, nest, perch, settings, treasure
from ui.theme import get_launch_kwargs

NAV = [
    ("nest", "Nest", "home"),
    ("hunt", "Hunt", "radar"),
    ("perch", "Perch", "table"),
    ("treasure", "Treasure", "wallet"),
    ("settings", "Settings", "cog"),
]
NAV_ORDER = [n for n, _, _ in NAV]


def build_app() -> gr.Blocks:
    with gr.Blocks(title=config.APP_NAME, analytics_enabled=False) as demo:
        with gr.Column(elem_id="owl-app"):
            with gr.Row(elem_classes=["owl-header"]):
                gr.HTML(header_left())

            tab_buttons = {}
            with gr.Row(elem_classes=["owl-nav"]):
                for key, label, icon_name in NAV:
                    tab_buttons[key] = gr.Button(
                        label,
                        elem_classes=["owl-tab", f"owl-ic-{icon_name}"]
                        + (["primary"] if key == "nest" else []),
                    )

            job_id_state = gr.State("")
            ctx = {"job_id": job_id_state}

            nest_mod = nest.build(ctx)
            hunt_mod = hunt.build(ctx)
            perch_mod = perch.build(ctx)
            treasure_mod = treasure.build(ctx)
            settings_mod = settings.build(ctx)

            screens = {
                "nest": nest_mod["screen"],
                "hunt": hunt_mod["screen"],
                "perch": perch_mod["screen"],
                "treasure": treasure_mod["screen"],
                "settings": settings_mod["screen"],
            }
            route_outputs = [screens[n] for n in NAV_ORDER] + [
                tab_buttons[n] for n in NAV_ORDER
            ]

            def route(target):
                updates = []
                for name in NAV_ORDER:
                    updates.append(gr.update(visible=(name == target)))
                for name, _, icon_name in NAV:
                    classes = ["owl-tab", f"owl-ic-{icon_name}"] + (
                        ["primary"] if name == target else []
                    )
                    updates.append(gr.update(elem_classes=classes))
                return updates

            for key in NAV_ORDER:
                tab_buttons[key].click(lambda k=key: route(k), outputs=route_outputs)

            tab_buttons["perch"].click(
                perch_mod["load"],
                inputs=perch_mod["load_inputs"],
                outputs=perch_mod["load_outputs"],
            )
            tab_buttons["treasure"].click(
                treasure_mod["load"], outputs=treasure_mod["load_outputs"]
            )
            nest_mod["start_btn"].click(
                lambda: route("hunt"), outputs=route_outputs
            ).then(
                hunt_mod["run"],
                inputs=[
                    nest_mod["uploader"],
                    gr.State(config.DEFAULT_MODEL),
                    job_id_state,
                ],
                outputs=hunt_mod["outputs"],
            )

            hunt_mod["view_btn"].click(
                lambda: route("perch"), outputs=route_outputs
            ).then(
                perch_mod["load"],
                inputs=perch_mod["load_inputs"],
                outputs=perch_mod["load_outputs"],
            )
            hunt_mod["view_btn"].click(
                lambda: (None, gr.update(interactive=False)),
                outputs=[nest_mod["uploader"], nest_mod["start_btn"]],
            )

            settings_mod["reset_done_event"].then(
                perch_mod["load"],
                inputs=perch_mod["load_inputs"],
                outputs=perch_mod["load_outputs"],
            ).then(treasure_mod["load"], outputs=treasure_mod["load_outputs"])

            demo.load(
                perch_mod["load"],
                inputs=perch_mod["load_inputs"],
                outputs=perch_mod["load_outputs"],
            )
            demo.load(treasure_mod["load"], outputs=treasure_mod["load_outputs"])

    return demo


if __name__ == "__main__":
    from database.db import reports_dir

    app = build_app()
    kwargs = get_launch_kwargs()
    app.queue().launch(
        server_name="0.0.0.0",
        server_port=7860,
        allowed_paths=[str(reports_dir())],
        **kwargs,
    )
