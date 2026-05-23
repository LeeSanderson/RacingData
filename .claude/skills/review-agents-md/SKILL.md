---
name: review-agents-md
description: Review the AGENTS.md file to ensure all rules are up-to-date, removing any redundant or overly vague rules and updating deterministic guardrails as needed.
---

Please review the current AGENTS.md file. Remove any redundant or overly vague rules that are no longer necessary or that the latest model versions handle automatically.

Specifically ensure that any deterministic guardrails are updated to ensure they continue to be effective in guiding the model's behavior.

If a conversation has just completed successfully, review our agreed outcomes. If a new constraint, preference, or architectural decision was made, reflect on it and propose an update to the rules in agents.md. 

Always wait for my approval before saving.

## Best practices for reviewing AGENTS.md:

- Put commands early: Put relevant executable commands in an early section: npm test, npm run build, pytest -v. Include flags and options, not just tool names. Your agent will reference these often.

- Code examples over explanations: One real code snippet showing your style beats three paragraphs describing it. Show what good output looks like.

- Set clear boundaries: Tell AI what it should never touch (e.g., secrets, vendor directories, production configs, or specific folders). “Never commit secrets” was the most common helpful constraint.

- Be specific about your stack: Say “React 18 with TypeScript, Vite, and Tailwind CSS” not “React project.” Include versions and key dependencies.

- Cover six core areas: Hitting these areas puts you in the top tier: commands, testing, project structure, code style, git workflow, and boundaries. 

- Aim for a maximum of 150 lines of instructions: Long enough to be specific, but short enough to be read and followed. If you need more, consider using progressive disclosure and link to separate files for detailed guidelines thereby keeping AGENTS.md focused on the most critical rules and examples.

- Do not reference in flight work in the current issues/PRD.md or issues/NNN-some-issue.md files. AGENTS.md should contain timeless rules and examples that are not tied to specific in-flight work. Avoid mentioning specific issue numbers, PRDs, or temporary architectural decisions that may change frequently. Focus on general principles and practices that will remain relevant over time.
