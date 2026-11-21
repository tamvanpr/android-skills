# Compose patterns (and XML equivalents)

## File structure

```
ui/
  theme/Color.kt  Type.kt  Theme.kt  Spacing.kt
  components/     (small reusable components)
  screen/<name>/  <Name>Screen.kt  <Name>ViewModel.kt  <Name>UiState.kt
```

Rule: one screen composable receives `state` and `onEvent` (state hoisting). No repository or network access inside composables.

## Screen skeleton

```kotlin
@Composable
fun NotesScreen(
    state: NotesUiState,
    onEvent: (NotesEvent) -> Unit,
    modifier: Modifier = Modifier,
) {
    Scaffold(
        modifier = modifier,
        topBar = { NotesTopBar(onSearch = { onEvent(NotesEvent.OpenSearch) }) },
        containerColor = MaterialTheme.colorScheme.background,
    ) { inner ->
        when (state) {
            NotesUiState.Loading -> LoadingBox(Modifier.padding(inner))
            is NotesUiState.Error -> ErrorBox(state.message, { onEvent(NotesEvent.Retry) }, Modifier.padding(inner))
            is NotesUiState.Content ->
                if (state.items.isEmpty()) EmptyBox("No notes yet", Modifier.padding(inner))
                else NotesList(state.items, { onEvent(NotesEvent.Open(it)) }, Modifier.padding(inner))
        }
    }
}
```

## Plain list rows (no cards)

```kotlin
@Composable
fun NoteRow(title: String, subtitle: String, onClick: () -> Unit) {
    Column(
        Modifier
            .fillMaxWidth()
            .clickable(onClick = onClick)
            .heightIn(min = 56.dp)
            .padding(horizontal = Space.lg, vertical = Space.md),
        verticalArrangement = Arrangement.spacedBy(Space.xs),
    ) {
        Text(title, style = MaterialTheme.typography.titleMedium, maxLines = 1, overflow = TextOverflow.Ellipsis)
        Text(subtitle, style = MaterialTheme.typography.bodyMedium,
             color = MaterialTheme.colorScheme.onSurfaceVariant, maxLines = 2, overflow = TextOverflow.Ellipsis)
    }
}
```

Divider: `HorizontalDivider(color = MaterialTheme.colorScheme.outlineVariant)` with a 16dp inset (Material3 1.2+; older versions call it `Divider`).

## Buttons

- Primary action: `Button` (one per screen).
- Secondary: `OutlinedButton` or `TextButton`.
- Minimum height 48dp. Full width only for the primary action in a form or bottom bar.

## Edge-to-edge and insets

```kotlin
// Activity
enableEdgeToEdge()
// Scaffold already applies inner padding. For manual content:
Modifier.windowInsetsPadding(WindowInsets.safeDrawing)
```

Use `imePadding()` for screens with fields.

## Required previews

```kotlin
@Preview(name = "Light") @Composable private fun P1() = AppTheme(darkTheme = false) { NotesScreen(sampleState, {}) }
@Preview(name = "Dark", uiMode = UI_MODE_NIGHT_YES) @Composable private fun P2() = AppTheme(darkTheme = true) { NotesScreen(sampleState, {}) }
@Preview(name = "Large font", fontScale = 1.5f) @Composable private fun P3() = AppTheme { NotesScreen(sampleState, {}) }
```

## Accessibility

```kotlin
Icon(Icons.Outlined.Delete, contentDescription = "Delete note")
Modifier.semantics { heading() }          // section heading
Modifier.clearAndSetSemantics { }         // decorative
Modifier.minimumInteractiveComponentSize() // 48dp target
```

## Basic performance

- `remember` for expensive objects, `derivedStateOf` for derived state.
- Stable lambda parameters. Avoid creating new objects on every recomposition inside a list.
- `LazyColumn(key = { it.id }, contentType = { ... })`.
- Images: Coil with fixed sizes so they do not jump.

## XML Views equivalents

| Compose | XML |
|---|---|
| `MaterialTheme.colorScheme.*` | Theme attributes `?attr/colorSurface`, `?attr/colorOnSurface` |
| `Space.lg` | `@dimen/space_lg` (in `dimens.xml`) |
| `typography.titleMedium` | `?attr/textAppearanceTitleMedium` |
| `Scaffold` | `CoordinatorLayout` + `MaterialToolbar` |
| `LazyColumn` | `RecyclerView` + `ListAdapter` + `DiffUtil` |

No hex colors in XML layouts. Define them in `colors.xml` and `values-night/colors.xml`, reference them via theme attributes.

## Do not

- `Color(0xFF...)` inside screens.
- Ad-hoc `fontSize = 15.sp`.
- `Modifier.padding(13.dp)` off-scale numbers.
- Calling `viewModel()` inside a small reusable component.
- Hiding important content behind gestures without an alternative.
