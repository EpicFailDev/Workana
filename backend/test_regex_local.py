import re

def test_regex_on_text():
    with open("lucas_full_text.txt", "r", encoding="utf-8") as f:
        body_text = f.read()

    # Simulation of getMetric in JS (with fixed patterns)
    # In JS, the regexes were:
    # Ranking: (?:Ranking Workana|Ranking).*?([\d.]+)
    # Projects: (?:Projetos realizados|Completed projects)[\s\n]*(\d+)
    # Reviews: (?:Classificações dos clientes|Ratings from clients)[\s\n]*\(?(\d+)\)?
    
    patterns = {
        "Ranking": r"(?:Ranking Workana|Ranking).*?([\d.]+)",
        "Projects": r"(?:Projetos realizados|Completed projects)[\s\n]*(\d+)",
        "Hours": r"(?:Horas trabalhadas|Hours worked)[\s\n]*(\d+)",
        "Reviews": r"(?:Classificações dos clientes|Ratings from clients)[\s\n]*\(?(\d+)\)?",
        "Member Since": r"(?:Ingressou|Joined|Member since)[\s\n]+([^\n]{3,30})",
        "Last Login": r"(?:Último login|Last login)[\s\n]+([^\n]{3,30})"
    }

    results = {}
    for name, pattern in patterns.items():
        match = re.search(pattern, body_text, re.IGNORECASE | re.DOTALL)
        results[name] = match.group(1) if match else "MISS"

    print("--- REGEX RESULTS ---")
    for name, val in results.items():
        print(f"{name}: {val}")

if __name__ == "__main__":
    test_regex_on_text()
