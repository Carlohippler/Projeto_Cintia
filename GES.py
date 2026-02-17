import tkinter as tk
import sqlite3
import os
import time
from tkinter import messagebox
from tkinter import ttk
from tkinter import filedialog
from pathlib import Path
import shutil
from winsound import MessageBeep

janela = tk.Tk()
nome_janela = janela.title("Gerenciador Empresarial Simplificado")

janela.geometry("900x500")

pasta_imagens = "imagens"
pasta_config = "config"
caminho_config = os.path.join(pasta_config, pasta_imagens)

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
    # Remove tudo que estiver dentro da janela
    for widget in janela.winfo_children():
        widget.destroy()

def aba_vendas():
    limpar_tela()
    #tk.Label(janela, text="--- TELA DE VENDAS ---", font=("Arial", 14)).pack()
    tk.Button(janela, text="Voltar", command=menu_principal).pack()
    tk.Button(janela, text =  "Sair", command=janela.quit).place(x =800, y = 50)
    tk.Button(janela, text = "Abrir nova janela", command=abrir_janela).pack(pady = 20)
    nome_janela = janela.title("Vendas")
    filedialog = tk.__file__


def menu_principal():
    limpar_tela()
    

    tk.Button(janela, text="Vendas", command=aba_vendas).pack(pady=20)
    tk.Button(janela, text="Estoque", command=estoque).pack()
    tk.Button(janela, text =  "Sair", command=janela.quit).place(x = 800, y = 50)
    tk.Button(janela, text= "Configuração", command = configuracoes).place(x = 100, y = 50)

def estoque():
    limpar_tela()
    nome_janela = janela.title("Estoque")
    
   # tk.Label(janela, text = "--- TELA DE ESTOQUE ---", font = ("Arial", 14)).pack()
    tk.Button(janela, text = "Voltar", command = menu_principal).place(x = 10, y = 50)
    tk.Button(janela, text =  "Sair", command=janela.quit).place(x = 800, y = 50)
    tk.Label(janela, text= "Produto:").place(x = 100, y = 110 )
    entrada_produto = tk.Entry(janela)
    entrada_produto.place(x = 100, y = 135)



def configuracoes():
    limpar_tela()

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



