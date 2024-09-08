import spaces
import gradio as gr
import torch
from PIL import Image
from diffusers import DiffusionPipeline
import random
import uuid
from typing import Tuple
import numpy as np

DESCRIPTIONz = """## FLUX REALISM 🔥"""

def save_image(img):
    unique_name = str(uuid.uuid4()) + ".png"
    img.save(unique_name)
    return unique_name

def randomize_seed_fn(seed: int, randomize_seed: bool) -> int:
    if randomize_seed:
        seed = random.randint(0, MAX_SEED)
    return seed

MAX_SEED = np.iinfo(np.int32).max

if not torch.cuda.is_available():
    DESCRIPTIONz += "\n<p>⚠️Running on CPU, This may not work on CPU.</p>"

base_model = "black-forest-labs/FLUX.1-dev"
pipe = DiffusionPipeline.from_pretrained(base_model, torch_dtype=torch.bfloat16)

lora_repo = "prithivMLmods/Canopus-LoRA-Flux-FaceRealism"
trigger_word = "Realism"  # Leave trigger_word blank if not used.
pipe.load_lora_weights(lora_repo)

pipe.to("cuda")

style_list = [
    {
        "name": "3840 x 2160",
        "prompt": "hyper-realistic 8K image of {prompt}. ultra-detailed, lifelike, high-resolution, sharp, vibrant colors, photorealistic",
    },
    {
        "name": "2560 x 1440",
        "prompt": "hyper-realistic 4K image of {prompt}. ultra-detailed, lifelike, high-resolution, sharp, vibrant colors, photorealistic",
    },
    {
        "name": "HD+",
        "prompt": "hyper-realistic 2K image of {prompt}. ultra-detailed, lifelike, high-resolution, sharp, vibrant colors, photorealistic",
    },
    {
        "name": "Style Zero",
        "prompt": "{prompt}",
    },
]

styles = {k["name"]: k["prompt"] for k in style_list}

DEFAULT_STYLE_NAME = "3840 x 2160"
STYLE_NAMES = list(styles.keys())

def apply_style(style_name: str, positive: str) -> str:
    return styles.get(style_name, styles[DEFAULT_STYLE_NAME]).replace("{prompt}", positive)

@spaces.GPU(duration=60, enable_queue=True)
def generate(
    prompt: str,
    seed: int = 0,
    width: int = 1024,
    height: int = 1024,
    guidance_scale: float = 3,
    randomize_seed: bool = False,
    style_name: str = DEFAULT_STYLE_NAME,
    progress=gr.Progress(track_tqdm=True),
):
    seed = int(randomize_seed_fn(seed, randomize_seed))

    positive_prompt = apply_style(style_name, prompt)
    
    if trigger_word:
        positive_prompt = f"{trigger_word} {positive_prompt}"

    images = pipe(
        prompt=positive_prompt,
        width=width,
        height=height,
        guidance_scale=guidance_scale,
        num_inference_steps=16,
        num_images_per_prompt=1,
        output_type="pil",
    ).images
    image_paths = [save_image(img) for img in images]
    print(image_paths)
    return image_paths, seed


def load_predefined_images():
    predefined_images = [
        "assets/11.png",
        "assets/22.png",
        "assets/33.png",
        "assets/44.png",
        "assets/55.webp",
        "assets/66.png",
        "assets/77.png",
        "assets/88.png",
        "assets/99.png",
    ]
    return predefined_images



examples = [
    "A portrait of an attractive woman in her late twenties with light brown hair and purple, wearing large a a yellow sweater. She is looking directly at the camera, standing outdoors near trees.. --ar 128:85 --v 6.0 --style raw",
    "A photo of the model wearing a white bodysuit and beige trench coat, posing in front of a train station with hands on head, soft light, sunset, fashion photography, high resolution, 35mm lens, f/22, natural lighting, global illumination. --ar 85:128 --v 6.0 --style raw",
]


css = '''
.gradio-container{max-width: 575px !important}
h1{text-align:center}
footer {
    visibility: hidden
}
'''

with gr.Blocks(css=css, theme="bethecloud/storj_theme") as demo:
    gr.Markdown(DESCRIPTIONz)
    with gr.Row():
        prompt = gr.Text(
            label="Prompt",
            show_label=False,
            max_lines=1,
            placeholder="Enter your prompt",
            container=False,
        )
        run_button = gr.Button("Run", scale=0)
    result = gr.Gallery(label="Result", columns=1, show_label=False) 
    
    with gr.Accordion("Advanced options", open=False, visible=True):
        seed = gr.Slider(
            label="Seed",
            minimum=0,
            maximum=MAX_SEED,
            step=1,
            value=0,
            visible=True
        )
        randomize_seed = gr.Checkbox(label="Randomize seed", value=True)
        
        with gr.Row(visible=True):
            width = gr.Slider(
                label="Width",
                minimum=512,
                maximum=2048,
                step=64,
                value=1024,
            )
            height = gr.Slider(
                label="Height",
                minimum=512,
                maximum=2048,
                step=64,
                value=1024,
            )
        
        with gr.Row():
            guidance_scale = gr.Slider(
                label="Guidance Scale",
                minimum=0.1,
                maximum=20.0,
                step=0.1,
                value=3.0,
            )
            num_inference_steps = gr.Slider(
                label="Number of inference steps",
                minimum=1,
                maximum=40,
                step=1,
                value=16,
            )

        style_selection = gr.Radio(
            show_label=True,
            container=True,
            interactive=True,
            choices=STYLE_NAMES,
            value=DEFAULT_STYLE_NAME,
            label="Quality Style",
        )



    gr.Examples(
        examples=examples,
        inputs=prompt,
        outputs=[result, seed],
        fn=generate,
        cache_examples=False,
    )

    gr.on(
        triggers=[
            prompt.submit,
            run_button.click,
        ],
        fn=generate,
        inputs=[
            prompt,
            seed,
            width,
            height,
            guidance_scale,
            randomize_seed,
            style_selection,
        ],
        outputs=[result, seed],
        api_name="run",
    )
    
    gr.Markdown("### Generated Images")
    predefined_gallery = gr.Gallery(label="Generated Images", columns=3, show_label=False, value=load_predefined_images())
    gr.Markdown("**Disclaimer/Note:**")
    
    gr.Markdown("🔥This space provides realistic image generation, which works better for human faces and portraits. Realistic trigger works properly, better for photorealistic trigger words, close-up shots, face diffusion, male, female characters.")
   
    gr.Markdown("🔥users are accountable for the content they generate and are responsible for ensuring it meets appropriate ethical standards.")
    
if __name__ == "__main__":
    demo.queue(max_size=40).launch()