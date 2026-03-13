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

IF_KEYWORD = "eyes"
WHILE_KEYWORD = "stream"
CLASS_KEYWORD = "forge"
OBJECT_KEYWORD = "bind"

ASSIGNMENT_OPERATOR = "~"
EQUALITY_OPERATOR = "~~"
DELIMITER = "."

SYMBOL_TABLE = {}
CLASS_TABLE = {}
OBJECT_TABLE = {}

MAX_STREAM_ITERATIONS = 5


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
        ("OPERATOR", r"~~|!~|>~|<~|[+\-*/><]"),
        ("ASSIGN", r"~"),
        ("COLON", r":"),
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
    if value == IF_KEYWORD:
        return "Eyes Keyword"
    if value == WHILE_KEYWORD:
        return "Stream Keyword"
    if value == CLASS_KEYWORD:
        return "Class Keyword"
    if value == OBJECT_KEYWORD:
        return "Object Keyword"
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

    core_tokens = tokens[:-1]

    if not core_tokens:
        raise CompilerError("Syntax Error", "Statement body is empty before delimiter.", "Panic Mode Recovery")

    first = core_tokens[0]["value"]

    if first in DATATYPES:
        story("\n[PARSER] You study the cabin's strange grammar...")
        story("  Rule checked: <declaration> -> <datatype> <identifier> ~ <expression> .")
        return parse_declaration(core_tokens), syntax_notes

    if first in OUTPUT_KEYWORDS:
        story("\n[PARSER] You speak into the stillness of the room...")
        story("  Rule checked: <output> -> <output_keyword> : <expression> .")
        return parse_output(core_tokens), syntax_notes

    if first == IF_KEYWORD:
        story("\n[PARSER] The cabin tests whether your eyes are open to truth...")
        story(f"  Rule checked: <eyes> -> {IF_KEYWORD} : <condition> : <action> .")
        return parse_eyes(core_tokens), syntax_notes

    if first == WHILE_KEYWORD:
        story("\n[PARSER] The cabin yields to the stream of repeating motion...")
        story(f"  Rule checked: <stream> -> {WHILE_KEYWORD} : <condition> : <action> .")
        return parse_stream(core_tokens), syntax_notes

    if first == CLASS_KEYWORD:
        story("\n[PARSER] A new structure is being forged in memory...")
        story("  Rule checked: <class_decl> -> forge <ClassName> .")
        return parse_class_declaration(core_tokens), syntax_notes

    if first == OBJECT_KEYWORD:
        story("\n[PARSER] A structure is being bound into form...")
        story("  Rule checked: <object_inst> -> bind <ClassName> <objectName> .")
        return parse_object_instantiation(core_tokens), syntax_notes

    raise CompilerError(
        "Syntax Error",
        f"Unknown statement start '{first}'. Expected datatype, output, eyes, stream, forge, or bind.",
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
        raise CompilerError("Syntax Error", f"Expected identifier, found '{identifier['value']}'.")

    if identifier["value"] in DATATYPES or identifier["value"] in OUTPUT_KEYWORDS or identifier["value"] in {
        INPUT_KEYWORD, IF_KEYWORD, WHILE_KEYWORD, CLASS_KEYWORD, OBJECT_KEYWORD
    }:
        raise CompilerError("Syntax Error", f"'{identifier['value']}' is reserved and cannot be used as an identifier.")

    if assign["value"] != ASSIGNMENT_OPERATOR:
        raise CompilerError(
            "Syntax Error",
            f"Expected assignment operator '{ASSIGNMENT_OPERATOR}', but found '{assign['value']}'."
        )

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
            f"Expected ':' after output keyword, but found '{core_tokens[1]['value']}'."
        )

    expression_tokens = core_tokens[2:]

    return {
        "node_type": "output",
        "keyword": core_tokens[0]["value"],
        "expression": expression_tokens
    }


def split_by_colons(tokens, expected_parts):
    colon_positions = [i for i, t in enumerate(tokens) if t["value"] == ":"]
    if len(colon_positions) < expected_parts - 1:
        raise CompilerError("Syntax Error", "Missing ':' separator in control structure.")

    parts = []
    start = 0
    for pos in colon_positions[:expected_parts - 1]:
        parts.append(tokens[start:pos])
        start = pos + 1
    parts.append(tokens[start:])
    return parts


def parse_eyes(core_tokens):
    parts = split_by_colons(core_tokens, 3)

    if not (len(parts[0]) == 1 and parts[0][0]["value"] == IF_KEYWORD):
        raise CompilerError("Syntax Error", "Malformed eyes statement.")

    condition_tokens = parts[1]
    action_tokens = parts[2]

    if not condition_tokens or not action_tokens:
        raise CompilerError("Syntax Error", "Eyes statement requires both condition and action.")

    return {
        "node_type": "eyes",
        "condition": condition_tokens,
        "action_tokens": action_tokens
    }


def parse_stream(core_tokens):
    parts = split_by_colons(core_tokens, 3)

    if not (len(parts[0]) == 1 and parts[0][0]["value"] == WHILE_KEYWORD):
        raise CompilerError("Syntax Error", "Malformed stream statement.")

    condition_tokens = parts[1]
    action_tokens = parts[2]

    if not condition_tokens or not action_tokens:
        raise CompilerError("Syntax Error", "Stream statement requires both condition and action.")

    return {
        "node_type": "stream",
        "condition": condition_tokens,
        "action_tokens": action_tokens
    }


def parse_class_declaration(core_tokens):
    if len(core_tokens) != 2:
        raise CompilerError("Syntax Error", "Expected: forge <ClassName> .")

    class_name = core_tokens[1]
    if class_name["type"] != "IDENTIFIER":
        raise CompilerError("Syntax Error", f"Expected class name, found '{class_name['value']}'.")

    return {
        "node_type": "class_decl",
        "class_name": class_name["value"]
    }


def parse_object_instantiation(core_tokens):
    if len(core_tokens) != 3:
        raise CompilerError("Syntax Error", "Expected: bind <ClassName> <objectName> .")

    class_name = core_tokens[1]
    object_name = core_tokens[2]

    if class_name["type"] != "IDENTIFIER":
        raise CompilerError("Syntax Error", f"Expected class name, found '{class_name['value']}'.")

    if object_name["type"] != "IDENTIFIER":
        raise CompilerError("Syntax Error", f"Expected object name, found '{object_name['value']}'.")

    return {
        "node_type": "object_inst",
        "class_name": class_name["value"],
        "object_name": object_name["value"]
    }


def is_seek_call(tokens):
    if len(tokens) == 2:
        return tokens[0]["value"] == INPUT_KEYWORD and tokens[1]["value"] == ":"
    if len(tokens) == 3:
        return tokens[0]["value"] == INPUT_KEYWORD and tokens[1]["value"] == ":" and tokens[2]["type"] == "TEXT"
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
                "Only numeric arithmetic using +, -, *, / is allowed in expressions."
            )
        if isinstance(node, ast.Constant) and not isinstance(node.value, (int, float)):
            raise CompilerError(
                "Semantic Error",
                "Arithmetic expressions must only contain numeric values."
            )

    return eval(compile(tree, "<expr>", "eval"), {"__builtins__": {}}, {})


def convert_input_to_type(user_value, datatype):
    if datatype == "mrkn":
        try:
            return int(user_value)
        except ValueError:
            raise CompilerError("Semantic Error", f"Expected Integer input, but received '{user_value}'.")
    if datatype == "mrkdbgn":
        try:
            return float(user_value)
        except ValueError:
            raise CompilerError("Semantic Error", f"Expected Big Decimal input, but received '{user_value}'.")
    if datatype == "mrktxt":
        return user_value
    if datatype == "mrksym":
        if len(user_value) != 1:
            raise CompilerError("Semantic Error", "A mrksym value must contain exactly one character.")
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
        return convert_input_to_type(user_value, expected_datatype) if expected_datatype else user_value

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
            if name in SYMBOL_TABLE:
                return SYMBOL_TABLE[name]["value"]
            if name in OBJECT_TABLE:
                return OBJECT_TABLE[name]
            raise CompilerError(
                "Semantic Error",
                f"Identifier '{name}' was used before being bound in the cabin registry."
            )

    expression_parts = []
    for token in tokens:
        if token["type"] in {"INTEGER", "FLOAT"}:
            expression_parts.append(token["value"])
        elif token["type"] == "IDENTIFIER":
            name = token["value"]
            if name not in SYMBOL_TABLE:
                raise CompilerError("Semantic Error", f"Identifier '{name}' is not defined for arithmetic.")
            bound_value = SYMBOL_TABLE[name]["value"]
            if not isinstance(bound_value, (int, float)):
                raise CompilerError("Semantic Error", f"Identifier '{name}' is not numeric.")
            expression_parts.append(str(bound_value))
        elif token["value"] in {"+", "-", "*", "/", "(", ")"}:
            expression_parts.append(token["value"])
        else:
            raise CompilerError("Semantic Error", f"Invalid token '{token['value']}' inside expression.")

    return safe_numeric_eval(" ".join(expression_parts))


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


def evaluate_condition(tokens):
    ops = {EQUALITY_OPERATOR, "!~", ">", "<", ">~", "<~"}
    op_index = None

    for i, token in enumerate(tokens):
        if token["value"] in ops:
            op_index = i
            break

    if op_index is None:
        raise CompilerError("Semantic Error", "Condition requires a comparison operator.")

    left_tokens = tokens[:op_index]
    op = tokens[op_index]["value"]
    right_tokens = tokens[op_index + 1:]

    if not left_tokens or not right_tokens:
        raise CompilerError("Semantic Error", "Incomplete condition.")

    left_value = evaluate_expression(left_tokens)
    right_value = evaluate_expression(right_tokens)

    if op == EQUALITY_OPERATOR:
        return left_value == right_value
    if op == "!~":
        return left_value != right_value
    if op == ">":
        return left_value > right_value
    if op == "<":
        return left_value < right_value
    if op == ">~":
        return left_value >= right_value
    if op == "<~":
        return left_value <= right_value

    raise CompilerError("Semantic Error", f"Unsupported condition operator '{op}'.")


def rebuild_statement_tokens(action_tokens):
    return action_tokens + [{"type": "DELIMITER", "value": DELIMITER}]


def get_action_gate_reason(action_tokens):
    if not action_tokens:
        return None

    if len(action_tokens) >= 2 and action_tokens[0]["value"] in OUTPUT_KEYWORDS:
        expr = action_tokens[2:] if len(action_tokens) > 2 else []
        if len(expr) == 1 and expr[0]["type"] == "IDENTIFIER" and expr[0]["value"] == "drawer":
            if "framekey" not in SYMBOL_TABLE:
                return "The drawer does not open. You do not yet carry the key hidden behind the picture frame."

    if len(action_tokens) >= 2 and action_tokens[0]["value"] in DATATYPES:
        identifier = action_tokens[1]["value"]
        if identifier == "drawer" and "framekey" not in SYMBOL_TABLE:
            return "The drawer remains sealed. Memory recognizes that the framekey has not yet been found."

    return None


def semantic_analyze(ast_node):
    story("\n[SEMANTIC] Meaning gathers like candlelight in the room...")

    if ast_node["node_type"] == "declaration":
        datatype = ast_node["datatype"]
        identifier = ast_node["identifier"]
        value = evaluate_expression(ast_node["expression"], expected_datatype=datatype)

        if not type_matches(datatype, value):
            raise CompilerError(
                "Semantic Error",
                f"Type mismatch. Cannot bind value '{value}' to variable '{identifier}' of type '{datatype}'."
            )

        if datatype == "mrkdbgn" and isinstance(value, int):
            value = float(value)

        if identifier == "drawer" and "framekey" not in SYMBOL_TABLE:
            raise CompilerError(
                "Semantic Error",
                "The drawer cannot be bound as opened because the framekey has not been found yet.",
                "Find the framekey first, then return to the drawer."
            )

        SYMBOL_TABLE[identifier] = {"type": datatype, "value": value}

        story(f"  Meaning confirmed: '{identifier}' belongs to type '{datatype}'.")
        story(f"  Binding successful: '{identifier}' is now stored in the cabin registry.")
        return ("declaration", identifier, value)

    if ast_node["node_type"] == "output":
        expr = ast_node["expression"]

        if len(expr) == 1 and expr[0]["type"] == "IDENTIFIER" and expr[0]["value"] == "all":
            story("  The cabin listens. All remembered truths are being revealed.")

            full_reveal = [
                "You fell into a hidden forest trap and woke inside a quiet cabin.",
                "Beside the bed were a lamp, a photograph, and the feeling that time had stopped.",
                "The photograph showed a weary but warm mother and her young daughter in front of this same cabin.",
                "A note pointed toward what had been loved most, and behind the picture frame a hidden key was waiting.",
                "That key opened a locked drawer, where unread letters had been kept for years.",
                "The letters were written by the mother to her daughter long after the daughter had died in the cabin.",
                "The mother never truly left, because grief turned the house into a memorial.",
                "You were not brought here to solve a horror puzzle, but to witness memory and the love that refused to disappear."
            ]

            return ("output_all", full_reveal)

        value = evaluate_expression(expr)
        story("  The cabin listens. Your words are ready to be revealed.")
        return ("output", value)

    if ast_node["node_type"] == "class_decl":
        class_name = ast_node["class_name"]
        CLASS_TABLE[class_name] = {"name": class_name}
        story(f"  Structure forged: class '{class_name}' is now known to the cabin.")
        return ("class_decl", class_name)

    if ast_node["node_type"] == "object_inst":
        class_name = ast_node["class_name"]
        object_name = ast_node["object_name"]

        if class_name not in CLASS_TABLE:
            raise CompilerError(
                "Semantic Error",
                f"Cannot bind object '{object_name}' because class '{class_name}' does not exist."
            )

        OBJECT_TABLE[object_name] = {"class": class_name}
        story(f"  Object formed: '{object_name}' is now an instance of '{class_name}'.")
        return ("object_inst", object_name, class_name)

    if ast_node["node_type"] == "eyes":
        condition_result = evaluate_condition(ast_node["condition"])
        story(f"  Eyes condition checked: result is {condition_result}.")

        if condition_result:
            gate_reason = get_action_gate_reason(ast_node["action_tokens"])
            if gate_reason:
                story("  The eyes are open, but memory itself blocks your way.")
                return ("eyes", False, None, gate_reason)

            story("  The eyes are open. Truth may be seen.")
            nested_tokens = rebuild_statement_tokens(ast_node["action_tokens"])
            nested_ast, _ = parse(nested_tokens)
            nested_result = semantic_analyze(nested_ast)
            return ("eyes", True, nested_result, None)

        story("  The eyes remain closed. You shall not pass.")
        return ("eyes", False, None, "The eyes remain closed. You shall not pass.")

    if ast_node["node_type"] == "stream":
        iteration = 0
        last_result = None

        while evaluate_condition(ast_node["condition"]):
            if iteration >= MAX_STREAM_ITERATIONS:
                story("  The stream is halted by a safety boundary. The cabin refuses endless repetition.")
                break

            story(f"  Stream iteration {iteration + 1} begins.")
            nested_tokens = rebuild_statement_tokens(ast_node["action_tokens"])
            nested_ast, _ = parse(nested_tokens)
            last_result = semantic_analyze(nested_ast)
            iteration += 1

        story(f"  The stream settles after {iteration} iteration(s).")
        return ("stream", iteration, last_result)

    raise CompilerError("Semantic Error", "Unknown AST node encountered.")


def story_lore(ast_node, result):
    node_type = ast_node["node_type"]

    if node_type == "declaration":
        identifier = ast_node["identifier"]
        assigned_value = result[2]

        symbolic_value_lore = {
            ("photo", "remembered"): "The photograph is no longer just an object. It becomes the first wound opened by memory.",
            ("note", "unfolded"): "The note is carefully unfolded, as if grief trusted your hands enough to continue.",
            ("letters", "unsealed"): "The silence inside the drawer finally breaks. The mother's hidden years of mourning are no longer alone.",
            ("truth", "veilgone"): "Nothing remains covered now. The cabin stops being a riddle and becomes a memorial.",
            ("grief", "witnessed"): "At last, the house is understood for what it truly is: grief preserved so it would not vanish unheard."
        }

        default_lore = {
            "wakeup": "You wake in the cabin because someone chose to save you from the forest trap.",
            "drawer": "The locked drawer yields, as though it had been waiting for the one person who noticed the frame.",
            "grief": "The order of the cabin reveals itself as grief given form.",
            "mother": "The mother's presence lingers in every preserved object and untouched corner.",
            "child": "The child is gone, yet every clue bends back toward her.",
            "framekey": "The hidden key behind the photograph proves that memory here is never merely decorative.",
            "code": "Even numbers in this place feel ceremonial, as if the cabin remembers through counting.",
        }

        if (identifier, assigned_value) in symbolic_value_lore:
            story(f"\nStory Lore:\n{symbolic_value_lore[(identifier, assigned_value)]}")
        elif identifier in default_lore:
            story(f"\nStory Lore:\n{default_lore[identifier]}")

    elif node_type == "output":
        if len(ast_node["expression"]) == 1 and ast_node["expression"][0]["type"] == "IDENTIFIER":
            name = ast_node["expression"][0]["value"]

            if name == "all":
                story(
                    "\nStory Lore:\n"
                    "The cabin no longer offers clues one at a time.\n"
                    "Everything rises together, and the full weight of the house can finally be understood."
                )
                return

            lore_map = {
                "photo": "The photograph shows a mother and daughter outside this same cabin, before grief made it still.",
                "note": "Reading the note aloud makes the silence feel less empty, as though someone needed these words heard.",
                "letters": "The letters reveal the mother writing to her daughter long after the daughter's death.",
                "truth": "You realize you were not brought here merely to survive. You were brought here to witness.",
                "grief": "You understand that the cabin was never a trap of horror, but a memorial where love and grief became architecture.",
                "drawer": "The drawer opens only because memory now recognizes that you have earned it."
            }
            if name in lore_map:
                story(f"\nStory Lore:\n{lore_map[name]}")

    elif node_type == "class_decl":
        story("\nStory Lore:\nA new structure has been forged, as if the cabin itself is learning how to preserve memory in form.")

    elif node_type == "object_inst":
        story("\nStory Lore:\nWhat was once only an idea now takes shape. In this house, even structures feel like memory made tangible.")

    elif node_type == "eyes":
        if result[1]:
            story("\nStory Lore:\nYour eyes are open, and the cabin permits what was once hidden to be seen.")
        else:
            reason = result[3]
            if reason and "key" in reason.lower():
                story(f"\nStory Lore:\n{reason}")
            else:
                story("\nStory Lore:\nYour eyes remain closed. You shall not pass.")

    elif node_type == "stream":
        story("\nStory Lore:\nThe world moves with the chaotic flow of life. What returns is not always repetition, but motion that refuses stillness.")


def print_symbol_table():
    if SYMBOL_TABLE:
        story("\n[SYMBOL TABLE] Cabin Registry")
        story("-" * 52)
        story(f"{'Identifier':<18}{'Datatype':<16}{'Value':<18}")
        story("-" * 52)
        for name, info in SYMBOL_TABLE.items():
            story(f"{name:<18}{info['type']:<16}{str(info['value']):<18}")
        story("-" * 52)

    if CLASS_TABLE:
        story("\n[CLASS TABLE]")
        for name in CLASS_TABLE:
            story(f"  Class: {name}")

    if OBJECT_TABLE:
        story("\n[OBJECT TABLE]")
        for name, info in OBJECT_TABLE.items():
            story(f"  Object: {name} -> Class: {info['class']}")


def run_full_story_demo():
    demo_lines = [
        "mrkn wakeup ~ 1.",
        "mrktxt photo ~ *remembered*.",
        "reveal:photo.",
        "mrktxt note ~ *unfolded*.",
        "reveal:note.",
        "mrksym framekey ~ 'K'.",
        "eyes:framekey ~~ 'K':mrkn drawer ~ 1.",
        "mrktxt letters ~ *unsealed*.",
        "reveal:letters.",
        "mrktxt truth ~ *veilgone*.",
        "eyes:wakeup ~~ 1:reveal:truth.",
        "mrktxt grief ~ *witnessed*.",
        "reveal:grief."
    ]

    story("\n" + "=" * 72)
    story("REVEAL ALL MODE")
    story("The cabin chooses to show everything at once.")
    story("=" * 72)

    for line in demo_lines:
        story(f"\n[DEMO INPUT] {line}")
        compile_line(line, from_demo=True)


def compile_line(source_code, from_demo=False):
    if source_code.strip() == "reveal:all." and not from_demo:
        run_full_story_demo()
        return

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
        story("\nStory Lore:\nYou try to name what you have seen, but the cabin does not accept careless runes.")
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
        elif result[0] == "output_all":
            story("\n[OUTPUT]")
            for item in result[1]:
                story(f"  {item}")
        elif result[0] == "declaration":
            story(f"\n[BINDING RESULT] '{result[1]}' now holds: {result[2]}")
        elif result[0] == "class_decl":
            story(f"\n[CLASS RESULT] '{result[1]}' has been forged.")
        elif result[0] == "object_inst":
            story(f"\n[OBJECT RESULT] '{result[1]}' now exists as an instance of '{result[2]}'.")
        elif result[0] == "eyes":
            story(f"\n[EYES RESULT] Condition outcome: {result[1]}")
            if result[3]:
                story(f"  Gate: {result[3]}")
        elif result[0] == "stream":
            story(f"\n[STREAM RESULT] Total iterations: {result[1]}")

        story_lore(ast_node, result)
        print_symbol_table()
        story("\nStatus: COMPILATION SUCCESS")

    except CompilerError as err:
        story(f"\n[{err.phase.upper()}]")
        story(f"  Error found: {err.message}")
        story(f"  Recovery: {err.recovery}")

        if err.phase == "Syntax Error":
            story("\nStory Lore:\nThe sentence breaks apart before the room can understand it.")
        elif err.phase == "Semantic Error":
            story("\nStory Lore:\nYou reached for meaning before the cabin believed you were ready.")

        print_symbol_table()
        story("\nStatus: COMPILATION FAILED")


def main():
    print("=" * 72)
    print(f"Welcome to {LANGUAGE_NAME}")
    print("Enter one line at a time.")
    print(f"Type '{LANGUAGE_NAME}' to exit.")
    print("Memory is preserved while the program runs.")
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