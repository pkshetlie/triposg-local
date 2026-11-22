# TripoSG local — image → modèle 3D sur ton PC

Installation clé en main de [TripoSG](https://github.com/VAST-AI-Research/TripoSG) (VAST-AI, licence MIT) pour Windows, avec une petite interface web locale. Tu donnes une image, il sort un modèle 3D `.glb` (géométrie seule, sans texture).

## Ce qu'il faut

| | |
|---|---|
| Système | Windows 10/11 64 bits |
| Carte graphique | NVIDIA **8 Go de VRAM minimum** (RTX 2060 12 Go, 3060, 3070, 4060 Ti, 4070…). Testé sur RTX 3070 8 Go. **Les RTX 50xx ne sont pas supportées** par cette version. |
| Pilote NVIDIA | récent (2024 ou plus) |
| Python | **3.10** exactement — [python.org](https://www.python.org/downloads/release/python-31011/), cocher *Add python.exe to PATH* |
| Git | [git-scm.com](https://git-scm.com/download/win) |
| Disque | ~15 Go libres |

Pas besoin de CUDA Toolkit ni de Visual Studio : le module compilé (`diso`) est fourni dans `wheels/`.

## Installation

1. Télécharger ce dépôt (bouton **Code → Download ZIP**, puis extraire) ou `git clone`.
   Mets-le dans un **chemin court**, par ex. `C:\triposg-local` ou `D:\triposg-local` (Windows coince sur les chemins trop longs).
2. Double-cliquer sur **`installer.bat`**. Ça prend 10 à 30 min selon la connexion (≈3 Go de paquets + les poids du modèle).
3. À la fin : « Installation terminée ! ».

Si ça coupe en route, relance `installer.bat` : il reprend là où il en était.

## Utilisation

Double-cliquer sur **`lancer.bat`** → après 1 à 4 min de chargement, le navigateur s'ouvre sur http://127.0.0.1:7860.

Ferme Blender, les jeux et les onglets lourds avant : si la VRAM est pleine, Windows déborde sur la RAM et une génération peut passer de 30 s à plus de 10 min.

- Dépose une image (un seul objet, entier, bien éclairé ; le fond est retiré tout seul) puis **Générer**.
- ~30 s par modèle sur une RTX 3070. Résultat visible en 3D + téléchargeable, et sauvegardé dans `outputs\`.
- **Faces max** : 50 000 par défaut. Pour un jeu : ~2-5 k (petits props), ~10-20 k (objets importants). `-1` = maillage brut (~1,3 M faces).
- **Seed** : change-la pour obtenir une autre variante.
- Pour arrêter : fermer la fenêtre noire.

Les `.glb` s'ouvrent dans Blender (*File → Import → glTF 2.0*), Godot, Unity, Roblox Studio, etc.

## En ligne de commande

```powershell
cd D:\triposg-local\TripoSG
..\.venv\Scripts\python -m scripts.inference_triposg --image-input C:\chemin\image.png --output-path C:\chemin\modele.glb --faces 20000
```

(Les poids doivent être dans `TripoSG\pretrained_weights\` pour ce script : sinon il les retélécharge. L'interface, elle, utilise `pretrained_weights\` à la racine.)

## Problèmes fréquents

- **« CUDA out of memory »** : ferme les jeux / autres applis qui utilisent le GPU, et ne lance qu'une génération à la fois.
- **« Nom de fichier ou extension trop long »** : déplace le dossier vers un chemin court (`C:\triposg-local`) et relance `installer.bat`.
- **« Python 3.10 est requis »** : installe Python 3.10 (pas 3.11/3.12), en cochant *Add to PATH*.
- **Ne fais pas de `pip install -U`** dans `.venv` : les versions de `requirements-lock.txt` sont figées exprès (les plus récentes de diffusers/transformers/numpy cassent avec PyTorch 2.5).

## Contenu

- `install.ps1` / `installer.bat` : clone TripoSG (version testée), crée `.venv`, installe les versions figées, télécharge les poids.
- `app.py` / `lancer.bat` : l'interface Gradio.
- `wheels/diso-0.1.4-cp310-cp310-win_amd64.whl` : `diso` compilé pour Python 3.10 + PyTorch 2.5.1/CUDA 12.1, GPU RTX 20xx → 40xx.

## Licences

- TripoSG (code et poids) : © VAST-AI-Research, licence MIT.
- `diso` (wheel fourni, compilé sans modification) : © 2023 Xinyue Wei, [CC BY-NC 4.0](https://creativecommons.org/licenses/by-nc/4.0/) — **non commercial**.
- Détourage [briaai/RMBG-1.4](https://huggingface.co/briaai/RMBG-1.4) : licence BRIA AI, **non commerciale**.
- Scripts de ce dépôt : MIT (voir `LICENSE`).

⚠️ Si tu comptes vendre ce que tu produis, vérifie ces deux licences non commerciales.
