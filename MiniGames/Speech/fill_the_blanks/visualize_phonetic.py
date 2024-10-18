"""
This script is used to test the dynamic phonetic comparison function and visualize the results. It is useful to set a good threshold for the function. Since the choice can be a bit arbitrary, having a lot of example cases can help to see if we need to adjust.
"""
import matplotlib.pyplot as plt
import seaborn as sns
import numpy as np
from phonetic_comparison import dynamic_phonetic_comparision

# Example usage:
print(dynamic_phonetic_comparision("dog", "doug"), "\n")        # True
print(dynamic_phonetic_comparision("fox", "folks"), "\n")       # True
print(dynamic_phonetic_comparision("dog", "phone"), "\n")       # False
print(dynamic_phonetic_comparision("adventure", "inventor"), "\n") # False
# Example usage:
test_cases = [
    # Obviously TRUE (phonetic similarities, minor differences)
    ("dog", "doug"),      # TRUE
    ("fox", "folks"),     # TRUE
    ("cat", "kat"),       # TRUE
    ("mouse", "mousse"),  # TRUE
    ("read", "reed"),     # TRUE
    ("phone", "fone"),    # TRUE
    ("write", "rite"),    # TRUE
    ("bat", "batt"),      # TRUE
    ("peace", "piece"),   # TRUE
    ("car", "kar"),       # TRUE
    ("their", "there"),   # TRUE
    ("sun", "son"),       # TRUE
    ("tie", "tai"),       # TRUE
    ("flow", "flou"),     # TRUE
    ("sell", "cell"),     # TRUE

    # Obviously FALSE (different words, not close phonetically)
    ("dog", "cat"),       # FALSE
    ("apple", "orange"),  # FALSE
    ("table", "chair"),   # FALSE
    ("book", "phone"),    # FALSE
    ("train", "plane"),   # FALSE
    ("ship", "car"),      # FALSE
    ("jump", "run"),      # FALSE
    ("banana", "monkey"), # FALSE
    ("moon", "sun"),      # FALSE
    ("river", "mountain"),# FALSE
    ("grass", "stone"),   # FALSE
    ("computer", "paper"),# FALSE
    ("laptop", "bottle"), # FALSE
    ("shark", "fish"),    # FALSE
    ("sugar", "salt"),    # FALSE

    # Middle (could go either way based on thresholds)
    ("adventure", "inventor"),   # Middle
    ("brake", "break"),          # Middle
    ("flower", "flour"),         # Middle
    ("duck", "luck"),            # Middle
    ("heart", "hurt"),           # Middle
    ("plane", "plain"),          # Middle
    ("meat", "meet"),            # Middle
    ("bake", "cake"),            # Middle
    ("coat", "cot"),             # Middle
    ("note", "node"),            # Middle
    ("pole", "pale"),            # Middle
    ("light", "late"),           # Middle
    ("write", "right"),          # Middle
    ("close", "clothes"),        # Middle
    ("blue", "blow"),            # Middle
    ("deep", "peep"),            # Middle
    ("find", "fine"),            # Middle
    ("stop", "shop"),            # Middle
    ("know", "no"),              # Middle
    ("lead", "lid")              # Middle
]


for word1, word2 in test_cases:
    print(f"{word1} vs {word2}: {dynamic_phonetic_comparision(word1, word2)}\n")

# Full results from your test cases (updated)
results = [
    # TRUE
    ("dog", "doug", 86, 100, 63, True),
    ("fox", "folks", 50, 86, 83, True),
    ("cat", "kat", 67, 100, 73, True),
    ("mouse", "mousse", 91, 100, 65, True),
    ("read", "reed", 75, 100, 74, True),
    ("phone", "fone", 67, 100, 74, True),
    ("write", "rite", 89, 100, 64, True),
    ("bat", "batt", 86, 100, 63, True),
    ("peace", "piece", 80, 100, 75, True),
    ("car", "kar", 67, 100, 73, True),
    ("their", "there", 80, 100, 75, True),
    ("sun", "son", 67, 100, 73, True),
    ("tie", "tai", 67, 100, 73, True),
    ("flow", "flou", 75, 100, 74, True),
    ("sell", "cell", 75, 100, 74, True),
    # FALSE
    ("dog", "cat", 0, 50, 83, False),
    ("apple", "orange", 36, 33, 85, False),
    ("table", "chair", 20, 0, 85, False),
    ("book", "phone", 22, 0, 84, False),
    ("train", "plane", 40, 33, 85, False),
    ("ship", "car", 0, 0, 83, False),
    ("jump", "run", 29, 0, 83, False),
    ("banana", "monkey", 17, 33, 86, False),
    ("moon", "sun", 29, 50, 83, False),
    ("river", "mountain", 15, 0, 85, False),
    ("grass", "stone", 20, 33, 85, False),
    ("computer", "paper", 46, 50, 85, False),
    ("laptop", "bottle", 17, 57, 86, False),
    ("shark", "fish", 44, 40, 84, False),
    ("sugar", "salt", 44, 0, 84, False),
    
    # MIDDLE (borderline cases)
    ("adventure", "inventor", 59, 83, 88, False),
    ("brake", "break", 80, 100, 75, True),
    ("flower", "flour", 73, 100, 75, True),
    ("duck", "luck", 75, 50, 74, False),
    ("heart", "hurt", 67, 100, 74, True),
    ("plane", "plain", 80, 100, 75, True),
    ("meat", "meet", 75, 100, 74, True),
    ("bake", "cake", 75, 50, 74, False),
    ("coat", "cot", 86, 100, 63, True),
    ("note", "node", 75, 100, 74, True),
    ("pole", "pale", 75, 100, 74, True),
    ("light", "late", 44, 100, 84, True),
    ("write", "right", 60, 100, 85, True),
    ("close", "clothes", 67, 86, 75, True),
    ("blue", "blow", 50, 100, 84, True),
    ("deep", "peep", 75, 50, 74, False),
    ("find", "fine", 75, 80, 74, True),
    ("stop", "shop", 75, 40, 74, False),
    ("know", "no", 67, 100, 72, True),
    ("lead", "lid", 57, 100, 83, True)
]

# Extracting data into lists
word_pairs = [f"{w1} vs {w2}" for w1, w2, _, _, _, _ in results]
string_similarities = [s for _, _, s, _, _, _ in results]
phonetic_similarities = [p for _, _, _, p, _, _ in results]
thresholds = [t for _, _, _, _, t, _ in results]
is_similar = [sim for _, _, _, _, _, sim in results]

# 1. Plot String Similarity vs. Phonetic Similarity
plt.figure(figsize=(10, 6))
sns.scatterplot(x=string_similarities, y=phonetic_similarities, hue=is_similar, style=is_similar, palette="coolwarm", s=100)
plt.title("String Similarity vs Phonetic Similarity")
plt.xlabel("String Similarity")
plt.ylabel("Phonetic Similarity")
plt.legend(title="Is Similar")
plt.grid(True)
plt.show()

# 2. Plot Word Length vs. String Similarity
word_lengths = [min(len(w1), len(w2)) for w1, w2, _, _, _, _ in results]  # Min length of the two words

plt.figure(figsize=(10, 6))
sns.scatterplot(x=word_lengths, y=string_similarities, hue=is_similar, style=is_similar, palette="viridis", s=100)
plt.title("Word Length vs String Similarity")
plt.xlabel("Word Length (Min Length)")
plt.ylabel("String Similarity")
plt.legend(title="Is Similar")
plt.grid(True)
plt.show()

# 3. Histogram of Dynamic Phonetic Thresholds
plt.figure(figsize=(10, 6))
sns.histplot(thresholds, bins=np.arange(60, 101, 5), kde=True, color="skyblue")
plt.title("Distribution of Dynamic Phonetic Thresholds")
plt.xlabel("Dynamic Phonetic Threshold")
plt.ylabel("Frequency")
plt.grid(True)
plt.show()
