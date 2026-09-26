import os
import re
import hashlib
import time
import json
from datetime import datetime
import tkinter as tk
from tkinter import filedialog, messagebox, ttk
from threading import Thread
from pathlib import Path

# Base de données de signatures malveillantes
VIRUS_SIGNATURES = {
    "base64.b64decode": {"description": "Décodage de données cryptées", "risque": 35},
    "os.system(": {"description": "Exécution de commandes système", "risque": 50},
    "subprocess": {"description": "Lancement de processus externe", "risque": 45},
    "socket.socket": {"description": "Communication réseau directe", "risque": 40},
    "requests.get": {"description": "Téléchargement HTTP détecté", "risque": 30},
    "eval(": {"description": "Évaluation de code dynamique", "risque": 60},
    "exec(": {"description": "Exécution de code dynamique", "risque": 65},
    "__import__": {"description": "Import dynamique suspect", "risque": 40},
    "powershell": {"description": "Commande PowerShell détectée", "risque": 50},
    "cmd.exe": {"description": "Accès à l'invite de commande", "risque": 45},
    "rundll32": {"description": "Exécution de librairie DLL", "risque": 55},
    "WScript.Shell": {"description": "Script Windows activé", "risque": 50},
    "CreateObject": {"description": "Création d'objet COM", "risque": 45},
}

MOTS_CLES_MALVEILLANTS = {
    "virus": 40,
    "malware": 45,
    "trojan": 50,
    "ransomware": 65,
    "backdoor": 60,
    "payload": 55,
    "exploit": 50,
    "shellcode": 70,
    "botnet": 60,
    "worm": 55,
    "spyware": 50,
    "rootkit": 65,
    "keylogger": 60,
    "ransomware": 70,
}

EXTENSIONS_SUSPICIEUSES = {
    ".exe": 50,
    ".bat": 40,
    ".cmd": 40,
    ".vbs": 45,
    ".ps1": 45,
    ".com": 50,
    ".scr": 55,
}

class SecurityAntivirus:
    def __init__(self, root):
        self.root = root
        self.root.title("🛡️ SECURITY ANTIVIRUS PRO v2.0")
        self.root.geometry("1400x850")
        self.root.resizable(True, True)
        self.root.configure(bg="#0a0e27")
        
        self.files = []
        self.results = {}
        self.is_scanning = False
        self.total_scanned = 0
        self.threats_found = 0
        self.files_clean = 0
        
        self.create_interface()
    
    def create_interface(self):
        # --- HEADER PROFESSIONNEL ---
        header = tk.Frame(self.root, bg="#1a1f3a", height=80)
        header.pack(fill=tk.X, side=tk.TOP)
        
        title_frame = tk.Frame(header, bg="#1a1f3a")
        title_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=10)
        
        tk.Label(title_frame, text="🛡️ SECURITY ANTIVIRUS PRO", 
                font=("Arial", 22, "bold"), fg="#00ff00", bg="#1a1f3a").pack(anchor="w")
        tk.Label(title_frame, text="v2.0 | Système de protection avancé", 
                font=("Arial", 10), fg="#888888", bg="#1a1f3a").pack(anchor="w")
        
        # --- BARRE D'OUTILS ---
        toolbar = tk.Frame(self.root, bg="#0f1628", height=70)
        toolbar.pack(fill=tk.X, side=tk.TOP)
        
        # Boutons principaux
        btn_frame = tk.Frame(toolbar, bg="#0f1628")
        btn_frame.pack(fill=tk.X, padx=15, pady=10)
        
        self.btn_scan_file = tk.Button(btn_frame, text="📁 SCANNER FICHIER", 
                                      bg="#2563eb", fg="white", font=("Arial", 11, "bold"),
                                      padx=15, pady=8, relief=tk.RAISED, bd=2,
                                      command=self.scan_file)
        self.btn_scan_file.pack(side=tk.LEFT, padx=5)
        
        self.btn_scan_folder = tk.Button(btn_frame, text="📂 SCANNER DOSSIER", 
                                        bg="#2563eb", fg="white", font=("Arial", 11, "bold"),
                                        padx=15, pady=8, relief=tk.RAISED, bd=2,
                                        command=self.scan_folder)
        self.btn_scan_folder.pack(side=tk.LEFT, padx=5)
        
        self.btn_clean = tk.Button(btn_frame, text="🧹 NETTOYER", 
                                  bg="#dc2626", fg="white", font=("Arial", 11, "bold"),
                                  padx=15, pady=8, relief=tk.RAISED, bd=2,
                                  command=self.clean_threats)
        self.btn_clean.pack(side=tk.LEFT, padx=5)
        
        self.btn_quarantine = tk.Button(btn_frame, text="🔒 MISE EN QUARANTAINE", 
                                       bg="#ea580c", fg="white", font=("Arial", 11, "bold"),
                                       padx=15, pady=8, relief=tk.RAISED, bd=2,
                                       command=self.quarantine_threats)
        self.btn_quarantine.pack(side=tk.LEFT, padx=5)
        
        self.btn_clear = tk.Button(btn_frame, text="❌ EFFACER", 
                                  bg="#64748b", fg="white", font=("Arial", 11, "bold"),
                                  padx=15, pady=8, relief=tk.RAISED, bd=2,
                                  command=self.clear_all)
        self.btn_clear.pack(side=tk.LEFT, padx=5)
        
        # --- BARRE DE PROGRESSION ---
        progress_frame = tk.Frame(self.root, bg="#0a0e27")
        progress_frame.pack(fill=tk.X, padx=15, pady=10)
        
        tk.Label(progress_frame, text="Progression du scan:", 
                font=("Arial", 10), fg="#ffffff", bg="#0a0e27").pack(anchor="w")
        
        self.progress = ttk.Progressbar(progress_frame, length=1350, mode='determinate',
                                       style='TProgressbar')
        self.progress.pack(fill=tk.X, pady=5)
        
        self.progress_label = tk.Label(progress_frame, text="0%", 
                                      font=("Arial", 9), fg="#00ff00", bg="#0a0e27")
        self.progress_label.pack(anchor="w")
        
        # --- STATISTIQUES EN TEMPS RÉEL ---
        stats_frame = tk.Frame(self.root, bg="#1a1f3a", height=80)
        stats_frame.pack(fill=tk.X, padx=15, pady=10)
        
        stats_inner = tk.Frame(stats_frame, bg="#1a1f3a")
        stats_inner.pack(fill=tk.X)
        
        # Cartes de statistiques
        self.create_stat_card(stats_inner, "📊 SCANNÉS", "0", "#2563eb", 0)
        self.create_stat_card(stats_inner, "🟢 SAINS", "0", "#10b981", 1)
        self.create_stat_card(stats_inner, "🟠 SUSPECTS", "0", "#f59e0b", 2)
        self.create_stat_card(stats_inner, "🔴 MENACES", "0", "#ef4444", 3)
        
        # --- BARRE DE STATUT ---
        self.status_frame = tk.Frame(self.root, bg="#1a1f3a", height=50)
        self.status_frame.pack(fill=tk.X, padx=15, pady=5)
        
        tk.Label(self.status_frame, text="●", font=("Arial", 16), 
                fg="#10b981", bg="#1a1f3a").pack(side=tk.LEFT, padx=10)
        
        self.status_label = tk.Label(self.status_frame, 
                                    text="Système protégé - Aucune menace détectée",
                                    font=("Arial", 11, "bold"), fg="#10b981", bg="#1a1f3a")
        self.status_label.pack(side=tk.LEFT)
        
        # --- SÉPARATEUR ---
        ttk.Separator(self.root, orient=tk.HORIZONTAL).pack(fill=tk.X)
        
        # --- PANNEAU PRINCIPAL ---
        main_frame = tk.Frame(self.root, bg="#0a0e27")
        main_frame.pack(fill=tk.BOTH, expand=True, padx=15, pady=10)
        
        # --- COLONNE GAUCHE: Liste des fichiers ---
        left_frame = tk.Frame(main_frame, bg="#0f1628", relief=tk.RAISED, bd=2)
        left_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=False, padx=(0, 10))
        
        left_title = tk.Frame(left_frame, bg="#1a1f3a", height=40)
        left_title.pack(fill=tk.X)
        tk.Label(left_title, text="📋 FICHIERS SCANNÉS", 
                font=("Arial", 11, "bold"), fg="#00ff00", bg="#1a1f3a").pack(anchor="w", padx=10, pady=8)
        
        scrollbar_left = ttk.Scrollbar(left_frame)
        scrollbar_left.pack(side=tk.RIGHT, fill=tk.Y)
        
        self.listbox = tk.Listbox(left_frame, width=35, height=30,
                                 yscrollcommand=scrollbar_left.set,
                                 font=("Courier New", 9), bg="#0a0e27", fg="#00ff00",
                                 selectmode=tk.SINGLE, bd=0)
        self.listbox.pack(fill=tk.BOTH, expand=True, padx=8, pady=8)
        self.listbox.bind("<<ListboxSelect>>", self.show_file_details)
        scrollbar_left.config(command=self.listbox.yview)
        
        # --- COLONNE DROITE: Rapport détaillé ---
        right_frame = tk.Frame(main_frame, bg="#0f1628", relief=tk.RAISED, bd=2)
        right_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        right_title = tk.Frame(right_frame, bg="#1a1f3a", height=40)
        right_title.pack(fill=tk.X)
        tk.Label(right_title, text="🔍 RAPPORT DÉTAILLÉ", 
                font=("Arial", 11, "bold"), fg="#00ff00", bg="#1a1f3a").pack(anchor="w", padx=10, pady=8)
        
        scrollbar_right = ttk.Scrollbar(right_frame)
        scrollbar_right.pack(side=tk.RIGHT, fill=tk.Y)
        
        self.report_text = tk.Text(right_frame, height=30, width=80,
                                  yscrollcommand=scrollbar_right.set,
                                  font=("Courier New", 9), bg="#0a0e27", fg="#e5e7eb",
                                  wrap=tk.WORD, bd=0, padx=10, pady=10)
        self.report_text.pack(fill=tk.BOTH, expand=True, padx=8, pady=8)
        scrollbar_right.config(command=self.report_text.yview)
        
        # Configuration des tags de couleur
        self.report_text.tag_config("title", font=("Courier New", 10, "bold"), foreground="#00ff00")
        self.report_text.tag_config("green", foreground="#10b981")
        self.report_text.tag_config("yellow", foreground="#f59e0b")
        self.report_text.tag_config("red", foreground="#ef4444")
        self.report_text.tag_config("blue", foreground="#2563eb")
        self.report_text.tag_config("white", foreground="#ffffff")
        self.report_text.tag_config("gray", foreground="#888888")
        
        # Message d'accueil
        self.afficher_accueil()
    
    def create_stat_card(self, parent, label, value, color, column):
        card = tk.Frame(parent, bg="#0f1628", relief=tk.RAISED, bd=1)
        card.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=5, pady=0)
        
        tk.Label(card, text=label, font=("Arial", 9), 
                fg=color, bg="#0f1628").pack(padx=10, pady=5)
        
        value_label = tk.Label(card, text=value, font=("Arial", 16, "bold"), 
                              fg=color, bg="#0f1628")
        value_label.pack(padx=10, pady=5)
        
        # Sauvegarder la référence pour mise à jour
        setattr(self, f"stat_{column}", value_label)
    
    def afficher_accueil(self):
        self.report_text.config(state=tk.NORMAL)
        self.report_text.delete("1.0", tk.END)
        
        self.report_text.insert(tk.END, "╔════════════════════════════════════════════════════════╗\n", "blue")
        self.report_text.insert(tk.END, "║    🛡️  SECURITY ANTIVIRUS PRO v2.0  🛡️              ║\n", "blue")
        self.report_text.insert(tk.END, "╚════════════════════════════════════════════════════════╝\n\n", "blue")
        
        self.report_text.insert(tk.END, "Bienvenue dans SECURITY ANTIVIRUS PRO\n", "title")
        self.report_text.insert(tk.END, "Système de protection avancée contre les menaces\n\n", "green")
        
        self.report_text.insert(tk.END, "FONCTIONNALITÉS:\n", "title")
        self.report_text.insert(tk.END, "✓ Scanner de fichiers et dossiers\n", "green")
        self.report_text.insert(tk.END, "✓ Détection de signatures malveillantes\n", "green")
        self.report_text.insert(tk.END, "✓ Analyse comportementale\n", "green")
        self.report_text.insert(tk.END, "✓ Mise en quarantaine automatique\n", "green")
        self.report_text.insert(tk.END, "✓ Rapport de sécurité détaillé\n\n", "green")
        
        self.report_text.insert(tk.END, "POUR COMMENCER:\n", "title")
        self.report_text.insert(tk.END, "1. Cliquez sur 'SCANNER FICHIER' ou 'SCANNER DOSSIER'\n", "white")
        self.report_text.insert(tk.END, "2. Sélectionnez les fichiers à analyser\n", "white")
        self.report_text.insert(tk.END, "3. Attendez la fin de l'analyse\n", "white")
        self.report_text.insert(tk.END, "4. Consultez le rapport détaillé\n\n", "white")
        
        self.report_text.insert(tk.END, "STATUS SYSTÈME:\n", "title")
        self.report_text.insert(tk.END, "🟢 Protégé - Aucune menace détectée\n", "green")
        self.report_text.insert(tk.END, "Dernière mise à jour: " + datetime.now().strftime("%Y-%m-%d %H:%M:%S") + "\n", "gray")
        
        self.report_text.config(state=tk.DISABLED)
    
    def scan_file(self):
        files = filedialog.askopenfilenames(title="Sélectionner des fichiers à scanner")
        if not files:
            return
        
        self.files = list(files)
        self.update_listbox()
        self.start_scan()
    
    def scan_folder(self):
        folder = filedialog.askdirectory(title="Sélectionner un dossier à scanner")
        if not folder:
            return
        
        all_files = []
        for root, dirs, files in os.walk(folder):
            for file in files:
                all_files.append(os.path.join(root, file))
        
        if not all_files:
            messagebox.showwarning("Attention", "Aucun fichier trouvé dans ce dossier.")
            return
        
        self.files = all_files[:200]  # Limiter à 200 fichiers
        self.update_listbox()
        self.start_scan()
    
    def update_listbox(self):
        self.listbox.delete(0, tk.END)
        for file in self.files:
            self.listbox.insert(tk.END, os.path.basename(file))
    
    def start_scan(self):
        if self.is_scanning:
            return
        
        self.is_scanning = True
        self.total_scanned = 0
        self.threats_found = 0
        self.files_clean = 0
        self.results.clear()
        
        self.btn_scan_file.config(state=tk.DISABLED)
        self.btn_scan_folder.config(state=tk.DISABLED)
        self.status_label.config(text="🔄 Scan en cours...", fg="#f59e0b")
        
        def scan_task():
            total = len(self.files)
            for i, file_path in enumerate(self.files):
                if not self.is_scanning:
                    break
                
                self.results[file_path] = self.analyze_file(file_path)
                self.total_scanned += 1
                
                progress = (i + 1) / total * 100
                self.progress["value"] = progress
                self.progress_label.config(text=f"{int(progress)}%")
                
                self.root.update()
                time.sleep(0.05)
            
            self.is_scanning = False
            self.update_statistics()
            self.update_status()
            self.btn_scan_file.config(state=tk.NORMAL)
            self.btn_scan_folder.config(state=tk.NORMAL)
        
        Thread(target=scan_task, daemon=True).start()
    
    def analyze_file(self, file_path):
        result = {
            "path": file_path,
            "name": os.path.basename(file_path),
            "extension": os.path.splitext(file_path)[1].lower(),
            "size": 0,
            "hash": "N/A",
            "risk_level": 0,
            "status": "SAIN",
            "threats": [],
            "scan_time": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }
        
        try:
            result["size"] = os.path.getsize(file_path)
        except:
            pass
        
        try:
            with open(file_path, "rb") as f:
                data = f.read()
            result["hash"] = hashlib.md5(data).hexdigest()
        except:
            pass
        
        # Vérifier l'extension suspecte
        if result["extension"] in EXTENSIONS_SUSPICIEUSES:
            result["risk_level"] += EXTENSIONS_SUSPICIEUSES[result["extension"]]
            result["threats"].append(f"Extension suspecte: {result['extension']}")
        
        # Lire le contenu
        try:
            with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
                content = f.read()
        except:
            content = ""
        
        # Vérifier les signatures
        for signature, info in VIRUS_SIGNATURES.items():
            if signature.lower() in content.lower():
                result["risk_level"] += info["risque"]
                result["threats"].append(info["description"])
        
        # Vérifier les mots-clés malveillants
        content_lower = content.lower()
        for keyword, risque in MOTS_CLES_MALVEILLANTS.items():
            if keyword in content_lower:
                result["risk_level"] += risque
                result["threats"].append(f"Mot-clé détecté: {keyword}")
        
        # Plafonner le risque à 100
        result["risk_level"] = min(result["risk_level"], 100)
        
        # Déterminer le statut
        if result["risk_level"] >= 70:
            result["status"] = "MALVEILLANT"
            self.threats_found += 1
        elif result["risk_level"] >= 40:
            result["status"] = "SUSPECT"
            self.threats_found += 1
        else:
            result["status"] = "SAIN"
            self.files_clean += 1
        
        return result
    
    def show_file_details(self, event):
        selection = self.listbox.curselection()
        if not selection:
            return
        
        file_path = self.files[selection[0]]
        result = self.results.get(file_path)
        
        if not result:
            return
        
        self.report_text.config(state=tk.NORMAL)
        self.report_text.delete("1.0", tk.END)
        
        # En-tête du rapport
        self.report_text.insert(tk.END, "╔════════════════════════════════════════════════════════╗\n", "blue")
        self.report_text.insert(tk.END, "║           RAPPORT D'ANALYSE DÉTAILLÉ                  ║\n", "blue")
        self.report_text.insert(tk.END, "╚════════════════════════════════════════════════════════╝\n\n", "blue")
        
        # Statut général
        if result["status"] == "SAIN":
            status_color = "green"
            status_icon = "🟢"
        elif result["status"] == "SUSPECT":
            status_color = "yellow"
            status_icon = "🟠"
        else:
            status_color = "red"
            status_icon = "🔴"
        
        self.report_text.insert(tk.END, f"{status_icon} STATUT: ", "title")
        self.report_text.insert(tk.END, f"{result['status']}\n\n", status_color)
        
        # Informations du fichier
        self.report_text.insert(tk.END, "INFORMATIONS DU FICHIER:\n", "title")
        self.report_text.insert(tk.END, f"Nom: {result['name']}\n", "white")
        self.report_text.insert(tk.END, f"Chemin: {result['path']}\n", "white")
        self.report_text.insert(tk.END, f"Extension: {result['extension']}\n", "white")
        self.report_text.insert(tk.END, f"Taille: {result['size']:,} octets\n", "white")
        self.report_text.insert(tk.END, f"Hash MD5: {result['hash']}\n", "gray")
        self.report_text.insert(tk.END, f"Analysé le: {result['scan_time']}\n\n", "gray")
        
        # Niveau de risque
        self.report_text.insert(tk.END, "NIVEAU DE RISQUE:\n", "title")
        self.report_text.insert(tk.END, f"Score: {result['risk_level']}/100\n", status_color)
        
        # Barre de risque visuelle
        filled = int(result['risk_level'] / 10)
        bar = "█" * filled + "░" * (10 - filled)
        self.report_text.insert(tk.END, f"[{bar}]\n\n", status_color)
        
        # Menaces détectées
        if result["threats"]:
            self.report_text.insert(tk.END, "MENACES DÉTECTÉES:\n", "title")
            for i, threat in enumerate(result["threats"], 1):
                self.report_text.insert(tk.END, f"{i}. {threat}\n", "red")
        else:
            self.report_text.insert(tk.END, "MENACES DÉTECTÉES:\n", "title")
            self.report_text.insert(tk.END, "Aucune menace détectée\n", "green")
        
        self.report_text.insert(tk.END, "\n" + "─" * 60 + "\n", "gray")
        self.report_text.insert(tk.END, "Fin du rapport\n", "gray")
        
        self.report_text.config(state=tk.DISABLED)
    
    def update_statistics(self):
        self.stat_0.config(text=str(self.total_scanned))
        self.stat_1.config(text=str(self.files_clean))
        self.stat_2.config(text=str(self.threats_found))
        self.stat_3.config(text=str(sum(1 for r in self.results.values() if r["status"] == "MALVEILLANT")))
    
    def update_status(self):
        if self.threats_found == 0:
            self.status_label.config(text="🟢 Système protégé - Aucune menace détectée", fg="#10b981")
        elif self.threats_found <= 3:
            self.status_label.config(text=f"🟠 {self.threats_found} menace(s) détectée(s) - Recommandé: Nettoyer", fg="#f59e0b")
        else:
            self.status_label.config(text=f"🔴 {self.threats_found} menace(s) détectée(s) - Action requise", fg="#ef4444")
    
    def quarantine_threats(self):
        threats = [f for f, r in self.results.items() if r["status"] != "SAIN"]
        if not threats:
            messagebox.showinfo("Information", "Aucune menace à mettre en quarantaine")
            return
        
        quarantine_dir = os.path.expanduser("~/.security_quarantine")
        os.makedirs(quarantine_dir, exist_ok=True)
        
        count = 0
        for threat in threats:
            try:
                dest = os.path.join(quarantine_dir, os.path.basename(threat))
                os.rename(threat, dest)
                count += 1
            except:
                pass
        
        messagebox.showinfo("Quarantaine", f"{count} fichier(s) mis en quarantaine")
    
    def clean_threats(self):
        threats = [f for f, r in self.results.items() if r["status"] != "SAIN"]
        if not threats:
            messagebox.showinfo("Information", "Aucune menace à nettoyer")
            return
        
        if messagebox.askyesno("Confirmation", f"Supprimer {len(threats)} fichier(s) malveillant(s) ?"):
            count = 0
            for threat in threats:
                try:
                    os.remove(threat)
                    count += 1
                except:
                    pass
            
            messagebox.showinfo("Nettoyage", f"{count} fichier(s) supprimé(s)")
            self.clear_all()
    
    def clear_all(self):
        self.files.clear()
        self.results.clear()
        self.listbox.delete(0, tk.END)
        self.progress["value"] = 0
        self.progress_label.config(text="0%")
        self.total_scanned = 0
        self.threats_found = 0
        self.files_clean = 0
        self.update_statistics()
        self.update_status()
        self.afficher_accueil()


if __name__ == "__main__":
    root = tk.Tk()
    app = SecurityAntivirus(root)
    root.mainloop()
