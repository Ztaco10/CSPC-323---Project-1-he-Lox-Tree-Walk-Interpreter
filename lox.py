from __future__ import annotations

import sys
import time
from dataclasses import dataclass
from enum import Enum, auto
from typing import Any, Callable, Dict, List, Optional, Sequence, Tuple


###############################################################################
# Token and Scanner
###############################################################################

class TokenType(Enum):

    # Single‑character tokens.
    LEFT_PAREN = auto()
    RIGHT_PAREN = auto()
    LEFT_BRACE = auto()
    RIGHT_BRACE = auto()
    COMMA = auto()
    DOT = auto()
    MINUS = auto()
    PLUS = auto()
    SEMICOLON = auto()
    SLASH = auto()
    STAR = auto()

    # One or two character tokens.
    BANG = auto()
    BANG_EQUAL = auto()
    EQUAL = auto()
    EQUAL_EQUAL = auto()
    GREATER = auto()
    GREATER_EQUAL = auto()
    LESS = auto()
    LESS_EQUAL = auto()

    # Literals.
    IDENTIFIER = auto()
    STRING = auto()
    NUMBER = auto()

    # Keywords.
    AND = auto()
    CLASS = auto()
    ELSE = auto()
    FALSE = auto()
    FUN = auto()
    FOR = auto()
    IF = auto()
    NIL = auto()
    OR = auto()
    PRINT = auto()
    RETURN = auto()
    SUPER = auto()
    THIS = auto()
    TRUE = auto()
    VAR = auto()
    WHILE = auto()

    EOF = auto()


KEYWORDS: Dict[str, TokenType] = {
    "and": TokenType.AND,
    "class": TokenType.CLASS,
    "else": TokenType.ELSE,
    "false": TokenType.FALSE,
    "fun": TokenType.FUN,
    "for": TokenType.FOR,
    "if": TokenType.IF,
    "nil": TokenType.NIL,
    "or": TokenType.OR,
    "print": TokenType.PRINT,
    "return": TokenType.RETURN,
    "super": TokenType.SUPER,
    "this": TokenType.THIS,
    "true": TokenType.TRUE,
    "var": TokenType.VAR,
    "while": TokenType.WHILE,
}


@dataclass
class Token:


    type: TokenType
    lexeme: str
    literal: Optional[Any]
    line: int

    def __str__(self) -> str:
        return f"{self.type.name} {self.lexeme} {self.literal}"


class Scanner:


    def __init__(self, source: str) -> None:
        self.source = source
        self.tokens: List[Token] = []
        self.start = 0
        self.current = 0
        self.line = 1

    def scan_tokens(self) -> List[Token]:
        """Scan the entire input and return the sequence of tokens."""
        while not self._is_at_end():
            self.start = self.current
            self._scan_token()
        self.tokens.append(Token(TokenType.EOF, "", None, self.line))
        return self.tokens

    # Helpers for scanning
    def _is_at_end(self) -> bool:
        return self.current >= len(self.source)

    def _advance(self) -> str:
        ch = self.source[self.current]
        self.current += 1
        return ch

    def _add_token(self, type: TokenType, literal: Optional[Any] = None) -> None:
        text = self.source[self.start:self.current]
        self.tokens.append(Token(type, text, literal, self.line))

    def _match(self, expected: str) -> bool:
        if self._is_at_end() or self.source[self.current] != expected:
            return False
        self.current += 1
        return True

    def _peek(self) -> str:
        return '\0' if self._is_at_end() else self.source[self.current]

    def _peek_next(self) -> str:
        if self.current + 1 >= len(self.source):
            return '\0'
        return self.source[self.current + 1]

    def _scan_token(self) -> None:
        c = self._advance()
        if c == '(': self._add_token(TokenType.LEFT_PAREN)
        elif c == ')': self._add_token(TokenType.RIGHT_PAREN)
        elif c == '{': self._add_token(TokenType.LEFT_BRACE)
        elif c == '}': self._add_token(TokenType.RIGHT_BRACE)
        elif c == ',': self._add_token(TokenType.COMMA)
        elif c == '.': self._add_token(TokenType.DOT)
        elif c == '-': self._add_token(TokenType.MINUS)
        elif c == '+': self._add_token(TokenType.PLUS)
        elif c == ';': self._add_token(TokenType.SEMICOLON)
        elif c == '*': self._add_token(TokenType.STAR)
        elif c == '!': self._add_token(TokenType.BANG_EQUAL if self._match('=') else TokenType.BANG)
        elif c == '=': self._add_token(TokenType.EQUAL_EQUAL if self._match('=') else TokenType.EQUAL)
        elif c == '<': self._add_token(TokenType.LESS_EQUAL if self._match('=') else TokenType.LESS)
        elif c == '>': self._add_token(TokenType.GREATER_EQUAL if self._match('=') else TokenType.GREATER)
        elif c == '/':
            if self._match('/'):
                # A comment goes until the end of the line.
                while self._peek() != '\n' and not self._is_at_end():
                    self._advance()
            else:
                self._add_token(TokenType.SLASH)
        elif c in (' ', '\r', '\t'):
            # Ignore whitespace.
            pass
        elif c == '\n':
            self.line += 1
        elif c == '"':
            self._string()
        else:
            if c.isdigit():
                self._number()
            elif c.isalpha() or c == '_':
                self._identifier()
            else:
                Lox.error(self.line, f"Unexpected character '{c}'.")

    def _string(self) -> None:
        while self._peek() != '"' and not self._is_at_end():
            if self._peek() == '\n':
                self.line += 1
            self._advance()
        if self._is_at_end():
            Lox.error(self.line, "Unterminated string.")
            return
        # The closing quote
        self._advance()
        value = self.source[self.start + 1:self.current - 1]
        self._add_token(TokenType.STRING, value)

    def _number(self) -> None:
        while self._peek().isdigit():
            self._advance()
        if self._peek() == '.' and self._peek_next().isdigit():
            self._advance()  # consume '.'
            while self._peek().isdigit():
                self._advance()
        number_text = self.source[self.start:self.current]
        try:
            value: float = float(number_text)
        except ValueError:
            Lox.error(self.line, f"Invalid number literal '{number_text}'.")
            value = 0.0
        self._add_token(TokenType.NUMBER, value)

    def _identifier(self) -> None:
        while self._peek().isalnum() or self._peek() == '_':
            self._advance()
        text = self.source[self.start:self.current]
        token_type = KEYWORDS.get(text, TokenType.IDENTIFIER)
        self._add_token(token_type)


###############################################################################
# AST Nodes
###############################################################################

class ExprVisitor:
    def visit_assign_expr(self, expr: 'Assign') -> Any: ...
    def visit_binary_expr(self, expr: 'Binary') -> Any: ...
    def visit_call_expr(self, expr: 'Call') -> Any: ...
    def visit_grouping_expr(self, expr: 'Grouping') -> Any: ...
    def visit_literal_expr(self, expr: 'Literal') -> Any: ...
    def visit_logical_expr(self, expr: 'Logical') -> Any: ...
    def visit_unary_expr(self, expr: 'Unary') -> Any: ...
    def visit_variable_expr(self, expr: 'Variable') -> Any: ...


class Expr:
    def accept(self, visitor: ExprVisitor) -> Any:
        raise NotImplementedError()


@dataclass
class Assign(Expr):
    name: Token
    value: Expr
    def accept(self, visitor: ExprVisitor) -> Any:
        return visitor.visit_assign_expr(self)


@dataclass
class Binary(Expr):
    left: Expr
    operator: Token
    right: Expr
    def accept(self, visitor: ExprVisitor) -> Any:
        return visitor.visit_binary_expr(self)


@dataclass
class Call(Expr):
    callee: Expr
    paren: Token
    arguments: List[Expr]
    def accept(self, visitor: ExprVisitor) -> Any:
        return visitor.visit_call_expr(self)


@dataclass
class Grouping(Expr):
    expression: Expr
    def accept(self, visitor: ExprVisitor) -> Any:
        return visitor.visit_grouping_expr(self)


@dataclass
class Literal(Expr):
    value: Any
    def accept(self, visitor: ExprVisitor) -> Any:
        return visitor.visit_literal_expr(self)


@dataclass
class Logical(Expr):
    left: Expr
    operator: Token
    right: Expr
    def accept(self, visitor: ExprVisitor) -> Any:
        return visitor.visit_logical_expr(self)


@dataclass
class Unary(Expr):
    operator: Token
    right: Expr
    def accept(self, visitor: ExprVisitor) -> Any:
        return visitor.visit_unary_expr(self)


@dataclass
class Variable(Expr):
    name: Token
    def accept(self, visitor: ExprVisitor) -> Any:
        return visitor.visit_variable_expr(self)


###############################################################################
# Statement Nodes
###############################################################################

class StmtVisitor:
    def visit_block_stmt(self, stmt: 'Block') -> Any: ...
    def visit_expression_stmt(self, stmt: 'Expression') -> Any: ...
    def visit_function_stmt(self, stmt: 'Function') -> Any: ...
    def visit_if_stmt(self, stmt: 'If') -> Any: ...
    def visit_print_stmt(self, stmt: 'Print') -> Any: ...
    def visit_return_stmt(self, stmt: 'Return') -> Any: ...
    def visit_var_stmt(self, stmt: 'Var') -> Any: ...
    def visit_while_stmt(self, stmt: 'While') -> Any: ...


class Stmt:
    def accept(self, visitor: StmtVisitor) -> Any:
        raise NotImplementedError()


@dataclass
class Block(Stmt):
    statements: List[Stmt]
    def accept(self, visitor: StmtVisitor) -> Any:
        return visitor.visit_block_stmt(self)


@dataclass
class Expression(Stmt):
    expression: Expr
    def accept(self, visitor: StmtVisitor) -> Any:
        return visitor.visit_expression_stmt(self)


@dataclass
class Function(Stmt):
    name: Token
    params: List[Token]
    body: List[Stmt]
    def accept(self, visitor: StmtVisitor) -> Any:
        return visitor.visit_function_stmt(self)


@dataclass
class If(Stmt):
    condition: Expr
    then_branch: Stmt
    else_branch: Optional[Stmt]
    def accept(self, visitor: StmtVisitor) -> Any:
        return visitor.visit_if_stmt(self)


@dataclass
class Print(Stmt):
    expression: Expr
    def accept(self, visitor: StmtVisitor) -> Any:
        return visitor.visit_print_stmt(self)


@dataclass
class Return(Stmt):
    keyword: Token
    value: Optional[Expr]
    def accept(self, visitor: StmtVisitor) -> Any:
        return visitor.visit_return_stmt(self)


@dataclass
class Var(Stmt):
    name: Token
    initializer: Optional[Expr]
    def accept(self, visitor: StmtVisitor) -> Any:
        return visitor.visit_var_stmt(self)


@dataclass
class While(Stmt):
    condition: Expr
    body: Stmt
    def accept(self, visitor: StmtVisitor) -> Any:
        return visitor.visit_while_stmt(self)


###############################################################################
# Parser
###############################################################################

class ParseError(RuntimeError):
    pass


class Parser:
    """Recursive descent parser for Lox.

    This parser implements the grammar given in Appendix I, with rules
    organized from the lowest‑level expressions up to full statements and
    declarations. It throws ``ParseError`` on invalid syntax.
    """

    def __init__(self, tokens: Sequence[Token]) -> None:
        self.tokens = list(tokens)
        self.current = 0

    def parse(self) -> List[Stmt]:
        statements: List[Stmt] = []
        while not self._is_at_end():
            decl = self._declaration()
            if decl is not None:
                statements.append(decl)
        return statements

    def _declaration(self) -> Optional[Stmt]:
        try:
            if self._match(TokenType.FUN):
                return self._function("function")
            if self._match(TokenType.VAR):
                return self._var_declaration()
            return self._statement()
        except ParseError:
            self._synchronize()
            return None

    def _function(self, kind: str) -> Function:
        name = self._consume(TokenType.IDENTIFIER, f"Expect {kind} name.")
        self._consume(TokenType.LEFT_PAREN, f"Expect '(' after {kind} name.")
        parameters: List[Token] = []
        if not self._check(TokenType.RIGHT_PAREN):
            while True:
                if len(parameters) >= 255:
                    Lox.error(self._peek().line, "Cannot have more than 255 parameters.")
                parameters.append(self._consume(TokenType.IDENTIFIER, "Expect parameter name."))
                if not self._match(TokenType.COMMA):
                    break
        self._consume(TokenType.RIGHT_PAREN, "Expect ')' after parameters.")
        self._consume(TokenType.LEFT_BRACE, f"Expect '{{' before {kind} body.")
        body = self._block()
        return Function(name, parameters, body)

    def _var_declaration(self) -> Stmt:
        name = self._consume(TokenType.IDENTIFIER, "Expect variable name.")
        initializer: Optional[Expr] = None
        if self._match(TokenType.EQUAL):
            initializer = self._expression()
        self._consume(TokenType.SEMICOLON, "Expect ';' after variable declaration.")
        return Var(name, initializer)

    def _statement(self) -> Stmt:
        if self._match(TokenType.FOR):
            return self._for_statement()
        if self._match(TokenType.IF):
            return self._if_statement()
        if self._match(TokenType.PRINT):
            return self._print_statement()
        if self._match(TokenType.RETURN):
            return self._return_statement()
        if self._match(TokenType.WHILE):
            return self._while_statement()
        if self._match(TokenType.LEFT_BRACE):
            return Block(self._block())
        return self._expression_statement()

    def _for_statement(self) -> Stmt:
        self._consume(TokenType.LEFT_PAREN, "Expect '(' after 'for'.")
        # initializer
        if self._match(TokenType.SEMICOLON):
            initializer = None
        elif self._match(TokenType.VAR):
            initializer = self._var_declaration()
        else:
            initializer = self._expression_statement()
        # condition
        condition: Optional[Expr] = None
        if not self._check(TokenType.SEMICOLON):
            condition = self._expression()
        self._consume(TokenType.SEMICOLON, "Expect ';' after loop condition.")
        # increment
        increment: Optional[Expr] = None
        if not self._check(TokenType.RIGHT_PAREN):
            increment = self._expression()
        self._consume(TokenType.RIGHT_PAREN, "Expect ')' after for clauses.")
        body = self._statement()
        # desugar for into while
        if increment is not None:
            body = Block([body, Expression(increment)])
        if condition is None:
            condition = Literal(True)
        body = While(condition, body)
        if initializer is not None:
            body = Block([initializer, body])
        return body

    def _if_statement(self) -> Stmt:
        self._consume(TokenType.LEFT_PAREN, "Expect '(' after 'if'.")
        condition = self._expression()
        self._consume(TokenType.RIGHT_PAREN, "Expect ')' after if condition.")
        then_branch = self._statement()
        else_branch = None
        if self._match(TokenType.ELSE):
            else_branch = self._statement()
        return If(condition, then_branch, else_branch)

    def _print_statement(self) -> Stmt:
        value = self._expression()
        self._consume(TokenType.SEMICOLON, "Expect ';' after value.")
        return Print(value)

    def _return_statement(self) -> Stmt:
        keyword = self._previous()
        value: Optional[Expr] = None
        if not self._check(TokenType.SEMICOLON):
            value = self._expression()
        self._consume(TokenType.SEMICOLON, "Expect ';' after return value.")
        return Return(keyword, value)

    def _while_statement(self) -> Stmt:
        self._consume(TokenType.LEFT_PAREN, "Expect '(' after 'while'.")
        condition = self._expression()
        self._consume(TokenType.RIGHT_PAREN, "Expect ')' after condition.")
        body = self._statement()
        return While(condition, body)

    def _block(self) -> List[Stmt]:
        statements: List[Stmt] = []
        while not self._check(TokenType.RIGHT_BRACE) and not self._is_at_end():
            decl = self._declaration()
            if decl is not None:
                statements.append(decl)
        self._consume(TokenType.RIGHT_BRACE, "Expect '}' after block.")
        return statements

    def _expression_statement(self) -> Stmt:
        expr = self._expression()
        self._consume(TokenType.SEMICOLON, "Expect ';' after expression.")
        return Expression(expr)

    def _expression(self) -> Expr:
        return self._assignment()

    def _assignment(self) -> Expr:
        expr = self._or()
        if self._match(TokenType.EQUAL):
            equals = self._previous()
            value = self._assignment()
            if isinstance(expr, Variable):
                return Assign(expr.name, value)
            Lox.error(equals.line, "Invalid assignment target.")
        return expr

    def _or(self) -> Expr:
        expr = self._and()
        while self._match(TokenType.OR):
            operator = self._previous()
            right = self._and()
            expr = Logical(expr, operator, right)
        return expr

    def _and(self) -> Expr:
        expr = self._equality()
        while self._match(TokenType.AND):
            operator = self._previous()
            right = self._equality()
            expr = Logical(expr, operator, right)
        return expr

    def _equality(self) -> Expr:
        expr = self._comparison()
        while self._match(TokenType.BANG_EQUAL, TokenType.EQUAL_EQUAL):
            operator = self._previous()
            right = self._comparison()
            expr = Binary(expr, operator, right)
        return expr

    def _comparison(self) -> Expr:
        expr = self._term()
        while self._match(TokenType.GREATER, TokenType.GREATER_EQUAL, TokenType.LESS, TokenType.LESS_EQUAL):
            operator = self._previous()
            right = self._term()
            expr = Binary(expr, operator, right)
        return expr

    def _term(self) -> Expr:
        expr = self._factor()
        while self._match(TokenType.MINUS, TokenType.PLUS):
            operator = self._previous()
            right = self._factor()
            expr = Binary(expr, operator, right)
        return expr

    def _factor(self) -> Expr:
        expr = self._unary()
        while self._match(TokenType.SLASH, TokenType.STAR):
            operator = self._previous()
            right = self._unary()
            expr = Binary(expr, operator, right)
        return expr

    def _unary(self) -> Expr:
        if self._match(TokenType.BANG, TokenType.MINUS):
            operator = self._previous()
            right = self._unary()
            return Unary(operator, right)
        return self._call()

    def _call(self) -> Expr:
        expr = self._primary()
        while True:
            if self._match(TokenType.LEFT_PAREN):
                expr = self._finish_call(expr)
            else:
                break
        return expr

    def _finish_call(self, callee: Expr) -> Expr:
        arguments: List[Expr] = []
        if not self._check(TokenType.RIGHT_PAREN):
            while True:
                if len(arguments) >= 255:
                    Lox.error(self._peek().line, "Cannot have more than 255 arguments.")
                arguments.append(self._expression())
                if not self._match(TokenType.COMMA):
                    break
        paren = self._consume(TokenType.RIGHT_PAREN, "Expect ')' after arguments.")
        return Call(callee, paren, arguments)

    def _primary(self) -> Expr:
        if self._match(TokenType.FALSE): return Literal(False)
        if self._match(TokenType.TRUE): return Literal(True)
        if self._match(TokenType.NIL): return Literal(None)
        if self._match(TokenType.NUMBER, TokenType.STRING): return Literal(self._previous().literal)
        if self._match(TokenType.IDENTIFIER): return Variable(self._previous())
        if self._match(TokenType.LEFT_PAREN):
            expr = self._expression()
            self._consume(TokenType.RIGHT_PAREN, "Expect ')' after expression.")
            return Grouping(expr)
        raise self._error(self._peek(), "Expect expression.")

    # Utility methods
    def _match(self, *types: TokenType) -> bool:
        for t in types:
            if self._check(t):
                self._advance()
                return True
        return False

    def _check(self, type: TokenType) -> bool:
        if self._is_at_end():
            return False
        return self._peek().type == type

    def _advance(self) -> Token:
        if not self._is_at_end():
            self.current += 1
        return self._previous()

    def _is_at_end(self) -> bool:
        return self._peek().type == TokenType.EOF

    def _peek(self) -> Token:
        return self.tokens[self.current]

    def _previous(self) -> Token:
        return self.tokens[self.current - 1]

    def _consume(self, type: TokenType, message: str) -> Token:
        if self._check(type):
            return self._advance()
        raise self._error(self._peek(), message)

    def _error(self, token: Token, message: str) -> ParseError:
        Lox.parse_error(token, message)
        return ParseError()

    def _synchronize(self) -> None:
        self._advance()
        while not self._is_at_end():
            if self._previous().type == TokenType.SEMICOLON:
                return
            if self._peek().type in (TokenType.CLASS, TokenType.FUN, TokenType.VAR,
                                     TokenType.FOR, TokenType.IF, TokenType.WHILE,
                                     TokenType.PRINT, TokenType.RETURN):
                return
            self._advance()


###############################################################################
# Runtime support
###############################################################################

class LoxRuntimeError(Exception):
    def __init__(self, token: Token, message: str) -> None:
        self.token = token
        self.message = message
        super().__init__(message)


class Environment:
    """Represents a lexical scope mapping variable names to values."""
    def __init__(self, enclosing: Optional['Environment'] = None) -> None:
        self.enclosing = enclosing
        self.values: Dict[str, Any] = {}

    def define(self, name: str, value: Any) -> None:
        self.values[name] = value

    def get(self, name: Token) -> Any:
        if name.lexeme in self.values:
            return self.values[name.lexeme]
        if self.enclosing is not None:
            return self.enclosing.get(name)
        raise LoxRuntimeError(name, f"Undefined variable '{name.lexeme}'.")

    def assign(self, name: Token, value: Any) -> None:
        if name.lexeme in self.values:
            self.values[name.lexeme] = value
            return
        if self.enclosing is not None:
            self.enclosing.assign(name, value)
            return
        raise LoxRuntimeError(name, f"Undefined variable '{name.lexeme}'.")


class LoxCallable:
    """Interface for callable Lox entities (functions, native functions)."""
    def arity(self) -> int:
        raise NotImplementedError()
    def call(self, interpreter: 'Interpreter', arguments: List[Any]) -> Any:
        raise NotImplementedError()


class LoxFunction(LoxCallable):
    def __init__(self, declaration: Function, closure: Environment) -> None:
        self.declaration = declaration
        self.closure = closure

    def arity(self) -> int:
        return len(self.declaration.params)

    def call(self, interpreter: 'Interpreter', arguments: List[Any]) -> Any:
        # Create new environment for the function body.
        environment = Environment(self.closure)
        for param, arg in zip(self.declaration.params, arguments):
            environment.define(param.lexeme, arg)
        try:
            interpreter._execute_block(self.declaration.body, environment)
        except ReturnException as return_value:
            return return_value.value
        return None

    def __str__(self) -> str:
        return f"<fn {self.declaration.name.lexeme}>"


class ClockFunction(LoxCallable):
    """A native function that returns the current time in seconds."""
    def arity(self) -> int:
        return 0
    def call(self, interpreter: 'Interpreter', arguments: List[Any]) -> float:
        return time.time()
    def __str__(self) -> str:
        return "<native fn>"


class ReturnException(RuntimeError):
    def __init__(self, value: Any) -> None:
        self.value = value
        super().__init__()


class Interpreter(ExprVisitor, StmtVisitor):
    """Evaluates expressions and executes statements to run Lox programs."""

    def __init__(self) -> None:
        self.globals = Environment()
        self.environment = self.globals
        # Define a native function 'clock'
        self.globals.define("clock", ClockFunction())

    def interpret(self, statements: Sequence[Stmt]) -> None:
        try:
            for stmt in statements:
                self._execute(stmt)
        except LoxRuntimeError as error:
            Lox.runtime_error(error)

    # Expression visitor methods
    def visit_literal_expr(self, expr: Literal) -> Any:
        return expr.value
    def visit_grouping_expr(self, expr: Grouping) -> Any:
        return self._evaluate(expr.expression)
    def visit_unary_expr(self, expr: Unary) -> Any:
        right = self._evaluate(expr.right)
        if expr.operator.type == TokenType.MINUS:
            self._check_number_operand(expr.operator, right)
            return -float(right)
        if expr.operator.type == TokenType.BANG:
            return not self._is_truthy(right)
        return None
    def visit_binary_expr(self, expr: Binary) -> Any:
        left = self._evaluate(expr.left)
        right = self._evaluate(expr.right)
        t = expr.operator.type
        if t == TokenType.MINUS:
            self._check_number_operands(expr.operator, left, right)
            return float(left) - float(right)
        if t == TokenType.SLASH:
            self._check_number_operands(expr.operator, left, right)
            if float(right) == 0:
                raise LoxRuntimeError(expr.operator, "Division by zero.")
            return float(left) / float(right)
        if t == TokenType.STAR:
            self._check_number_operands(expr.operator, left, right)
            return float(left) * float(right)
        if t == TokenType.PLUS:
            # Support number addition and string concatenation
            if isinstance(left, (float, int)) and isinstance(right, (float, int)):
                return float(left) + float(right)
            if isinstance(left, str) and isinstance(right, str):
                return left + right
            raise LoxRuntimeError(expr.operator, "Operands must be two numbers or two strings.")
        if t == TokenType.GREATER:
            self._check_number_operands(expr.operator, left, right)
            return float(left) > float(right)
        if t == TokenType.GREATER_EQUAL:
            self._check_number_operands(expr.operator, left, right)
            return float(left) >= float(right)
        if t == TokenType.LESS:
            self._check_number_operands(expr.operator, left, right)
            return float(left) < float(right)
        if t == TokenType.LESS_EQUAL:
            self._check_number_operands(expr.operator, left, right)
            return float(left) <= float(right)
        if t == TokenType.BANG_EQUAL:
            return not self._is_equal(left, right)
        if t == TokenType.EQUAL_EQUAL:
            return self._is_equal(left, right)
        return None
    def visit_variable_expr(self, expr: Variable) -> Any:
        return self.environment.get(expr.name)
    def visit_assign_expr(self, expr: Assign) -> Any:
        value = self._evaluate(expr.value)
        self.environment.assign(expr.name, value)
        return value
    def visit_logical_expr(self, expr: Logical) -> Any:
        left = self._evaluate(expr.left)
        if expr.operator.type == TokenType.OR:
            if self._is_truthy(left):
                return left
        else:  # AND
            if not self._is_truthy(left):
                return left
        return self._evaluate(expr.right)
    def visit_call_expr(self, expr: Call) -> Any:
        callee = self._evaluate(expr.callee)
        arguments = [self._evaluate(arg) for arg in expr.arguments]
        if not isinstance(callee, LoxCallable):
            raise LoxRuntimeError(expr.paren, "Can only call functions and classes.")
        if len(arguments) != callee.arity():
            raise LoxRuntimeError(expr.paren, f"Expected {callee.arity()} arguments but got {len(arguments)}.")
        return callee.call(self, arguments)

    # Statement visitor methods
    def visit_expression_stmt(self, stmt: Expression) -> None:
        self._evaluate(stmt.expression)
        return None
    def visit_print_stmt(self, stmt: Print) -> None:
        value = self._evaluate(stmt.expression)
        print(self._stringify(value))
    def visit_var_stmt(self, stmt: Var) -> None:
        value = None
        if stmt.initializer is not None:
            value = self._evaluate(stmt.initializer)
        self.environment.define(stmt.name.lexeme, value)
    def visit_block_stmt(self, stmt: Block) -> None:
        self._execute_block(stmt.statements, Environment(self.environment))
    def visit_if_stmt(self, stmt: If) -> None:
        if self._is_truthy(self._evaluate(stmt.condition)):
            self._execute(stmt.then_branch)
        elif stmt.else_branch is not None:
            self._execute(stmt.else_branch)
    def visit_while_stmt(self, stmt: While) -> None:
        while self._is_truthy(self._evaluate(stmt.condition)):
            self._execute(stmt.body)
    def visit_function_stmt(self, stmt: Function) -> None:
        function = LoxFunction(stmt, self.environment)
        self.environment.define(stmt.name.lexeme, function)
    def visit_return_stmt(self, stmt: Return) -> None:
        value = None
        if stmt.value is not None:
            value = self._evaluate(stmt.value)
        raise ReturnException(value)

    # Internal helpers
    def _execute(self, stmt: Stmt) -> None:
        stmt.accept(self)

    def _evaluate(self, expr: Expr) -> Any:
        return expr.accept(self)

    def _execute_block(self, statements: Sequence[Stmt], environment: Environment) -> None:
        previous = self.environment
        try:
            self.environment = environment
            for statement in statements:
                self._execute(statement)
        finally:
            self.environment = previous

    @staticmethod
    def _is_truthy(value: Any) -> bool:
        if value is None: return False
        if isinstance(value, bool): return value
        return True
    @staticmethod
    def _is_equal(a: Any, b: Any) -> bool:
        if a is None and b is None: return True
        if a is None: return False
        return a == b
    @staticmethod
    def _stringify(value: Any) -> str:
        if value is None: return "nil"
        if isinstance(value, float):
            text = str(value)
            if text.endswith(".0"):
                text = text[:-2]
            return text
        return str(value)
    @staticmethod
    def _check_number_operand(operator: Token, operand: Any) -> None:
        if isinstance(operand, (float, int)):
            return
        raise LoxRuntimeError(operator, "Operand must be a number.")
    @staticmethod
    def _check_number_operands(operator: Token, left: Any, right: Any) -> None:
        if isinstance(left, (float, int)) and isinstance(right, (float, int)):
            return
        raise LoxRuntimeError(operator, "Operands must be numbers.")


###############################################################################
# Front end
###############################################################################

class Lox:
    """Entry point and error reporting for the interpreter."""
    had_error: bool = False
    had_runtime_error: bool = False

    @classmethod
    def main(cls, argv: Sequence[str]) -> None:
        interpreter = Interpreter()
        if len(argv) > 1:
            print("Usage: lox.py [script]")
            sys.exit(64)
        elif len(argv) == 1:
            cls._run_file(argv[0], interpreter)
        else:
            cls._run_prompt(interpreter)

    @classmethod
    def _run_file(cls, path: str, interpreter: Interpreter) -> None:
        with open(path, "r", encoding="utf-8") as f:
            source = f.read()
        cls._run(source, interpreter)
        if cls.had_error:
            sys.exit(65)
        if cls.had_runtime_error:
            sys.exit(70)

    @classmethod
    def _run_prompt(cls, interpreter: Interpreter) -> None:
        try:
            while True:
                line = input("?> ")
                if not line:
                    continue
                cls._run(line, interpreter)
                cls.had_error = False
        except (EOFError, KeyboardInterrupt):
            print()

    @classmethod
    def _run(cls, source: str, interpreter: Interpreter) -> None:
        scanner = Scanner(source)
        tokens = scanner.scan_tokens()
        parser = Parser(tokens)
        statements = parser.parse()
        # Stop if there was a syntax error.
        if cls.had_error:
            return
        interpreter.interpret(statements)

    # Error reporting helpers
    @classmethod
    def error(cls, line: int, message: str) -> None:
        cls._report(line, "", message)

    @classmethod
    def parse_error(cls, token: Token, message: str) -> None:
        if token.type == TokenType.EOF:
            cls._report(token.line, " at end", message)
        else:
            cls._report(token.line, f" at '{token.lexeme}'", message)

    @classmethod
    def _report(cls, line: int, where: str, message: str) -> None:
        print(f"[line {line}] Error{where}: {message}", file=sys.stderr)
        cls.had_error = True

    @classmethod
    def runtime_error(cls, error: LoxRuntimeError) -> None:
        print(f"{error.message}\n[line {error.token.line}]", file=sys.stderr)
        cls.had_runtime_error = True


if __name__ == "__main__":
    Lox.main(sys.argv[1:])
