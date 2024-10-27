import ast
import operator
import math
import re

allowed_operators = {
    ast.Add: operator.add,
    ast.Sub: operator.sub,
    ast.Mult: operator.mul,
    ast.Div: operator.truediv,
    ast.Pow: operator.pow,
    ast.USub: operator.neg
}

# Allowed mathematical functions
allowed_functions = {
    'sqrt': math.sqrt,
    'sin': math.sin,
    'cos': math.cos,
    'tan': math.tan,
    'log': math.log,
    'exp': math.exp,
    'abs': abs,
    'max': max,
    'min': min,
    'floor': math.floor,
    'ceil': math.ceil,
    'round': round
}

def safe_eval(expr):
    """
    Safely evaluate a mathematical expression using AST parsing.
    """
    def _eval(node):
        if isinstance(node, ast.Num):  # <number>
            return node.n
        elif isinstance(node, ast.BinOp):  # <left> <operator> <right>
            left = _eval(node.left)
            right = _eval(node.right)
            op_type = type(node.op)
            if op_type in allowed_operators:
                return allowed_operators[op_type](left, right)
            else:
                raise ValueError(f"Unsupported operator: {op_type}")
        elif isinstance(node, ast.UnaryOp):  # - <operand>
            operand = _eval(node.operand)
            op_type = type(node.op)
            if op_type in allowed_operators:
                return allowed_operators[op_type](operand)
            else:
                raise ValueError(f"Unsupported unary operator: {op_type}")
        elif isinstance(node, ast.Call):  # Function calls like sin(x)
            func_name = node.func.id
            if func_name in allowed_functions:
                args = [_eval(arg) for arg in node.args]
                return allowed_functions[func_name](*args)
            else:
                raise ValueError(f"Unsupported function: {func_name}")
        elif isinstance(node, ast.Name):
            if node.id in ('pi', 'e'):
                return getattr(math, node.id)
            else:
                raise ValueError(f"Unknown variable: {node.id}")
        else:
            raise ValueError(f"Unsupported expression: {node}")

    node = ast.parse(expr, mode='eval').body
    return _eval(node)


async def try_handle_ace(message):
    if message.content.startswith('eval'):
        pattern = r'eval\s*`(.+?)`'
        match = re.match(pattern, message.content)
        if match:
            expression = match.group(1)
            expression = expression.replace('^', '**')
            try:
                result = safe_eval(expression)
                await message.reply(f"> `{result}`")
            except Exception as e:
                await message.reply(f"Error evaluating expression: {e}")
        else:
            await message.reply("Please enclose the expression in backticks (`).")
