# UI locale image -> 3D avec choix du modèle. Lancer via lancer.bat
import os
import time

import gradio as gr
import torch

import backends

ROOT = os.path.dirname(os.path.abspath(__file__))
OUT_DIR = os.path.join(ROOT, "outputs")
os.makedirs(OUT_DIR, exist_ok=True)
EXAMPLES = os.path.join(ROOT, "TripoSG", "assets", "example_data")
LABELS = list(backends.MODELS)


def generate(model_label, image_path, prompt, seed, faces, progress=gr.Progress()):
    if not image_path:
        raise gr.Error("Ajoute une image d'abord.")
    cls = backends.MODELS[model_label]
    if cls.needs_prompt and not (prompt or "").strip():
        raise gr.Error("Ce modèle a besoin d'une description texte.")
    progress(0, desc=f"Chargement de {model_label} (long au premier usage)")
    try:
        model = backends.get(model_label)
    except RuntimeError as e:
        raise gr.Error(str(e))
    progress(0.3, desc="Génération")
    mesh = model.run(image_path, int(seed), prompt, int(faces))
    out = os.path.join(OUT_DIR, f"{cls.__name__}_{time.strftime('%Y%m%d_%H%M%S')}_s{int(seed)}.glb")
    mesh.export(out)
    torch.cuda.empty_cache()
    return out, out


with gr.Blocks(title="Image vers 3D local") as demo:
    gr.Markdown("## Image vers 3D (local)")
    with gr.Row():
        with gr.Column():
            model = gr.Dropdown(LABELS, value=LABELS[0], label="Modèle")
            image = gr.Image(type="filepath", label="Image")
            prompt = gr.Textbox(label="Description (en anglais)", visible=False,
                                placeholder="a cat with wings")
            seed = gr.Number(42, label="Seed", precision=0)
            faces = gr.Slider(-1, 500000, 50000, step=1000, label="Faces max (-1 = pas de réduction)")
            btn = gr.Button("Générer", variant="primary")
        with gr.Column():
            viewer = gr.Model3D(label="Résultat", clear_color=[0.9, 0.9, 0.9, 1])
            file = gr.File(label="Télécharger le .glb")
    gr.Examples([os.path.join(EXAMPLES, f) for f in sorted(os.listdir(EXAMPLES))[:8]], inputs=image)
    model.change(lambda m: gr.update(visible=backends.MODELS[m].needs_prompt), model, prompt)
    btn.click(generate, [model, image, prompt, seed, faces], [viewer, file])

demo.queue(max_size=4).launch(server_name="127.0.0.1", inbrowser=True)
