def input_int(prompt: str) -> int:
    while True:
        val = input(prompt).strip()
        try:
            return int(val)
        except ValueError:
            print("Valor inválido. Digite um número inteiro.")

def input_float(prompt: str) -> float:
    while True:
        val = input(prompt).strip().replace(",", ".")
        try:
            return float(val)
        except ValueError:
            print("Valor inválido. Digite um número (use '.' para decimais).")

def input_nonempty(prompt: str) -> str:
    while True:
        val = input(prompt).strip()
        if val:
            return val
        print("Este campo não pode ficar vazio.")