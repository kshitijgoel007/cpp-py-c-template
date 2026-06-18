from my_c_wrapper import Accumulator, add

print("--- DEMO: USING THE PYTHON PACKAGE ---")
a, b = 150, 50

print(f"[Python] Calling add({a}, {b}) from the 'my_c_wrapper' package...")
result = add(a, b)

print(f"[Python] Result: {result}")
with Accumulator(10) as accumulator:
    accumulator.add(5)
    accumulator.add(-2)
    print(f"[Python] Accumulator total: {accumulator.total}")
print("\n[Python] Script finished successfully.")
