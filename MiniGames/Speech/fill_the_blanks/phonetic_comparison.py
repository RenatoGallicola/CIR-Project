import jellyfish

# Function to compare two words phonetically to help with speech recognition errors
def is_phonetically_similar(word1, word2, threshold=0.5):
    # Compare using Jaro-Winkler distance
    jaro_distance = jellyfish.jaro_winkler_similarity(word1, word2)
    print(f"Jaro-Winkler distance: {jaro_distance}")
    # Compare using Metaphone
    metaphone1 = jellyfish.metaphone(word1)
    metaphone2 = jellyfish.metaphone(word2)
    metaphone_match = (metaphone1 == metaphone2)
    print(f"Metaphone match: {metaphone_match}")
    # Return True if either Jaro-Winkler distance is above threshold or Metaphone matches
    return jaro_distance > threshold or metaphone_match