import os
import sys
import tempfile

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import database

database.DB_PATH = os.path.join(tempfile.mkdtemp(), "test_cafe.db")     # test ka apna database
database.init_db()

DATE = "2026-12-25"

# 1) khali database me jagah honi chahiye
print("1)", database.check_availability(DATE, "dinner", 4))
assert database.check_availability(DATE, "dinner", 4)["available"]

# 2) booking ho gayi, seats ghatni chahiye
print("2)", database.create_booking(DATE, "dinner", 4, "Ravi"))
assert database.check_availability(DATE, "dinner", 1)["seats_left"] == 26

# 3) dinner ki saari seats bharo (26 aur), phir ek aur booking nahi honi chahiye
database.create_booking(DATE, "dinner", 26, "Group")
r = database.create_booking(DATE, "dinner", 1, "Late guest")
print("3)", r)
assert r["status"] == "not_available"

# 4) doosra meal / doosri date alag hai
assert database.check_availability(DATE, "lunch", 4)["available"]
assert database.check_availability("2026-12-26", "dinner", 4)["available"]

print("\nAll tests pass")