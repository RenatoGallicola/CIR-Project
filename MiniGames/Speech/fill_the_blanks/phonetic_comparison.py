import jellyfish
import phonetics
from fuzzywuzzy import fuzz

# Function to compare two words phonetically to help with speech recognition errors
def is_phonetically_similar(word1, word2, threshold=0.5):
    """
    Compare two words phonetically using Jaro-Winkler distance and Metaphone codes.
    
    Args:
    word1 (str): The first word to compare.
    word2 (str): The second word to compare.
    threshold (float): The threshold for Jaro-Winkler distance.
    
    Returns:
    bool: True if the words are phonetically similar, False otherwise.
    """
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

def dynamic_phonetic_threshold(word1, word2):
    """
    Calculate a dynamic phonetic threshold based on string similarity and word length.
    
    Args:
    word1 (str): The first word to compare.
    word2 (str): The second word to compare.
    
    Returns:
    int: The dynamic phonetic threshold.
    """
    # Calculate string similarity
    string_similarity = fuzz.ratio(word1, word2)
    print(f"String similarity: {string_similarity}")
    
    # Adjust the threshold based on the length of the words
    min_length = min(len(word1), len(word2))
    print(f"Minimum length of words: {min_length}")
    
    # Dynamically set the phonetic threshold based on string similarity and word length
    if string_similarity > 80:
        return 60 + (min_length)  # Looser phonetic threshold for close strings
    elif string_similarity > 60:
        return 70 + (min_length)  # Moderate phonetic threshold for somewhat similar strings
    else:
        return 80 + (min_length)  # Stricter phonetic threshold for very different strings


def dynamic_phonetic_comparision(word1, word2):
    """
    Compare two words phonetically using Metaphone codes and a dynamic phonetic threshold.

    Args:
    word1 (str): The first word to compare.
    word2 (str): The second word to compare.

    Returns:
    bool: True if the words are phonetically similar, False otherwise.
    """

    # Convert words to Metaphone codes for phonetic similarity
    word1_meta = phonetics.metaphone(word1)
    word2_meta = phonetics.metaphone(word2)
    print(f"Metaphone codes: {word1_meta}, {word2_meta}")
    print(f"Words: {word1}, {word2}")
    
    # Get dynamic phonetic threshold
    phonetic_threshold = dynamic_phonetic_threshold(word1, word2)
    print(f"Dynamic phonetic threshold: {phonetic_threshold}")
    
    # Phonetic comparison
    phonetic_similarity = fuzz.ratio(word1_meta, word2_meta)
    print(f"Phonetic similarity: {phonetic_similarity}")
    
    # Return true if phonetic similarity exceeds the dynamic threshold

    # Make a print like this : (word1, word2, string_similarity, phonetic_similarity, dynamic_threshold, is_similar)
    return phonetic_similarity >= phonetic_threshold

