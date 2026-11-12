import pandas as pd

print("Reading local parquet file...")

# ঠিক যে নামে ফাইলটি আছে, হুবহু সেই নাম দেওয়া হলো
df = pd.read_parquet("train-00000-of-00001.parquet")

# CSV ফাইলে কনভার্ট করে সেভ করা
df.to_csv("bipod_erao_dataset.csv", index=False)

print("Successfully converted and saved as bipod_erao_dataset.csv!")