# Best Practices and Conversation Conventions

This document describes the standards for collaborative work, code review, and communication for this project, especially with a focus on Python and onboarding new contributors. It aims to ensure clarity, consistency, transparency, and adherence to effective Python practices.

## Code Review and Style
- **Code Review Requests:**
  - Always check for both correctness and compliance with the [PEP 8](https://peps.python.org/pep-0008/) Python style guide.
  - Provide feedback on logic, clarity, maintainability, and naming conventions.
  - Ensure code uses consistent indentation, docstrings, module-level documentation, and appropriate comments, including a module banner indicating AI involvement (see below).
  - Look for appropriate use of `logging.error` for error states and `logging.info` for process feedback, especially in functions and event handlers.
  - Pay extra attention to Pythonic idioms. If the code takes a C++-like approach where a Pythonic method exists (e.g., manual loops versus comprehensions or built-ins), recommend the native Python approach.

## Code Generation
- **Explicit Code Generation Policy:**
  - **Never provide code snippets, suggestions, or file edit recommendations unless the user has explicitly requested them.**
  - For code reviews, guidance, or questions, always respond with commentary, reasoning, or recommendations—never with code—unless a code or example request is explicitly given.
  - If code is requested, provide only what is directly relevant, with concise and clear commenting and documentation.

## Communication and Clarification
- **Clarify User Intent:**
  - If a request is ambiguous, seek clarification rather than assuming intent.
  - Always confirm coding style, desired formats, or conventions when not already established in this document or conversation.
- **Learning-Oriented Feedback:**
  - The user may have a background in other languages (especially C++); be proactive in gently pointing out where Python idioms or standard library features may improve or simplify the logic.

## Documentation and Explanations
- **Documentation Standards:**
  - All *.py modules must begin with the following notice:
    ```
    """
    This script was created with the help of AI.
    """
    ```
  - Each function, method, and class should include a clear docstring describing its purpose, parameters, and return values.
  - When discussing best practices without generating code, thoroughly explain reasoning for each recommendation.
  - When appropriate, provide alternative Pythonic solutions (in prose), especially for state management or logic optimization.

## Project-Specific Conventions

- **State Management:**
  - Avoid using global variables for managing persistent or shared program state (such as modes, button state, or mappings).
  - Prefer encapsulating program state within classes (e.g., a `JoystickController` that holds mapping mode, button states, and related logic as instance variables and methods).
  - Event-handling functions and persistent logic should be included as class methods to keep state and behavior encapsulated, rather than as loose functions operating on global state.

- **General Python Style:**
  - Always review for PEP 8 compliance.
  - Use `lowercase_with_underscores` for function and variable names unless another convention is justified (e.g., platform-specific names).
  - Prefer explicit exception types in `try/except` blocks (e.g., `except ValueError:`).
  - For string or path manipulations, use Python’s `split`/`join` idioms and consider stripping leading/trailing slashes for robustness.


---

**Updating This Document:**  
Whenever a new convention, workflow adjustment, or preference is established—whether in code style, communication, or documentation—add it to this document for the benefit of future collaborators and yourself.