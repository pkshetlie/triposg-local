# UI locale pour TripoSG (image -> modèle 3D). Lancer via lancer.bat
import os
import sys
import time

ROOT = os.path.dirname(os.path.abspath(__file__))
TRIPOSG = os.path.join(ROOT, "TripoSG")  # code officiel, cloné par install.ps1
sys.path.insert(0, TRIPOSG)

import gradio as gr
import torch

from scripts.inference_triposg import run_triposg
from scripts.briarmbg import BriaRMBG
from triposg.pipelines.pipeline_triposg import TripoSGPipeline

OUT_DIR = os.path.join(ROOT, "outputs")
os.makedirs(OUT_DIR, exist_ok=True)
EXAMPLES = os.path.join(TRIPOSG, "assets", "example_data")

rmbg_net = BriaRMBG.from_pretrained(os.path.join(ROOT, "pretrained_weights", "RMBG-1.4")).to("cuda").eval()
pipe = TripoSGPipeline.from_pretrained(os.path.join(ROOT, "pretrained_weights", "TripoSG")).to("cuda", torch.float16)


def generate(image_path, seed, steps, guidance, faces):
    if not image_path:
        raise gr.Error("Ajoute une image d'abord.")
    mesh = run_triposg(pipe, image_path, rmbg_net, int(seed), int(steps), float(guidance), int(faces))
    out = os.path.join(OUT_DIR, f"triposg_{time.strftime('%Y%m%d_%H%M%S')}_s{int(seed)}.glb")
    mesh.export(out)
    torch.cuda.empty_cache()
    return out, out


with gr.Blocks(title="TripoSG local") as demo:
    gr.Markdown("## TripoSG — image vers 3D (local)")
    with gr.Row():
        with gr.Column():
            image = gr.Image(type="filepath", label="Image (fond retiré automatiquement)")
            seed = gr.Number(42, label="Seed", precision=0)
            steps = gr.Slider(10, 100, 50, step=1, label="Étapes de diffusion")
            guidance = gr.Slider(1, 15, 7.0, step=0.5, label="Guidance scale")
            faces = gr.Slider(-1, 500000, 50000, step=1000, label="Faces max (-1 = pas de réduction)")
            btn = gr.Button("Générer", variant="primary")
        with gr.Column():
            viewer = gr.Model3D(label="Résultat", clear_color=[0.9, 0.9, 0.9, 1])
            file = gr.File(label="Télécharger le .glb")
    gr.Examples([os.path.join(EXAMPLES, f) for f in sorted(os.listdir(EXAMPLES))[:8]], inputs=image)
    btn.click(generate, [image, seed, steps, guidance, faces], [viewer, file])

demo.queue(max_size=4).launch(server_name="127.0.0.1", inbrowser=True)
