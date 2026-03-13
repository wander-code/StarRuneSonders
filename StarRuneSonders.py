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
    """
    Lexer:
    Converts the source line into tokens while catching invalid identifiers and unknown symbols.
    """
    token_specification = [
        ("STRING", r'"[^"\n]*"'),
        ("CHAR", r"'[^'\n]'"),
        ("FLOAT", r"\d+\.\d+"),
        ("INVALID_IDENTIFIER", r"\d+[A-Za-z_][A-Za-z0-9_]*"),
        ("INTEGER", r"\d+"),
        ("ASSIGN", r"~"),
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
    if kind == "DELIMITER":
        return "Delimiter"
    if kind == "INTEGER":
        return "Integer Literal"
    if kind == "FLOAT":
        return "Float Literal"
    if kind == "STRING":
        return "String Literal"
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
    story("\n[LEXER] The wanderer searches the forest floor for signs...")
    for token in tokens:
        story(f"  Rune found: {token['value']:<12} -> {classify_token(token)}")


def parse(tokens):
    """
    Parser:
    Supports one-line statements only.
    Grammar:
      <declaration> -> <datatype> <identifier> ~ <expression> .
      <output>      -> <output_keyword> <expression> .
    """
    syntax_notes = []

    if not tokens:
        raise CompilerError("Syntax Error", "No statement found.", "Panic Mode Recovery (Discard empty input)")

    # Phrase-level recovery for missing delimiter
    if tokens[-1]["value"] != DELIMITER:
        syntax_notes.append(
            "Phrase-Level Recovery: Missing delimiter '.' detected. The tavern keeper quietly places it at the end."
        )
        tokens = tokens + [{"type": "DELIMITER", "value": DELIMITER}]

    if tokens[-1]["value"] != DELIMITER:
        raise CompilerError("Syntax Error", "Statement must end with '.'.", "Phrase-Level Recovery (Insert delimiter)")

    core_tokens = tokens[:-1]

    if not core_tokens:
        raise CompilerError("Syntax Error", "Statement body is empty before delimiter.", "Panic Mode Recovery")

    first = core_tokens[0]["value"]

    if first in DATATYPES:
        story("\n[PARSER] The wanderer studies the tavern ledger...")
        story("  Rule checked: <declaration> -> <datatype> <identifier> ~ <expression> .")
        ast_node = parse_declaration(core_tokens)
        return ast_node, syntax_notes

    if first in OUTPUT_KEYWORDS:
        story("\n[PARSER] The wanderer reads the wall inscription...")
        story("  Rule checked: <output> -> <output_keyword> <expression> .")
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
    if len(core_tokens) < 2:
        raise CompilerError(
            "Syntax Error",
            "Incomplete output statement. Expected: <output_keyword> <expression>",
            "Panic Mode Recovery (Discard incomplete output)"
        )

    return {
        "node_type": "output",
        "keyword": core_tokens[0]["value"],
        "expression": core_tokens[1:]
    }


def is_seek_call(tokens):
    """
    Valid forms:
      seek()
      seek("Prompt here")
    """
    if len(tokens) == 3:
        return tokens[0]["value"] == INPUT_KEYWORD and tokens[1]["value"] == "(" and tokens[2]["value"] == ")"

    if len(tokens) == 4:
        return (
            tokens[0]["value"] == INPUT_KEYWORD and
            tokens[1]["value"] == "(" and
            tokens[2]["type"] == "STRING" and
            tokens[3]["value"] == ")"
        )

    return False


def safe_numeric_eval(expression_text):
    """
    Safe arithmetic evaluation using AST.
    Only allows numbers and + - * / and parentheses.
    """
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
                f"Type mismatch. Expected {DATATYPES[datatype]} input for '{datatype}', but received '{user_value}'.",
                "Type Coercion or Re-enter Input"
            )

    if datatype == "mrkdbgn":
        try:
            return float(user_value)
        except ValueError:
            raise CompilerError(
                "Semantic Error",
                f"Type mismatch. Expected {DATATYPES[datatype]} input for '{datatype}', but received '{user_value}'.",
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
    """
    Evaluates literals, identifiers, seek(...), and arithmetic expressions.
    """
    if not tokens:
        raise CompilerError("Semantic Error", "Missing expression to evaluate.")

    # seek()
    if is_seek_call(tokens):
        prompt_text = "Enter value: "
        if len(tokens) == 4:
            prompt_text = tokens[2]["value"][1:-1]

        user_value = input(prompt_text)

        if expected_datatype is None:
            return user_value

        return convert_input_to_type(user_value, expected_datatype)

    # Single-token expression
    if len(tokens) == 1:
        token = tokens[0]

        if token["type"] == "INTEGER":
            return int(token["value"])
        if token["type"] == "FLOAT":
            return float(token["value"])
        if token["type"] == "STRING":
            return token["value"][1:-1]
        if token["type"] == "CHAR":
            return token["value"][1:-1]
        if token["type"] == "IDENTIFIER":
            name = token["value"]
            if name not in SYMBOL_TABLE:
                raise CompilerError(
                    "Semantic Error",
                    f"Identifier '{name}' was used before being bound in the tavern registry.",
                    "Panic Mode Recovery (Discard statement)"
                )
            return SYMBOL_TABLE[name]["value"]

    # Multi-token arithmetic expression
    expression_parts = []

    for token in tokens:
        if token["type"] in {"INTEGER", "FLOAT"}:
            expression_parts.append(token["value"])
        elif token["type"] == "IDENTIFIER":
            name = token["value"]
            if name not in SYMBOL_TABLE:
                raise CompilerError(
                    "Semantic Error",
                    f"Identifier '{name}' was used before being bound in the tavern registry.",
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


def semantic_analyze(ast_node):
    """
    Semantic analysis + binding
    """
    story("\n[SEMANTIC] The wanderer follows the tavern clues and checks what each rune truly means...")

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

        # Normalize int result for mrkdbgn if expression returns int
        if datatype == "mrkdbgn" and isinstance(value, int):
            value = float(value)

        SYMBOL_TABLE[identifier] = {
            "type": datatype,
            "value": value
        }

        story(f"  Meaning confirmed: '{identifier}' belongs to type '{datatype}'.")
        story(f"  Binding successful: '{identifier}' is now stored in the tavern registry.")
        return ("declaration", identifier, value)

    if ast_node["node_type"] == "output":
        value = evaluate_expression(ast_node["expression"])
        story(f"  The clue glows. Output can now be revealed.")
        return ("output", value)

    raise CompilerError("Semantic Error", "Unknown AST node encountered.")


def print_symbol_table():
    if not SYMBOL_TABLE:
        story("\n[SYMBOL TABLE] The registry is still empty.")
        return

    story("\n[SYMBOL TABLE] Tavern Registry")
    story("-" * 45)
    story(f"{'Identifier':<15}{'Datatype':<15}{'Value':<15}")
    story("-" * 45)
    for name, info in SYMBOL_TABLE.items():
        story(f"{name:<15}{info['type']:<15}{str(info['value']):<15}")
    story("-" * 45)


def compile_line(source_code):
    story("=" * 68)
    story(f"{LANGUAGE_NAME} Front-End Compiler")
    story("Story Mode: Lost in the forest, awakened in a tavern, solving the mystery through code.")
    story("=" * 68)

    tokens, lexical_errors = tokenize(source_code)
    print_tokens(tokens)

    if lexical_errors:
        story("\n[LEXER RESULT] Trouble in the forest path:")
        for err in lexical_errors:
            story(f"  Error found: {err.message}")
            story(f"  Recovery: {err.recovery}")
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

        print_symbol_table()
        story("\nStatus: COMPILATION SUCCESS")

    except CompilerError as err:
        story(f"\n[{err.phase.upper()}]")
        story(f"  Error found: {err.message}")
        story(f"  Recovery: {err.recovery}")
        print_symbol_table()
        story("\nStatus: COMPILATION FAILED")


def main():
    source_code = input("\nEnter one StarRuneSonders line: ").strip()
    compile_line(source_code)


if __name__ == "__main__":
    main()