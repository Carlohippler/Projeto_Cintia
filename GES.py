import tkinter as tk
import sqlite3
import os
import time
from tkinter import messagebox, filedialog
from tkinter import ttk
from pathlib import Path
import shutil
from winsound import MessageBeep
from PIL import Image, ImageTk

janela = tk.Tk()
nome_janela = janela.title("Gerenciador Empresarial Simplificado")

tamanho_janela = janela.geometry("900x500")

image_fundo = None

pasta_imagens = "imagens"
pasta_config = "config"
caminho_config = os.path.join(pasta_config, pasta_imagens)
caminho_background = os.path.join(pasta_config, pasta_imagens, "background.png")


def aplicar_fundo(event=None):
    global image_fundo
    if os.path.exists(caminho_background):
        try:
            # largura e altura atuais da janela
            largura = janela.winfo_width()
            altura = janela.winfo_height()

            # Evita erro se a janela ainda estiver iniciando (tamanho 1x1)
            if largura > 1 and altura > 1:
                img_original = Image.open(caminho_background)
                img_redimensionada = img_original.resize((largura, altura), Image.LANCZOS)
                image_fundo = ImageTk.PhotoImage(img_redimensionada)

                # Verifica se já existe um label de fundo para não criar vários novos
                # Se não existir, ele cria. Se existir, apenas atualiza a imagem.
                if hasattr(janela, 'label_background'):
                    janela.label_background.config(image=image_fundo)
                else:
                    janela.label_background = tk.Label(janela, image=image_fundo)
                    janela.label_background.place(x=0, y=0, relwidth=1, relheight=1)
                    janela.label_background.lower()

        except Exception as e:
            print(f"Erro ao carregar a imagem de fundo: {e}")

 

janela.bind("<Configure>", aplicar_fundo)



if not os.path.exists(caminho_config):
    os.makedirs(caminho_config)
    print(f"Pasta: {pasta_imagens} criada com sucesso!")
else: print(f"A pasta: {pasta_imagens} ja existe!")

# geometry define o tamanho manualmente, ja o grid define tudo por colunas e linhas, o pacl é mais simples porem muito limitado
def abrir_janela():
    janela_nova = tk.Toplevel()
    janela_nova.title("Nova Janela")
    janela_nova.geometry("300x200")
    

def limpar_tela():
 
    for widget in janela.winfo_children():
        widget.destroy()
     
def aba_vendas():
    limpar_tela()
    aplicar_fundo()
    tk.Button(janela, text="Voltar", command=menu_principal).pack()
    tk.Button(janela, text =  "Sair", command=janela.quit).place(x =800, y = 50)
    tk.Button(janela, text = "Abrir nova janela", command=abrir_janela).pack(pady = 20)
    nome_janela = janela.title("Vendas")
    filedialog = tk.__file__


def menu_principal():
    limpar_tela()
    aplicar_fundo()

    tk.Button(janela, text="Vendas", command=aba_vendas).place(x = 100, y = 150)
    tk.Button(janela, text="Estoque", command=estoque).place(x = 100, y = 80)
    tk.Button(janela, text =  "Sair", command=janela.quit).place(x = 400, y = 20)
    tk.Button(janela, text= "Configuração", command = configuracoes).place(x = 163, y = 20)
    tk.Button(janela, text = "Gerar relatorio de Estoque", command= gerar_relatorio_txt).place(x = 250, y = 20)

def estoque():
    limpar_tela()
    aplicar_fundo()
    janela.title("Estoque - Gerenciamento")

    # --- CAMPOS DE ENTRADA ---
    tk.Label(janela, text="Nome do Produto:").place(x=10, y=10)
    ent_nome = tk.Entry(janela)
    ent_nome.place(x=10, y=30)

    tk.Label(janela, text="Preço Custo:").place(x=150, y=10)
    ent_custo = tk.Entry(janela)
    ent_custo.place(x=150, y=30)

    # --- TABELA (TREEVIEW) ---
    colunas = ("ID", "Produto", "Custo", "Qtd")
    tabela = ttk.Treeview(janela, columns=colunas, show="headings")
    for col in colunas:
        tabela.heading(col, text=col)
        tabela.column(col, width=100)
    tabela.place(x=10, y=100, width=600, height=300)

    # --- FUNÇÕES INTERNAS ---
    def salvar_produto():
        nome = ent_nome.get()
        custo = ent_custo.get()
        
        if nome and custo:
            conn = sqlite3.connect("ges_dados.db")
            cur = conn.cursor()
            cur.execute("INSERT INTO produtos (nome, preco_custo, quantidade) VALUES (?, ?, ?)", (nome, custo, 0))
            conn.commit()
            conn.close()
            messagebox.showinfo("Sucesso", "Produto cadastrado!")
            atualizar_tabela()
        else:
            messagebox.showwarning("Atenção", "Preencha todos os campos!")

    def atualizar_tabela():
        for i in tabela.get_children(): tabela.delete(i) # Limpa a tabela visual
        conn = sqlite3.connect("ges_dados.db")
        cur = conn.cursor()
        cur.execute("SELECT id, nome, preco_custo, quantidade FROM produtos")
        for linha in cur.fetchall():
            tabela.insert("", "end", values=linha)
        conn.close()

    # Botões
    tk.Button(janela, text="Salvar Produto", command=salvar_produto).place(x=300, y=25)
    tk.Button(janela, text="Voltar", command=menu_principal).place(x=10, y=420)
    
    atualizar_tabela() # Carrega os dados assim que abre a tela


def conectar_banco():
    conexao = sqlite3.connect("ges_dados.db")
    cursor = conexao.cursor()
    # Tabela de Produtos
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS produtos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nome TEXT NOT NULL,
            preco_custo REAL,
            preco_venda REAL,
            quantidade INTEGER
        )
    """)
    conexao.commit()
    conexao.close()

conectar_banco()

def gerar_relatorio_txt():
    conn = sqlite3.connect("ges_dados.db")
    cur = conn.cursor()
    cur.execute("SELECT * FROM produtos")
    dados = cur.fetchall()
    
    with open("relatorio_estoque.txt", "w") as f:
        f.write("RELATÓRIO DE ESTOQUE\n")
        f.write("-" * 30 + "\n")
        for p in dados:
            f.write(f"ID: {p[0]} | Nome: {p[1]} | Custo: R${p[2]}\n")
    
    messagebox.showinfo("Relatório", "Relatório gerado com sucesso!")
    conn.close()

def configuracoes():
    limpar_tela()
    aplicar_fundo()

    nome_janela = janela.title("Configurações")

    tk.Button(janela, text = "Voltar", command = menu_principal).place(x = 10, y = 50)
    tk.Button(janela, text = "Escolher imagem", command = salvar_imagem).place(x = 100, y = 300)



def salvar_imagem():
    caminho_config = filedialog.askopenfilename(
        title = "Selecione uma imagem", 
        filetypes=[("Imagens","*.png *.jpg *.png *.jpeg *.bmp")])

    if caminho_config:

        pasta_destino = os.path.join(pasta_config, pasta_imagens)
        nome_arquivo = os.path.basename(caminho_config)

        destino_final = os.path.join(pasta_destino, nome_arquivo)

        try:
            shutil.copy(caminho_config, destino_final)

        except Exception as e:
            messagebox.showinfo("Erro ao salvar a imagem: ", f"{destino_final}")

        print(f"IMagem salva com sucesso em: {destino_final}")
    else:
            print("Nenhuma imagem selecionada/nao pode ser baixada")


menu_principal()
# mainloop faz a janela "rodar" infinitamente, não desativar
janela.mainloop()



