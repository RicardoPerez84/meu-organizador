import flet as ft
import json
import os

def main(page: ft.Page):
    page.title = "Meu Organizador Universal"
    # Ajuste simples de tema
    page.theme_mode = "light" 
    page.window_width = 400
    page.window_height = 600
    page.padding = 20

    # Nome do arquivo onde as tarefas ficam salvas no Windows
    arquivo_banco_dados = "tarefas.json"

    # --- FUNÇÃO DE SALVAR (Compatível com versões antigas) ---
    def save_tasks():
        task_list = []
        # Varre a coluna de tarefas
        for row in tasks_view.controls:
            if len(row.controls) > 0:
                checkbox = row.controls[0]
                task_list.append({"label": checkbox.label, "value": checkbox.value})
        
        try:
            with open(arquivo_banco_dados, "w", encoding="utf-8") as f:
                json.dump(task_list, f, indent=4)
        except Exception as e:
            print(f"Erro ao salvar: {e}")

    # --- FUNÇÃO DE CARREGAR ---
    def load_tasks():
        if os.path.exists(arquivo_banco_dados):
            try:
                with open(arquivo_banco_dados, "r", encoding="utf-8") as f:
                    saved = json.load(f)
                    for item in saved:
                        add_task_to_screen(item["label"], item["value"])
            except:
                pass 

    # --- FUNÇÃO QUE CRIA O VISUAL DA TAREFA ---
    def add_task_to_screen(text, is_checked=False):
        def delete_clicked(e):
            tasks_view.controls.remove(row)
            save_tasks()
            page.update()

        def checkbox_changed(e):
            save_tasks()
        
        checkbox = ft.Checkbox(label=text, value=is_checked, on_change=checkbox_changed, expand=True)
        
        # Botão Vermelho usando string simples "red" para não dar erro
        delete_btn = ft.ElevatedButton(
            "Excluir", 
            on_click=delete_clicked, 
            bgcolor="#ffcccc", 
            color="red" 
        )

        row = ft.Row([checkbox, delete_btn], alignment="spaceBetween")
        tasks_view.controls.append(row)
        page.update()

    # --- AÇÃO DO BOTÃO ADICIONAR ---
    def add_clicked(e):
        if not new_task.value:
            return

        add_task_to_screen(new_task.value)
        save_tasks()
        new_task.value = ""
        new_task.focus()
        page.update()

    # --- MONTAGEM DA TELA ---
    new_task = ft.TextField(hint_text="Escreva a tarefa...", expand=True, on_submit=add_clicked)
    tasks_view = ft.Column()

    # Tenta carregar dados antigos
    load_tasks()

    page.add(
        ft.Text("Minhas Tarefas", size=30, weight="bold"),
        ft.Row(
            [
                new_task,
                ft.ElevatedButton("Adicionar", on_click=add_clicked),
            ]
        ),
        tasks_view,
    )

ft.app(target=main)