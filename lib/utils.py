def input_int(prompt: str) -> int:
    """
    Solicita uma entrada do usuário e garante que o valor seja um número inteiro.
    O método usa um laço `while True` para continuar pedindo a entrada até que
    o usuário digite um valor válido. Ele tenta converter a entrada para `int`
    dentro de um bloco `try...except ValueError`. Se a conversão for bem-sucedida,
    o valor é retornado; caso contrário, uma mensagem de erro é exibida e o laço
    continua para uma nova tentativa.
    """
    while True:
        val = input(prompt).strip()
        try:
            return int(val)
        except ValueError:
            print("Valor inválido. Digite um número inteiro.")


def input_nonempty(prompt: str) -> str:
    """
    Solicita uma entrada de string do usuário e garante que o valor não seja vazio.
    O laço `while True` continua pedindo a entrada até que uma string não vazia seja fornecida.
    O método `strip()` é usado para remover espaços em branco no início e no fim,
    evitando que o usuário insira apenas espaços.
    """
    while True:
        val = input(prompt).strip()
        if val:
            return val
        print("Este campo não pode ficar vazio.")