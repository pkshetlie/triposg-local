# Vérifie que chaque modèle charge et produit un maillage. Usage : .venv\Scripts\python test_backends.py [nom...]
import os
import sys
import time

import backends

ROOT = os.path.dirname(os.path.abspath(__file__))
IMG = os.path.join(ROOT, "TripoSG", "assets", "example_data", "hjswed.png")
SCRIBBLE = os.path.join(ROOT, "TripoSG", "assets", "example_scribble_data", "cat_with_wings.png")

wanted = sys.argv[1:] or [c.__name__ for c in backends.MODELS.values()]
for label, cls in backends.MODELS.items():
    if cls.__name__ not in wanted:
        continue
    img, prompt = IMG, None
    if cls.needs_prompt:
        img, prompt = SCRIBBLE, "a cat with wings"
    t = time.time()
    m = backends.get(label)
    t_load = time.time() - t
    t = time.time()
    mesh = m.run(img, 42, prompt, 20000)
    out = os.path.join(ROOT, "outputs", f"test_{cls.__name__}.glb")
    os.makedirs(os.path.dirname(out), exist_ok=True)
    mesh.export(out)
    n = len(getattr(mesh, "faces", []))
    assert n > 100, f"{cls.__name__}: maillage vide"
    print(f"OK {cls.__name__}: {n} faces, chargement {t_load:.0f} s, génération {time.time() - t:.0f} s", flush=True)
    del m, mesh  # sinon l'ancien modèle reste en VRAM pendant le chargement du suivant
