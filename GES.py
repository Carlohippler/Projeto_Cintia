import subprocess
import tkinter as tk
import sqlite3
import os
import sys
from tkinter import Toplevel, messagebox, filedialog, ttk
import shutil
import time
from PIL import Image, ImageTk
import csv
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import webbrowser
import threading
from playwright.sync_api import sync_playwright
from datetime import datetime

if __name__ == "__main__":
    # Isso evita que processos secundários (como o do Playwright) 
    # iniciem a interface gráfica novamente
    import multiprocessing
    multiprocessing.freeze_support()

def garantir_playwright():
    """Verifica e instala o Chromium de forma silenciosa se necessário."""
    try:
        # Tenta listar os navegadores instalados. Se falhar, é porque precisa instalar.
        subprocess.run([sys.executable, "-m", "playwright", "install", "chromium"], 
                       check=True, 
                       creationflags=subprocess.CREATE_NO_WINDOW)
        return True
    except Exception as e:
        print(f"Erro ao instalar Playwright: {e}")
        return False

janela = tk.Tk()
janela.title("Gerenciador Empresarial Simplificado")


janela.state("zoomed")
janela.resizable(False, False)

janela.iconbitmap(r"config\imagens\Ges_icon.ico")

if getattr(sys, 'frozen', False):
    BASE_DIR = os.path.dirname(sys.executable)
else:
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))


pasta_config = os.path.join(BASE_DIR, "config")
pasta_imagens = os.path.join(pasta_config, "imagens")
caminho_background = os.path.join(pasta_imagens, "background.png")

caminho_banco = os.path.join(BASE_DIR, "dados", "ges_dados.db")

image_fundo = None
pasta_imagens = "imagens"
pasta_config = "config"
caminho_config = os.path.join(pasta_config, pasta_imagens)
caminho_background = os.path.join(pasta_config, pasta_imagens, "background.png")

# Configurações Visuais 
COR_PRIMARIA = "#2c3e50"  # Azul escuro 
COR_SUCESSO = "#27ae60"   # Verde
COR_ALERTA = "#e67e22"    # Laranja
COR_TEXTO_BOTAO = "white"
FONTE_PADRAO = ("Segoe UI", 10, "bold")

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

def janela_gerenciar_produtos():
    top = tk.Frame(janela, bg="white", highlightbackground="gray", highlightthickness=2)

    tk.Label(top, text="Gerenciamento de Produtos", bg="white", 
             font=("Arial", 12, "bold")).place(x=15, y=10)

    top.place(relx=0.5, rely=0.5, width=600, height=500, anchor="center")

    es_admin = (usuario_logado_tipo == 3)
    es_func  = (usuario_logado_tipo >= 2)
    es_visi  = (usuario_logado_tipo >= 1)

    btn_sair = tk.Button(top, text="X", fg="white", bg="red", 
                         font=("Arial", 10, "bold"), command=top.destroy)
    btn_sair.place(x=555, y=10, width=30, height=30)
    
    frame_campos = tk.Frame(top, bg="white")
    frame_campos.pack(pady=(50, 10), fill="x", padx=20)

    tk.Label(frame_campos, text="Nome:", bg="white").grid(row=0, column=0, sticky="w")
    ent_nome = tk.Entry(frame_campos, width=25)
    ent_nome.grid(row=1, column=0, padx=5)

    tk.Label(frame_campos, text="Preço Custo:", bg="white").grid(row=0, column=1, sticky="w")
    ent_custo = tk.Entry(frame_campos, width=15)
    ent_custo.grid(row=1, column=1, padx=5)

    tk.Label(frame_campos, text="Qtd:", bg="white").grid(row=0, column=2, sticky="w")
    ent_qtd = tk.Entry(frame_campos, width=10)
    ent_qtd.grid(row=1, column=2, padx=5)

    # Variável invisível para guardar o ID do produto que está sendo editado
    id_produto_editando = tk.StringVar()

    
    def carregar_dados():
        for i in tree.get_children(): tree.delete(i)
        conn = sqlite3.connect("dados/ges_dados.db")
        cur = conn.cursor()
        cur.execute("SELECT id, nome, preco_custo, quantidade FROM produtos")
    
        for linha in cur.fetchall():
            # Transforma o valor da coluna 3 em int para a comparação
            try:
                quantidade = int(linha[3])
            except (ValueError, TypeError):
                quantidade = 0  # Caso o valor seja nulo ou inválido

            tag = "alerta" if quantidade <= 0 else "normal"
            tree.insert("", "end", values=linha, tags=(tag,))
    
        conn.close()

    def salvar_produto():
        nome, custo, qtd = ent_nome.get(), ent_custo.get(), ent_qtd.get()
        if not nome or not custo or not qtd:
            messagebox.showwarning("Atenção", "Preencha todos os campos!")
            return

        try:
            # Converter para os tipos corretos antes de salvar
            custo_val = float(custo.replace(',', '.'))
            qtd_val = int(qtd)
        except ValueError:
            messagebox.showerror("Erro", "Preço deve ser numérico e Quantidade um número inteiro!")
            return

        conn = sqlite3.connect("dados/ges_dados.db")
        cur = conn.cursor()
    
        if id_produto_editando.get(): 
            cur.execute("UPDATE produtos SET nome=?, preco_custo=?, quantidade=? WHERE id=?", 
                    (nome, custo_val, qtd_val, id_produto_editando.get()))
        else: 
            cur.execute("INSERT INTO produtos (nome, preco_custo, quantidade) VALUES (?, ?, ?)", 
                    (nome, custo_val, qtd_val))
    
        conn.commit()
        conn.close()
        limpar_campos()
        carregar_dados()

        if tabela_estoque_referencia and tabela_estoque_referencia.winfo_exists():
            tabela_estoque_referencia.atualizar()

        messagebox.showinfo("Sucesso", "Produto salvo com sucesso!", parent=top)
    
    

    def limpar_campos():
        ent_nome.delete(0, tk.END)
        ent_custo.delete(0, tk.END)
        ent_qtd.delete(0, tk.END)
        id_produto_editando.set("")
        btn_salvar.config(text="Cadastrar Novo")

    def preparar_edicao(event):
        item = tree.selection()
        if item:
            valores = tree.item(item)['values']
            id_produto_editando.set(valores[0])
            ent_nome.delete(0, tk.END)
            ent_nome.insert(0, valores[1])
            ent_custo.delete(0, tk.END)
            ent_custo.insert(0, valores[2])
            ent_qtd.delete(0, tk.END)
            ent_qtd.insert(0, valores[3])
            btn_salvar.config(text="Atualizar Cadastro")

    
    # --- TABELA ---
    colunas = ("ID", "Produto", "Preço Custo", "Estoque")
    tree = ttk.Treeview(top, columns=colunas, show="headings")
    for col in colunas: tree.heading(col, text=col)
    
    # Cores para o indicador de zerado
    tree.tag_configure("alerta", background="#ffcccc", foreground="red") # Fundo vermelho claro, letra vermelha
    
    tree.pack(fill="both", expand=True, padx=10, pady=10)
    tree.bind("<Double-1>", preparar_edicao)

    # --- BOTÕES ---
    btn_frame = tk.Frame(top, bg="white")
    btn_frame.pack(pady=10)

    btn_salvar = tk.Button(btn_frame, text="Cadastrar Novo", bg=COR_SUCESSO, fg="white", font=FONTE_PADRAO, command=salvar_produto)
    btn_salvar.pack(side="left", padx=5)

    pulo_sequencial([ent_nome, ent_custo, ent_qtd, btn_salvar])

    btn_salvar.bind("<Return>", lambda e: salvar_produto())

    tk.Button(btn_frame, text="Limpar/Novo", bg="gray", fg="white", font=FONTE_PADRAO, command=limpar_campos).pack(side="left", padx=5)
    
    tk.Label(top, text="* Dica: Clique duplo na tabela para editar um produto. Linhas vermelhas = Estoque zerado.", 
             font=("Arial", 8, "italic"), bg="white").pack()

    carregar_dados()


def janela_busca_produto(event=None, campo_nome=None, campo_preco=None):
    top = tk.Toplevel(janela)
    top.title("Localizar Produto (F3)")
    top.geometry("450x400")
    top.attributes("-topmost", True)
    top.grab_set() # Bloqueia a janela de trás até fechar esta

    tk.Label(top, text="Digite para filtrar:").pack(pady=5)
    ent_filtro = tk.Entry(top)
    ent_filtro.pack(pady=5, fill="x", padx=10)
    ent_filtro.focus_set()

    colunas = ("ID", "Nome", "Preço", "Qtd")
    tree_busca = ttk.Treeview(top, columns=colunas, show="headings")
    tree_busca.heading("ID", text="ID")
    tree_busca.heading("Nome", text="Nome")
    tree_busca.heading("Preço", text="Preço")
    tree_busca.heading("Qtd", text="Estoque")
    
    
    tree_busca.column("ID", width=40)
    tree_busca.column("Nome", width=150)
    tree_busca.column("Preço", width=80)
    tree_busca.column("Qtd", width=60)
    tree_busca.pack(pady=10, fill="both", expand=True)

    def carregar_busca(filtro=""):
        for i in tree_busca.get_children(): tree_busca.delete(i)
        conn = sqlite3.connect("dados/ges_dados.db")
        cur = conn.cursor()
        # Busca o preço de custo 
        cur.execute("SELECT id, nome, preco_custo, quantidade FROM produtos WHERE nome LIKE ?", (f'%{filtro}%',))
        for linha in cur.fetchall():
            tree_busca.insert("", "end", values=linha)
        conn.close()

    ent_filtro.bind("<KeyRelease>", lambda e: carregar_busca(ent_filtro.get()))
    
    def selecionar_produto(event_extra=None):
        item_selecionado = tree_busca.selection()
        if item_selecionado:
            valores = tree_busca.item(item_selecionado)['values']
            nome_prod = valores[1]
            preco_prod = valores[2]
            
            # Preenche os campos específicos que passamos por argumento
            if campo_nome:
                campo_nome.delete(0, tk.END)
                campo_nome.insert(0, nome_prod)
            if campo_preco:
                campo_preco.delete(0, tk.END)
                campo_preco.insert(0, preco_prod)
            
            top.destroy() 
            janela.event_generate("<Tab>") # Pula para o campo de quantidade

    tree_busca.bind("<Double-1>", selecionar_produto)
    top.bind("<Return>", selecionar_produto)
    carregar_busca() 


def clientes_cad():
    limpar_tela()
    aplicar_fundo()
    janela.title("Gerenciamento Clientes")
    BarraInferior()

    tk.Label(janela, text="Nome:", bg="white").place(x=10, y=10)
    ent_nome_cliente= tk.Entry(janela, width=30)
    ent_nome_cliente.place(x=10, y=30)

    tk.Button(janela, text="Voltar", command=menu_principal).place(x=10, y=420)
    
  
def aba_compras():
    limpar_tela()
    aplicar_fundo()
    janela.title("Registrar Compra (Entrada de Estoque)")
    BarraInferior()
    
    tk.Label(janela, text="Produto:", bg="white").place(x=10, y=10)
    ent_prod_compra = tk.Entry(janela, width=30)
    ent_prod_compra.place(x=10, y=30)

    # F3 para abrir a busca 
    ent_prod_compra.bind("<F3>", lambda e: janela_busca_produto(e, ent_prod_compra))

    tk.Label(janela, text="Qtd Comprada:", bg="white").place(x=210, y=10)
    ent_qtd_compra = tk.Entry(janela, width=15)
    ent_qtd_compra.place(x=210, y=30)

    tk.Button(janela, text="➕ Gerenciar Produtos", bg="#3498db", fg="white", 
          font=("Arial", 9, "bold"), command=janela_gerenciar_produtos).place(x=550, y=80)

    def registrar_compra():
        prod = ent_prod_compra.get().strip()
        qtd_texto = ent_qtd_compra.get().strip()

        if not prod or not qtd_texto:
            messagebox.showwarning("Atenção", "Preencha o produto e a quantidade!")
            return

        try:
            qtd_entrada = int(qtd_texto)
            if qtd_entrada <= 0: raise ValueError
        except ValueError:
            messagebox.showerror("Erro", "Quantidade deve ser um número inteiro positivo!")
            return

        conn = sqlite3.connect("dados/ges_dados.db")
        cur = conn.cursor()

        # Verifica se o produto já existe no cadastro
        cur.execute("SELECT id FROM produtos WHERE nome = ?", (prod,))
        resultado = cur.fetchone()

        if resultado:
            
            cur.execute("UPDATE produtos SET quantidade = quantidade + ? WHERE nome = ?", (qtd_entrada, prod))
            
            
            
            cur.execute("""
                INSERT INTO movimentacoes (tipo, produto, quantidade, valor_total) 
                VALUES ('ENTRADA', ?, ?, 0)
            """, (prod, qtd_entrada))
            
            conn.commit()
            messagebox.showinfo("Sucesso", f"Estoque atualizado! +{qtd_entrada} unidades de {prod}")
            aba_compras() 
        else:
            messagebox.showwarning("Produto não cadastrado", 
                                 "Este produto não existe no estoque.\nCadastre-o primeiro no menu 'Estoque'.")
        
        conn.close()

    
    btn_salvar = tk.Button(janela, text="Confirmar Entrada", bg="blue", fg="white", 
                          font=("Arial", 10, "bold"), command=registrar_compra)
    btn_salvar.place(x=320, y=26)

    tk.Button(janela, text="Voltar", command=menu_principal).place(x=10, y=450)

    
    pulo_sequencial([ent_prod_compra, ent_qtd_compra, btn_salvar])

    btn_salvar.bind("<Return>", lambda e: registrar_compra())


def configuracoes():
    limpar_tela()
    aplicar_fundo()
    BarraInferior()

    tk.Button(janela, text="Voltar", command=menu_principal).place(x=10, y=10)
    tk.Button(janela, text="Escolher imagem", command=salvar_imagem).place(x=100, y=100)
    tk.Label(janela, text="Usuario:").place(x=100, y=180)
    tk.Label(janela, text="Senha:").place(x=100, y=230)
    tk.Label(janela, text="Acesso:").place(x=100, y=280)

    tk.Label(janela, text="Usuário:", bg="white").place(x=100, y=180)
    cad_usuario = tk.Entry(janela, width=25)
    cad_usuario.place(x=100, y=200)

    tk.Label(janela, text="Senha:", bg="white").place(x=100, y=230)
    cad_senha = tk.Entry(janela, width=25, show="*")
    cad_senha.place(x=100, y=250)

    tk.Label(janela, text="Nível de Acesso:", bg="white").place(x=100, y=280)
    combo_tipo = ttk.Combobox(janela, values=["Administrador", "Funcionário", "Visitante"], state="readonly")
    combo_tipo.place(x=100, y=300)
    combo_tipo.current(2) # Começa marcado como Visitante

    tk.Button(janela, text="Cadastrar Usuário", bg=COR_SUCESSO, fg="white", 
              command=lambda: salvar_novo_usuario(cad_usuario, cad_senha, combo_tipo)).place(x=100, y=340)


def salvar_novo_usuario(ent_usuario, ent_senha, combo_tipo):
    usuario = ent_usuario.get().strip()
    senha = ent_senha.get().strip()
    
    
    niveis = {
        "Administrador": 3,
        "Funcionário": 2,
        "Visitante": 1
    }
    tipo = niveis.get(combo_tipo.get(), 1) # Padrão é Visitante 

    if not usuario or not senha:
        messagebox.showwarning("Atenção", "Preencha todos os campos!")
        return

    conn = None
    try:
        conn = sqlite3.connect("dados/ges_dados.db", timeout=10)
        cur = conn.cursor()
        cur.execute("INSERT INTO usuarios (usuario, senha, tipo) VALUES (?, ?, ?)", 
                    (usuario, senha, tipo))
        conn.commit()
        messagebox.showinfo(f"Usuário {usuario} cadastrado como {combo_tipo.get()}!", "#27ae60")
        
        ent_usuario.delete(0, tk.END)
        ent_senha.delete(0, tk.END)
    except sqlite3.IntegrityError:
        messagebox.showerror("Erro", "Este usuário já existe!")
    finally:
        if conn: conn.close()



def salvar_imagem():
    caminho = filedialog.askopenfilename(filetypes=[("Imagens","*.png *.jpg *.jpeg")])
    if caminho:
        if not os.path.exists(caminho_config): os.makedirs(caminho_config)
        shutil.copy(caminho, caminho_background)
        messagebox.showinfo("Sucesso", "Imagem alterada! Reinicie para aplicar.")
        aplicar_fundo()


def configurar_whatsapp():
    def tarefa():
        # Verificação/Instalação de Dependências
        try:
            
            print("Verificando Playwright...")
            
            
            subprocess.run([sys.executable, "-m", "playwright", "install", "chromium"], 
                           check=True, creationflags=subprocess.CREATE_NO_WINDOW)
            
        except Exception as e:
            messagebox.showerror("Erro de Dependência", f"Falha ao preparar navegadores: {e}")
            return 

        
        caminho_sessao = os.path.join(os.getcwd(), "config", "sessao_whatsapp")
        if not os.path.exists(caminho_sessao):
            os.makedirs(caminho_sessao)

        try:
            with sync_playwright() as p:
                browser = p.chromium.launch_persistent_context(
                    user_data_dir=caminho_sessao,
                    headless=False,
                    ignore_default_args=["--disable-component-update"],
                    args=["--no-sandbox"]
                )
                page = browser.new_page()
                page.goto("https://web.whatsapp.com")
                
                messagebox.showinfo("WhatsApp", "1. Faça o login no QR Code.\n2. Espere as conversas carregarem.\n3. FECHE A JANELA DO NAVEGADOR para salvar.")
                
                # Aguarda o fechamento manual para garantir que o Playwright salve os cookies
                page.wait_for_event("close", timeout=0) 
                
                
                messagebox.showinfo("Sucesso", "Conexão estabelecida e salva com sucesso!")
                
        except Exception as e:
            messagebox.showerror("Erro", f"Erro na configuração: {e}")

    threading.Thread(target=tarefa, daemon=True).start()

def enviar_doc_whatsapp(numero, mensagem, caminho_arquivo):
    def tarefa():
        if not garantir_playwright():
            messagebox.showerror("Erro", "Não foi possível preparar o motor de envio.")
            return
        
        caminho_sessao = os.path.join(os.getcwd(), "config", "sessao_whatsapp")
        numero_final = "55" + numero if not numero.startswith("55") else numero

        try:
            with sync_playwright() as p:
                browser = p.chromium.launch_persistent_context(
                    user_data_dir=caminho_sessao,
                    headless=False,
                    args=["--no-sandbox"]
                )
                page = browser.new_page()
                
                # Abre o chat diretamente
                url = f"https://web.whatsapp.com/send?phone={numero_final}&text={mensagem}"
                page.goto(url)

                # Espera o carregamento das conversas
                print("Carregando chat...")
                page.wait_for_selector('div[contenteditable="true"]', timeout=40000)
                page.wait_for_timeout(3000) 

                # Envia o texto da mensagem primeiro
                page.keyboard.press("Enter")
                page.wait_for_timeout(2000)

                
                print("Injetando arquivo no Chromium...")
                
                
                with page.expect_file_chooser() as fc_info:
                    # Clica no botão de anexo (+)
                    
                    print("Injetando arquivo...")
                    page.set_input_files("input[type='file']", caminho_arquivo)

                    # esperar o botão send e clicar
                    page.wait_for_selector('span[data-icon="send"]', timeout=30000)
                    page.keyboard.press("Enter")

                
                file_chooser = fc_info.value
                file_chooser.set_files(caminho_arquivo)
                print(f"Arquivo {os.path.basename(caminho_arquivo)} injetado com sucesso!")

                
                print("Aguardando prévia...")
                try:
                    # Espera o botão verde de enviar aparecer na prévia
                    botao_enviar = page.wait_for_selector('div[aria-label="Enviar"], span[data-icon="send"]', timeout=30000)
                    page.wait_for_timeout(2000)
                    botao_enviar.click()
                    print("Enviado!")
                except:
                    # Caso o botão falhe, o Enter funciona na tela de prévia
                    page.keyboard.press("Enter")

                # Tempo para garantir o upload antes de fechar o browser
                page.wait_for_timeout(6000) 
                
                browser.close()
                messagebox.showinfo("Sucesso", "Documento enviado com sucesso!")

        except Exception as e:
            print(f"Erro detectado: {e}")
            messagebox.showerror("Erro WhatsApp", f"Falha no envio:\n{e}")

    threading.Thread(target=tarefa, daemon=True).start()



def aba_vendas():
    limpar_tela()
    aplicar_fundo() 
    janela.title("Vendas")

    es_admin = (usuario_logado_tipo == 3)
    es_func  = (usuario_logado_tipo >= 2)
    es_visi  = (usuario_logado_tipo >= 1)

    BarraInferior()
    
    tk.Label(janela, text="Produto:", bg="white").place(x=10, y=10)
    ent_prod = tk.Entry(janela)
    ent_prod.place(x=10, y=30)

    ent_prod.bind("<F3>", lambda e: janela_busca_produto(e, ent_prod, ent_preco))

    tk.Label(janela, text="Preço Unitário:", bg="white").place(x=150, y=10)
    ent_preco = tk.Entry(janela)
    ent_preco.place(x=150, y=30)

    tk.Label(janela, text="Quantidade:", bg="white").place(x=290, y=10)
    ent_qtd = tk.Entry(janela)
    ent_qtd.place(x=290, y=30)

    tk.Label(janela, text="Total:", bg="white", font=("Arial", 10, "bold")).place(x=430, y=10)
    lbl_total = tk.Label(janela, text="R$ 0.00", bg="yellow", width=15)
    lbl_total.place(x=430, y=30)

    tk.Button(janela, text="➕ Gerenciar Produtos", bg="#3498db", fg="white", 
          font=("Arial", 9, "bold"), command=janela_gerenciar_produtos).place(x=550, y=80)
   
    def registrar_venda():
        prod = ent_prod.get() 
        try:
            preco = float(ent_preco.get())
            qtd_venda = int(ent_qtd.get())
            total = preco * qtd_venda
        except ValueError:
            messagebox.showerror("Erro", "Valores de preço ou quantidade inválidos!")
            return

        if prod and qtd_venda > 0: 
            conn = sqlite3.connect("dados/ges_dados.db")
            cur = conn.cursor()
    
            cur.execute("SELECT quantidade FROM produtos WHERE nome = ?", (prod,))
            resultado = cur.fetchone()

            if resultado:
                estoque_atual = resultado[0]
                if estoque_atual >= qtd_venda:
                    cur.execute("UPDATE produtos SET quantidade = quantidade - ? WHERE nome = ?", (qtd_venda, prod))
                    
                    
                    cur.execute("""
                        INSERT INTO vendas (tipo, produto, quantidade, valor_total) 
                        VALUES ('SAIDA', ?, ?, ?)
                    """, (prod, qtd_venda, total))
                
                    conn.commit()
                    messagebox.showinfo("Sucesso", f"Venda de {prod} realizada!\nTotal: R$ {total:.2f}")
                    aba_vendas() 
                else:
                    messagebox.showwarning("Estoque Insuficiente", f"Você só tem {estoque_atual} unidades.")
            else:
                messagebox.showerror("Erro", "Produto não encontrado!")
        
            conn.close()
        else:
            messagebox.showwarning("Atenção", "Preencha todos os campos corretamente!")

    finalizar_venda = tk.Button(janela, 
                                text="Finalizar Venda", 
                                bg=COR_SUCESSO, 
                                fg="white", 
                                cursor="hand2", 
                                command=registrar_venda)

    finalizar_venda.place(x=550, y=28)
    tk.Button(janela, text="Voltar", command=menu_principal).place(x=10, y=450)

    campos_venda = [ent_prod, ent_preco, ent_qtd, finalizar_venda]
    pulo_sequencial(campos_venda)

    finalizar_venda.bind("<Return>", lambda e: registrar_venda())

tabela_estoque_referencia = None



def estoque():
    global tabela_estoque_referencia
    limpar_tela()
    aplicar_fundo()
    janela.title("Estoque - Gerenciamento")

    es_admin = (usuario_logado_tipo == 3)
    es_func  = (usuario_logado_tipo >= 2)
    es_visi  = (usuario_logado_tipo >= 1)

    BarraInferior()

    tk.Label(janela, text="Nome do Produto:", bg="white").place(x=10, y=10)
    ent_nome = tk.Entry(janela)
    ent_nome.place(x=10, y=30)

    tk.Label(janela, text="Preço Custo:", bg="white").place(x=150, y=10)
    ent_custo = tk.Entry(janela)
    ent_custo.place(x=150, y=30)

    tk.Label(janela, text="Quantidade Inicial:", bg="white").place(x=290, y=10)
    ent_quantidade = tk.Entry(janela)
    ent_quantidade.place(x=290, y=30)

    tk.Button(janela, text="➕ Gerenciar Produtos", bg="#3498db", fg="white", 
          font=("Arial", 9, "bold"), command=janela_gerenciar_produtos).place(x=550, y=80)

    colunas = ("ID", "Produto", "Custo", "Qtd")
    tabela = ttk.Treeview(janela, columns=colunas, show="headings")

    for col in colunas:
        tabela.heading(col, text=col)
        tabela.column(col, width=100)
    tabela.place(x=10, y=110, width=600, height=300)

    

    def salvar_produto():
        nome = ent_nome.get()
        custo = ent_custo.get()
        qtd = ent_quantidade.get()
        if nome and custo and qtd:
            conn = sqlite3.connect("dados/ges_dados.db")
            cur = conn.cursor()
            cur.execute("INSERT INTO produtos (nome, preco_custo, quantidade) VALUES (?, ?, ?)", (nome, custo, qtd))
            conn.commit()
            conn.close()
            
            if tabela_estoque_referencia and tabela_estoque_referencia.winfo_exists():
               tabela_estoque_referencia.atualizar()
            
            messagebox.showinfo("Sucesso", "Produto cadastrado!")
            atualizar_tabela()
            
            
        else:
            messagebox.showwarning("Atenção", "Preencha todos os campos!")

    def atualizar_tabela():
        if not tabela.winfo_exists(): return 

        for i in tabela.get_children(): #Limpa a tabela 
            tabela.delete(i)

        conn = sqlite3.connect("dados/ges_dados.db")
        cur = conn.cursor()
        cur.execute("SELECT id, nome, preco_custo, quantidade FROM produtos")
        for linha in cur.fetchall():
            tabela.insert("", "end", values=linha)
        conn.close()


    tabela.atualizar = atualizar_tabela
    tabela_estoque_referencia = tabela
        
    atualizar_tabela()

    def acao_salvar_local():
        salvar_produto()
        atualizar_tabela()

    salvar_estoque = tk.Button(janela, text="Salvar Produto", command=acao_salvar_local)
    salvar_estoque.place(x=430, y=25)

    campos_estoque = [ent_nome, ent_custo, ent_quantidade, salvar_estoque]
    pulo_sequencial(campos_estoque)

    salvar_estoque.bind("<Return>", lambda e: salvar_produto())

    tk.Button(janela, text="Voltar", command=menu_principal).place(x=10, y=420)
    atualizar_tabela()


def gerar_relatorio_excel():
    nome_arquivo = "relatorio_estoque.csv"
    conn = sqlite3.connect("dados/ges_dados.db")
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


def abrir_no_libre_office():
    import subprocess
    nome_arquivo = "relatorio_geral_estoque.csv"
    
    try:
        conn = sqlite3.connect("dados/ges_dados.db")
        cur = conn.cursor()
        cur.execute("SELECT id, nome, preco_custo, quantidade FROM produtos")
        dados = cur.fetchall()
        conn.close()

        # Criado o CSV usando o ponto e vírgula (;) que o Calc reconhece 
        with open(nome_arquivo, "w", newline="", encoding="utf-8-sig") as f:
            escritor = csv.writer(f, delimiter=";")
            escritor.writerow(["ID", "PRODUTO", "PRECO CUSTO", "ESTOQUE ATUAL"])
            escritor.writerows(dados)

        # O comando os.startfile abre o arquivo no programa padrão do Windows.
        # Se o LibreOffice for o leitor padrão de planilhas, ele abrirá na hora.
        os.startfile(nome_arquivo)
        
    except Exception as e:
        messagebox.showerror("Erro", f"Não foi possível abrir o LibreOffice: {e}")
    
    caminhos = [
        r"C:\Program Files\LibreOffice\program\scalc.exe",
        r"C:\Program Files (x86)\LibreOffice\program\scalc.exe"
    ]
    
    abriu = False
    for caminho in caminhos:
        if os.path.exists(caminho):
            subprocess.Popen([caminho, nome_arquivo])
            abriu = True
            break
            
    if not abriu:
        os.startfile(nome_arquivo)

def atualizar_relogio():
    try:
        agora = datetime.now().strftime("%H:%M  %d/%m/%Y")
        # Verifica se o label ainda existe antes de configurar
        if 'lbl_relogio' in globals() and lbl_relogio.winfo_exists():
            lbl_relogio.config(text=agora)
            janela.after(1000, atualizar_relogio)
    except Exception:
        pass

def BarraInferior():
    global usuario_logado_tipo

    es_admin = (usuario_logado_tipo == 3)

    barra = tk.Frame(janela, bg="#0a0f24", height=40)
    barra.pack(side="bottom", fill="x")

    # Versão
    tk.Label(barra, text="V.00.00.01", fg="white", bg="#0a0f24", font=("Segoe UI", 9)).pack(side="left", padx=20)

    
    global lbl_relogio 
    lbl_relogio = tk.Label(barra, text="", fg="white", bg="#0a0f24", font=("Segoe UI", 10))
    lbl_relogio.pack(side="right", padx=20)

    # botao Config
    btn_settings = tk.Label(
        barra, text="⚙️", 
        fg="white" if es_admin else "#444", 
        bg="#0a0f24", font=("Segoe UI", 12),
        cursor="hand2" if es_admin else "arrow"
    )
    btn_settings.pack(side="right", padx=15)

    
    if es_admin:
        btn_settings.bind("<Button-1>", lambda e: configuracoes())
    
    atualizar_relogio()

 
def menu_principal():
    limpar_tela()
    aplicar_fundo()
    janela.title("Menu Principal - GES")

    es_admin = (usuario_logado_tipo == 3)
    es_func  = (usuario_logado_tipo >= 2)
    es_visi  = (usuario_logado_tipo >= 1)
    
    BarraInferior()

    # Função auxiliar para criar botões rapidamente
    def criar_btn(texto, comando, row, col, cor=COR_PRIMARIA, estado="normal"):
        btn = tk.Button(frame_menu, text=texto, command=comando, bg=cor, fg=COR_TEXTO_BOTAO,
                        font=FONTE_PADRAO, width=25, height=2, bd=0, cursor="hand2", state=estado)
        btn.grid(row=row, column=col, padx=10, pady=10)
        # Efeito de "hover" (muda cor ao passar o mouse)
        btn.bind("<Enter>", lambda e: btn.config(bg="#34495e"))
        btn.bind("<Leave>", lambda e: btn.config(bg=cor))
        return btn

    # Frame central para organizar os botões
    frame_menu = tk.Frame(janela, bg="white", bd=2, relief="groove")
    frame_menu.place(relx=0.5, rely=0.5, anchor="center") 

    tk.Label(frame_menu, text="PAINEL DE CONTROLE", bg="white", 
             fg=COR_PRIMARIA, font=("Segoe UI", 14, "bold")).grid(row=0, column=0, columnspan=2, pady=20)

    
    # Coluna 1: Operacional
    criar_btn("🛒 VENDAS (SAÍDA)", 
              aba_vendas, 1, 0, 
              cor="#c91441", 
              estado="normal" if es_visi else "disabled")

    criar_btn("📦 ESTOQUE (PRODUTOS)", 
              estoque, 2, 0, 
              cor="#50a0e6", 
              estado="normal" if es_visi else "disabled")

    criar_btn("📥 COMPRAS (ENTRADA)", 
              aba_compras, 3, 0, 
              cor="#d6a229", 
              estado="normal" if es_visi else "disabled")

    whatsapp = criar_btn("📱 CONECTAR WHATSAPP", 
                         configurar_whatsapp, 4, 0, 
                         cor="#25D366", 
                         estado="normal" if es_admin else "disabled")
    whatsapp.configure(fg="black")

    # Coluna 2: Administrativo
    criar_btn("📊 RELATÓRIO LOCAL", 
              gerar_relatorio_excel, 1, 1, 
              cor=COR_SUCESSO, 
              estado="normal" if es_visi else "disabled")

    criar_btn("📊 LIBREOFFICE CALC", 
              abrir_no_libre_office, 2, 1, 
              cor=COR_SUCESSO, 
              estado="normal" if es_visi else "disabled")

    criar_btn("🗣️ Clientes", 
              clientes_cad, 4, 1, 
              cor="#4a40a8", 
              estado="normal" if es_visi else "disabled")
    
    btn_sair = tk.Button(janela, text="SAIR", command=janela.quit, bg="#c0392b", 
                         fg="white", font=FONTE_PADRAO, padx=20)
    btn_sair.place(relx=0.98, rely=0.02, anchor="ne")
    

    def janela_envio_whatsapp():
        # Seleciona o arquivo
        arquivo = filedialog.askopenfilename(title="Selecione o Documento para enviar")
        if not arquivo:
            return

        
        top_zap = tk.Toplevel(janela)
        top_zap.title("Enviar via WhatsApp")
        top_zap.geometry("300x200")
        top_zap.attributes("-topmost", True)
        top_zap.configure(bg="white")
    
        # Centralizar a janelinha
        top_zap.update_idletasks()
        x = (top_zap.winfo_screenwidth() // 2) - (150)
        y = (top_zap.winfo_screenheight() // 2) - (100)
        top_zap.geometry(f"+{x}+{y}")

        tk.Label(top_zap, text="Número do Cliente (com DDD):", bg="white", font=FONTE_PADRAO).pack(pady=10)
    
        ent_num = tk.Entry(top_zap, font=("Arial", 12), justify="center")
        ent_num.pack(pady=5, padx=20, fill="x")
        ent_num.insert(0, "45") 
        ent_num.focus_set()

        def confirmar_envio():
            numero = ent_num.get().strip().replace(" ", "").replace("-", "")
            if len(numero) < 10:
                messagebox.showwarning("Atenção", "Digite um número válido com DDD!", parent=top_zap)
                return
            
            # Fecha a janelinha e chama a função pesada no fundo (Thread)
            top_zap.destroy()
            enviar_doc_whatsapp(numero, "Olá, segue o documento da sua compra!", arquivo)

        btn_enviar = tk.Button(top_zap, text="ENVIAR AGORA", bg="#25D366", fg="white", 
                           font=FONTE_PADRAO, command=confirmar_envio)
        btn_enviar.pack(pady=20)
    
        # Atalho: apertar Enter para enviar
        top_zap.bind("<Return>", lambda e: confirmar_envio())

    Enviar_zap = criar_btn("📄 ENVIAR NOTA (WHATSAPP)", 
                           janela_envio_whatsapp, 3, 1, 
                           cor="#075E54", 
                           estado="normal" if es_visi else "disabled")
    
    


def tela_login():
    janela_login = tk.Toplevel(janela)
    janela_login.title("Acesso ao Sistema")
    janela_login.geometry("300x250")
    janela_login.grab_set()  # Bloqueia interação com a janela principal

    janela_login.attributes("-topmost", True)
    janela_login.focus_force()
    janela_login.grab_set()

    agora = datetime.now()
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

    ent_usuario.focus_set()
    
    janela_login.after(100, lambda: ent_usuario.focus_force())

    def realizar_login(event=None):

        global usuario_logado_tipo, tentativas
        u = var_usuario.get()
        s = var_senha.get()
        
        if not u or not s:
            messagebox.showwarning("Atenção", "Preencha todos os campos!", parent=janela_login)
            return

        conn = sqlite3.connect("dados/ges_dados.db")
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

    btn_entrar = tk.Button(janela_login, text="Entrar", bg="green", fg="black", command=realizar_login)
    btn_entrar.pack(pady=20)
    
    # Faz o login funcionar ao apertar Enter
    janela_login.bind("<Return>", realizar_login)


def conectar_banco():

    pasta_db = os.path.dirname(caminho_banco)
    if not os.path.exists(pasta_db):
        os.makedirs(pasta_db)
    
    conexao = sqlite3.connect(caminho_banco)

    def instalar_dependencias_playwright():
        try:
            # Tenta verificar se o chromium está instalado
            subprocess.run(["playwright", "install", "chromium"], check=True)
        except:
            pass

    conexao = sqlite3.connect(caminho_banco)
    cursor = conexao.cursor()
    
    # Tabelas Existentes
    cursor.execute("CREATE TABLE IF NOT EXISTS produtos (id INTEGER PRIMARY KEY AUTOINCREMENT, nome TEXT NOT NULL, preco_custo REAL NOT NULL, quantidade INTEGER NOT NULL DEFAULT 1)")
    cursor.execute("CREATE TABLE IF NOT EXISTS vendas (id INTEGER PRIMARY KEY AUTOINCREMENT, tipo TEXT, produto TEXT NOT NULL, quantidade INTEGER NOT NULL DEFAULT 1, valor_total REAL NOT NULL, data TIMESTAMP DEFAULT CURRENT_TIMESTAMP)")

    
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS usuarios (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            usuario TEXT NOT NULL UNIQUE,
            senha TEXT NOT NULL,
            tipo INTEGER NOT NULL -- 1 para Admin, 0 para Geral
        )
    """)

   
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS clientes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nome TEXT NOT NULL UNIQUE,
            cpf TEXT NOT NULL UNIQUE,
            telefone_Whats TEXT NOT NULL
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS vendas
            (id INTEGER PRIMARY KEY AUTOINCREMENT,
            nome TEXT NOT NULL UNIQUE,
            tipo TEXT,
            produto TEXT NOT NULL,
            quantidade INTEGER NOT NULL,
            valor_total REAL NOT NULL,
            data TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # Criar usuários padrão 
    cursor.execute("SELECT COUNT(*) FROM usuarios")
    if cursor.fetchone()[0] == 0:
        cursor.execute("INSERT INTO usuarios (usuario, senha, tipo) VALUES ('admin', 'admin123', 3)")
        cursor.execute("INSERT INTO usuarios (usuario, senha, tipo) VALUES ('geral', '1', 0)")

    conexao.commit()
    conexao.close()


conectar_banco()

janela.withdraw() 
tela_login()       
janela.mainloop()