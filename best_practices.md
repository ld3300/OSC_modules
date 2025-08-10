# Best Practices and Conversation Conventions

This document outlines the conventions and expectations established for collaborative work and conversation, especially as applied to Python projects and code review. These guidelines are intended to ensure clarity, consistency, and efficiency in future chats or when onboarding new collaborators.

## Code Review and Style
- **Code Review Requests:**
  - When a code review is requested, always check for both correctness and PEP8/Python style guide compliance.
  - Provide feedback on logic, clarity, and maintainability, as well as adherence to naming conventions, indentation, and documentation standards.
  - Ensure logging.error messages are present where appropriate, and that functions and events use logging.info to provide feedback.

## Code Generation
- **Explicit Code Generation:**
  - Do not generate or output code unless explicitly requested by the user.
  - When code is requested, provide only the code relevant to the request, with minimal extraneous explanation unless clarification is needed.

## Communication and Clarification
- **Clarify User Intent:**
  - If a request is ambiguous, ask for clarification before proceeding.
  - Confirm the user’s preferences for code style, output format, or other conventions if not already established.

## Documentation and Explanations
- **Reasoning and Alternatives:**
  - When discussing code manipulation or best practices, explain the reasoning behind recommendations.
  - Offer alternative approaches when appropriate, especially if there are multiple valid solutions.

## Project-Specific Conventions

- All modules should include, at the top:

    """
    This script was created with the help of AI.
    """
- **Document Evolving Practices:**
  - As new conventions or preferences are established during a project or conversation, add them to this document for future reference.

## Example Conventions from This Project
- Always check for PEP8 compliance during code review.
- Do not output or generate code unless the user specifically asks for it.
- When reviewing code, provide both correctness and style feedback.
- When manipulating path-like strings, use split/join for segment replacement and consider stripping leading/trailing slashes for robustness.
- Use explicit exception types in try/except blocks (e.g., `except ValueError:`).
- Use lowercase_with_underscores for function and variable names, unless a specific naming convention is required for clarity (e.g., manufacturer names).

---

This document should be updated as new best practices and conventions are established.