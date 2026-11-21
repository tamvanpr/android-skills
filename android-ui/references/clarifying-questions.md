# When to ask

Asking is mandatory, not optional, when any of the conditions below holds. The goal is to prevent building the wrong thing and wasting the user's time.

## Trigger conditions

1. **Platform unclear.** It is not visible whether the project uses Jetpack Compose, XML Views, or a mix. Check `build.gradle(.kts)` first (`buildFeatures { compose = true }`). If still unclear, ask.
2. **Screen purpose unclear.** "Make a nice page" without knowing what it does.
3. **Conflicting visual references.** E.g. the user asks for minimalism but attaches a dense, colorful screenshot.
4. **Real data unknown.** What is in the list, how many items, maximum text length, with images or not.
5. **Large scope.** The request touches more than 3 screens, or changes the global theme.
6. **Brand color mentioned but not given.** The user says "my app's color" without values.
7. **A choice that changes a lot of code.** E.g. changing the font, changing navigation, changing the state pattern.
8. **Language and content.** UI text in English or another language, or both (needs separate `strings.xml`).

## When not to ask

- Small, clear changes (adjust padding, tidy one button).
- The answer can be read from the existing code. Read the code before asking.
- Questions whose answer has a safe default. Take the default, state it at the top of the report, and proceed.

## Question format

- At most 4 questions at once.
- One question, one thing.
- Give 2–4 options and mark the recommendation.
- Write in the language the user is using.
- Do not ask what the user already answered in a previous message.

## Template

```
Before starting, a few things to confirm:

1. Does this project use Compose or XML Views?
   a. Compose (recommended — I see compose = true in build.gradle)
   b. XML Views
   c. Mixed

2. Which accent color?
   a. Keep the current color (#xxxxxx)
   b. Suggest one cool-neutral accent
   c. I'll provide my own hex value

3. How many items does this screen usually show, and are there images?
   (Affects the choice of list, card, or plain rows)
```

## After the user answers

Summarize the decisions in one short block ("Decision: Compose, accent steel-blue #3B5BA9, plain rows without cards"), then proceed. Do not re-ask the same things.

## If the user does not reply or is unreachable

Take the most conservative assumptions, write the assumption list at the top of the report, and make the changes easy to swap (tokens, not scattered values).
