import tkinter as tk
import sqlite3
import os
from tkinter import messagebox, filedialog, ttk
import shutil
from PIL import Image, ImageTk
import csv
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import webbrowser

# Janela principal
janela = tk.Tk()
janela.title("Gerenciador Empresarial Simplificado")


janela.state("zoomed")
janela.resizable(False, False)

janela.iconbitmap(r"config\imagens\Ges_icon.ico")

image_fundo = None
pasta_imagens = "imagens"
pasta_config = "config"
caminho_config = os.path.join(pasta_config, pasta_imagens)
caminho_background = os.path.join(pasta_config, pasta_imagens, "background.png")

usuario_logado_tipo = None
tentativas = 0

if not os.path.exists(caminho_config):
    os.makedirs(caminho_config)

# Background padrao
def aplicar_fundo(event=None):
    global image_fundo
    if os.path.exists(caminho_background):
        try:
            largura = janela.winfo_width()
            altura = janela.winfo_height()
            
            if largura > 1 and altura > 1:
                img_original = Image.open(caminho_background)
                img_redimensionada = img_original.resize((largura, altura), Image.LANCZOS)
                image_fundo = ImageTk.PhotoImage(img_redimensionada)
                
                # Se o label não existir ou foi destruído pelo limpar_tela
                if not hasattr(janela, 'label_background') or not janela.label_background.winfo_exists():
                    janela.label_background = tk.Label(janela, image=image_fundo)
                    janela.label_background.place(x=0, y=0, relwidth=1, relheight=1)
                else:
                    janela.label_background.config(image=image_fundo)
                
                janela.label_background.lower() 
        except Exception as e:
            print(f"Erro ao carregar fundo: {e}")


janela.bind("<Configure>", aplicar_fundo)

# serve para dar enter nos campos e pular para o proximo
def pulo_sequencial(lista_campos):
    
    for i in range(len(lista_campos) - 1):
        lista_campos[i].bind("<Return>", lambda e, prox=lista_campos[i+1]:prox.focus_set())


def limpar_tela():
  
    for widget in janela.winfo_children():
        if widget != getattr(janela, 'label_background', None):
            widget.destroy()

# Compras (Entrada de produtos)
def aba_compras():
    limpar_tela()
    aplicar_fundo()
    janela.title("Registrar Compra (Entrada)")

    tk.Label(janela, text="Produto:", bg="white").place(x=10, y=10)
    ent_prod = tk.Entry(janela)
    ent_prod.place(x=10, y=30)

    tk.Label(janela, text="Qtd Comprada:", bg="white").place(x=150, y=10)
    ent_qtd = tk.Entry(janela)
    ent_qtd.place(x=150, y=30)

    def registrar_compra():
        prod = ent_prod.get()
        qtd = ent_qtd.get()
        if prod and qtd:
            conn = sqlite3.connect("ges_dados.db")
            cur = conn.cursor()
            # 1. Registra a movimentação
            cur.execute("INSERT INTO movimentacoes (tipo, produto, quantidade) VALUES ('ENTRADA', ?, ?)", (prod, qtd))
            # 2. Atualiza o estoque (Soma)
            cur.execute("UPDATE produtos SET quantidade = quantidade + ? WHERE nome = ?", (qtd, prod))
            conn.commit()
            conn.close()
            messagebox.showinfo("Sucesso", "Compra registrada e estoque atualizado!")
            menu_principal()

    tk.Button(janela, text="Salvar Compra", bg="blue", fg="white", command=registrar_compra).place(x=290, y=28)
    tk.Button(janela, text="Voltar", command=menu_principal).place(x=10, y=450)



# Vendas
def aba_vendas():
    limpar_tela()
    aplicar_fundo() 
    janela.title("Vendas")
    
    
    tk.Label(janela, text="Produto:", bg="white").place(x=10, y=10)
    ent_prod = tk.Entry(janela)
    ent_prod.place(x=10, y=30)

    tk.Label(janela, text="Preço Unitário:", bg="white").place(x=150, y=10)
    ent_preco = tk.Entry(janela)
    ent_preco.place(x=150, y=30)

    tk.Label(janela, text="Quantidade:", bg="white").place(x=290, y=10)
    ent_qtd = tk.Entry(janela)
    ent_qtd.place(x=290, y=30)

    tk.Label(janela, text="Total:", bg="white", font=("Arial", 10, "bold")).place(x=430, y=10)
    lbl_total = tk.Label(janela, text="R$ 0.00", bg="yellow", width=15)
    lbl_total.place(x=430, y=30)

   
    def registrar_venda():
     prod = ent_prod.get()
    try:
        preco = float(ent_preco.get())
        qtd_venda = int(ent_qtd.get())
        total = preco * qtd_venda
    except ValueError:
        messagebox.showerror("Erro", "Valores de preço ou quantidade inválidos!")
        return

    if ent_prod and qtd_venda > 0:
        conn = sqlite3.connect("ges_dados.db")
        cur = conn.cursor()

        # 1. Verifica se o produto existe e tem estoque suficiente
        cur.execute("SELECT quantidade FROM produtos WHERE nome = ?", (ent_prod,))
        resultado = cur.fetchone()

        if resultado:
            estoque_atual = resultado[0]
            if estoque_atual >= qtd_venda:
                # 2. Diminui do estoque
                cur.execute("UPDATE produtos SET quantidade = quantidade - ? WHERE nome = ?", (qtd_venda, ent_prod))
                
                # 3. Registra a movimentação de SAÍDA
                cur.execute("""
                    INSERT INTO movimentacoes (tipo, produto, quantidade, valor_total) 
                    VALUES ('SAIDA', ?, ?, ?)
                """, (ent_prod, qtd_venda, total))
                
                conn.commit()
                messagebox.showinfo("Sucesso", f"Venda de {ent_prod} realizada!\nTotal: R$ {total:.2f}")
                aba_vendas() # Limpa os campos recarregando a aba
            else:
                messagebox.showwarning("Estoque Insuficiente", f"Você só tem {estoque_atual} unidades em estoque.")
        else:
            messagebox.showerror("Erro", "Produto não encontrado no cadastro!")
        
        conn.close()
    else:
        messagebox.showwarning("Atenção", "Preencha todos os campos corretamente!")


# Estoque 
def estoque():
    limpar_tela()
    aplicar_fundo()
    janela.title("Estoque - Gerenciamento")

    tk.Label(janela, text="Nome do Produto:", bg="white").place(x=10, y=10)
    ent_nome = tk.Entry(janela)
    ent_nome.place(x=10, y=30)

    tk.Label(janela, text="Preço Custo:", bg="white").place(x=150, y=10)
    ent_custo = tk.Entry(janela)
    ent_custo.place(x=150, y=30)

    tk.Label(janela, text="Quantidade Inicial:", bg="white").place(x=290, y=10)
    ent_quantidade = tk.Entry(janela)
    ent_quantidade.place(x=290, y=30)

    colunas = ("ID", "Produto", "Custo", "Qtd")
    tabela = ttk.Treeview(janela, columns=colunas, show="headings")

    for col in colunas:
        tabela.heading(col, text=col)
        tabela.column(col, width=100)
    tabela.place(x=10, y=100, width=600, height=300)

    

    def salvar_produto():
        nome = ent_nome.get()
        custo = ent_custo.get()
        qtd = ent_quantidade.get()
        if nome and custo and qtd:
            conn = sqlite3.connect("ges_dados.db")
            cur = conn.cursor()
            cur.execute("INSERT INTO produtos (nome, preco_custo, quantidade) VALUES (?, ?, ?)", (nome, custo, qtd))
            conn.commit()
            conn.close()
            messagebox.showinfo("Sucesso", "Produto cadastrado!")
            atualizar_tabela()
            
        else:
            messagebox.showwarning("Atenção", "Preencha todos os campos!")

    def atualizar_tabela():
        for i in tabela.get_children(): tabela.delete(i)
        conn = sqlite3.connect("ges_dados.db")
        cur = conn.cursor()
        cur.execute("SELECT id, nome, preco_custo, quantidade FROM produtos")
        
        for linha in cur.fetchall():
            tabela.insert("", "end", values=linha)
        conn.close()
        

    salvar_estoque = tk.Button(janela, text="Salvar Produto", command=salvar_produto)
    salvar_estoque.place(x=430, y=25)

    campos_estoque = [ent_nome, ent_custo, ent_quantidade, salvar_estoque]
    pulo_sequencial(campos_estoque)

    salvar_estoque.bind("<Return>", lambda e: salvar_produto())

    tk.Button(janela, text="Voltar", command=menu_principal).place(x=10, y=420)
    atualizar_tabela()


def gerar_relatorio_excel():
    nome_arquivo = "relatorio_estoque.csv"
    conn = sqlite3.connect("ges_dados.db")
    cur = conn.cursor()
    cur.execute("SELECT id, nome, preco_custo, quantidade FROM produtos")
    dados = cur.fetchall()
    
    with open(nome_arquivo, "w", newline="", encoding="utf-8-sig") as f:
        escritor = csv.writer(f, delimiter=";") # Ponto e vírgula é melhor para o Excel 
        # Cabeçalho
        escritor.writerow(["ID", "Nome do Produto", "Preço de Custo", "Quantidade em Estoque"])
        # Dados
        escritor.writerows(dados)
    
    conn.close()
    messagebox.showinfo("Sucesso", "Relatório CSV gerado! Abrindo no Excel...")
    os.startfile(nome_arquivo)


def enviar_para_google_sheets():
    
    caminho_json = r"C:\Users\carlo\source\repos\GES\config\ges-gerenciador-empresarial-4f5496b6a95e.json"
    
    if not os.path.exists(caminho_json):
        messagebox.showerror("Erro", "Arquivo de credenciais não encontrado na pasta config!")
        return

    scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
    
    try:

        top = tk.Toplevel(janela)
        top.title("Enviando...")
        progress = ttk.Progressbar(top, orient="horizontal", length=200, mode="determinate")
        progress.place(x=20, y=20)

        # Carrega as credenciais
        creds = ServiceAccountCredentials.from_json_keyfile_name(caminho_json, scope)
        cliente = gspread.authorize(creds)

        # Tenta abrir a planilha
        planilha_doc = cliente.open("Relatorio_Estoque")
        planilha_sheet = planilha_doc.sheet1

        url_planilha = planilha_doc.url

        progress['value'] = 100
        janela.update()
        top.destroy()

        webbrowser.open(url_planilha)

        messagebox.showinfo("Nuvem", "Dados sincronizados e planilha aberta!")
        
        conn = sqlite3.connect("ges_dados.db")
        cur = conn.cursor()
        cur.execute("SELECT id, nome, preco_custo, quantidade FROM produtos")
        dados = cur.fetchall()
        conn.close()

        planilha_doc.clear()
        planilha_doc.append_row(["ID", "Nome", "Custo", "Quantidade"])
        
        
        planilha_doc.append_rows([list(linha) for linha in dados])
        
        messagebox.showinfo("Nuvem", "Dados enviados para o Google Sheets!")

    except gspread.exceptions.SpreadsheetNotFound:
        messagebox.showerror("Erro", "A planilha 'Relatorio_Estoque' não foi encontrada. Verifique o nome ou se você a compartilhou com o e-mail do Service Account.")
    except Exception as e:
        messagebox.showerror("Erro", f"Ocorreu um erro: {e}")


# Configuracao 
def menu_principal():
    limpar_tela()
    aplicar_fundo()
    janela.title("Menu Principal - Gerenciador Empresarial Simplificado")

    estado_restrito = "normal" if usuario_logado_tipo == 1 else "disabled"

    tk.Button(janela, text="Vendas", width=20, command=aba_vendas).place(x=100, y=150)
    tk.Button(janela, text="Estoque", width=20, command=estoque).place(x=100, y=110)
    tk.Button(janela, text="Configuração", state = estado_restrito , command=configuracoes).place(x=10, y=10)
    tk.Button(janela, text="Sair", command=janela.quit).place(x=800, y=10)
    tk.Button(janela, text="Relatório Estoque", state = estado_restrito, command=gerar_relatorio_excel).place(x=250, y=10)
    tk.Button(janela, text = "Compras", command = aba_compras).place(x=200, y=50)
    tk.Button(janela, text="Relatorio Estoque (Google Sheets)", state = estado_restrito , command = enviar_para_google_sheets).place(x=350, y=10)
    
def tela_login():
    janela_login = tk.Toplevel(janela)
    janela_login.title("Acesso ao Sistema")
    janela_login.geometry("300x250")
    janela_login.grab_set()  # Bloqueia interação com a janela principal

    janela_login.attributes("-topmost", True)
    janela_login.focus_force()
    janela_login.grab_set()


    largura_janela = 300
    altura_janela = 250
    
    largura_tela = janela_login.winfo_screenwidth()
    altura_tela = janela_login.winfo_screenheight()
    
    pos_x = (largura_tela // 2) - (largura_janela // 2)
    pos_y = (altura_tela // 2) - (altura_janela // 2)
    
    janela_login.geometry(f"{largura_janela}x{altura_janela}+{pos_x}+{pos_y}")


    # Se fechar o login no 'X', encerra o programa todo
    janela_login.protocol("WM_DELETE_WINDOW", janela.quit)

    tk.Label(janela_login, text="Usuário:").pack(pady=5)
    
    var_usuario = tk.StringVar()
    var_senha = tk.StringVar()

    # Lógica Automática: Senha '1' preenche 'geral'
    def verificar_atalho_geral(*args):
        if var_senha.get() == "1":
            var_usuario.set("geral")
        elif var_senha.get() == "admin123":
            var_usuario.set("admin")

    var_senha.trace_add("write", verificar_atalho_geral)

    ent_usuario = tk.Entry(janela_login, textvariable=var_usuario)
    ent_usuario.pack(pady=5)

    tk.Label(janela_login, text="Senha:").pack(pady=5)
    ent_senha = tk.Entry(janela_login, textvariable=var_senha, show="*")
    ent_senha.pack(pady=5)

    ent_senha.focus_set()
    
    janela_login.after(100, lambda: ent_senha.focus_force())

    def realizar_login(event=None):
        global usuario_logado_tipo, tentativas
        u = var_usuario.get()
        s = var_senha.get()
        
        if not u or not s:
            messagebox.showwarning("Atenção", "Preencha todos os campos!", parent=janela_login)
            return

        conn = sqlite3.connect("ges_dados.db")
        cur = conn.cursor()
        cur.execute("SELECT tipo FROM usuarios WHERE usuario = ? AND senha = ?", (u, s))
        resultado = cur.fetchone()
        conn.close()

        if resultado is not None:
            tentativas = 0
            usuario_logado_tipo = resultado[0]
            janela_login.destroy()
            janela.deiconify()
            menu_principal()

            janela.deiconify()
            janela.state("zoomed")
            menu_principal()
        else:
            tentativas +=1

            if tentativas >=3:
                messagebox.showerror("Erro", "Muitas tentativas falhas! O programa será encerrado. ", parent=janela_login)
                janela.quit()
            else:
                messagebox.showerror("Erro", "Login ou Senha incorretos!", parent=janela_login)

    btn_entrar = tk.Button(janela_login, text="Entrar", bg="green", fg="white", command=realizar_login)
    btn_entrar.pack(pady=20)
    
    # Faz o login funcionar ao apertar Enter
    janela_login.bind("<Return>", realizar_login)

# Config e banco de dados

def configuracoes():
    limpar_tela()
    aplicar_fundo()
    tk.Button(janela, text="Voltar", command=menu_principal).place(x=10, y=10)
    tk.Button(janela, text="Escolher imagem", command=salvar_imagem).place(x=100, y=100)

def salvar_imagem():
    caminho = filedialog.askopenfilename(filetypes=[("Imagens","*.png *.jpg *.jpeg")])
    if caminho:
        if not os.path.exists(caminho_config): os.makedirs(caminho_config)
        shutil.copy(caminho, caminho_background)
        messagebox.showinfo("Sucesso", "Imagem alterada! Reinicie para aplicar.")
        aplicar_fundo()

def conectar_banco():
    conexao = sqlite3.connect("ges_dados.db")
    cursor = conexao.cursor()
    
    # Tabelas Existentes
    cursor.execute("CREATE TABLE IF NOT EXISTS produtos (id INTEGER PRIMARY KEY AUTOINCREMENT, nome TEXT NOT NULL, preco_custo REAL NOT NULL, quantidade INTEGER NOT NULL DEFAULT 1)")
    cursor.execute("CREATE TABLE IF NOT EXISTS movimentacoes (id INTEGER PRIMARY KEY AUTOINCREMENT, tipo TEXT, produto TEXT NOT NULL, quantidade INTEGER NOT NULL DEFAULT 1, valor_total REAL NOT NULL, data TIMESTAMP DEFAULT CURRENT_TIMESTAMP)")

    # Tabela de Usuários
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS usuarios (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            usuario TEXT NOT NULL UNIQUE,
            senha TEXT NOT NULL,
            tipo INTEGER NOT NULL -- 1 para Admin, 0 para Geral
        )
    """)

    # Criar usuários padrão caso não existam
    cursor.execute("SELECT COUNT(*) FROM usuarios")
    if cursor.fetchone()[0] == 0:
        cursor.execute("INSERT INTO usuarios (usuario, senha, tipo) VALUES ('admin', 'admin123', 1)")
        cursor.execute("INSERT INTO usuarios (usuario, senha, tipo) VALUES ('geral', '1', 0)")

    conexao.commit()
    conexao.close()


conectar_banco()
janela.withdraw() 
tela_login()       
janela.mainloop()