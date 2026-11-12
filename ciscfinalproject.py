from dataclasses import dataclass
from bakery import assert_equal
from drafter import *


# This website gives general password-strength feedback.
# It does not check whether a password has appeared in a data breach.
# IMPORTANT: Test with an invented password, not a real password.
# The password is analyzed when the form is submitted, but is NOT saved
# in the State or in the check history.


@dataclass
class PasswordCheck:
    """
    One saved result. We keep only general feedback, never the password.

    length: Number of characters in the submitted password.
    score: A simple score from 0 to 7.
    rating: A word describing the score.
    summary: A short explanation of the result.
    """
    length: int
    score: int
    rating: str
    summary: str


@dataclass
class State:
    """
    Information remembered while the website is running.

    checks: Past results. These are PasswordCheck objects, not passwords.
    latest_score: Score from the most recent check.
    latest_rating: Rating from the most recent check.
    checks_completed: How many checks have been completed.
    latest_suggestions: Suggestions from the most recent check.
    """
    checks: list[PasswordCheck]
    latest_score: int
    latest_rating: str
    checks_completed: int
    latest_suggestions: list[str]


def calculate_strength(password: str) -> int:
    """Return a simple score from 0 (weak) to 7 (very strong)."""
    score = 0

    # Length is important. Longer passwords are generally harder to guess.
    if len(password) >= 16:
        score += 3
    elif len(password) >= 12:
        score += 2
    elif len(password) >= 8:
        score += 1

    has_lower = False
    has_upper = False
    has_number = False
    has_symbol = False

    for character in password:
        if character.islower():
            has_lower = True
        if character.isupper():
            has_upper = True
        if character.isdigit():
            has_number = True
        if not character.isalnum() and not character.isspace():
            has_symbol = True

    if has_lower:
        score += 1
    if has_upper:
        score += 1
    if has_number:
        score += 1
    if has_symbol:
        score += 1

    # Common patterns can make a password easier to guess.
    lower_password = password.lower()
    if "password" in lower_password or "123" in lower_password:
        score -= 2
    if "qwerty" in lower_password or "admin" in lower_password:
        score -= 2

    if score < 0:
        score = 0
    if score > 7:
        score = 7

    return score
def get_rating(score: int) -> str:
    """Turn the numeric score into a word rating."""
    if score <= 2:
        return "Weak"
    elif score <= 4:
        return "Fair"
    elif score <= 6:
        return "Strong"
    else:
        return "Very strong"


def make_suggestions(password: str, focus: str, reused: bool) -> list[str]:
    """Create improvement ideas without repeating the submitted password."""
    suggestions = []

    if len(password) < 12:
        suggestions.append(
            "Make it longer. Try a memorable passphrase made from several "
            "unrelated words."
        )

    has_lower = False
    has_upper = False
    has_number = False
    has_symbol = False
    for character in password:
        if character.islower():
            has_lower = True
        if character.isupper():
            has_upper = True
        if character.isdigit():
            has_number = True
        if not character.isalnum() and not character.isspace():
            has_symbol = True

    if not has_upper or not has_lower:
        suggestions.append(
            "Use a mix of uppercase and lowercase letters if that is easy "
            "for you to remember."
        )

    if not has_number:
        suggestions.append(
            "Consider adding a number that is not an obvious date or "
            "repeated sequence."
        )

    if not has_symbol:
        suggestions.append(
            "Consider adding a symbol, if the website you use allows it."
        )

    lower_password = password.lower()
    if ("password" in lower_password or "123" in lower_password
            or "qwerty" in lower_password or "admin" in lower_password):
        suggestions.append(
            "Avoid common words and predictable sequences. Choose unrelated "
            "words instead."
        )
    if reused:
        suggestions.append(
            "Do not reuse passwords. Give every account its own password."
        )

    if focus == "memorable":
        suggestions.append(
            "For something easier to remember, create a longer passphrase "
            "from unrelated words."
        )
    elif focus == "extra":
        suggestions.append(
            "For extra protection, use a password manager to create and "
            "save a unique password for each account."
        )

    if not suggestions:
        suggestions.append(
            "This password meets the basic checks. Keep it unique to one "
            "account and do not share it."
        )

    return suggestions


# Small tests for the helper functions.
assert_equal(get_rating(1), "Weak")
assert_equal(get_rating(3), "Fair")
assert_equal(get_rating(5), "Strong")
assert_equal(get_rating(7), "Very strong")
assert_equal(calculate_strength("password123"), 1)

@route
def index(state: State) -> Page:
    """Home page with the password-checking form."""
    return Page(state, [
        Header("Password Strength Checker"),
        "Try the checker with an invented example password.",
        "Safety note: Do not enter a password you actually use. "
        "This form is not a secure password vault, and the checker "
        "does not test for data breaches.",
        Header("Check a sample password", 2),
        "Sample password:",
        TextBox("password", ""),
        "What kind of advice would help most?",
        SelectBox(
            "focus",
            ["balanced", "memorable", "extra"],
            "balanced"
        ),
        CheckBox("reused", False),
        "Check this box if you were thinking of reusing this password.",
        Button("Check Strength", "check_password"),
        Button("View Past Results", "history"),
        Button("Password Tips", "tips"),
        Button("About This Checker", "about")
    ])
@route
def check_password(
    state: State, password: str, focus: str, reused: bool = False
) -> Page:
    """Analyze the submitted password without saving the password itself."""
    if not password:
        return Page(state, [
            Header("Please enter a sample"),
            "The password box was empty. Enter an invented example to test.",
            Button("Go Back", "index")
        ])

    score = calculate_strength(password)
    rating = get_rating(score)
    suggestions = make_suggestions(password, focus, reused)

    if rating == "Weak":
        summary = "This sample would benefit from major improvements."
    elif rating == "Fair":
        summary = "This sample has some good features, but could be stronger."
    else:
        summary = "This sample did well on these basic checks."

    # Update five State fields. The password itself is never stored.
    state.latest_score = score
    state.latest_rating = rating
    state.latest_suggestions = suggestions
    state.checks_completed += 1
    state.checks.append(PasswordCheck(len(password), score, rating, summary))

    return results(state)
@route
def results(state: State) -> Page:
    """Show the most recent result and improvement ideas."""
    suggestions_display = []
    for suggestion in state.latest_suggestions:
        suggestions_display.append(suggestion)

    return Page(state, [
        Header("Your Result"),
        "Rating: " + state.latest_rating,
        "Score: " + str(state.latest_score) + " out of 7",
        "Checks completed: " + str(state.checks_completed),
        "The score is a simple classroom estimate, not a guarantee "
        "of how long a password would resist an attack.",
        Header("Ideas to improve", 2),
        BulletedList(suggestions_display),
        Button("Check Another Sample", "index"),
        Button("View Past Results", "history"),
        Button("Password Tips", "tips")
    ])


@route
def history(state: State) -> Page:
    """Show previous result summaries without displaying passwords."""
    content = [
        Header("Past Results"),
        "Number of checks: " + str(state.checks_completed)
    ]
    if not state.checks:
        content.append("There are no results yet. Try checking a sample.")
    else:
        # This loop meaningfully visits each PasswordCheck object.
        for number, check in enumerate(state.checks):
            content.append(
                str(number + 1) + ". " + check.rating
                + " — score " + str(check.score) + " out of 7"
                + " — length " + str(check.length)
                + " characters. " + check.summary
            )
    content.append(Button("Check a Password", "index"))
    content.append(Button("Clear Past Results", "clear_history"))
    return Page(state, content)


@route
def clear_history(state: State) -> Page:
    """Clear saved result summaries."""
    state.checks = []
    state.checks_completed = 0
    state.latest_score = 0
    state.latest_rating = "No result yet"
    state.latest_suggestions = []

    return Page(state, [
        Header("Past Results Cleared"),
        "The saved summaries have been cleared.",
        Button("Home", "index")
    ])


@route
def tips(state: State) -> Page:
    """Give general password advice."""
    return Page(state, [
        Header("Password Tips"),
        "1. Use a long password or passphrase.",
        "2. Use a different password for every account.",
        "3. Avoid names, birthdays, common phrases, and keyboard patterns.",
        "4. A password manager can help create and remember unique passwords.",
        "5. Turn on multi-factor authentication when it is available.",
        "6. Never share your password with someone else.",
        Button("Try the Checker", "index"),
        Button("About This Checker", "about")
    ])
@route
def about(state: State) -> Page:
    """Explain what the checker does and does not do."""
    return Page(state, [
        Header("About This Checker"),
        "This project uses a small set of rules to estimate password strength.",
        "It checks length, character variety, and a few predictable patterns.",
        "It does not connect to the internet, search breach databases, "
        "or guarantee that a password is safe.",
        "The app saves only the length, score, rating, and general feedback "
        "for each check. It does not add the password to the history.",
        "Use invented sample passwords for this class project.",
        Button("Home", "index"),
        Button("Password Tips", "tips")
    ])


@route
def privacy(state: State) -> Page:
    """A separate page describing the data kept by this demo."""
    return Page(state, [
        Header("Privacy Information"),
        "The app's State stores result summaries only.",
        "It does not intentionally save the password text.",
        "This is a learning project, not a production security service. "
        "Do not enter a real password.",
        Button("Home", "index")
    ])


start_server(State([], 0, "No result yet", 0, []))

