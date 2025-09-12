# SalomeUtils

[![License: LGPL v2.1](https://img.shields.io/badge/License-LGPL%20v2.1-blue.svg)](https://www.gnu.org/licenses/lgpl-2.1)
[![Python](https://img.shields.io/badge/Python-3.6+-blue.svg)](https://www.python.org/)
[![Salome](https://img.shields.io/badge/Salome-9.0+-green.svg)](https://www.salome-platform.org/)

Collection de scripts Python pour automatiser les tâches dans la plateforme Salome, particulièrement orientés vers la préparation de simulations par éléments finis avec Code_Aster.

## 📋 Table des matières

- [Fonctionnalités](#-fonctionnalités)
- [Prérequis](#-prérequis)
- [Installation](#-installation)
- [Utilisation](#-utilisation)
- [Scripts disponibles](#-scripts-disponibles)
- [Structure du projet](#-structure-du-projet)
- [Contribution](#-contribution)
- [Licence](#-licence)
- [Auteur](#-auteur)

## 🚀 Fonctionnalités

### Génération automatique de contacts 3D
- Détection automatique des intersections entre pièces
- Interface graphique intuitive pour la configuration
- Export direct vers Code_Aster
- Gestion des contacts maître/esclave

### Boulons virtuels 1D
- Reconnaissance automatique des vis, écrous et trous
- Conversion en éléments 1D pour optimiser les calculs
- Calcul automatique des propriétés mécaniques
- Support des différents types de fixations

### Gestion des pièces
- Renommage automatique par lot
- Création de groupes géométriques
- Organisation de l'arbre d'étude Salome

## 📋 Prérequis

- **Salome Platform** 9.0 ou supérieur
- **Python** 3.6+ (inclus avec Salome)
- **PyQt5** (inclus avec Salome)
- **NumPy** (inclus avec Salome)

### Modules Python requis
```python
import salome
from salome.geom import geomBuilder
from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
import numpy as np
```

## 🔧 Installation

### Méthode 1 : Clonage direct
```bash
git clone https://github.com/marcDuboc/SalomeUtils.git
cd SalomeUtils
```

### Méthode 2 : Téléchargement
1. Téléchargez le repository en ZIP
2. Extrayez dans votre répertoire de travail Salome
3. Ajoutez le chemin aux scripts Python de Salome

### Configuration dans Salome
1. Ouvrez Salome
2. Allez dans **Fichier > Préférences > Python**
3. Ajoutez le chemin vers le dossier `scripts/` dans le PYTHONPATH

## 📖 Utilisation

### Lancement des scripts

#### Dans l'interface Salome
1. Ouvrez le module **Geometry**
2. Allez dans **Fichier > Charger un script**
3. Sélectionnez le script désiré dans le dossier `scripts/`

#### En ligne de commande
```bash
# Depuis Salome
salome -t python contactAuto.py

# Ou directement dans la console Python de Salome
exec(open('/path/to/SalomeUtils/scripts/contactAuto.py').read())
```

### Workflow typique

1. **Préparation** : Importez votre géométrie dans Salome
2. **Renommage** : Utilisez `renameAuto.py` pour organiser vos pièces
3. **Contacts** : Lancez `contactAuto.py` pour générer les contacts
4. **Boulons** : Utilisez `virtualBolt.py` pour simplifier les fixations
5. **Export** : Exportez vers Code_Aster pour la simulation

## 📁 Scripts disponibles

### 🔗 contactAuto.py
**Génération automatique de contacts entre pièces**

```python
# Fonctionnalités principales
- Détection d'intersections géométriques
- Configuration des paramètres de contact (gap, angle)
- Gestion maître/esclave automatique
- Export Code_Aster (.comm)
```

**Interface graphique :**
- Sélection de compound ou pièces multiples
- Paramètres de tolérance configurables
- Prévisualisation des contacts détectés
- Export en format RAW ou ASTER

### 🔩 virtualBolt.py
**Création de boulons virtuels 1D**

```python
# Méthodes de détection
- SCREW : Détection vis + écrou + trous
- HOLE : Détection par trous alignés
```

**Fonctionnalités :**
- Reconnaissance automatique des formes cylindriques
- Calcul des propriétés mécaniques (rayon, précharge)
- Création d'éléments 1D dans Salome
- Export des propriétés pour Code_Aster

### 📝 renameAuto.py
**Renommage et organisation des pièces**

```python
# Options disponibles
- Préfixe personnalisable
- Création automatique de groupes
- Renommage par lot
```

## 🏗️ Structure du projet

```
SalomeUtils/
├── README.md
├── scripts/
│   ├── contactAuto.py          # Script principal contacts
│   ├── virtualBolt.py          # Script principal boulons
│   ├── renameAuto.py          # Script renommage
│   └── common/                # Modules partagés
│       ├── __init__.py        # Configuration logging
│       ├── properties.py      # Classes géométriques
│       ├── tree.py           # Navigation arbre Salome
│       ├── contact/          # Modules contacts
│       │   ├── data.py       # Gestion données contacts
│       │   ├── intersect.py  # Algorithmes intersection
│       │   ├── aster.py      # Export Code_Aster
│       │   └── cgui/         # Interface graphique
│       ├── bolt/             # Modules boulons
│       │   ├── data.py       # Gestion données boulons
│       │   ├── shape.py      # Reconnaissance formes
│       │   ├── aster.py      # Export Code_Aster
│       │   └── bgui/         # Interface graphique
│       └── img/              # Ressources graphiques
└── template/
    ├── base.comm             # Template Code_Aster
    └── ref_NL_MPI.txt       # Référence calculs parallèles
```

## 🔧 Configuration avancée

### Paramètres de contact
```python
# Dans contactAuto.py
gap = 0.1          # Écart maximum pour détection
angle = 5.0        # Tolérance angulaire (degrés)
merge_by_part = True      # Fusion par pièce
merge_by_proximity = True # Fusion par proximité
```

### Paramètres de boulons
```python
# Dans virtualBolt.py
d_min = 3.0        # Diamètre minimum (mm)
d_max = 36.0       # Diamètre maximum (mm)
tol_axis = 0.01    # Tolérance axe (mm)
tol_dist = 0.01    # Tolérance distance (mm)
```

## 🐛 Dépannage

### Problèmes courants

**Script ne se lance pas :**
```python
# Vérifiez le PYTHONPATH dans Salome
import sys
sys.path.append('/path/to/SalomeUtils/scripts')
```

**Erreur d'import PyQt5 :**
```bash
# Vérifiez l'installation PyQt5 dans Salome
python -c "from PyQt5.QtWidgets import QApplication"
```

**Problèmes de détection géométrique :**
- Vérifiez que les pièces sont des solides valides
- Ajustez les paramètres de tolérance
- Utilisez la fonction de debug dans les logs

### Logs de debug
Les logs sont automatiquement créés dans `scripts/log/debug.log`

## 🤝 Contribution

Les contributions sont les bienvenues ! Pour contribuer :

1. Forkez le projet
2. Créez une branche pour votre fonctionnalité (`git checkout -b feature/AmazingFeature`)
3. Committez vos changements (`git commit -m 'Add some AmazingFeature'`)
4. Poussez vers la branche (`git push origin feature/AmazingFeature`)
5. Ouvrez une Pull Request

### Standards de code
- Suivez PEP 8 pour le style Python
- Documentez les nouvelles fonctions
- Ajoutez des tests si possible
- Utilisez des messages de commit descriptifs

## 📄 Licence

Ce projet est sous licence LGPL v2.1 - voir le fichier [LICENSE](LICENSE) pour plus de détails.

## 👨‍💻 Auteur

**Marc DUBOC**
- Email : [marcduboc@hotmail.com](mailto:marc.duboc@example.com)
- GitHub : [@marcDuboc](https://github.com/marcDuboc)

## 🙏 Remerciements

- Équipe de développement Salome Platform
- Communauté Code_Aster
- Contributeurs du projet

## 📚 Documentation supplémentaire

- [Documentation Salome](https://docs.salome-platform.org/)
- [Guide Code_Aster](https://www.code-aster.org/spip.php?rubrique2)
- [PyQt5 Documentation](https://doc.qt.io/qtforpython/)

---

**Version :** 11/08/2023  
**Compatibilité :** Salome 9.0+, Python 3.6+
