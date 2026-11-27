# Modèles image -> 3D interchangeables. Chacun : load() puis run(image_path, seed, prompt) -> trimesh
import os
import sys
import threading

import numpy as np
import torch
from huggingface_hub import snapshot_download
from PIL import Image

ROOT = os.path.dirname(os.path.abspath(__file__))
W = os.path.join(ROOT, "pretrained_weights")
for repo in ("TripoSG", "TripoSR", "stable-fast-3d"):  # pas "sf3d" : ce dossier masquerait le paquet sf3d
    sys.path.insert(0, os.path.join(ROOT, repo))


def _weights(repo_id, name):
    path = os.path.join(W, name)
    snapshot_download(repo_id=repo_id, local_dir=path)  # rapide si déjà là
    return path


STOP = threading.Event()  # mis par le bouton « Arrêter » de l'UI


def _check_stop(*_):
    if STOP.is_set():
        raise RuntimeError("Génération arrêtée.")


_rembg = None


def _rembg_session():
    global _rembg
    if _rembg is None:
        import rembg
        _rembg = rembg.new_session()
    return _rembg


class TripoSG:
    label = "TripoSG (forme précise, sans texture)"
    needs_prompt = False

    def load(self):
        from scripts.briarmbg import BriaRMBG
        from triposg.pipelines.pipeline_triposg import TripoSGPipeline
        self.rmbg = BriaRMBG.from_pretrained(_weights("briaai/RMBG-1.4", "RMBG-1.4")).to("cuda").eval()
        self.pipe = TripoSGPipeline.from_pretrained(_weights("VAST-AI/TripoSG", "TripoSG")).to("cuda", torch.float16)
        self.pipe.transformer.register_forward_pre_hook(_check_stop)  # vérifié à chaque étape de diffusion

    def run(self, image_path, seed, prompt, faces):
        from scripts.inference_triposg import run_triposg
        return run_triposg(self.pipe, image_path, self.rmbg, seed, 50, 7.0, faces)


class TripoSGScribble:
    label = "TripoSG scribble (croquis + texte)"
    needs_prompt = True

    def load(self):
        from triposg.pipelines.pipeline_triposg_scribble import TripoSGScribblePipeline
        self.pipe = TripoSGScribblePipeline.from_pretrained(
            _weights("VAST-AI/TripoSG-scribble", "TripoSG-scribble")).to("cuda", torch.float16)
        self.pipe.transformer.register_forward_pre_hook(_check_stop)

    def run(self, image_path, seed, prompt, faces):
        from scripts.inference_triposg import simplify_mesh
        from scripts.inference_triposg_scribble import run_triposg_scribble
        mesh = run_triposg_scribble(self.pipe, image_path, prompt, seed)
        return simplify_mesh(mesh, faces) if faces > 0 else mesh


class TripoSR:
    label = "TripoSR (rapide, couleurs par sommet)"
    needs_prompt = False

    def load(self):
        from tsr.system import TSR
        self.model = TSR.from_pretrained(_weights("stabilityai/TripoSR", "TripoSR"),
                                         config_name="config.yaml", weight_name="model.ckpt")
        self.model.renderer.set_chunk_size(8192)
        self.model.to("cuda")

    def run(self, image_path, seed, prompt, faces):
        from tsr.utils import remove_background, resize_foreground
        from scripts.inference_triposg import simplify_mesh
        img = resize_foreground(remove_background(Image.open(image_path), _rembg_session()), 0.85)
        a = np.array(img).astype(np.float32) / 255.0
        a = a[:, :, :3] * a[:, :, 3:4] + (1 - a[:, :, 3:4]) * 0.5  # fond gris attendu par TripoSR
        with torch.no_grad():
            codes = self.model([Image.fromarray((a * 255).astype(np.uint8))], device="cuda")
        mesh = self.model.extract_mesh(codes, True, resolution=256)[0]
        # shortcut: la réduction de faces perd les couleurs par sommet, donc on ne réduit pas TripoSR (~100 k faces)
        return mesh


class StableFast3D:
    label = "Stable Fast 3D (texturé, compte Hugging Face requis)"
    needs_prompt = False

    def load(self):
        from sf3d.system import SF3D
        try:
            path = _weights("stabilityai/stable-fast-3d", "stable-fast-3d")
        except Exception as e:
            raise RuntimeError(
                "Poids Stable Fast 3D inaccessibles : accepte la licence sur "
                "https://huggingface.co/stabilityai/stable-fast-3d puis connecte-toi avec "
                "'.venv\\Scripts\\huggingface-cli login'.") from e
        self.model = SF3D.from_pretrained(path, config_name="config.yaml", weight_name="model.safetensors")
        self.model.eval().to("cuda")

    def run(self, image_path, seed, prompt, faces):
        from sf3d.utils import remove_background, resize_foreground
        img = resize_foreground(remove_background(Image.open(image_path).convert("RGBA"), _rembg_session()), 0.85)
        torch.manual_seed(seed)
        with torch.no_grad(), torch.autocast(device_type="cuda", dtype=torch.bfloat16):
            mesh, _ = self.model.run_image(img, bake_resolution=1024, remesh="triangle" if faces > 0 else "none",
                                           vertex_count=faces // 2 if faces > 0 else -1)
        return mesh


class Trellis2Online:
    label = "TRELLIS.2 (en ligne sur Hugging Face, quota limité)"
    needs_prompt = False

    def load(self):  # rien en VRAM : tourne sur les GPU de la page Hugging Face de Microsoft
        from gradio_client import Client
        from huggingface_hub import get_token
        try:
            self.client = Client("microsoft/TRELLIS.2", hf_token=get_token(), verbose=False)
        except Exception as e:
            raise RuntimeError(f"Page TRELLIS.2 injoignable (hors ligne ou en panne) : {e}") from e

    def run(self, image_path, seed, prompt, faces):
        import trimesh
        from gradio_client import handle_file
        c = self.client
        try:  # même ordre que l'interface web : l'état est gardé côté serveur pour cette session
            c.predict(api_name="/start_session")
            img = c.predict(handle_file(image_path), api_name="/preprocess_image")
            _check_stop()  # shortcut: une étape déjà envoyée au serveur va jusqu'au bout (~30 s max)
            c.predict(handle_file(img), seed, "1024", api_name="/image_to_3d")
            _check_stop()
            # shortcut: le serveur impose >= 100 000 faces ; réduire ici effacerait la texture
            glb, _ = c.predict(max(faces, 100000) if faces > 0 else 500000, 1024, api_name="/extract_glb")
        except Exception as e:
            if STOP.is_set():
                raise RuntimeError("Génération arrêtée.") from e
            raise RuntimeError(f"TRELLIS.2 en ligne a échoué (quota GPU gratuit épuisé ?) : {e}") from e
        return trimesh.load(glb)


MODELS = {c.label: c for c in (TripoSG, TripoSGScribble, TripoSR, StableFast3D, Trellis2Online)}
_current = None  # (label, instance) : un seul modèle en VRAM à la fois (8 Go)


def get(label):
    global _current
    if _current and _current[0] == label:
        return _current[1]
    if _current:
        _current = None
        import gc
        gc.collect()  # libère vraiment l'ancien modèle avant d'en charger un autre
        torch.cuda.empty_cache()
    inst = MODELS[label]()
    inst.load()
    _current = (label, inst)
    return inst
