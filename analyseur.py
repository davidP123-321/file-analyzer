import os
import re
import json
import csv
from collections import Counter
import tkinter as tk
from tkinter import filedialog, messagebox, ttk
from threading import Thread
import mimetypes

class AnalyseurFichiers:
    def __init__(self, root):
        self.root = root
        self.root.title("Analyseur de Fichiers 📊")
        self.root.geometry("1000x700")
        self.root.resizable(True, True)
        
        # Configuration du style
        style = ttk.Style()
        style.theme_use('clam')
        style.configure('TFrame', background='#f0f0f0')
        style.configure('Header.TLabel', font=('Helvetica', 14, 'bold'), background='#f0f0f0', foreground='#2c3e50')
        style.configure('Info.TLabel', font=('Helvetica', 10), background='#f0f0f0')
        style.configure('TButton', font=('Helvetica', 10))
        
        self.fichiers_selectionnes = []
        self.resultats = {}
        
        self.creer_interface()
    
    def creer_interface(self):
        # Barre d'outils
        toolbar = ttk.Frame(self.root)
        toolbar.pack(fill=tk.X, padx=10, pady=10)
        
        btn_ouvrir = ttk.Button(toolbar, text="📂 Ouvrir fichiers", command=self.ouvrir_fichiers)
        btn_ouvrir.pack(side=tk.LEFT, padx=5)
        
        btn_dossier = ttk.Button(toolbar, text="📁 Ouvrir dossier", command=self.ouvrir_dossier)
        btn_dossier.pack(side=tk.LEFT, padx=5)
        
        btn_effacer = ttk.Button(toolbar, text="🗑️ Effacer", command=self.effacer_tout)
        btn_effacer.pack(side=tk.LEFT, padx=5)
        
        # Séparateur
        ttk.Separator(self.root, orient=tk.HORIZONTAL).pack(fill=tk.X)
        
        # Panneau principal avec 2 colonnes
        main_frame = ttk.Frame(self.root)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # --- COLONNE GAUCHE: Liste des fichiers ---
        left_frame = ttk.Frame(main_frame)
        left_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=False, padx=(0, 10))
        
        ttk.Label(left_frame, text="Fichiers", style='Header.TLabel').pack(anchor=tk.W, pady=(0, 5))
        
        # Listbox avec scrollbar
        scrollbar = ttk.Scrollbar(left_frame)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        self.listbox = tk.Listbox(
            left_frame, 
            width=30, 
            height=25,
            yscrollcommand=scrollbar.set,
            font=('Helvetica', 9),
            bg='white',
            selectmode=tk.SINGLE
        )
        self.listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        self.listbox.bind('<<ListboxSelect>>', self.afficher_analyse)
        scrollbar.config(command=self.listbox.yview)
        
        # --- COLONNE DROITE: Détails de l'analyse ---
        right_frame = ttk.Frame(main_frame)
        right_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        ttk.Label(right_frame, text="Détails de l'analyse", style='Header.TLabel').pack(anchor=tk.W, pady=(0, 5))
        
        # Text widget avec scrollbar pour afficher les résultats
        scrollbar_text = ttk.Scrollbar(right_frame)
        scrollbar_text.pack(side=tk.RIGHT, fill=tk.Y)
        
        self.text_resultat = tk.Text(
            right_frame,
            height=25,
            width=60,
            yscrollcommand=scrollbar_text.set,
            font=('Courier', 9),
            bg='#2c3e50',
            fg='#ecf0f1',
            wrap=tk.WORD,
            padx=10,
            pady=10
        )
        self.text_resultat.pack(fill=tk.BOTH, expand=True)
        scrollbar_text.config(command=self.text_resultat.yview)
        
        # Tags pour coloration
        self.text_resultat.tag_config('titre', font=('Courier', 11, 'bold'), foreground='#3498db')
        self.text_resultat.tag_config('cle', foreground='#2ecc71')
        self.text_resultat.tag_config('valeur', foreground='#ecf0f1')
        self.text_resultat.tag_config('erreur', foreground='#e74c3c')
        self.text_resultat.tag_config('stats', foreground='#f39c12')
        
    def ouvrir_fichiers(self):
        fichiers = filedialog.askopenfilenames(
            title="Sélectionner des fichiers",
            filetypes=[("Tous les fichiers", "*.*")]
        )
        if fichiers:
            self.fichiers_selectionnes = list(fichiers)
            self.mettre_a_jour_listbox()
            self.analyser_tous()
    
    def ouvrir_dossier(self):
        dossier = filedialog.askdirectory(title="Sélectionner un dossier")
        if dossier:
            fichiers = []
            for root, dirs, files in os.walk(dossier):
                for file in files:
                    fichiers.append(os.path.join(root, file))
            
            if fichiers:
                self.fichiers_selectionnes = fichiers
                self.mettre_a_jour_listbox()
                self.analyser_tous()
            else:
                messagebox.showwarning("Attention", "Aucun fichier trouvé dans ce dossier.")
    
    def mettre_a_jour_listbox(self):
        self.listbox.delete(0, tk.END)
        for fichier in self.fichiers_selectionnes:
            nom = os.path.basename(fichier)
            self.listbox.insert(tk.END, nom)
    
    def analyser_tous(self):
        """Lance l'analyse dans un thread séparé"""
        def analyser():
            self.resultats.clear()
            for fichier in self.fichiers_selectionnes:
                self.resultats[fichier] = self.analyser_fichier(fichier)
            self.root.after(0, lambda: messagebox.showinfo("Analyse", "Analyse terminée !"))
        
        thread = Thread(target=analyser, daemon=True)
        thread.start()
    
    def analyser_fichier(self, chemin):
        """Analyse un fichier et retourne les résultats"""
        resultat = {
            "nom": os.path.basename(chemin),
            "chemin": chemin,
            "extension": os.path.splitext(chemin)[1].lower(),
            "taille_octets": os.path.getsize(chemin),
            "type": "inconnu"
        }
        
        if not os.path.exists(chemin):
            resultat["erreur"] = "Le fichier n'existe pas."
            return resultat
        
        # Essayer de lire comme texte
        try:
            with open(chemin, "r", encoding="utf-8", errors='ignore') as fichier:
                texte = fichier.read()
            resultat["type"] = "texte"
        except Exception as e:
            resultat["type"] = "binaire"
            resultat["erreur"] = f"Impossible de lire le fichier : {str(e)}"
            return resultat
        
        # Statistiques de base
        lignes = texte.splitlines()
        mots = re.findall(r"\b[\w-]+\b", texte.lower())
        resultat["nb_lignes"] = len(lignes)
        resultat["nb_mots"] = len(mots)
        resultat["nb_caracteres"] = len(texte)
        
        # Déterminer le type de fichier
        if resultat["extension"] == ".py":
            resultat["type_specifique"] = "Python"
            self.analyser_python(texte, resultat)
        elif resultat["extension"] == ".json":
            resultat["type_specifique"] = "JSON"
            self.analyser_json(texte, resultat)
        elif resultat["extension"] == ".csv":
            resultat["type_specifique"] = "CSV"
            self.analyser_csv(chemin, resultat)
        elif resultat["extension"] in [".txt", ".md", ".html", ".xml", ".css", ".js"]:
            resultat["type_specifique"] = resultat["extension"][1:].upper()
        
        # Mots les plus fréquents
        compteur = Counter(mots)
        resultat["mots_frequents"] = compteur.most_common(5)
        
        return resultat
    
    def analyser_python(self, texte, resultat):
        """Analyse spéciale pour fichiers Python"""
        # Compter les fonctions, classes, imports
        fonctions = len(re.findall(r"^def\s+\w+", texte, re.MULTILINE))
        classes = len(re.findall(r"^class\s+\w+", texte, re.MULTILINE))
        imports = len(re.findall(r"^import\s+|^from\s+", texte, re.MULTILINE))
        
        resultat["fonctions"] = fonctions
        resultat["classes"] = classes
        resultat["imports"] = imports
    
    def analyser_json(self, texte, resultat):
        """Analyse spéciale pour JSON"""
        try:
            data = json.loads(texte)
            resultat["json_valide"] = True
            if isinstance(data, dict):
                resultat["cles_json"] = list(data.keys())
            elif isinstance(data, list):
                resultat["nb_elements_json"] = len(data)
        except Exception as e:
            resultat["json_valide"] = False
            resultat["erreur_json"] = str(e)
    
    def analyser_csv(self, chemin, resultat):
        """Analyse spéciale pour CSV"""
        try:
            with open(chemin, "r", encoding="utf-8", newline="", errors='ignore') as f:
                lecteur = csv.reader(f)
                lignes_csv = list(lecteur)
            resultat["nb_lignes_csv"] = len(lignes_csv)
            if lignes_csv:
                resultat["nb_colonnes_csv"] = len(lignes_csv[0])
                resultat["colonnes"] = lignes_csv[0]
        except Exception as e:
            resultat["erreur_csv"] = str(e)
    
    def afficher_analyse(self, event):
        """Affiche l'analyse du fichier sélectionné"""
        selection = self.listbox.curselection()
        if not selection:
            return
        
        fichier = self.fichiers_selectionnes[selection[0]]
        if fichier not in self.resultats:
            self.text_resultat.config(state=tk.NORMAL)
            self.text_resultat.delete(1.0, tk.END)
            self.text_resultat.insert(1.0, "Analyse en cours...", 'stats')
            self.text_resultat.config(state=tk.DISABLED)
            return
        
        resultat = self.resultats[fichier]
        self.text_resultat.config(state=tk.NORMAL)
        self.text_resultat.delete(1.0, tk.END)
        
        # Affichage formaté
        self.text_resultat.insert(tk.END, "📄 ", 'titre')
        self.text_resultat.insert(tk.END, resultat["nom"] + "\n\n", 'titre')
        
        self.ajouter_ligne("Chemin", resultat["chemin"])
        self.ajouter_ligne("Extension", resultat["extension"])
        self.ajouter_ligne("Type", resultat.get("type_specifique", resultat["type"]))
        self.ajouter_ligne("Taille", f"{resultat['taille_octets']:,} octets")
        
        if "erreur" in resultat:
            self.text_resultat.insert(tk.END, "\n❌ Erreur: ", 'erreur')
            self.text_resultat.insert(tk.END, resultat["erreur"] + "\n", 'erreur')
        else:
            self.text_resultat.insert(tk.END, "\n📊 STATISTIQUES\n", 'stats')
            self.text_resultat.insert(tk.END, "─" * 40 + "\n", 'stats')
            self.ajouter_ligne("Lignes", str(resultat.get("nb_lignes", 0)))
            self.ajouter_ligne("Mots", str(resultat.get("nb_mots", 0)))
            self.ajouter_ligne("Caractères", str(resultat.get("nb_caracteres", 0)))
            
            # Infos spécifiques Python
            if resultat.get("type_specifique") == "Python":
                self.text_resultat.insert(tk.END, "\n🐍 PYTHON\n", 'stats')
                self.text_resultat.insert(tk.END, "─" * 40 + "\n", 'stats')
                self.ajouter_ligne("Fonctions", str(resultat.get("fonctions", 0)))
                self.ajouter_ligne("Classes", str(resultat.get("classes", 0)))
                self.ajouter_ligne("Imports", str(resultat.get("imports", 0)))
            
            # Infos spécifiques JSON
            if resultat.get("json_valide"):
                self.text_resultat.insert(tk.END, "\n✅ JSON VALIDE\n", 'stats')
                self.text_resultat.insert(tk.END, "─" * 40 + "\n", 'stats')
                if "cles_json" in resultat:
                    self.ajouter_ligne("Clés", ", ".join(resultat["cles_json"][:5]))
                if "nb_elements_json" in resultat:
                    self.ajouter_ligne("Éléments", str(resultat["nb_elements_json"]))
            elif "erreur_json" in resultat:
                self.text_resultat.insert(tk.END, "\n❌ JSON INVALIDE\n", 'erreur')
                self.text_resultat.insert(tk.END, resultat["erreur_json"] + "\n", 'erreur')
            
            # Infos spécifiques CSV
            if "nb_lignes_csv" in resultat:
                self.text_resultat.insert(tk.END, "\n📋 CSV\n", 'stats')
                self.text_resultat.insert(tk.END, "─" * 40 + "\n", 'stats')
                self.ajouter_ligne("Lignes", str(resultat["nb_lignes_csv"]))
                self.ajouter_ligne("Colonnes", str(resultat.get("nb_colonnes_csv", 0)))
                if "colonnes" in resultat:
                    self.ajouter_ligne("En-têtes", ", ".join(resultat["colonnes"][:5]))
            
            # Mots les plus fréquents
            if resultat.get("mots_frequents"):
                self.text_resultat.insert(tk.END, "\n🔤 MOTS FRÉQUENTS\n", 'stats')
                self.text_resultat.insert(tk.END, "─" * 40 + "\n", 'stats')
                for mot, nombre in resultat["mots_frequents"]:
                    self.ajouter_ligne(mot, f"{nombre} fois")
        
        self.text_resultat.config(state=tk.DISABLED)
    
    def ajouter_ligne(self, cle, valeur):
        """Ajoute une ligne formatée cle: valeur"""
        self.text_resultat.insert(tk.END, cle + ": ", 'cle')
        self.text_resultat.insert(tk.END, str(valeur) + "\n", 'valeur')
    
    def effacer_tout(self):
        """Efface tous les fichiers et résultats"""
        self.fichiers_selectionnes.clear()
        self.resultats.clear()
        self.listbox.delete(0, tk.END)
        self.text_resultat.config(state=tk.NORMAL)
        self.text_resultat.delete(1.0, tk.END)
        self.text_resultat.config(state=tk.DISABLED)


if __name__ == "__main__":
    root = tk.Tk()
    app = AnalyseurFichiers(root)
    root.mainloop()
