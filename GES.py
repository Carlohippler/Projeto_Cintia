import tkinter as tk
import sqlite3
import os
from tkinter import messagebox, filedialog, ttk
import shutil
from PIL import Image, ImageTk

# --- CONFIGURAÇÃO INICIAL ---
janela = tk.Tk()
janela.title("Gerenciador Empresarial Simplificado")
janela.geometry("900x500")

image_fundo = None
pasta_imagens = "imagens"
pasta_config = "config"
caminho_config = os.path.join(pasta_config, pasta_imagens)
caminho_background = os.path.join(pasta_config, pasta_imagens, "background.png")

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
    
    # 1. CRIA OS CAMPOS PRIMEIRO
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
        
       messagebox.showinfo("Venda", "Venda registrada com sucesso!")

    botao_registrar = tk.Button(janela, text="Registrar Venda", bg="green", fg="white", command=registrar_venda)
    botao_registrar.place(x=560, y=28)

    tk.Button(janela, text="Voltar", command=menu_principal).place(x=10, y=450)

    campos = [ent_prod, ent_preco, ent_qtd, botao_registrar]
    pulo_sequencial(campos)
 
    def calcular_total(event=None):
        try:
            p = float(ent_preco.get())
            q = int(ent_qtd.get())
            lbl_total.config(text=f"R$ {p * q:.2f}")
        except:
            lbl_total.config(text="Erro nos valores")

    ent_preco.bind("<KeyRelease>", calcular_total)
    ent_qtd.bind("<KeyRelease>", calcular_total)
    
    ent_qtd.bind("<Return>", lambda e: registrar_venda())

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

    tk.Button(janela, text="Salvar Produto", command=salvar_produto).place(x=430, y=25)
    tk.Button(janela, text="Voltar", command=menu_principal).place(x=10, y=420)
    atualizar_tabela()

# Configuracao 
def menu_principal():
    limpar_tela()
    aplicar_fundo()
    tk.Button(janela, text="Vendas", width=20, command=aba_vendas).place(x=100, y=150)
    tk.Button(janela, text="Estoque", width=20, command=estoque).place(x=100, y=110)
    tk.Button(janela, text="Configuração", command=configuracoes).place(x=10, y=10)
    tk.Button(janela, text="Sair", command=janela.quit).place(x=800, y=10)
    tk.Button(janela, text="Relatório Estoque", command=gerar_relatorio_txt).place(x=250, y=10)
    tk.Button(janela, text = "Compras", command = aba_compras).place(x=200, y=50)

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
        messagebox.showinfo("Sucesso", "Imagem alterada!")
        aplicar_fundo()

def conectar_banco():
    conexao = sqlite3.connect("ges_dados.db")
    cursor = conexao.cursor()
    # Tabela de Produtos (Estoque)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS produtos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nome TEXT NOT NULL,
            preco_custo REAL,
            quantidade INTEGER
        )
    """)
    # Tabela de Movimentações (Vendas e Compras)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS movimentacoes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            tipo TEXT, -- 'SAIDA' para venda, 'ENTRADA' para compra
            produto TEXT,
            quantidade INTEGER,
            valor_total REAL,
            data TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    conexao.commit()
    conexao.close()

# serve para dar enter nos campos e pular para o proximo
def pulo_sequencial(lista_campos):
    
    for i in range(len(lista_campos) - 1):
        lista_campos[i].bind("<Return>", lambda e, prox=lista_campos[i+1]:prox.focus_set())


def gerar_relatorio_txt():
    conn = sqlite3.connect("ges_dados.db")
    cur = conn.cursor()
    cur.execute("SELECT * FROM produtos")
    dados = cur.fetchall()
    with open("relatorio_estoque.txt", "w") as f:
        f.write("RELATÓRIO DE ESTOQUE\n" + "-"*30 + "\n")
        for p in dados:
            f.write(f"ID: {p[0]} | Nome: {p[1]} | Qtd: {p[4]}\n")
    messagebox.showinfo("Relatório", "Gerado!")
    conn.close()

conectar_banco()
menu_principal()
janela.mainloop()