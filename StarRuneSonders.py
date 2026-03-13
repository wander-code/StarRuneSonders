import re
import ast

LANGUAGE_NAME = "StarRuneSonders"

DATATYPES = {
    "mrkn": "Integer",
    "mrkdbgn": "Big Decimal",
    "mrktxt": "Text",
    "mrksym": "Symbol"
}

OUTPUT_KEYWORDS = {"reveal", "echo"}
INPUT_KEYWORD = "seek"
ASSIGNMENT_OPERATOR = "~"
DELIMITER = "."
SYMBOL_TABLE = {}


class CompilerError(Exception):
    def __init__(self, phase, message, recovery="Panic Mode Recovery (Discard statement)"):
        self.phase = phase
        self.message = message
        self.recovery = recovery
        super().__init__(f"{phase}: {message}")


def story(line=""):
    print(line)


def tokenize(source_code):
    token_specification = [
        ("TEXT", r"\*[^*\n]*\*"),
        ("CHAR", r"'[^'\n]'"),
        ("FLOAT", r"\d+\.\d+"),
        ("INVALID_IDENTIFIER", r"\d+[A-Za-z_][A-Za-z0-9_]*"),
        ("INTEGER", r"\d+"),
        ("ASSIGN", r"~"),
        ("COLON", r":"),
        ("OPERATOR", r"==|!=|>=|<=|[+\-*/><]"),
        ("LPAREN", r"\("),
        ("RPAREN", r"\)"),
        ("COMMA", r","),
        ("DELIMITER", r"\."),
        ("IDENTIFIER", r"[A-Za-z_][A-Za-z0-9_]*"),
        ("SKIP", r"[ \t]+"),
        ("MISMATCH", r".")
    ]

    master_pattern = "|".join(f"(?P<{name}>{pattern})" for name, pattern in token_specification)

    tokens = []
    lexical_errors = []

    for match in re.finditer(master_pattern, source_code):
        kind = match.lastgroup
        value = match.group()

        if kind == "SKIP":
            continue
        elif kind == "INVALID_IDENTIFIER":
            tokens.append({"type": kind, "value": value})
            lexical_errors.append(
                CompilerError(
                    "Lexical Error",
                    f"'{value}' is an invalid identifier. Identifiers cannot start with a number.",
                    "Panic Mode Recovery (Skip invalid token)"
                )
            )
        elif kind == "MISMATCH":
            tokens.append({"type": kind, "value": value})
            lexical_errors.append(
                CompilerError(
                    "Lexical Error",
                    f"Unexpected symbol '{value}'.",
                    "Panic Mode Recovery (Skip invalid symbol)"
                )
            )
        else:
            tokens.append({"type": kind, "value": value})

    return tokens, lexical_errors


def classify_token(token):
    value = token["value"]
    kind = token["type"]

    if value in DATATYPES:
        return "Datatype"
    if value in OUTPUT_KEYWORDS:
        return "Output Keyword"
    if value == INPUT_KEYWORD:
        return "Input Keyword"
    if kind == "ASSIGN":
        return "Assignment Operator"
    if kind == "COLON":
        return "Colon"
    if kind == "DELIMITER":
        return "Delimiter"
    if kind == "INTEGER":
        return "Integer Literal"
    if kind == "FLOAT":
        return "Float Literal"
    if kind == "TEXT":
        return "Text Literal"
    if kind == "CHAR":
        return "Char Literal"
    if kind == "IDENTIFIER":
        return "Identifier"
    if kind == "OPERATOR":
        return "Arithmetic/Relational Operator"
    if kind in {"LPAREN", "RPAREN", "COMMA"}:
        return "Symbol"
    if kind == "INVALID_IDENTIFIER":
        return "Invalid Identifier"
    return "Unknown"


def print_tokens(tokens):
    story("\n[LEXER] The forest listens as you speak into the dark...")
    for token in tokens:
        story(f"  Rune found: {token['value']:<20} -> {classify_token(token)}")


def safe_user_input(prompt, fallback="0"):
    try:
        return input(prompt)
    except OSError:
        print(f"[INPUT FALLBACK] Interactive input unavailable. Using fallback value: {fallback}")
        return fallback


def parse(tokens):
    syntax_notes = []

    if not tokens:
        raise CompilerError("Syntax Error", "No statement found.", "Panic Mode Recovery (Discard empty input)")

    if tokens[-1]["value"] != DELIMITER:
        syntax_notes.append(
            "Phrase-Level Recovery: Missing delimiter '.' detected. The sentence had holes, so the house sealed it for you."
        )
        tokens = tokens + [{"type": "DELIMITER", "value": DELIMITER}]

    if tokens[-1]["value"] != DELIMITER:
        raise CompilerError("Syntax Error", "Statement must end with '.'.", "Phrase-Level Recovery (Insert delimiter)")

    core_tokens = tokens[:-1]

    if not core_tokens:
        raise CompilerError("Syntax Error", "Statement body is empty before delimiter.", "Panic Mode Recovery")

    first = core_tokens[0]["value"]

    if first in DATATYPES:
        story("\n[PARSER] You study the cabin's strange grammar...")
        story("  Rule checked: <declaration> -> <datatype> <identifier> ~ <expression> .")
        ast_node = parse_declaration(core_tokens)
        return ast_node, syntax_notes

    if first in OUTPUT_KEYWORDS:
        story("\n[PARSER] You speak into the stillness of the room...")
        story("  Rule checked: <output> -> <output_keyword> : <expression> .")
        ast_node = parse_output(core_tokens)
        return ast_node, syntax_notes

    raise CompilerError(
        "Syntax Error",
        f"Unknown statement start '{first}'. Expected a datatype or an output keyword.",
        "Panic Mode Recovery (Discard statement)"
    )


def parse_declaration(core_tokens):
    if len(core_tokens) < 4:
        raise CompilerError(
            "Syntax Error",
            "Incomplete declaration. Expected: <datatype> <identifier> ~ <expression>",
            "Panic Mode Recovery (Discard incomplete declaration)"
        )

    datatype = core_tokens[0]
    identifier = core_tokens[1]
    assign = core_tokens[2]
    expression_tokens = core_tokens[3:]

    if datatype["value"] not in DATATYPES:
        raise CompilerError("Syntax Error", f"Unknown datatype '{datatype['value']}'.")

    if identifier["type"] != "IDENTIFIER":
        raise CompilerError(
            "Syntax Error",
            f"Expected an identifier after datatype, but found '{identifier['value']}'."
        )

    if identifier["value"] in DATATYPES or identifier["value"] in OUTPUT_KEYWORDS or identifier["value"] == INPUT_KEYWORD:
        raise CompilerError(
            "Syntax Error",
            f"'{identifier['value']}' is reserved and cannot be used as an identifier."
        )

    if assign["value"] != ASSIGNMENT_OPERATOR:
        raise CompilerError(
            "Syntax Error",
            f"Expected assignment operator '{ASSIGNMENT_OPERATOR}', but found '{assign['value']}'."
        )

    if not expression_tokens:
        raise CompilerError("Syntax Error", "Missing expression after assignment operator.")

    return {
        "node_type": "declaration",
        "datatype": datatype["value"],
        "identifier": identifier["value"],
        "expression": expression_tokens
    }


def parse_output(core_tokens):
    if len(core_tokens) < 3:
        raise CompilerError(
            "Syntax Error",
            "Incomplete output statement. Expected: <output_keyword> : <expression>",
            "Panic Mode Recovery (Discard incomplete output)"
        )

    if core_tokens[1]["value"] != ":":
        raise CompilerError(
            "Syntax Error",
            f"Expected ':' after output keyword, but found '{core_tokens[1]['value']}'.",
            "Panic Mode Recovery (Discard malformed output)"
        )

    expression_tokens = core_tokens[2:]
    if not expression_tokens:
        raise CompilerError("Syntax Error", "Missing expression after ':' in output statement.")

    return {
        "node_type": "output",
        "keyword": core_tokens[0]["value"],
        "expression": expression_tokens
    }


def is_seek_call(tokens):
    if len(tokens) == 2:
        return tokens[0]["value"] == INPUT_KEYWORD and tokens[1]["value"] == ":"

    if len(tokens) == 3:
        return (
            tokens[0]["value"] == INPUT_KEYWORD and
            tokens[1]["value"] == ":" and
            tokens[2]["type"] == "TEXT"
        )

    return False


def safe_numeric_eval(expression_text):
    allowed_nodes = (
        ast.Expression, ast.BinOp, ast.UnaryOp, ast.Constant,
        ast.Add, ast.Sub, ast.Mult, ast.Div, ast.UAdd, ast.USub
    )

    tree = ast.parse(expression_text, mode="eval")

    for node in ast.walk(tree):
        if not isinstance(node, allowed_nodes):
            raise CompilerError(
                "Semantic Error",
                "Only numeric arithmetic using +, -, *, / is allowed in expressions.",
                "Panic Mode Recovery (Discard invalid expression)"
            )
        if isinstance(node, ast.Constant) and not isinstance(node.value, (int, float)):
            raise CompilerError(
                "Semantic Error",
                "Arithmetic expressions must only contain numeric values.",
                "Panic Mode Recovery (Discard invalid expression)"
            )

    return eval(compile(tree, "<expr>", "eval"), {"__builtins__": {}}, {})


def convert_input_to_type(user_value, datatype):
    if datatype == "mrkn":
        try:
            return int(user_value)
        except ValueError:
            raise CompilerError(
                "Semantic Error",
                f"Type mismatch. Expected {DATATYPES[datatype]} input, but received '{user_value}'.",
                "Type Coercion or Re-enter Input"
            )

    if datatype == "mrkdbgn":
        try:
            return float(user_value)
        except ValueError:
            raise CompilerError(
                "Semantic Error",
                f"Type mismatch. Expected {DATATYPES[datatype]} input, but received '{user_value}'.",
                "Type Coercion or Re-enter Input"
            )

    if datatype == "mrktxt":
        return user_value

    if datatype == "mrksym":
        if len(user_value) != 1:
            raise CompilerError(
                "Semantic Error",
                f"Type mismatch. A '{datatype}' value must contain exactly one character.",
                "Trim input to one character or Re-enter Input"
            )
        return user_value

    raise CompilerError("Semantic Error", f"Unknown datatype '{datatype}'.")


def evaluate_expression(tokens, expected_datatype=None):
    if not tokens:
        raise CompilerError("Semantic Error", "Missing expression to evaluate.")

    if is_seek_call(tokens):
        prompt_text = "Speak your answer: "
        if len(tokens) == 3:
            prompt_text = tokens[2]["value"][1:-1]

        fallback_value = "0"
        if expected_datatype == "mrktxt":
            fallback_value = "memory"
        elif expected_datatype == "mrksym":
            fallback_value = "K"
        elif expected_datatype == "mrkdbgn":
            fallback_value = "0.0"

        user_value = safe_user_input(prompt_text, fallback=fallback_value)

        if expected_datatype is None:
            return user_value

        return convert_input_to_type(user_value, expected_datatype)

    if len(tokens) == 1:
        token = tokens[0]

        if token["type"] == "INTEGER":
            return int(token["value"])
        if token["type"] == "FLOAT":
            return float(token["value"])
        if token["type"] == "TEXT":
            return token["value"][1:-1]
        if token["type"] == "CHAR":
            return token["value"][1:-1]
        if token["type"] == "IDENTIFIER":
            name = token["value"]
            if name not in SYMBOL_TABLE:
                raise CompilerError(
                    "Semantic Error",
                    f"Identifier '{name}' was used before being bound in the cabin registry.",
                    "Panic Mode Recovery (Discard statement)"
                )
            return SYMBOL_TABLE[name]["value"]

    expression_parts = []

    for token in tokens:
        if token["type"] in {"INTEGER", "FLOAT"}:
            expression_parts.append(token["value"])
        elif token["type"] == "IDENTIFIER":
            name = token["value"]
            if name not in SYMBOL_TABLE:
                raise CompilerError(
                    "Semantic Error",
                    f"Identifier '{name}' was used before being bound in the cabin registry.",
                    "Panic Mode Recovery (Discard statement)"
                )

            bound_value = SYMBOL_TABLE[name]["value"]
            if not isinstance(bound_value, (int, float)):
                raise CompilerError(
                    "Semantic Error",
                    f"Identifier '{name}' is not numeric and cannot join an arithmetic expression.",
                    "Panic Mode Recovery (Discard invalid expression)"
                )

            expression_parts.append(str(bound_value))
        elif token["value"] in {"+", "-", "*", "/", "(", ")"}:
            expression_parts.append(token["value"])
        else:
            raise CompilerError(
                "Semantic Error",
                f"Invalid token '{token['value']}' inside expression.",
                "Panic Mode Recovery (Discard invalid expression)"
            )

    expression_text = " ".join(expression_parts)
    return safe_numeric_eval(expression_text)


def type_matches(datatype, value):
    if datatype == "mrkn":
        return isinstance(value, int) and not isinstance(value, bool)
    if datatype == "mrkdbgn":
        return isinstance(value, (int, float)) and not isinstance(value, bool)
    if datatype == "mrktxt":
        return isinstance(value, str)
    if datatype == "mrksym":
        return isinstance(value, str) and len(value) == 1
    return False


def story_lore(ast_node, result):
    if ast_node["node_type"] == "declaration":
        identifier = ast_node["identifier"]
        value = result[2]

        lore_map = {
            "wakeup": (
                "Story Lore:\n"
                "You stumble in the forest, your footing gives way, and the earth swallows you whole.\n"
                "Hours later, you wake in a narrow bed inside an unfamiliar cabin.\n"
                "Someone found you. Someone chose not to let you die."
            ),
            "photo": (
                "Story Lore:\n"
                "Beside the lamp rests a picture frame.\n"
                "A mother and a young daughter smile in front of this same cabin.\n"
                "The child looks about seven, still new to the world."
            ),
            "note": (
                "Story Lore:\n"
                "A note sticks halfway out from an old drawer.\n"
                "Its words do not feel like a puzzle, but a plea.\n"
                "Someone wanted the truth found gently."
            ),
            "framekey": (
                "Story Lore:\n"
                "Behind the photograph is a hidden slit in the wood.\n"
                "Inside it lies a small iron key.\n"
                "The frame was never only a memory. It was also a lock."
            ),
            "letters": (
                "Story Lore:\n"
                "Inside the newly opened drawer are letters, dozens of them.\n"
                "All sealed. All unread.\n"
                "You realize with a chill that you may be the first person to ever open them."
            ),
            "truth": (
                "Story Lore:\n"
                "The truth settles over the room like dust and mourning.\n"
                "The daughter died in this cabin years ago.\n"
                "Her mother never truly left, because grief made leaving impossible."
            ),
            "savior": (
                "Story Lore:\n"
                "The name in the final letter is no stranger's.\n"
                "It belongs to the mother herself, who kept the cabin unchanged.\n"
                "You were not trapped here by malice, but led here to bear witness."
            )
        }

        if identifier in lore_map:
            story("\n" + lore_map[identifier])
        else:
            story(f"\nStory Lore:\nThe rune '{identifier}' takes shape in the quiet cabin with value {value}.")

    elif ast_node["node_type"] == "output":
        expr_tokens = ast_node["expression"]

        if len(expr_tokens) == 1 and expr_tokens[0]["type"] == "IDENTIFIER":
            name = expr_tokens[0]["value"]
            lore_map = {
                "photo": (
                    "Story Lore:\n"
                    "You hold the frame closer to the light.\n"
                    "The woman's smile is tired but warm.\n"
                    "The child leans toward her as if she never feared the world."
                ),
                "note": (
                    "Story Lore:\n"
                    "You read the note aloud.\n"
                    "The room does not answer, but somehow feels less empty.\n"
                    "Whoever wrote it trusted that one day, someone would listen."
                ),
                "letters": (
                    "Story Lore:\n"
                    "You unfold the brittle pages one by one.\n"
                    "Every letter is addressed to the daughter.\n"
                    "None were ever sent. None were ever meant to be."
                ),
                "truth": (
                    "Story Lore:\n"
                    "At last, the cabin stops feeling like a riddle and starts feeling like a grave kept warm by memory.\n"
                    "The mother stayed because love gave her nowhere else to go."
                )
            }
            if name in lore_map:
                story("\n" + lore_map[name])


def semantic_analyze(ast_node):
    story("\n[SEMANTIC] Meaning gathers like candlelight in the room...")

    if ast_node["node_type"] == "declaration":
        datatype = ast_node["datatype"]
        identifier = ast_node["identifier"]
        value = evaluate_expression(ast_node["expression"], expected_datatype=datatype)

        if not type_matches(datatype, value):
            raise CompilerError(
                "Semantic Error",
                f"Type mismatch. Cannot bind value '{value}' to variable '{identifier}' of type '{datatype}'.",
                "Type Coercion or Discard Assignment"
            )

        if datatype == "mrkdbgn" and isinstance(value, int):
            value = float(value)

        SYMBOL_TABLE[identifier] = {
            "type": datatype,
            "value": value
        }

        story(f"  Meaning confirmed: '{identifier}' belongs to type '{datatype}'.")
        story(f"  Binding successful: '{identifier}' is now stored in the cabin registry.")
        return ("declaration", identifier, value)

    if ast_node["node_type"] == "output":
        value = evaluate_expression(ast_node["expression"])
        story("  The cabin listens. Your words are ready to be revealed.")
        return ("output", value)

    raise CompilerError("Semantic Error", "Unknown AST node encountered.")


def print_symbol_table():
    if not SYMBOL_TABLE:
        story("\n[SYMBOL TABLE] The registry is still empty.")
        return

    story("\n[SYMBOL TABLE] Cabin Registry")
    story("-" * 52)
    story(f"{'Identifier':<18}{'Datatype':<16}{'Value':<18}")
    story("-" * 52)
    for name, info in SYMBOL_TABLE.items():
        story(f"{name:<18}{info['type']:<16}{str(info['value']):<18}")
    story("-" * 52)


def compile_line(source_code):
    story("\n" + "=" * 72)
    story(f"{LANGUAGE_NAME} Front-End Compiler")
    story("Story Mode: Lost in the forest, awakened in a cabin, uncovering grief through clues.")
    story("=" * 72)

    tokens, lexical_errors = tokenize(source_code)
    print_tokens(tokens)

    if lexical_errors:
        story("\n[LEXER RESULT] The house rejects what was spoken incorrectly:")
        for err in lexical_errors:
            story(f"  Error found: {err.message}")
            story(f"  Recovery: {err.recovery}")

        story(
            "\nStory Lore:\n"
            "You try to name what you have seen, but the cabin does not accept careless runes.\n"
            "Some truths cannot begin in disorder."
        )
        story("\nStatus: COMPILATION FAILED")
        return

    story("\n[LEXER RESULT] No suspicious tracks were found. Lexical analysis passed.")

    try:
        ast_node, syntax_notes = parse(tokens)

        if syntax_notes:
            story("\n[PARSER NOTES]")
            for note in syntax_notes:
                story(f"  {note}")

        story("  Structure confirmed. Syntax analysis passed.")

        result = semantic_analyze(ast_node)
        story("\n[SEMANTIC RESULT] Meaning and binding check passed.")

        if result[0] == "output":
            story(f"\n[OUTPUT] {result[1]}")
        else:
            identifier = result[1]
            value = result[2]
            story(f"\n[BINDING RESULT] '{identifier}' now holds: {value}")

        story_lore(ast_node, result)
        print_symbol_table()
        story("\nStatus: COMPILATION SUCCESS")

    except CompilerError as err:
        story(f"\n[{err.phase.upper()}]")
        story(f"  Error found: {err.message}")
        story(f"  Recovery: {err.recovery}")

        if err.phase == "Syntax Error":
            story(
                "\nStory Lore:\n"
                "The sentence breaks apart before the room can understand it.\n"
                "In this cabin, even grief demands proper form."
            )
        elif err.phase == "Semantic Error":
            story(
                "\nStory Lore:\n"
                "You reached for meaning before you were ready.\n"
                "Some drawers do not open until the right memory has been found."
            )

        print_symbol_table()
        story("\nStatus: COMPILATION FAILED")


def main():
    print("=" * 72)
    print(f"Welcome to {LANGUAGE_NAME}")
    print("Enter one line at a time.")
    print(f"Type '{LANGUAGE_NAME}' to exit.")
    print("Your symbols remain remembered until you exit.")
    print("=" * 72)

    while True:
        try:
            source_code = input("\nEnter one StarRuneSonders line: ").strip()
        except OSError:
            print("Interactive input is not available in this environment.")
            print("Running default test line once, then exiting.")
            compile_line("mrkn wakeup ~ 1.")
            break

        if not source_code:
            print("Empty line ignored.")
            continue

        if source_code == LANGUAGE_NAME:
            print(f"\nThe cabin falls silent. Exiting {LANGUAGE_NAME}...")
            break

        compile_line(source_code)


if __name__ == "__main__":
    main()