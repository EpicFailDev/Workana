from datetime import datetime
import requests
import time
import os, sys
from playsound import playsound
from rich.console import Console
from rich.markdown import Markdown
from bs4 import BeautifulSoup
from rich.progress import Progress


def resource_path(relative_path):
    """Obter o caminho do recurso, considerando o ambiente de execução."""
    if hasattr(sys, '_MEIPASS'):
        return os.path.join(sys._MEIPASS, relative_path)
    return os.path.join(os.path.abspath("."), relative_path)

def write_logs(project):
    pass
    # with open("log-project.txt", 'a') as f:
    #     f.write(f'{datetime.now()}')
    #     f.write('\n')
    #     f.write(project)
    #     f.write('\n')
    #     f.close()

def reload_time(duracao: int):
    try:
        with Progress() as progress:
            task = progress.add_task("", total=duracao)
            while not progress.finished:
                time.sleep(0.1)  
                progress.update(task, advance=0.1)
    except KeyboardInterrupt:
        console.print("[bold red]Saindo...[/bold red]")
        exit(0)

# def gerarRemumoComGemini(desc: str):
    
#     try:
#         client = Gemini(cookies=cookies, auto_cookies=True, verify=True)
#         res = client.generate_content(f"""Crie um resumo conciso e informativo para o seguinte projeto:
# Descrição do projeto: {desc}

# Formato do resumo me retorne apenas isso e nada mais nada nenhum o ok nem nada só o resmumo nesse formato:
# Dá pra fazer: Sim ou Não, só quero utilizar flutter, firebase, mongodb, nextjs, typescript/javascript e só mente isso me retorne se dá pra fazer de acordo com essas caracteristicas
# Estimativa de Prazo: [Insira um prazo estimado em meses, considere 6 a 8 horas por dia de seg a sex no cauculo]
# Resumo do Projeto: Um resumo curto de no máximo 10 linhas, destacando os principais objetivos, funcionalidades e tecnologias envolvidas.""")
    
#         format_response = render_md(res.text)
#     except:
#         format_response = "Erro ao conectar com Gemmi"
    
#     return format_response

def remove_html(html_str):
    soup = BeautifulSoup(html_str, "html.parser")
    return soup.get_text()

# def render_md(md: str):
#     md_render = Markdown(md)
#     return md_render

def clear():
    os.system('cls' if os.name == 'nt' else 'clear')

def parser(html):
    results = html["results"]["results"]
    return [f"""[green][bold]🚸 Titulo: [/bold][/green]{remove_html(result['title'])}\n[bold][green]🔥 Postado em:[/bold][/green] {result['postedDate']}\n[bold][green]⚡️ Ultima Resposta:[/bold][/green] {result['lastEmployerMessage']}\n[bold][green]⛓️‍💥 Url:[/bold][/green] [link=https://www.workana.com/messages/bid/{result['slug']}/?tab=message&ref=project_view]Clique aqui[/link]""" for result in results if not result['isSearchFeatured'] and int(result['totalBids'].split(" ")[1]) < 4]


console = Console()

def main(url: str):
    output = []
    description = ""
    headers = {
        "User-Agent": "curl/8.7.1",
        "Accept": "*/*",
        "x-requested-with": "XMLHttpRequest"
    }

    while True:
        bak_output = output
        bak_description = description
        try:
            clear()
            console.print("[bold blue]🍃 Buscando Novos Projetos... [/bold blue]")
            res = requests.get(url=url, headers=headers)
            console.print(f"[bold blue]🍃 Status: {res.status_code} [/bold blue]")
            try:
                # print(res.json())
                # input("Press any key to continue...")
                output = parser(res.json())
                descriptions = [f"{result['description']}" for result in res.json()["results"]["results"] if not result["isSearchFeatured"]]            
            except Exception:
                console.print("[bold cyan]🍂 Tempo para n tomar timeout[/bold cyan]")
                print("Erro: err")
                reload_time(60)
                continue
            clear()
            console.print(output[0])
            if bak_description != "":
                console.print("[bold][blue]🤖 Resumo gerado pelo Gemini: [/bold][/blue]")
                console.print(description)
            if len(bak_output) > 0:
                i = output[0]
                i = i.split("\n")
                i = i[0]
                j = bak_output[0]
                j = j.split("\n")
                j = j[0]
                if j != i:
                    notification_path = resource_path("notification.mp3")
                    playsound(notification_path)
                    # description = gerarRemumoComGemini(descriptions[0])
                    # console.print("[bold][blue]🤖 Resumo gerado pelo Gemini: [/bold][/blue]")
                    # console.print(description)
                    write_logs(output[0])

        except ConnectionError:
            clear()
            console.print("[bold red]Erro de Conexão[/bold red]")
        except KeyboardInterrupt:
            console.print("[bold red]Saindo...[/bold red]")
            exit(0)
            break
        reload_time(60)

def banner():
    console.print("[bold green]------------------------------[/bold green]")
    console.print("[bold cyan]-    NOTIFICAÇÃO DA WORKANA  -[/bold cyan]")
    console.print("[bold green]------------------------------[/bold green]")

def menu():
    while True:
        clear()
        url1 = "https://www.workana.com/jobs?category=it-programming&has_few_bids=1&language=pt&publication=1d"
        url2 = "https://www.workana.com/jobs?category=it-programming&language=pt&publication=1d&subcategory=mobile-development"
        console.print("[bold green]---------------------------------[/bold green]")
        console.print("[bold cyan]-   SELECIONE QUAL FILTRO USAR  -[/bold cyan]")
        console.print("[bold green]---------------------------------[/bold green]")
        console.print(f"[bold green][[bold cyan]01[/bold cyan]][bold green] - Filtro 1 [bold cyan][link={url1}][Clique aqui][/link][/bold cyan][/bold green]")
        console.print(f"[bold green][[bold cyan]02[/bold cyan]][bold green] - Filtro 2 [bold cyan][link={url2}][Clique aqui][/link][/bold cyan][/bold green]")
        console.print(f"[bold green][[bold cyan]03[/bold cyan]][bold green] - Filtro Personalizado[/bold green]")
        console.print(f"[bold green][[bold red]00[/bold red]][bold green] - [bold red]Sair[/bold red][/bold green]")
        
        try:
            op = int(console.input("[bold green]=> [/bold green]"))
        except KeyboardInterrupt:
            console.print("[bold red]Saindo...[/bold red]")
            exit(0)
        except:
            op = None
        
        if op == 00:
            exit(0)
        elif op == 1:
            return url1
        elif op == 2:
            return url2
        elif op == 3:
            url = console.input("[bold green]Cole aqui a Url da Pesquisa: [/bold green]")
            return url
        else:
            clear()
            console.print(f"[bold yellow]DIGITE APENAS UMA DAS OPÇÕES A CIMA[/bold yellow]")
            console.print(f"[bold yellow]TENTE NOVAMENTE EM 3 SEGUNDOS[/bold yellow]")
            reload_time(3)
        
    
    
    
banner()
time.sleep(2)
url = menu()

main(url=url)