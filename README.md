# Image → 3D en local (TripoSG, TripoSR, Stable Fast 3D)

Installation clé en main pour Windows de plusieurs modèles image → 3D open source, avec une petite interface web locale où l'on choisit le modèle. Tu donnes une image, il sort un modèle 3D `.glb`.

| Modèle | Ce qu'il fait | Temps (RTX 3070) |
|---|---|---|
| [TripoSG](https://github.com/VAST-AI-Research/TripoSG) | forme la plus précise, **sans texture** | ~1 min |
| TripoSG scribble | à partir d'un **croquis + une description en anglais**, sans texture | ~25 s |
| [TripoSR](https://github.com/VAST-AI-Research/TripoSR) | très rapide, forme plus grossière, **couleurs par sommet** | ~10-35 s |
| [Stable Fast 3D](https://github.com/Stability-AI/stable-fast-3d) | **texturé** (UV + texture) ; demande un compte Hugging Face (voir plus bas) | ~5 s |
| [TRELLIS.2](https://huggingface.co/spaces/microsoft/TRELLIS.2) **en ligne** | **texturé**, très bonne qualité, calculé sur les GPU de Microsoft/Hugging Face (ton image y est envoyée). Quota gratuit : **~2 générations par jour** (PRO : 25 min/jour). 100 000 faces minimum. Peut casser si la page change. | ~1 min |

Temps mesurés modèle déjà chargé ; le premier usage d'un modèle ajoute son chargement (quelques secondes sur SSD, jusqu'à 4 min sur disque dur).

Un seul modèle est chargé à la fois (8 Go de VRAM) : changer de modèle dans le menu décharge l'ancien. Le premier usage de chaque modèle télécharge ses poids (1 à 4 Go).

## Ce qu'il faut

| | |
|---|---|
| Système | Windows 10/11 64 bits |
| Carte graphique | NVIDIA **8 Go de VRAM minimum** (RTX 2060 12 Go, 3060, 3070, 4060 Ti, 4070…). Testé sur RTX 3070 8 Go. **Les RTX 50xx ne sont pas supportées** par cette version. |
| Pilote NVIDIA | récent (2024 ou plus) |
| Python | **3.10** exactement — [python.org](https://www.python.org/downloads/release/python-31011/), cocher *Add python.exe to PATH* |
| Git | [git-scm.com](https://git-scm.com/download/win) |
| Disque | ~15 Go libres |

Pas besoin de CUDA Toolkit ni de Visual Studio : les modules compilés (`diso`, `torchmcubes`, `texture_baker`, `uv_unwrapper`) sont fournis dans `wheels/`.

### Stable Fast 3D : une étape en plus

Ses poids sont protégés par Stability AI. Une seule fois :
1. Crée un compte sur [huggingface.co](https://huggingface.co), puis ouvre [stabilityai/stable-fast-3d](https://huggingface.co/stabilityai/stable-fast-3d) et accepte la licence.
2. Crée un jeton de lecture dans *Settings → Access Tokens*.
3. Dans le dossier, lance `.venv\Scripts\huggingface-cli login` et colle le jeton.

Sans ça, les autres modèles marchent quand même ; Stable Fast 3D affiche juste un message d'erreur. Cette même connexion sert au quota de TRELLIS.2 en ligne.

## Installation

1. Télécharger ce dépôt (bouton **Code → Download ZIP**, puis extraire) ou `git clone`.
   Mets-le dans un **chemin court**, par ex. `C:\triposg-local` ou `D:\triposg-local` (Windows coince sur les chemins trop longs).
2. Double-cliquer sur **`installer.bat`**. Ça prend 10 à 30 min selon la connexion (≈3 Go de paquets + les poids du modèle).
3. À la fin : « Installation terminée ! ».

Si ça coupe en route, relance `installer.bat` : il reprend là où il en était.

## Utilisation

Double-cliquer sur **`lancer.bat`** → le navigateur s'ouvre sur http://127.0.0.1:7860. Installe de préférence sur un **SSD** : sur disque dur, charger un modèle prend plusieurs minutes.

Ferme Blender, les jeux et les onglets lourds avant : si la VRAM est pleine, Windows déborde sur la RAM et une génération peut passer de 30 s à plus de 10 min.

- Choisis le **modèle** dans le menu (pour *scribble*, un champ « Description » apparaît).
- Dépose une image (un seul objet, entier, bien éclairé ; le fond est retiré tout seul) puis **Générer**.
- Résultat visible en 3D + téléchargeable, et sauvegardé dans `outputs\`.
- **Faces max** : 50 000 par défaut. Pour un jeu : ~2-5 k (petits props), ~10-20 k (objets importants). `-1` = maillage brut (~1,3 M faces pour TripoSG). TripoSR ignore ce réglage (la réduction effacerait ses couleurs).
- **Seed** : change-la pour obtenir une autre variante.
- **Arrêter** : stoppe la génération en cours (TripoSG : tout de suite ; TRELLIS.2 en ligne : à la fin de l'étape en cours ; pendant le chargement d'un modèle : ne coupe pas le chargement).
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

- `install.ps1` / `installer.bat` : clone TripoSG, TripoSR et Stable Fast 3D (dossier `stable-fast-3d`, versions testées), crée `.venv`, installe les versions figées, télécharge les poids de TripoSG.
- `app.py` / `lancer.bat` : l'interface Gradio. `backends.py` : un petit bloc par modèle (ajouter un modèle = ajouter une classe).
- `test_backends.py` : vérifie que chaque modèle charge et génère.
- `wheels/` : modules compilés pour Python 3.10 + PyTorch 2.5.1/CUDA 12.1, GPU RTX 20xx → 40xx.

## Licences

- TripoSG et TripoSG scribble (code et poids) : © VAST-AI-Research, licence MIT.
- TripoSR (code et poids) : © Tripo AI & Stability AI, licence MIT. `torchmcubes` : MIT.
- Stable Fast 3D (code, poids, et les wheels `texture_baker` / `uv_unwrapper` fournis) : [Stability AI Community License](wheels/STABILITY_AI_COMMUNITY_LICENSE.md) — gratuit en usage perso, et en commercial sous 1 M$ de chiffre d'affaires annuel après inscription chez Stability AI. Voir `NOTICE`. **Powered by Stability AI.**
- Détourage de TripoSR / Stable Fast 3D : [rembg](https://github.com/danielgatis/rembg) (MIT) avec le modèle u2net.
- `diso` (wheel fourni, compilé sans modification) : © 2023 Xinyue Wei, [CC BY-NC 4.0](https://creativecommons.org/licenses/by-nc/4.0/) — **non commercial**.
- Détourage [briaai/RMBG-1.4](https://huggingface.co/briaai/RMBG-1.4) : licence BRIA AI, **non commerciale**.
- Scripts de ce dépôt : MIT (voir `LICENSE`).

⚠️ Si tu comptes vendre ce que tu produis, vérifie ces deux licences non commerciales.
