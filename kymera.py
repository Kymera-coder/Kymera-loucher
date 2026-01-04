import sys
import os
import threading
import time
import json
import subprocess
import shlex
import requests
import webbrowser
from io import BytesIO

# --- SISTEMA DE SEGURANÇA ---
try:
    import customtkinter as ctk
    from tkinter import filedialog, messagebox
    from PIL import Image, ImageFilter, ImageEnhance
except ImportError as e:
    import ctypes
    ctypes.windll.user32.MessageBoxW(0, f"Faltam bibliotecas!\nErro: {e}", "ERRO", 0x10)
    sys.exit()

# ==========================================================
# CONFIGURAÇÕES DE ATUALIZAÇÃO (EDITE AQUI)
# ==========================================================
VERSAO_ATUAL = "1.0.0"

# 1. Cole aqui o link RAW do seu arquivo versao.txt (Github Raw ou Pastebin Raw)
LINK_VERSAO_TXT = "https://raw.githubusercontent.com/Kymera-coder/Kymera-loucher/refs/heads/main/version.txt"

# 2. Cole aqui o site para onde o usuário vai se tiver update
LINK_SITE_DOWNLOAD = "https://github.com/Kymera-coder/Launcher-Kymera"
# ==========================================================

ctk.set_appearance_mode("Dark")
ctk.set_default_color_theme("dark-blue")

# ARQUIVOS LOCAIS
ARQUIVO_DADOS = "kymera_db.json"
ARQUIVO_LINKS = "kymera_links.json" 
ARQUIVO_CONFIGS = "kymera_configs.json"
PASTA_CAPAS = "kymera_capas"

if not os.path.exists(PASTA_CAPAS):
    try: os.makedirs(PASTA_CAPAS)
    except: pass

HEADERS = {"User-Agent": "Mozilla/5.0"}
LINK_DISCORD = "https://discord.gg/CWzevuH6hj"

# ==========================================================
# JANELAS AUXILIARES
# ==========================================================
class JanelaSettings(ctk.CTkToplevel):
    def __init__(self, parent, configs_atuais, lista_jogos, callback_salvar):
        super().__init__(parent)
        self.title("Painel de Controle")
        self.geometry("500x550")
        self.configs = configs_atuais
        self.lista_jogos = lista_jogos
        self.callback_salvar = callback_salvar
        self.attributes("-topmost", True)
        self.after(200, lambda: self.attributes("-topmost", False))

        ctk.CTkLabel(self, text="CENTRAL DE CONTROLE", font=("Arial", 18, "bold")).pack(pady=15)

        # Stats
        f_stats = ctk.CTkFrame(self, fg_color="#1a1a1a", border_color="#333", border_width=1)
        f_stats.pack(pady=10, padx=20, fill="x")
        ctk.CTkLabel(f_stats, text="📊 Estatísticas", font=("Arial", 12, "bold"), text_color="#5865F2").pack(pady=5)
        
        tempo = sum(j.get("tempo_jogado", 0) for j in lista_jogos)
        h, m = int(tempo/3600), int((tempo%3600)/60)
        ctk.CTkLabel(f_stats, text=f"Jogos: {len(lista_jogos)} | Tempo: {h}h {m}m", font=("Arial", 12)).pack(pady=10)

        # --- SEÇÃO: ATUALIZAÇÕES SIMPLES ---
        f_upd = ctk.CTkFrame(self, fg_color="#2b2b2b")
        f_upd.pack(pady=10, padx=20, fill="x")
        
        ctk.CTkLabel(f_upd, text=f"☁️ Versão Instalada: v{VERSAO_ATUAL}", font=("Arial", 12, "bold")).pack(pady=5)
        
        self.lbl_status = ctk.CTkLabel(f_upd, text="Verificação Online", font=("Arial", 10), text_color="gray")
        self.lbl_status.pack(pady=0)

        self.btn_upd = ctk.CTkButton(f_upd, text="🔄 VERIFICAR AGORA", fg_color="#2980b9", command=self.verificar_update)
        self.btn_upd.pack(pady=10, padx=20, fill="x")

        # Opções
        f_opt = ctk.CTkFrame(self, fg_color="transparent")
        f_opt.pack(pady=10, padx=20, fill="x")
        ctk.CTkButton(f_opt, text="🖼️ Mudar Fundo", fg_color="#8e44ad", command=self.bg).pack(fill="x", pady=5)
        self.sw = ctk.CTkSwitch(f_opt, text="Modo Foco (Esconder ao Jogar)")
        if self.configs.get("modo_foco", False): self.sw.select()
        self.sw.pack(pady=10)

        ctk.CTkButton(self, text="SALVAR", fg_color="green", height=40, command=self.salvar).pack(side="bottom", pady=20, padx=20, fill="x")

    def verificar_update(self):
        self.btn_upd.configure(text="Conectando...", state="disabled")
        self.lbl_status.configure(text="Lendo arquivo de versão...", text_color="yellow")
        
        def check_txt():
            try:
                # Baixa o conteúdo do arquivo de texto
                r = requests.get(LINK_VERSAO_TXT, headers=HEADERS, timeout=10)
                
                if r.status_code == 200:
                    # Limpa espaços e quebras de linha para pegar só o número
                    versao_online = r.text.strip()
                    
                    # Compara as versões
                    if versao_online != VERSAO_ATUAL:
                        self.lbl_status.configure(text=f"Nova versão detectada: {versao_online}!", text_color="green")
                        msg = f"Nova versão disponível: {versao_online}\nSua versão: {VERSAO_ATUAL}\n\nDeseja baixar agora?"
                        if messagebox.askyesno("Atualização", msg):
                            webbrowser.open(LINK_SITE_DOWNLOAD)
                    else:
                        self.lbl_status.configure(text="Você já tem a versão mais recente.", text_color="gray")
                        messagebox.showinfo("Atualizado", "Nenhuma atualização disponível.")
                else:
                    self.lbl_status.configure(text="Erro ao ler arquivo.", text_color="red")
                    messagebox.showerror("Erro", "Não foi possível ler o arquivo de versão.\nVerifique se o Link RAW está correto.")

            except Exception as e:
                self.lbl_status.configure(text="Erro de conexão.", text_color="red")
                print(e)
            
            # Reativa o botão
            self.btn_upd.configure(text="🔄 VERIFICAR AGORA", state="normal")

        threading.Thread(target=check_txt, daemon=True).start()

    def bg(self):
        c = filedialog.askopenfilename(filetypes=[("Img", "*.jpg *.png")])
        if c: self.configs["bg_path"] = c
    def salvar(self):
        self.configs["modo_foco"] = self.sw.get()
        self.callback_salvar(self.configs)
        self.destroy()

class JanelaCapas(ctk.CTkToplevel):
    def __init__(self, parent, nome_jogo, callback):
        super().__init__(parent)
        self.title("Capa")
        self.geometry("600x500")
        self.callback = callback
        self.nome_jogo = nome_jogo
        self.attributes("-topmost", True)
        ctk.CTkLabel(self, text=f"Arte: {nome_jogo}", font=("Arial", 16, "bold")).pack(pady=15)
        ctk.CTkButton(self, text="🌐 GOOGLE IMAGENS", fg_color="#ea4335", command=lambda: webbrowser.open(f"https://www.google.com/search?tbm=isch&q={nome_jogo} box art vertical")).pack(pady=5, padx=40, fill="x")
        f = ctk.CTkFrame(self)
        f.pack(pady=5, padx=40, fill="x")
        self.e = ctk.CTkEntry(f, placeholder_text="Link..."); self.e.pack(side="left", fill="x", expand=True, padx=5, pady=5)
        ctk.CTkButton(f, text="BAIXAR", width=80, fg_color="green", command=self.dl).pack(side="right", padx=5)
        ctk.CTkButton(self, text="📂 ARQUIVO PC", fg_color="#5865F2", command=self.local).pack(pady=5, padx=40, fill="x")
    def local(self):
        a = filedialog.askopenfilename()
        if a: self.save(Image.open(a))
    def dl(self):
        try: self.save(Image.open(BytesIO(requests.get(self.e.get(), headers=HEADERS, timeout=5).content)))
        except: pass
    def save(self, img):
        try:
            import random
            n = f"{''.join(c for c in self.nome_jogo if c.isalnum())[:15]}_{random.randint(100,999)}.jpg"
            c = os.path.join(PASTA_CAPAS, n)
            img.convert("RGB").save(c, "JPEG")
            self.callback(c); self.destroy()
        except: pass

class JanelaConfig(ctk.CTkToplevel):
    def __init__(self, parent, jogo, callback):
        super().__init__(parent)
        self.title("Opções")
        self.geometry("500x250")
        self.callback = callback; self.jogo = jogo; self.attributes("-topmost", True)
        ctk.CTkLabel(self, text=f"Config: {jogo['nome']}", font=("Arial", 14, "bold")).pack(pady=20)
        self.e = ctk.CTkEntry(self, width=400, placeholder_text="-windowed"); self.e.pack(pady=10)
        if "args" in jogo: self.e.insert(0, jogo["args"])
        ctk.CTkButton(self, text="SALVAR", fg_color="green", command=lambda: [callback(jogo, self.e.get()), self.destroy()]).pack(pady=20)

# ==========================================================
# APP PRINCIPAL (KYMERA V33 - COM ABAS)
# ==========================================================
class KymeraApp(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("Kymera Launcher")
        self.geometry("1100x750")
        self.lista_jogos = []
        self.lista_links = [] # Lista para os sites
        
        self.configs_gerais = {"bg_path": "", "modo_foco": False}
        self.carregar_configs_gerais()

        # Background
        self.bg_lbl = ctk.CTkLabel(self, text="")
        self.bg_lbl.place(x=0, y=0, relwidth=1, relheight=1)
        self.bg_lbl.lower()
        if self.configs_gerais["bg_path"]: self.aplicar_fundo(self.configs_gerais["bg_path"])

        # HEADER
        self.top = ctk.CTkFrame(self, height=70, fg_color="#111111", corner_radius=0)
        self.top.pack(fill="x", side="top")
        ctk.CTkLabel(self.top, text=" KYMERA", font=("Arial Black", 26), text_color="white").pack(side="left", padx=20)
        
        self.busca = ctk.CTkEntry(self.top, width=250, placeholder_text="🔍 Buscar jogo...")
        self.busca.pack(side="left", padx=20)
        self.busca.bind("<KeyRelease>", self.filtrar)

        ctk.CTkButton(self.top, text="💬 Discord", width=90, fg_color="#5865F2", command=lambda: webbrowser.open(LINK_DISCORD)).pack(side="right", padx=(10,20))
        ctk.CTkButton(self.top, text="⚙️", width=40, fg_color="#333", command=self.settings).pack(side="right", padx=5)

        # --- SISTEMA DE ABAS (O NOVO CORAÇÃO) ---
        self.abas = ctk.CTkTabview(self, width=1000, height=600, fg_color="transparent")
        self.abas.pack(fill="both", expand=True, padx=10, pady=10)
        
        # Cria as abas
        self.aba_lib = self.abas.add("BIBLIOTECA")
        self.aba_down = self.abas.add("DOWNLOADS")

        # --- ABA BIBLIOTECA ---
        # Botões de controle da biblioteca
        f_ctrl = ctk.CTkFrame(self.aba_lib, fg_color="transparent")
        f_ctrl.pack(fill="x", pady=5)
        ctk.CTkButton(f_ctrl, text="➕ Add Manual", width=100, fg_color="#333", command=self.add_manual).pack(side="right", padx=5)
        ctk.CTkButton(f_ctrl, text="🔍 Scan", width=80, fg_color="#5865F2", command=self.scan).pack(side="right", padx=5)

        # Scroll da Biblioteca
        self.scroll_lib = ctk.CTkScrollableFrame(self.aba_lib, fg_color="transparent")
        self.scroll_lib.pack(fill="both", expand=True)
        self.scroll_lib.grid_columnconfigure((0,1,2,3), weight=1)

        # --- ABA DOWNLOADS ---
        f_ctrl_d = ctk.CTkFrame(self.aba_down, fg_color="transparent")
        f_ctrl_d.pack(fill="x", pady=5)
        ctk.CTkLabel(f_ctrl_d, text="CENTRAL DE SITES", font=("Arial", 16, "bold")).pack(side="left", padx=10)
        ctk.CTkButton(f_ctrl_d, text="➕ Novo Site", width=100, fg_color="green", command=self.add_site).pack(side="right", padx=5)

        # Scroll de Downloads
        self.scroll_down = ctk.CTkScrollableFrame(self.aba_down, fg_color="transparent")
        self.scroll_down.pack(fill="both", expand=True)
        self.scroll_down.grid_columnconfigure((0,1,2), weight=1) # 3 colunas de sites

        # INICIALIZAÇÃO
        self.carregar_dados()
        self.carregar_links() # Carrega os sites

    # --- FUNÇÕES DOWNLOADS (NOVO) ---
    def carregar_links(self):
        if os.path.exists(ARQUIVO_LINKS):
            try:
                with open(ARQUIVO_LINKS, 'r') as f: self.lista_links = json.load(f)
            except: pass
        
        # Se estiver vazio, adiciona alguns padrões
        if not self.lista_links:
            self.lista_links = [
                {"nome": "Steam", "url": "https://store.steampowered.com"},
                {"nome": "Epic Games", "url": "https://store.epicgames.com"},
                {"nome": "GOG", "url": "https://www.gog.com"},
                {"nome": "FitGirl (Repacks)", "url": "https://fitgirl-repacks.site"},
                {"nome": "Dodi (Repacks)", "url": "https://dodi-repacks.site"}
            ]
            self.salvar_links()
        
        self.desenhar_links()

    def salvar_links(self):
        with open(ARQUIVO_LINKS, 'w') as f: json.dump(self.lista_links, f)

    def add_site(self):
        nome = ctk.CTkInputDialog(text="Nome do Site:", title="Novo").get_input()
        url = ctk.CTkInputDialog(text="Link (URL):", title="Novo").get_input()
        if nome and url:
            if not url.startswith("http"): url = "https://" + url
            self.lista_links.append({"nome": nome, "url": url})
            self.salvar_links()
            self.desenhar_links()

    def remover_site(self, site):
        if messagebox.askyesno("Remover", f"Tirar {site['nome']} da lista?"):
            self.lista_links.remove(site)
            self.salvar_links()
            self.desenhar_links()

    def desenhar_links(self):
        for w in self.scroll_down.winfo_children(): w.destroy()
        
        colunas = 3
        for i, site in enumerate(self.lista_links):
            r, c = i // colunas, i % colunas
            
            card = ctk.CTkFrame(self.scroll_down, fg_color="#181818", border_color="#333", border_width=2)
            card.grid(row=r, column=c, padx=10, pady=10, sticky="nsew")
            
            # Nome Grande
            ctk.CTkLabel(card, text=site["nome"], font=("Arial", 16, "bold"), text_color="white").pack(pady=15)
            
            # Botão Acessar
            ctk.CTkButton(card, text="ACESSAR 🔗", fg_color="#5865F2", 
                          command=lambda u=site["url"]: webbrowser.open(u)).pack(pady=5, padx=20, fill="x")
            
            # Botão Remover
            ctk.CTkButton(card, text="Remover", fg_color="transparent", text_color="red", height=20,
                          command=lambda s=site: self.remover_site(s)).pack(pady=5)

    # --- FUNÇÕES GERAIS (Mantidas) ---
    def carregar_configs_gerais(self):
        if os.path.exists(ARQUIVO_CONFIGS):
            try: 
                with open(ARQUIVO_CONFIGS, 'r') as f: self.configs_gerais.update(json.load(f))
            except: pass
    def salvar_configs_gerais(self, n):
        self.configs_gerais = n
        with open(ARQUIVO_CONFIGS, 'w') as f: json.dump(self.configs_gerais, f)
        if self.configs_gerais["bg_path"]: self.aplicar_fundo(self.configs_gerais["bg_path"])
    def settings(self): JanelaSettings(self, self.configs_gerais, self.lista_jogos, self.salvar_configs_gerais)
    def aplicar_fundo(self, c):
        try:
            if os.path.exists(c):
                img = ctk.CTkImage(Image.open(c).filter(ImageFilter.GaussianBlur(15)).point(lambda p: p * 0.5), size=(1920, 1080))
                self.bg_lbl.configure(image=img); self.bg_lbl.image = img
        except: pass
    def carregar_dados(self):
        if os.path.exists(ARQUIVO_DADOS):
            try:
                with open(ARQUIVO_DADOS, 'r') as f: self.lista_jogos = json.load(f)
                self.desenhar_lib(self.lista_jogos)
            except: pass
    def salvar_dados(self): 
        with open(ARQUIVO_DADOS, 'w') as f: json.dump(self.lista_jogos, f)
    
    # --- VISUAL BIBLIOTECA ---
    def desenhar_lib(self, lista):
        for w in self.scroll_lib.winfo_children(): w.destroy()
        lista.sort(key=lambda x: x.get("favorito", False), reverse=True)
        for i, j in enumerate(lista): self.card_lib(j, i//4, i%4)

    def card_lib(self, j, r, c):
        color = "#FFD700" if j.get("favorito") else "#333"
        card = ctk.CTkFrame(self.scroll_lib, fg_color="#181818", border_color=color, border_width=2 if j.get("favorito") else 0)
        card.grid(row=r, column=c, padx=5, pady=5, sticky="nsew")
        
        if j.get("imagem") and os.path.exists(j["imagem"]):
            try: ctk.CTkLabel(card, text="", image=ctk.CTkImage(Image.open(j["imagem"]), size=(160,220))).pack(pady=5)
            except: self.vazio(card)
        else: self.vazio(card)

        ctk.CTkButton(card, text="★" if j.get("favorito") else "☆", width=25, fg_color="transparent", text_color=color, font=("Arial", 22), command=lambda: self.fav(j)).place(relx=0.9, rely=0.01, anchor="ne")
        ctk.CTkLabel(card, text=j["nome"][:20], font=("Arial",12,"bold")).pack(pady=0)
        
        # Tempo
        s = j.get("tempo_jogado", 0)
        t_str = "Recente" if s < 60 else (f"{int(s/60)} min" if s < 3600 else f"{int(s/3600)}h {int((s%3600)/60)}m")
        ctk.CTkLabel(card, text=t_str, font=("Arial",10), text_color="gray").pack(pady=0)

        ctk.CTkButton(card, text="JOGAR", height=28, fg_color="green", command=lambda: self.play(j)).pack(pady=5, padx=10, fill="x")
        
        fo = ctk.CTkFrame(card, fg_color="transparent")
        fo.pack(pady=5)
        ctk.CTkButton(fo, text="🎨", width=30, fg_color="#333", command=lambda: JanelaCapas(self, j["nome"], lambda c: [j.update({"imagem":c}), self.salvar_dados(), self.desenhar_lib(self.lista_jogos)])).pack(side="left", padx=2)
        ctk.CTkButton(fo, text="⚙️", width=30, fg_color="#333", command=lambda: JanelaConfig(self, j, lambda o, a: [o.update({"args":a}), self.salvar_dados()])).pack(side="left", padx=2)
        ctk.CTkButton(fo, text="🗑️", width=30, fg_color="#900", command=lambda: self.rem(j)).pack(side="left", padx=2)

    def vazio(self, m): 
        f = ctk.CTkFrame(m, width=160, height=220, fg_color="#2b2b2b"); f.pack(pady=5); f.pack_propagate(False)
        ctk.CTkLabel(f, text="SEM CAPA").place(relx=0.5, rely=0.5, anchor="center")
    
    def filtrar(self, e):
        t = self.busca.get().lower()
        self.desenhar_lib([j for j in self.lista_jogos if t in j["nome"].lower()] if t else self.lista_jogos)
    
    def fav(self, j): j["favorito"] = not j.get("favorito"); self.salvar_dados(); self.desenhar_lib(self.lista_jogos)
    def rem(self, j): 
        if messagebox.askyesno("Confirmar", "Apagar?"): self.lista_jogos.remove(j); self.salvar_dados(); self.desenhar_lib(self.lista_jogos)
    
    def play(self, j):
        def t():
            cmd = [j["caminho"]] + (shlex.split(j["args"]) if j.get("args") else [])
            start = time.time()
            foco = self.configs_gerais.get("modo_foco", False)
            if foco: self.withdraw()
            try:
                subprocess.Popen(cmd, cwd=os.path.dirname(j["caminho"])).wait()
                j["tempo_jogado"] = j.get("tempo_jogado", 0) + (time.time()-start)
                if foco: self.deiconify()
                self.after(100, lambda: [self.salvar_dados(), self.desenhar_lib(self.lista_jogos)])
            except Exception as e: 
                if foco: self.deiconify()
        threading.Thread(target=t, daemon=True).start()

    def scan(self):
        d = filedialog.askdirectory()
        if not d: return
        for item in os.scandir(d):
            if item.is_dir():
                exe, maior = None, 0
                for r, _, fs in os.walk(item.path):
                    if "windows" in r.lower(): continue
                    for f in fs:
                        if f.endswith(".exe") and "uninstall" not in f.lower():
                            p = os.path.join(r, f)
                            try:
                                s = os.path.getsize(p)
                                if s > maior and s > 10*1024*1024: maior, exe = s, p
                            except: pass
                    if exe: break
                if exe and not any(j['caminho'] == exe for j in self.lista_jogos):
                    self.lista_jogos.append({"nome": item.name, "caminho": exe, "imagem":"", "favorito":False, "tempo_jogado":0, "args":""})
        self.salvar_dados(); self.desenhar_lib(self.lista_jogos)

    def add_manual(self):
        a = filedialog.askopenfilename(filetypes=[("EXE", "*.exe")])
        if a:
            n = ctk.CTkInputDialog(text="Nome:", title="Add").get_input()
            if n: self.lista_jogos.append({"nome": n, "caminho": a, "imagem":"", "favorito":False, "tempo_jogado":0, "args":""}); self.salvar_dados(); self.desenhar_lib(self.lista_jogos)

if __name__ == "__main__":
    app = KymeraApp()
    app.mainloop()



