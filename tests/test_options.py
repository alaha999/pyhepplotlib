import pyplotlib.pyplot as plt
from pyplotlib.help import discover, GROUPS


def show_menu():
    functions = discover()

    print("\n" + "=" * 60)
    print("                 pyhepplotlib API")
    print("=" * 60)

    shown = set()

    for group, names in GROUPS.items():
        available = [name for name in names if name in functions]
        if not available: continue

        print(f"\n  {group}")
        print("  " + "-" * 45)
        print("    " + "    ".join(available))
        shown.update(available)

    remaining = sorted(set(functions) - shown)
    if remaining:
        print("\n  OTHER")
        print("  " + "-" * 45)
        print("    " + "    ".join(remaining))

    print("\n" + "=" * 60)
    print("Type a function name to explore its options.")
    print("Commands: list, exit")
    print("=" * 60)


def main():
    show_menu()

    while True:
        try:
            command = input("\n>>> ").strip()
        except (KeyboardInterrupt, EOFError):
            print("\nGoodbye!")
            break

        if not command: continue

        if command.lower() in ("exit", "quit", "q"):
            print("Goodbye!")
            break

        if command.lower() in ("list", "help", "all"):
            show_menu()
            continue

        if command.startswith("plt."):
            command = command[4:]

        command = command.removesuffix("()")

        functions = discover()

        if command not in functions:
            print(f"Unknown function: {command}")
            print("Type 'list' to see available functions.")
            continue

        plt.options(command)


if __name__ == "__main__":
    main()
