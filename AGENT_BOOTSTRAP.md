# REPL Toolkit - Agent Bootstrap

**Purpose**: Build interactive command-line applications with unified action system and async support
**Type**: Library
**Language**: Python 3.8+
**Repository**: https://github.com/bassmanitram/repl-toolkit

---

## What You Need to Know

**This is**: A REPL framework that provides terminal UI, keyboard shortcuts, command routing, and both interactive and headless (batch) modes. Applications implement the `AsyncBackend` or `CancellableBackend` protocol to handle user input, and the library handles all the terminal UI complexity (input editing, history, completion, etc.). Supports explicit cooperative cancellation protocol and automatic prompt maintenance in interactive mode.

**Architecture in one sentence**: Protocol-based framework where user's backend implements `handle_input()` and the library wraps it with either AsyncREPL (interactive UI) or HeadlessREPL (stdin processing).

**The ONE constraint that must not be violated**: Backend must implement `AsyncBackend.handle_input()` or `CancellableBackend` protocol - this is the contract between library and application.

---

## Mental Model

- This is a **UI framework**, not a chatbot - it provides the terminal interface, applications provide the logic
- **Action system** unifies commands (`/help`) and keyboard shortcuts (`F1`) - same handler serves both
- **Late binding** - REPL can be initialized before backend exists (useful for resource initialization)
- **Two modes**: Interactive (prompt-toolkit UI) and Headless (stdin line-by-line) share action system
- **Protocol-based** - loose coupling via Python protocols, easy to test with mocks
- **Cancellation** - Explicit `CancellableBackend` protocol for type-safe cancellation support

---

## Codebase Organization

```
repl_toolkit/
├── async_repl.py       # Interactive REPL with prompt-toolkit UI
├── headless_repl.py    # Stdin batch processing mode
├── ptypes.py           # Protocol definitions: AsyncBackend, CancellableBackend, ActionHandler, Completer
├── actions/            # Action system: Action dataclass, ActionRegistry, ActionContext
├── completion/         # Tab completion: prefix, shell expansion
├── formatting.py       # Auto-formatting for JSON/YAML/etc
├── images.py           # Clipboard image handling
└── tests/              # Test suite mirroring package structure
```

**Navigation Guide**:

| When you need to... | Start here | Why |
|---------------------|------------|-----|
| Add new built-in command | `async_repl.py` → `_create_builtin_actions()` | Where built-ins are registered |
| Modify action execution | `actions/registry.py` → `execute_action()` | Central dispatch point |
| Change input handling | `async_repl.py` → `_process_input()` | Where Enter/Alt+Enter logic lives |
| Add completion type | `completion/` → create new module | Implement Completer protocol |
| Fix headless mode issue | `headless_repl.py` → `run()` | Stdin processing logic |
| Understand cancellation | `async_repl.py` → `_cancellation_context()` | Async context manager for cancel handling |

**Entry points**:
- Interactive: `AsyncREPL.run(backend)` - Starts prompt-toolkit session
- Headless: `run_headless_mode(backend)` - Processes stdin until EOF
- Tests: `tests/` - Protocol-based mocking makes testing easy

---

## Critical Invariants

These rules MUST be maintained:

1. **Backend protocol compliance**: Backend must implement `async def handle_input(user_input: str, images: Optional[Dict] = None, **kwargs) -> bool`
   - **Why**: This is the contract - REPL calls this method for every input
   - **Breaks if violated**: Type errors at runtime, REPL can't process input
   - **Enforced by**: Python protocols (mypy checks), runtime will fail immediately
   - **Note**: For cancellation support, implement `CancellableBackend` which adds `cancel()` method

2. **Action names must be unique**: ActionRegistry enforces one action per name
   - **Why**: Name is used for lookup when executing, duplicates cause ambiguity
   - **Breaks if violated**: Later registration overwrites earlier (silent failure mode)
   - **Enforced by**: ActionRegistry raises error on duplicate registration

3. **Async consistency**: All backend methods and REPL operations are async
   - **Why**: Enables non-blocking I/O for API calls, database queries
   - **Breaks if violated**: Sync code blocks event loop, UI freezes
   - **Enforced by**: Protocol signatures, type checking, runtime event loop errors

---

## Non-Obvious Behaviors & Gotchas

Things that surprise people:

1. **Enter vs Alt+Enter behavior changed in v2.0.2**:
   - **Why it's this way**: Commands execute immediately (better UX), Alt+Enter sends normal text
   - **Common mistake**: Expecting Enter to accumulate text
   - **Correct approach**: Type text, press Enter for commands; Alt+Enter to send text to backend without command execution

2. **Logging is silent by default (v2.0.0+)**:
   - **Why**: Library shouldn't pollute application output
   - **Watch out for**: Errors are logged but not displayed - applications must configure logging
   - **Correct approach**: Set up logging in your app: `logging.basicConfig(level=logging.ERROR)`

3. **Late backend binding means REPL can start before backend ready**:
   - **Why**: Useful for resources that need initialization (database connections, API clients)
   - **Pattern**: `repl = AsyncREPL()` then later `await repl.run(backend_instance)`
   - **Gotcha**: Actions can't access backend in `__init__`, only during execution via `ActionContext`

4. **Image placeholders are opaque to backend**:
   - **Why**: Backend receives `{{image:img_001}}` string, not actual image data
   - **Watch out for**: If you want image data, you must look it up in the `images` dict parameter
   - **Correct approach**: Use `parse_image_references()` and `images` dict together

5. **CancellableBackend vs AsyncBackend (v2.2.0+)**:
   - **Why**: Type-safe cancellation support via explicit protocol inheritance
   - **Pattern**: Implement `CancellableBackend` if you need cancellation, `AsyncBackend` otherwise
   - **Gotcha**: REPL checks `isinstance(backend, CancellableBackend)` not `hasattr(backend, 'cancel')`
   - **Correct approach**: Inherit protocol explicitly in type annotations

---

## Architecture Decisions

**Why protocol-based instead of inheritance?**
- **Trade-off**: Protocols are more flexible (duck typing) but less discoverable than base classes
- **Alternative considered**: `class MyBackend(REPLBackend)` base class approach
- **Why protocols win**: Users don't need to import anything, just match the signature. Easier testing (mock any object with matching methods).

**Why unified action system for commands and shortcuts?**
- **Trade-off**: Single Action dataclass is more complex but reduces code duplication
- **Alternative considered**: Separate CommandRegistry and ShortcutRegistry
- **Implications**: One registration point, one handler serves both triggers, simpler for users

**Why both AsyncREPL and HeadlessREPL?**
- **Trade-off**: Two implementations to maintain but enables different use cases
- **Alternative considered**: Single REPL with mode parameter
- **Why separate wins**: Different dependencies (prompt-toolkit not needed for headless), different testing strategies, cleaner code

**Why ActionContext instead of passing args directly to handlers?**
- **Trade-off**: Extra dataclass but enables future extension without breaking handlers
- **Alternative considered**: `handler(backend, args, trigger_method)` function signature
- **Why context wins**: Can add new metadata (user_id, session_id, etc.) without breaking existing handlers

**Why explicit CancellableBackend protocol (v2.2.0)?**
- **Trade-off**: Two protocols vs optional method with `hasattr()` check
- **Alternative considered**: Keep `hasattr(backend, 'cancel')` pattern from v2.1.0
- **Why explicit wins**: Type safety (mypy catches missing method), clear contract, better documentation, proper inheritance chain

---

## Key Patterns & Abstractions

**Pattern 1: Protocol-Based Interface**
- **Used for**: Backend, CancellableBackend, ActionHandler, Completer - all major extension points
- **Structure**: Define protocol with required methods, users implement matching signature
- **Examples in code**: `AsyncBackend` and `CancellableBackend` in `ptypes.py` - no inheritance required, just matching method

**Pattern 2: Registry Pattern**
- **Used for**: Action registration and lookup
- **Why not direct dict**: Registry validates (no duplicates), provides helper methods (list by category), encapsulates lookup logic
- **Structure**: `ActionRegistry` holds `Dict[str, Action]`, provides `register_action()` and `execute_action()`

**Pattern 3: Context Object**
- **Used for**: Passing rich metadata to action handlers
- **Structure**: `ActionContext` bundles registry, backend, args, trigger method
- **Why**: Future-proof (can add fields without breaking handlers), self-documenting (ctx.backend vs positional arg)

**Pattern 4: Async Context Manager for Cancellation (v2.2.0)**
- **Used for**: Encapsulating cancellation setup, execution, and cleanup
- **Structure**: `_cancellation_context()` yields cancel_future and trigger_cancel callback
- **Why**: Separation of concerns, guaranteed cleanup, easier testing, reduced duplication

**Anti-pattern to avoid: Blocking I/O in backend**
- **Don't do this**: `def handle_input(self, text: str)` (sync function) with `time.sleep()` or blocking HTTP calls
- **Why it fails**: Blocks event loop, freezes UI, defeats purpose of async
- **Instead**: `async def handle_input()` with `await asyncio.sleep()` or `await aiohttp.get()`

---

## State & Data Flow

**State management**:
- **Persistent state**: None (applications handle their own persistence)
- **Runtime state**: ActionRegistry (actions), REPL session state (history, completion cache), backend state (application-specific)
- **No state here**: Action handlers are stateless functions (access state via `context.backend`)

**Data flow**:
```
User input → prompt-toolkit → AsyncREPL._process_input() → ActionRegistry.execute_action()
                                                         ↓ (if action)           ↓ (if text)
                                                  Action.handler()         Backend.handle_input()
                                                         ↓                           ↓
                                                  Prints output          Returns bool (continue?)
```

**Cancellation flow (v2.2.0)**:
```
Ctrl+C/Alt+C → cancel_future.set_result() → isinstance(backend, CancellableBackend)?
                                              ↓ yes                    ↓ no
                                         backend.cancel()         (skip)
                                              ↓                        ↓
                                         backend_task.cancel() ← ← ← ←
```

**Critical paths**:
- Input processing must distinguish commands (starts with `/`) from text - this routing is core to UX
- Actions must be able to access backend via `ActionContext` - breaks if context doesn't carry backend reference
- Backend's return value controls REPL continuation - `False` means exit, `True` means continue
- Cancellation context must cleanup properly in all cases (success, cancel, exception)

---

## Integration Points

**This project depends on** (upstream):
- **prompt-toolkit**: Terminal UI framework, tightly coupled (core dependency for interactive mode)
- **pyclip**: Clipboard access, loosely coupled (optional, paste action degrades gracefully)

**Projects that depend on this** (downstream):
- **yacba**: Uses AsyncREPL for interactive chatbot UI
- **Your CLI applications**: Direct dependency for building interactive terminals

**Related projects** (siblings):
- **strands-agent-factory**: Complementary (agent creation) vs repl-toolkit (UI framework)
- **dataclass-args**: Related domain (CLI interfaces), different approach (arguments vs interactive)

---

## Configuration Philosophy

**What's configurable**: Actions (add/remove/modify), completion strategy, backend implementation, input processing behavior, cancellation behavior (via protocol implementation)

**What's hardcoded**:
- Input key bindings (Enter, Alt+Enter, F-keys) - defined in `async_repl.py`
- Built-in actions (help, exit, paste) - always available
- Protocol signatures - breaking these breaks compatibility

**The trap**: Trying to configure key bindings externally - currently hardcoded in `_create_key_bindings()`. If you need custom bindings, you must modify this function directly.

---

## Testing Strategy

**What we test**:
- **Action system**: Registration, execution, context passing, duplicate detection
- **Input processing**: Command detection, text passthrough, multiline handling
- **Completion**: Prefix matching, shell expansion, mid-word triggering
- **Image handling**: Clipboard extraction, placeholder generation, format detection
- **Cancellation**: Both cancellable and non-cancellable backends, all trigger paths

**What we don't test**:
- **prompt-toolkit internals**: Trust the library works
- **Terminal rendering**: Too complex to test reliably
- **Actual user interaction**: Manual testing only

**Test organization**: Tests mirror package structure (test_async_repl.py, test_actions.py, etc.). Heavy use of mocks for backend (MockBackend pattern).

**Mocking strategy**: Mock backends (simple class with list to track calls), mock clipboard (monkeypatch for tests), real action execution (no mocking of action system internals).

---

## Common Problems & Diagnostic Paths

**Symptom**: Commands not executing (e.g., `/help` does nothing)
- **Most likely cause**: Action not registered or name mismatch
- **Check**: Print `action_registry.list_actions()` to see what's registered
- **Fix**: Register action with correct name, ensure handler doesn't raise exception

**Symptom**: UI freezes when processing input
- **Likely cause**: Backend is doing blocking I/O (not using async)
- **Diagnostic**: Add print statement at start of `handle_input()` - if it prints but doesn't return, backend is blocking
- **Solution approach**: Convert blocking calls to async (use aiohttp instead of requests, asyncio.sleep instead of time.sleep)

**Symptom**: Alt+Enter doesn't send text to backend
- **Why it happens**: Application might be registering action that intercepts input
- **Diagnostic**: Check if custom actions are catching the input before backend
- **Prevention**: Ensure custom commands have `/` prefix, don't intercept plain text

**Symptom**: Tests pass individually but fail when run together
- **Why it happens**: Shared state in action registry or backend
- **Diagnostic**: Run tests with `pytest -v` to see which test fails when
- **Solution**: Use fresh ActionRegistry per test, reset backend state in fixtures

**Symptom**: Cancellation not working (v2.2.0+)
- **Why it happens**: Backend doesn't implement `CancellableBackend` protocol
- **Diagnostic**: Check `isinstance(backend, CancellableBackend)` - should be True
- **Solution**: Implement both `handle_input()` and `cancel()`, ensure proper type annotations

---

## Modification Patterns

**To add new built-in action**:
1. Add action creation in `async_repl.py` → `_create_builtin_actions()`
2. Implement handler function (can be nested function or module-level)
3. Register with ActionRegistry: `registry.register_action(Action(...))`
4. Add tests in `tests/test_async_repl.py` or `tests/test_actions.py`

**To add new completion strategy**:
1. Create module in `completion/my_completer.py`
2. Implement `Completer` protocol: `def get_completions(self, text: str, cursor_pos: int) -> List[str]`
3. Add tests in `tests/test_completion.py`
4. Document in `completion/README.md` and main README.md

**To modify input key behavior** (e.g., change Enter behavior):
1. Update `async_repl.py` → `_create_key_bindings()` function
2. Be aware: This affects all users, consider making it configurable via AsyncREPL constructor
3. Add tests to verify new behavior doesn't break existing use cases
4. Document as breaking change in CHANGELOG.md (likely requires major version bump)

**To implement cancellable backend**:
1. Import `CancellableBackend` from `repl_toolkit`
2. Implement both `handle_input()` and `cancel()` methods
3. Set internal cancellation flag in `cancel()`, check in `handle_input()` loops
4. Reset flag at start of each `handle_input()` call
5. Type annotation: `class MyBackend(CancellableBackend):` or use structural typing

---

## New in v2.2.0

**Explicit CancellableBackend Protocol**: Cancellation support moved from optional `cancel()` method to formal protocol inheritance. Backends implement `CancellableBackend` instead of `AsyncBackend` for type-safe cancellation support. Uses `isinstance()` check instead of `hasattr()`.

**cancel_callback Parameter**: Backends receive `cancel_callback` kwarg in `handle_input()`. Thread-safe function for tools/subprocesses to signal cancellation back to REPL.

**Major Refactoring**: `async_repl.py` reorganized with async context manager for cancellation (`_cancellation_context()`), separated helper methods, removed 200+ lines of debug logging. Better type annotations, improved mypy compliance.

**Implementation notes**:
- Cancellation uses `isinstance(backend, CancellableBackend)` not `hasattr(backend, 'cancel')`
- Context manager guarantees cleanup even on exception
- Method renames: `_should_exit()` → `_is_exit_command()`
- Type fixes: `action_registry: Optional[ActionRegistry]` (was ActionHandler)

---

## When to Update This Document

Update this bootstrap when:
- [x] Core architecture changes (e.g., remove protocol-based approach, add new REPL mode)
- [x] Action system fundamentally changes (e.g., remove unified command/shortcut pattern)
- [x] New major integration added (e.g., async context managers for backends)
- [x] Testing strategy shifts (e.g., add property-based testing)
- [x] Protocol definitions change (e.g., new CancellableBackend protocol in v2.2.0)

Don't update for:
- ❌ New built-in actions added (extend existing pattern)
- ❌ New completion strategies (extend existing protocol)
- ❌ Bug fixes in action execution or input processing
- ❌ UI improvements or prompt-toolkit integration changes
- ❌ Documentation/README updates

---

**Last Updated**: 2025-02-10
**Last Architectural Change**: v2.2.0 - Explicit CancellableBackend protocol, async context manager for cancellation, major refactoring
