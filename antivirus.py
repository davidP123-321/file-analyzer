import os
import re
import json
import csv
import hashlib
from collections import Counter
import tkinter as tk
from tkinter import filedialog, messagebox, ttk
from threading import Thread
import time

# Signatures de virus connues (simulé pour demo)
VIRUS_SIGNATURES = {
    "eval(": "Exécution de code dangereuse",
    "exec(": "Exécution de code dangereuse",
    "__import__": "Import dynamique suspect",
    "os.system": "Commande système dangereuse",
    "subprocess": "Exécution de processus",
    "open(": "Accès fichier",
    "requests": "Connexion réseau",
    "socket": "Socket réseau",
    "base64.b64decode": "Décodage suspect",
}

MOTS_CLES_DANGEREUX = [
    "malware", "trojan", "ransomware", "backdoor", "worm",
    "virus", "exploit", "payload", "shellcode", "injection"
]

class AntivirusScanner:
    def __init__(self, root):
        self.root = root
        self.root.title("🛡️ Antivirus Scanner v1.0")
        self.root.geometry("1100x750")
        self.root.resizable(True, True)
        
        self.fichiers_scannés = []
        self.resultats = {}
        self.menaces_detectées = 0
        self.fichiers_sains = 0
        self.en_cours_scan = False
        
        self.creer_interface()
    
    def creer_interface(self):
        # Barre de titre avec logo
        header = tk.Frame(self.root, bg="#1e1e2e", height=60)
        header.pack(fill=tk.X)
        
        titre = tk.Label(header, text="🛡️ ANTIVIRUS SCANNER v1.0", 
                         font=("Arial", 18, "bold"), bg="#1e1e2e", fg="#00ff00")
        titre.pack(pady=10)
        
        # Barre de boutons
        toolbar = tk.Frame(self.root, bg="#2a2a3e", height=50)
        toolbar.pack(fill=tk.X)
        
        btn_scan_fichier = tk.Button(toolbar, text="📁 Scanner fichier", 
                                     command=self.scanner_fichier, 
                                     bg="#ff4444", fg="white", font=("Arial", 10, "bold"),
                                     padx=10, pady=5)
        btn_scan_fichier.pack(side=tk.LEFT, padx=10, pady=10)
        
        btn_scan_dossier = tk.Button(toolbar, text="📂 Scanner dossier", 
                                     command=self.scanner_dossier,
                                     bg="#ff4444", fg="white", font=("Arial", 10, "bold"),
                                     padx=10, pady=5)
        btn_scan_dossier.pack(side=tk.LEFT, padx=10, pady=10)
        
        btn_nettoyer = tk.Button(toolbar, text="🧹 Nettoyer", 
                                command=self.nettoyer,
                                bg="#ffaa00", fg="white", font=("Arial", 10, "bold"),
                                padx=10, pady=5)
        btn_nettoyer.pack(side=tk.LEFT, padx=10, pady=10)
        
        btn_effacer = tk.Button(toolbar, text="❌ Effacer rapport", 
                               command=self.effacer_tout,
                               bg="#666666", fg="white", font=("Arial", 10, "bold"),
                               padx=10, pady=5)
        btn_effacer.pack(side=tk.LEFT, padx=10, pady=10)
        
        # Barre de progression
        self.progress = ttk.Progressbar(self.root, mode='determinate', length=1000)
        self.progress.pack(fill=tk.X, padx=10, pady=5)
        
        # Statut
        self.label_statut = tk.Label(self.root, text="Prêt à scanner", 
                                    font=("Arial", 10), bg="#f0f0f0")
        self.label_statut.pack(fill=tk.X, padx=10, pady=5)
        
        # Séparateur
        ttk.Separator(self.root, orient=tk.HORIZONTAL).pack(fill=tk.X)
        
        # Panneau principal avec 2 colonnes
        main_frame = tk.Frame(self.root)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # --- COLONNE GAUCHE: Liste des fichiers ---
        left_frame = tk.Frame(main_frame, bg="#f5f5f5", relief=tk.SUNKEN, bd=1)
        left_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=False, padx=(0, 10))
        
        tk.Label(left_frame, text="📋 Fichiers scannés", 
                font=("Arial", 12, "bold"), bg="#f5f5f5").pack(anchor=tk.W, padx=5, pady=5)
        
        scrollbar = ttk.Scrollbar(left_frame)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        self.listbox = tk.Listbox(
            left_frame,
            width=35,
            height=28,
            yscrollcommand=scrollbar.set,
            font=("Courier", 8),
            bg="white"
        )
        self.listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=5, pady=5)
        self.listbox.bind("<<ListboxSelect>>", self.afficher_details)
        scrollbar.config(command=self.listbox.yview)
        
        # --- COLONNE DROITE: Détails du scan ---
        right_frame = tk.Frame(main_frame, bg="#f5f5f5", relief=tk.SUNKEN, bd=1)
        right_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        tk.Label(right_frame, text="🔍 Résultats du scan", 
                font=("Arial", 12, "bold"), bg="#f5f5f5").pack(anchor=tk.W, padx=5, pady=5)
        
        scrollbar_text = ttk.Scrollbar(right_frame)
        scrollbar_text.pack(side=tk.RIGHT, fill=tk.Y)
        
        self.text_resultat = tk.Text(
            right_frame,
            height=28,
            width=70,
            yscrollcommand=scrollbar_text.set,
            font=("Courier", 9),
            bg="#1e1e2e",
            fg="#00ff00",
            wrap=tk.WORD,
            padx=10,
            pady=10
        )
        self.text_resultat.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        scrollbar_text.config(command=self.text_resultat.yview)
        
        # Tags pour coloration
        self.text_resultat.tag_config("titre", font=("Courier", 11, "bold"), foreground="#00ff00")
        self.text_resultat.tag_config("sain", foreground="#00ff00")
        self.text_resultat.tag_config("risque", foreground="#ffaa00")
        self.text_resultat.tag_config("malveillant", foreground="#ff4444")
        self.text_resultat.tag_config("info", foreground="#00ddff")
        self.text_resultat.tag_config("chemin", foreground="#ffffff")
    
    def scanner_fichier(self):
        fichiers = filedialog.askopenfilenames(
            title="Sélectionner des fichiers à scanner",
            filetypes=[("Tous les fichiers", "*.*")]
        )
        if fichiers:
            self.fichiers_scannés = list(fichiers)
            self.mettre_a_jour_listbox()
            self.lancer_scan()
    
    def scanner_dossier(self):
        dossier = filedialog.askdirectory(title="Sélectionner un dossier")
        if dossier:
            fichiers = []
            for root, dirs, files in os.walk(dossier):
                for file in files:
                    fichiers.append(os.path.join(root, file))
            
            if fichiers:
                self.fichiers_scannés = fichiers[:100]  # Limiter à 100 fichiers
                self.mettre_a_jour_listbox()
                self.lancer_scan()
            else:
                messagebox.showwarning("Attention", "Aucun fichier trouvé.")
    
    def mettre_a_jour_listbox(self):
        self.listbox.delete(0, tk.END)
        for fichier in self.fichiers_scannés:
            nom = os.path.basename(fichier)
            self.listbox.insert(tk.END, nom)
    
    def lancer_scan(self):
        if self.en_cours_scan:
            return
        
        self.en_cours_scan = True
        self.menaces_detectées = 0
        self.fichiers_sains = 0
        self.resultats.clear()
        
        def scanner():
            nb_fichiers = len(self.fichiers_scannés)
            for i, fichier in enumerate(self.fichiers_scannés):
                self.label_statut.config(text=f"Scan en cours... {i+1}/{nb_fichiers}")
                self.progress["value"] = (i / nb_fichiers) * 100
                self.root.update()
                
                self.resultats[fichier] = self.analyser_fichier(fichier)
                time.sleep(0.1)  # Simulation du temps de scan
            
            self.progress["value"] = 100
            self.label_statut.config(text=f"Scan terminé ! {self.menaces_detectées} menace(s) - {self.fichiers_sains} fichier(s) sain(s)")
            self.en_cours_scan = False
            messagebox.showinfo("Scan terminé", 
                              f"Menaces détectées: {self.menaces_detectées}\nFichiers sains: {self.fichiers_sains}")
        
        thread = Thread(target=scanner, daemon=True)
        thread.start()
    
    def analyser_fichier(self, chemin):
        resultat = {
            "nom": os.path.basename(chemin),
            "chemin": chemin,
            "extension": os.path.splitext(chemin)[1].lower(),
            "taille": os.path.getsize(chemin),
            "menaces": [],
            "score_risque": 0
        }
        
        # Calculer le hash
        try:
            with open(chemin, "rb") as f:
                resultat["hash"] = hashlib.md5(f.read()).hexdigest()
        except:
            resultat["hash"] = "N/A"
        
        # Lire le fichier
        try:
            with open(chemin, "r", encoding="utf-8", errors="ignore") as f:
                contenu = f.read()
            resultat["type"] = "texte"
        except:
            resultat["type"] = "binaire"
            resultat["statut"] = "⚠️ SUSPECT"
            resultat["menaces"].append("Fichier binaire (non scannable)")
            resultat["score_risque"] = 30
            return resultat
        
        # Vérifier les signatures de virus
        for signature, description in VIRUS_SIGNATURES.items():
            if signature in contenu:
                resultat["menaces"].append(f"Signature trouvée: {description}")
                resultat["score_risque"] += 40
        
        # Vérifier les mots-clés dangereux
        contenu_lower = contenu.lower()
        for mot in MOTS_CLES_DANGEREUX:
            if mot in contenu_lower:
                resultat["menaces"].append(f"Mot-clé dangereux: {mot}")
                resultat["score_risque"] += 20
        
        # Déterminer le statut
        if resultat["score_risque"] >= 60:
            resultat["statut"] = "🔴 MALVEILLANT"
            self.menaces_detectées += 1
        elif resultat["score_risque"] >= 30:
            resultat["statut"] = "🟠 RISQUE"
            self.menaces_detectées += 1
        else:
            resultat["statut"] = "🟢 SAIN"
            self.fichiers_sains += 1
        
        return resultat
    
    def afficher_details(self, event):
        selection = self.listbox.curselection()
        if not selection:
            return
        
        fichier = self.fichiers_scannés[selection[0]]
        if fichier not in self.resultats:
            return
        
        resultat = self.resultats[fichier]
        self.text_resultat.config(state=tk.NORMAL)
        self.text_resultat.delete(1.0, tk.END)
        
        # Affichage du rapport
        self.text_resultat.insert(tk.END, "═" * 70 + "\n", "titre")
        self.text_resultat.insert(tk.END, resultat["statut"] + " " + resultat["nom"] + "\n", "titre")
        self.text_resultat.insert(tk.END, "═" * 70 + "\n\n", "titre")
        
        # Infos générales
        self.ajouter_ligne_rapport("Chemin", resultat["chemin"], "chemin")
        self.ajouter_ligne_rapport("Extension", resultat["extension"], "info")
        self.ajouter_ligne_rapport("Taille", f"{resultat['taille']} octets", "info")
        self.ajouter_ligne_rapport("Type", resultat["type"], "info")
        self.ajouter_ligne_rapport("Hash MD5", resultat["hash"], "info")
        
        # Score de risque
        self.text_resultat.insert(tk.END, "\n" + "─" * 70 + "\n", "titre")
        self.text_resultat.insert(tk.END, "SCORE DE RISQUE: ", "titre")
        
        if resultat["score_risque"] >= 60:
            tag = "malveillant"
        elif resultat["score_risque"] >= 30:
            tag = "risque"
        else:
            tag = "sain"
        
        self.text_resultat.insert(tk.END, f"{resultat['score_risque']}/100\n", tag)
        self.text_resultat.insert(tk.END, "─" * 70 + "\n", "titre")
        
        # Menaces détectées
        if resultat["menaces"]:
            self.text_resultat.insert(tk.END, "\n⚠️ MENACES DÉTECTÉES:\n", "malveillant")
            for i, menace in enumerate(resultat["menaces"], 1):
                self.text_resultat.insert(tk.END, f"  {i}. {menace}\n", "malveillant")
        else:
            self.text_resultat.insert(tk.END, "\n✅ AUCUNE MENACE DÉTECTÉE\n", "sain")
        
        self.text_resultat.insert(tk.END, "\n" + "─" * 70 + "\n", "titre")
        self.text_resultat.insert(tk.END, "Scan effectué le: " + 
                                 time.strftime("%Y-%m-%d %H:%M:%S") + "\n", "info")
        
        self.text_resultat.config(state=tk.DISABLED)
    
    def ajouter_ligne_rapport(self, cle, valeur, tag="info"):
        self.text_resultat.insert(tk.END, cle + ": ", "titre")
        self.text_resultat.insert(tk.END, str(valeur) + "\n", tag)
    
    def nettoyer(self):
        if messagebox.askyesno("Confirmation", "Êtes-vous sûr de vouloir supprimer les fichiers malveillants ?"):
            count = 0
            for fichier, resultat in self.resultats.items():
                if resultat["score_risque"] >= 60:
                    try:
                        os.remove(fichier)
                        count += 1
                    except:
                        pass
            messagebox.showinfo("Nettoyage", f"{count} fichier(s) supprimé(s)")
    
    def effacer_tout(self):
        self.fichiers_scannés.clear()
        self.resultats.clear()
        self.menaces_detectées = 0
        self.fichiers_sains = 0
        self.listbox.delete(0, tk.END)
        self.text_resultat.config(state=tk.NORMAL)
        self.text_resultat.delete(1.0, tk.END)
        self.text_resultat.config(state=tk.DISABLED)
        self.progress["value"] = 0
        self.label_statut.config(text="Prêt à scanner")


if __name__ == "__main__":
    root = tk.Tk()
    app = AntivirusScanner(root)
    root.mainloop()
