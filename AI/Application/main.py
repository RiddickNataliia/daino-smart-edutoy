from game_manager import GameManager

def main():
    gm = GameManager()
    modes = ["Learn Shapes", "Test Shapes", "Learn Colors", "Test Colors"]

    while True:
        print("\nSelect a game mode:")
        for idx, mode in enumerate(modes, 1):
            print(f"{idx}. {mode}")
        print("0. Exit")

        try:
            choice = int(input("Enter the number of the mode: "))
        except ValueError:
            print("Invalid input. Please enter a number.")
            continue

        if choice == 0:
            print("Exiting.")
            break
        elif 1 <= choice <= len(modes):
            selected_mode = modes[choice - 1]
            print(f"Starting '{selected_mode}' mode...")
            gm.switch_mode(selected_mode)
        else:
            print("Invalid selection. Please choose a valid number.")

if __name__ == "__main__":
    main()
