from my_c_wrapper import add

print("--- DEMO: USING THE INSTALLED PYTHON PACKAGE ---")
a, b = 150, 50

print(f"[Python] Calling add({a}, {b}) from the 'my_c_wrapper' package...")
result = add(a, b)

print(f"[Python] Result: {result}")
print("\n[Python] Script finished successfully.")
