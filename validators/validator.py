import inspect
import ast
import importlib
import traceback

# --- dane testowe i ograniczenia ---
TEST_CASES = [0, 7, 70, 807, 1234, 120305, 90007, 111111, 987654321]
FORBIDDEN_KEYWORDS = ["str", "list", "map", "filter", "reversed", "sorted"]

# --- referencyjna funkcja ---
def przestaw_ref(n: int) -> int:
    r = n % 100
    a = r // 10
    b = r % 10
    n = n // 100
    if n > 0:
        return a + 10 * b + 100 * przestaw_ref(n)
    else:
        return a + 10 * b if a > 0 else b


# --- pomocnicze: sprawdzanie inicjalizacji i modyfikacji p ---
def sprawdz_inicjalizacje(tree: ast.AST) -> bool:
    w_zero = False
    p_jeden = False
    p_modyfikacja = False

    for node in ast.walk(tree):
        # w = 0
        if isinstance(node, ast.Assign):
            if (len(node.targets) == 1
                and isinstance(node.targets[0], ast.Name)
                and node.targets[0].id == "w"
                and isinstance(node.value, ast.Constant)
                and node.value.value == 0):
                w_zero = True

            # p = 1
            if (len(node.targets) == 1
                and isinstance(node.targets[0], ast.Name)
                and node.targets[0].id == "p"
                and isinstance(node.value, ast.Constant)
                and node.value.value == 1):
                p_jeden = True

            # p = p * 100
            if (len(node.targets) == 1
                and isinstance(node.targets[0], ast.Name)
                and node.targets[0].id == "p"
                and isinstance(node.value, ast.BinOp)
                and isinstance(node.value.left, ast.Name)
                and node.value.left.id == "p"
                and isinstance(node.value.op, ast.Mult)
                and isinstance(node.value.right, ast.Constant)
                and node.value.right.value == 100):
                p_modyfikacja = True

        # p *= 100
        if isinstance(node, ast.AugAssign):
            if (isinstance(node.target, ast.Name)
                and node.target.id == "p"
                and isinstance(node.op, ast.Mult)
                and isinstance(node.value, ast.Constant)
                and node.value.value == 100):
                p_modyfikacja = True

    return w_zero and p_jeden and p_modyfikacja


# --- pomocnicze: sprawdzanie poprawności pętli ---
def sprawdz_petle(tree: ast.AST) -> bool:
    """
    Kryteria:
    - musi wystąpić pętla while
    - warunek dotyczy zmiennej n
    - w ciele pętli musi być dzielenie przez 100 (n //= 100 lub n = n // 100)
    """
    petla_ok = False
    dzielenie_ok = False

    for node in ast.walk(tree):
        if isinstance(node, ast.While):
            if (isinstance(node.test, ast.Compare)
                and isinstance(node.test.left, ast.Name)
                and node.test.left.id == "n"):
                petla_ok = True

        # n = n // 100
        if isinstance(node, ast.Assign):
            if (len(node.targets) == 1
                and isinstance(node.targets[0], ast.Name)
                and node.targets[0].id == "n"
                and isinstance(node.value, ast.BinOp)
                and isinstance(node.value.left, ast.Name)
                and node.value.left.id == "n"
                and isinstance(node.value.op, ast.FloorDiv)
                and isinstance(node.value.right, ast.Constant)
                and node.value.right.value == 100):
                dzielenie_ok = True

        # n //= 100
        if isinstance(node, ast.AugAssign):
            if (isinstance(node.target, ast.Name)
                and node.target.id == "n"
                and isinstance(node.op, ast.FloorDiv)
                and isinstance(node.value, ast.Constant)
                and node.value.value == 100):
                dzielenie_ok = True

    return petla_ok and dzielenie_ok


# --- pomocnicze: sprawdzanie zamiany cyfr ---
def sprawdz_zamiane_cyfr(tree: ast.AST) -> bool:
    """
    Kryteria:
    - występuje operacja n % 100
    - występuje operacja r // 10
    - występuje operacja r % 10
    """
    mod100 = False
    div10 = False
    mod10 = False

    for node in ast.walk(tree):
        # n % 100
        if isinstance(node, ast.BinOp) and isinstance(node.op, ast.Mod):
            if (isinstance(node.left, ast.Name)
                and node.left.id == "n"
                and isinstance(node.right, ast.Constant)
                and node.right.value == 100):
                mod100 = True

        # r // 10
        if isinstance(node, ast.BinOp) and isinstance(node.op, ast.FloorDiv):
            if (isinstance(node.left, ast.Name)
                and node.left.id == "r"
                and isinstance(node.right, ast.Constant)
                and node.right.value == 10):
                div10 = True

        # r % 10
        if isinstance(node, ast.BinOp) and isinstance(node.op, ast.Mod):
            if (isinstance(node.left, ast.Name)
                and node.left.id == "r"
                and isinstance(node.right, ast.Constant)
                and node.right.value == 10):
                mod10 = True

    return mod100 and div10 and mod10



def print_verdict(score, message):
    print(score)
    print(message)


# --- główna funkcja oceniająca ---
def validate(solution_path):
    # --- 1. Import rozwiązania ucznia ---
    mod = importlib.import_module(solution_path)
    if not hasattr(mod, "przestaw2"):
        print_verdict(0, "Brak funkcji przestaw2")
        return

    src = inspect.getsource(mod.przestaw2)
    tree = ast.parse(src)

    # --- 2. Sprawdzenie ograniczeń ---
    if "przestaw2(" in src and "def przestaw2" not in src:
        print_verdict(0, "Rekurencja niedozwolona")
        return

    if any(f + "(" in src for f in FORBIDDEN_KEYWORDS):
        print_verdict(0, "Użyto niedozwolonych funkcji")
        return
    
    # --- 3. Poprawność wyniku ---
    ok = True
    for n in TEST_CASES:
        try:
            if mod.przestaw2(n) != przestaw_ref(n):
                ok = False
                break
        except Exception:
            ok = False
            break
    if ok:
        print_verdict(4, "Algorytm poprawny")
        return

    score = 0

    # tylko jeśli ograniczenia spełnione → oceniamy dalej

    # --- 4. Inicjalizacja ---
    if sprawdz_inicjalizacje(tree):
        score += 1

    # --- 5. Pętla ---
    if sprawdz_petle(tree):
        score += 1

    # --- 6. Zamiana cyfr ---
    if sprawdz_zamiane_cyfr(tree):
        score += 1

    print_verdict(score, "")