import flet as ft
import sqlite3
from datetime import datetime, timedelta

# --- 1. BANCO DE DADOS ---
class Database:
    def __init__(self):
        self.conn = sqlite3.connect("dados.db", check_same_thread=False)
        self.cursor = self.conn.cursor()
        self.criar_tabela()

    def criar_tabela(self):
        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS tarefas (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                titulo TEXT,
                status TEXT,
                responsavel TEXT,
                prazo_dias INTEGER,
                data_criacao TEXT,
                data_conclusao TEXT
            )
        """)
        self.conn.commit()

    def adicionar(self, titulo, responsavel, prazo):
        agora = datetime.now().strftime("%d/%m/%Y %H:%M")
        self.cursor.execute("""
            INSERT INTO tarefas (titulo, status, responsavel, prazo_dias, data_criacao, data_conclusao) 
            VALUES (?, ?, ?, ?, ?, ?)""", 
            (titulo, "pendente", responsavel, prazo, agora, "")
        )
        self.conn.commit()

    def listar(self, filtro_status, termo_busca=""):
        query = "SELECT * FROM tarefas WHERE status = ?"
        params = [filtro_status]
        if termo_busca:
            termo = f"%{termo_busca.lower()}%"
            query += " AND (LOWER(titulo) LIKE ? OR LOWER(responsavel) LIKE ?)"
            params.append(termo)
            params.append(termo)
        self.cursor.execute(query, params)
        return self.cursor.fetchall()
    
    def listar_todas(self):
        self.cursor.execute("SELECT * FROM tarefas")
        return self.cursor.fetchall()
    
    def listar_nomes_usados(self):
        self.cursor.execute("SELECT DISTINCT responsavel FROM tarefas")
        return [row[0] for row in self.cursor.fetchall() if row[0]]

    def atualizar_status(self, id_tarefa, novo_status):
        data_fim = datetime.now().strftime("%d/%m/%Y %H:%M") if novo_status == "concluida" else ""
        self.cursor.execute("""
            UPDATE tarefas SET status = ?, data_conclusao = ? WHERE id = ?""", 
            (novo_status, data_fim, id_tarefa)
        )
        self.conn.commit()

    def excluir(self, id_tarefa):
        self.cursor.execute("DELETE FROM tarefas WHERE id = ?", (id_tarefa,))
        self.conn.commit()

db = Database()

# --- 2. FRONTEND ---
def main(page: ft.Page):
    page.title = "Tarefas do dia a dia"
    page.bgcolor = "white"
    page.window_width = 450
    page.window_height = 800
    page.padding = 15
    page.scroll = "auto"
    page.vertical_alignment = "start" 

    lista_pendentes = ft.Column()
    lista_concluidas = ft.Column(visible=False)
    area_estatisticas = ft.Column(visible=False)
    
    linha_sugestoes = ft.Row(wrap=True, spacing=5) 

    # --- NAVEGAÇÃO ---
    def navegar(e):
        if isinstance(e, str): tela = e
        else: tela = e.control.data 
        
        lista_pendentes.visible = False
        lista_concluidas.visible = False
        area_estatisticas.visible = False
        
        btn_pendentes.bgcolor = "white"
        btn_concluidas.bgcolor = "white"
        btn_stats.bgcolor = "white"

        if tela == "pendente":
            lista_pendentes.visible = True
            btn_pendentes.bgcolor = "#BBDEFB"
        elif tela == "concluida":
            lista_concluidas.visible = True
            btn_concluidas.bgcolor = "#C8E6C9"
        elif tela == "stats":
            gerar_relatorio()
            area_estatisticas.visible = True
            btn_stats.bgcolor = "#FFECB3"
        page.update()

    def gerar_relatorio():
        area_estatisticas.controls.clear()
        todas = db.listar_todas()
        placar = {}
        for t in todas:
            resp = t[3]
            status = t[2]
            if resp not in placar: placar[resp] = {"total": 0, "concluidas": 0}
            placar[resp]["total"] += 1
            if status == "concluida": placar[resp]["concluidas"] += 1

        area_estatisticas.controls.append(ft.Text("Resumo Geral:", size=20, weight="bold", color="black"))
        for nome, dados in placar.items():
            area_estatisticas.controls.append(
                ft.Container(
                    padding=10, bgcolor="#F0F0F0", border_radius=10, margin=ft.margin.only(bottom=5),
                    content=ft.Row([
                        ft.Text(f"👤 {nome}", weight="bold", size=16, color="black"),
                        ft.Text(f"Total: {dados['total']} | ✅ {dados['concluidas']}", color="grey")
                    ], alignment="spaceBetween")
                )
            )
        page.update()

    # --- SUGESTÕES DE NOMES ---
    def usar_sugestao(nome_clicado):
        campo_responsavel.value = nome_clicado
        campo_responsavel.focus()
        page.update()

    def carregar_sugestoes():
        linha_sugestoes.controls.clear()
        nomes = db.listar_nomes_usados()
        
        for nome in nomes:
            if nome.strip():
                btn = ft.ElevatedButton(
                    nome,
                    height=30,
                    bgcolor="#E3F2FD",
                    color="#1565C0",
                    on_click=lambda e, n=nome: usar_sugestao(n)
                )
                linha_sugestoes.controls.append(btn)
        page.update()

    # --- CARTÃO DE TAREFA ---
    def criar_card(dados, feito):
        id_t, titulo, status, resp, prazo, criacao, conclusao = dados
        
        cor_fundo = "#F5F5F5"
        texto_extra = ""
        cor_texto_prazo = "grey"
        
        try:
            dt_criacao = datetime.strptime(criacao, "%d/%m/%Y %H:%M")
            texto_info = f"👤 {resp} | Criado: {dt_criacao.strftime('%d/%m')}"
            
            if prazo > 0:
                dt_limite = dt_criacao + timedelta(days=prazo)
                hoje = datetime.now()
                texto_info += f" | 🎯 {dt_limite.strftime('%d/%m')}"
                
                if not feito and hoje > dt_limite:
                    cor_fundo = "#FFCDD2" # Alerta Vermelho
                    texto_extra = "⚠️ ATRASADO"
                    cor_texto_prazo = "red"
        except:
            texto_info = f"👤 {resp}"

        painel_card = ft.Container(
            padding=10, bgcolor=cor_fundo, border_radius=8, margin=ft.margin.only(bottom=10)
        )

        def check_changed(e):
            novo = "concluida" if e.control.value else "pendente"
            db.atualizar_status(id_t, novo)
            carregar_tarefas()

        def mostrar_confirmacao(e):
            painel_card.content = layout_confirmacao
            painel_card.bgcolor = "#FFEBEE"
            page.update()

        conteudo_normal = [
            ft.Row([
                ft.Checkbox(label=titulo, value=feito, on_change=check_changed),
                ft.TextButton("X", on_click=mostrar_confirmacao, style=ft.ButtonStyle(color="red"))
            ], alignment="spaceBetween"),
            ft.Row([
                ft.Text(texto_info, size=11, color=cor_texto_prazo),
                ft.Text(texto_extra, size=11, weight="bold", color="red")
            ], alignment="spaceBetween")
        ]
        
        layout_normal = ft.Column(conteudo_normal)

        def cancelar_exclusao(e):
            painel_card.content = layout_normal
            painel_card.bgcolor = cor_fundo
            page.update()

        def confirmar_exclusao(e):
            db.excluir(id_t)
            carregar_tarefas()

        layout_confirmacao = ft.Column([
            ft.Text("Apagar tarefa?", color="red", weight="bold", size=12),
            ft.Row([
                ft.ElevatedButton("Não", on_click=cancelar_exclusao, height=30),
                ft.ElevatedButton("Sim", on_click=confirmar_exclusao, bgcolor="red", color="white", height=30)
            ], alignment="end")
        ])

        painel_card.content = layout_normal
        return painel_card

    # --- LÓGICA PRINCIPAL ---
    def carregar_tarefas(e=None):
        termo = campo_busca.value
        lista_pendentes.controls.clear()
        lista_concluidas.controls.clear()
        
        for t in db.listar("pendente", termo):
            lista_pendentes.controls.append(criar_card(t, False))
        for t in db.listar("concluida", termo):
            lista_concluidas.controls.append(criar_card(t, True))
        page.update()

    def adicionar_click(e):
        if not campo_tarefa.value: return

        nome = campo_tarefa.value
        resp = campo_responsavel.value if campo_responsavel.value else "Geral"
        try: dias = int(campo_prazo.value) if campo_prazo.value else 0
        except: dias = 0
            
        db.adicionar(nome, resp, dias)
        
        campo_tarefa.value = ""
        campo_responsavel.value = "" 
        campo_prazo.value = ""
        
        carregar_tarefas()
        carregar_sugestoes()
        navegar("pendente")

    # --- INPUTS ---
    campo_busca = ft.TextField(hint_text="🔍 Buscar...", expand=True, on_change=carregar_tarefas, height=40, text_size=14)
    btn_buscar = ft.ElevatedButton("Ir", on_click=carregar_tarefas, height=40)

    campo_tarefa = ft.TextField(label="O que fazer?", border_color="blue", expand=True)
    campo_responsavel = ft.TextField(label="Quem?", hint_text="Nome", expand=True, height=50)
    campo_prazo = ft.TextField(label="Dias", width=80, keyboard_type="number", text_align="center", height=50)

    btn_add = ft.ElevatedButton("+", on_click=adicionar_click, bgcolor="blue", color="white", width=50, height=50)

    linha_detalhes = ft.Row(
        controls=[campo_responsavel, campo_prazo, btn_add],
        alignment="spaceBetween"
    )

    painel_criacao = ft.Container(
        padding=15,
        bgcolor="#F9F9F9",
        border_radius=15,
        border=ft.border.all(1, "#E0E0E0"),
        content=ft.Column([
            ft.Text("Nova Tarefa", weight="bold", size=16, color="#1565C0"),
            campo_tarefa,
            linha_detalhes,
            ft.Text("Usar recente:", size=12, color="grey"),
            linha_sugestoes
        ])
    )

    btn_pendentes = ft.ElevatedButton("A Fazer", data="pendente", on_click=navegar, bgcolor="#BBDEFB", expand=True)
    btn_concluidas = ft.ElevatedButton("Feitas", data="concluida", on_click=navegar, bgcolor="white", expand=True)
    btn_stats = ft.ElevatedButton("Resumo", data="stats", on_click=navegar, bgcolor="white", expand=True)

    # --- MONTAGEM DA PÁGINA (COM BANDEIRAS) ---
    page.add(
        # TOPO: Título + Bandeiras
        ft.Row([
            # Título (com expand para empurrar as bandeiras pro canto)
            ft.Text("Tarefas do dia a dia", size=24, weight="bold", color="#1565C0"),
            ft.Container(expand=True), 
            
            # Bandeira de Cuba (Esquerda)
            ft.Image(
                src="https://flagcdn.com/w40/cu.png",
                width=30, height=20, border_radius=3,
                tooltip="Cuba"
            ),
            
            ft.Container(width=5), # Espacinho entre elas
            
            # Bandeira do Brasil (Direita)
            ft.Image(
                src="https://flagcdn.com/w40/br.png",
                width=30, height=20, border_radius=3,
                tooltip="Brasil"
            ),
        ]),
        
        ft.Row([campo_busca, btn_buscar]),
        
        ft.Divider(height=10, color="transparent"),
        painel_criacao,
        ft.Divider(height=10, color="transparent"),
        
        ft.Row([btn_pendentes, btn_concluidas, btn_stats]),
        
        ft.Column([lista_pendentes, lista_concluidas, area_estatisticas], expand=True, scroll="auto"),
        
        ft.Divider(),
        ft.Container(
            content=ft.Text("Desenvolvido por Ricardo Perez", size=12, color="grey", italic=True),
            alignment=ft.Alignment(0, 0),
            padding=10
        )
    )
    
    carregar_tarefas()
    carregar_sugestoes()

ft.app(target=main)
