"""Minimal Gradio web UI for ClearCut."""

from __future__ import annotations

import tempfile
from pathlib import Path

from clearcut.models import PipelineConfig
from clearcut.pipeline import Pipeline


def process_video(
    main_file: str,
    remove_silence: bool,
    generate_captions: bool,
    burn_captions: bool,
    template: str,
    format: str,
    audio_target: float,
    progress=...,  # type: ignore[valid-type]
) -> str:
    """Process a video through the ClearCut pipeline.

    Args:
        main_file: Path to uploaded video.
        remove_silence: Whether to remove silence.
        generate_captions: Whether to generate captions.
        burn_captions: Whether to burn captions into video.
        template: Template preset name.
        format: Output aspect ratio.
        audio_target: Target loudness in LUFS.
        progress: Gradio Progress indicator.

    Returns:
        Path to the output file as a string.
    """
    input_path = Path(main_file)
    if not input_path.exists():
        return f"Error: File not found: {input_path}"

    output_dir = Path(tempfile.mkdtemp(prefix="clearcut_web_"))
    output_path = output_dir / "output.mp4"

    try:
        config_kwargs: dict = {
            "main": input_path,
            "output": output_path,
            "remove_silence": remove_silence,
            "generate_captions": generate_captions,
            "burn_captions": burn_captions,
            "encoder_preset": "fast",
            "hardware": "auto",
        }

        if template and template != "none":
            config_kwargs["template"] = template

        if format and format != "16:9":
            config_kwargs["format"] = format

        if audio_target != -14.0:
            config_kwargs["audio_target_lufs"] = audio_target

        config = PipelineConfig(**config_kwargs)
        pipeline = Pipeline(config)
        try:
            pipeline.run()
        finally:
            pipeline.clean()

        if output_path.exists():
            return str(output_path.resolve())
        return "Error: Pipeline completed but output file not found."

    except Exception as e:
        return f"Error: {e}"


def launch() -> None:
    """Launch the Gradio web interface."""
    try:
        import gradio as gr
    except ImportError:
        print("Gradio not installed. Run: pip install gradio")
        return

    with gr.Blocks(title="ClearCut", theme=gr.themes.Soft()) as demo:
        gr.Markdown(
            """
            # 🎬 ClearCut
            ## Raw footage to publish-ready video. One click.

            Upload your video, tweak the settings, and download the result.
            """
        )

        with gr.Row():
            with gr.Column(scale=1):
                main_file = gr.File(
                    label="Upload Video",
                    file_types=[".mp4", ".mov", ".mkv", ".avi"],
                )

                with gr.Group():
                    remove_silence = gr.Checkbox(label="Remove Silence", value=True)
                    generate_captions = gr.Checkbox(label="Generate Captions", value=False)
                    burn_captions = gr.Checkbox(label="Burn Captions", value=False)

                with gr.Group():
                    template = gr.Dropdown(
                        label="Template",
                        choices=["none", "clean", "tiktok", "cinematic", "bold"],
                        value="none",
                    )
                    format = gr.Dropdown(
                        label="Output Format",
                        choices=["16:9", "9:16", "1:1"],
                        value="16:9",
                    )
                    audio_target = gr.Slider(
                        label="Audio Target (LUFS)",
                        minimum=-23.0,
                        maximum=-8.0,
                        value=-14.0,
                        step=0.5,
                    )

                process_btn = gr.Button("Process Video", variant="primary")

            with gr.Column(scale=1):
                output = gr.File(label="Download Result")
                status = gr.Textbox(label="Status", interactive=False)

        process_btn.click(
            fn=process_video,
            inputs=[
                main_file,
                remove_silence,
                generate_captions,
                burn_captions,
                template,
                format,
                audio_target,
            ],
            outputs=[output, status],
        )

        gr.Markdown(
            """
            ---
            **Note:** Processing runs locally on this machine.
            GPU acceleration will be used if available.
            """
        )

    demo.launch()


if __name__ == "__main__":
    launch()
