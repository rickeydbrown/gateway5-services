import sys

print("\n")
print("What we got in stdin")
# Read from stdin
for line in sys.stdin:
    print(line.strip())

print("\nWhat we got in cli args\n")
print(sys.argv)
