import tkinter as tk
import sqlite3
import os
import time
from tkinter import messagebox
from tkinter import ttk


janela = tk.Tk()
janela.geometry("800x450")

# geometry define o tamanho manualmente, ja o grid define tudo por colunas e linhas, o pacl é mais simples porem muito limitado


def limpar_tela():
    # Remove tudo que estiver dentro da janela
    for widget in janela.winfo_children():
        widget.destroy()

def aba_vendas():
    limpar_tela()
    tk.Label(janela, text="--- TELA DE VENDAS ---", font=("Arial", 14)).pack()
    tk.Button(janela, text="Voltar", command=menu_principal).pack()
    tk.Button(janela, text =  "Sair", command=janela.quit).pack(pady = 40)

def menu_principal():
    limpar_tela()
    tk.Button(janela, text="Vendas", command=aba_vendas).pack(pady=20)
    tk.Button(janela, text="Estoque", command=estoque).pack()
    tk.Button(janela, text =  "Sair", command=janela.quit).pack(pady = 40)

def estoque():
    limpar_tela()
    tk.Label(janela, text = "--- TELA DE ESTOQUE ---", font = ("Arial", 14)).pack()
    tk.Button(janela, text = "Voltar", command = menu_principal).pack()
    tk.Button(janela, text =  "Sair", command=janela.quit).pack(pady = 40)




menu_principal()
# mainloop faz a janela "rodar" infinitamente, não desativar
janela.mainloop()


"""
# Banco de dados temporário
estoque = {} # {id: {"nome": str, "qtd": int, "custo": float, "venda": float}}
vendas = []
proximo_id_produto = 1
proximo_id_venda = 1
"""
"""
def limpar_tela():

    os.system('cls' if os.name == 'nt' else 'clear')
"""

"""def menu_principal():
    while True:
        limpar_tela()
        print("\r--- GES: Gerenciador Empresarial Simplificado ---")
        print("1. Vendas")
        print("2. Compras (Entrada de Estoque)")
        print("3. Gerenciar Estoque")
        print("0. Sair")

       
        
        opcao = input("\nEscolha uma opção: ")
        
        if opcao == '1': tela_vendas()
        elif opcao == '2': tela_compras()
        elif opcao == '3': tela_estoque()
        elif opcao == '0': break
"""
def tela_vendas():
    global proximo_id_venda
    limpar_tela()
    print("--- MÓDULO DE VENDAS ---")
    
    if not estoque:
        print("Erro: Não há produtos cadastrados para vender.")
    else:
        id_p = int(input("ID do produto: "))
        if id_p in estoque and estoque[id_p]['qtd'] > 0:
            qtd = int(input(f"Quantidade (Disponível: {estoque[id_p]['qtd']}): "))
            if qtd <= estoque[id_p]['qtd']:
                estoque[id_p]['qtd'] -= qtd
                venda = {"id_venda": proximo_id_venda, "prod": estoque[id_p]['nome'], "qtd": qtd}
                vendas.append(venda)
                proximo_id_venda += 1
                print("\nVenda realizada com sucesso!")
            else:
                print("Quantidade insuficiente.")
        else:
            print("Produto esgotado ou inexistente.")
    
    input("\nPressione Enter para voltar...")

def tela_compras():
    global proximo_id_produto
    limpar_tela()
    print("--- MÓDULO DE COMPRAS (ENTRADA) ---")
    nome = input("Nome do produto: ")
    custo = float(input("Valor de custo: "))
    qtd = int(input("Quantidade comprada: "))
    venda_sugerida = custo * 1.20 # Sugestão inicial de 20%
    
    # Verifica se produto já existe pelo nome ou cria novo
    estoque[proximo_id_produto] = {
        "nome": nome, 
        "qtd": qtd, 
        "custo": custo, 
        "venda": venda_sugerida
    }
    proximo_id_produto += 1
    print("\nCompra lançada e estoque atualizado!")
    input("\nPressione Enter para voltar...")

def tela_estoque():
    limpar_tela()
    print("--- GERENCIAMENTO DE ESTOQUE ---")
    print(f"{'ID':<4} | {'Produto':<15} | {'Quantidade':<5} | {'Custo':<8} | {'Valor Sugerido':<8}")
    
    for id_p, dados in estoque.items():
        # Lógica de alerta de margem de lucro (15% a 25%)
        margem_min = dados['custo'] * 1.15
        alerta = ""
        if dados['venda'] <= dados['custo']:
            alerta = f" -> SUGERIDO: R$ {margem_min:.2f}"
            
        print(f"{id_p:<4} | {dados['nome']:<15} | {dados['qtd']:<5} | {dados['custo']:<8.2f} | {dados['venda']:<8.2f} {alerta}")

    print("\nOpções: [1] Apagar Zerados [2] Editar Margem [0] Voltar")
    # Aqui você implementaria a lógica de deletar ou editar...
    input("\nPressione Enter para continuar...")

if __name__ == "__main__":
    menu_principal()

