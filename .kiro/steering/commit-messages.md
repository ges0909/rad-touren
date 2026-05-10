---
inclusion: always
---

<!------------------------------------------------------------------------------------
   Add rules to this file or a short description and have Kiro refine them for you.

   Learn about inclusion modes: https://kiro.dev/docs/steering/#inclusion-modes
------------------------------------------------------------------------------------->

# Commit Messages

Use [Conventional Commits](https://www.conventionalcommits.org/) format. Language: **English**.

## Format

```
<type>(<optional scope>): <short summary>

<optional body>
```

## Rules

- **Subject line**: imperative mood, lowercase, no period, max 70 chars
- **Types**: `feat`, `fix`, `docs`, `refactor`, `chore`, `style`, `test`, `ci`
- **Scope**: optional, e.g. `feat(routing):`, `docs(readme):`
- **Body**: bullet list of changes, each line starting with `-`
- Keep body lines under 80 chars
- Reference tour names or file names when relevant
