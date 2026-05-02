import nltk
import json
import random
import os


nltk.download('punkt', quiet=True)
nltk.download('punkt_tab', quiet=True)
nltk.download('wordnet', quiet=True)

from nltk.stem import WordNetLemmatizer

lemmatizer = WordNetLemmatizer()


STOP_WORDS = {
    'i', 'me', 'my', 'we', 'our', 'you', 'your', 'he', 'she', 'it',
    'is', 'am', 'are', 'was', 'were', 'be', 'been', 'being',
    'a', 'an', 'the', 'and', 'or', 'but', 'if', 'so',
    'do', 'does', 'did', 'have', 'has', 'had',
    'what', 'which', 'who', 'whom', 'this', 'that',
    'in', 'on', 'at', 'to', 'for', 'of', 'with', 'about',
    'can', 'could', 'would', 'should', 'will', 'shall',
    'not', 'no', 'there', 'here', 'where', 'when', 'how',
    'tell', 'please', 'know', 'want', 'need', 'get',
    '?', '!', '.', ','
}


def process_text(text):
    """Tokenize and lemmatize input text."""
    tokens = nltk.word_tokenize(text.lower())
    return [lemmatizer.lemmatize(w) for w in tokens]


def get_keywords(text):
    """Extract meaningful keywords by removing stop words."""
    tokens = process_text(text)
    return set(word for word in tokens if word not in STOP_WORDS)


def calculate_similarity(input_keywords, pattern_keywords):
    """Jaccard similarity: overlap / union of keyword sets."""
    if not pattern_keywords or not input_keywords:
        return 0.0
    union = input_keywords.union(pattern_keywords)
    overlap = input_keywords.intersection(pattern_keywords)
    return len(overlap) / len(union)


class CeylonEngine:
    # At least 30% keyword overlap required to match
    SIMILARITY_THRESHOLD = 0.3

    def __init__(self):
        intents_path = os.path.join(os.path.dirname(__file__), 'data', 'intents.json')
        with open(intents_path, 'r') as f:
            self.intents = json.load(f)

    def get_response(self, user_input, db):
        """
        3-Tier lookup :
          Tier 1: Static intents.json 
          Tier 2: learned_facts DB     
          Tier 3: Learning mode        
        Returns: (response_text, is_learning_mode)
        """
        # Check if it's a transit query first (bus/train routes)
        if self._is_transit_query(user_input):
            result = self._search_transit(user_input, db)
            if result:
                db.log_chat(user_input, result)
                return result, False

        input_keywords = get_keywords(user_input)

        # --- Tier 1: Static Intents ---
        best_score = 0.0
        best_intent = None
        for intent in self.intents['intents']:
            for pattern in intent['patterns']:
                pattern_keywords = get_keywords(pattern)
                score = calculate_similarity(input_keywords, pattern_keywords)
                if score > best_score:
                    best_score = score
                    best_intent = intent

        if best_score >= self.SIMILARITY_THRESHOLD and best_intent:
            response = random.choice(best_intent['responses'])
            db.log_chat(user_input, response)
            return response, False

        # --- Tier 2: Learned Facts from DB ---
        all_facts = db.get_all_learned_facts()
        best_fact_score = 0.0
        best_fact_response = None
        for pattern, response in all_facts:
            pattern_keywords = get_keywords(pattern)
            score = calculate_similarity(input_keywords, pattern_keywords)
            if score > best_fact_score:
                best_fact_score = score
                best_fact_response = response

        if best_fact_score >= self.SIMILARITY_THRESHOLD and best_fact_response:
            db.log_chat(user_input, best_fact_response)
            return best_fact_response, False

        # --- Tier 3: Learning Mode ---
        return (
            "Hmm, I don't have information on that yet! 🤔 "
            "What should I say in response to this? Your suggestion will be reviewed by our team.",
            True
        )

    def _is_transit_query(self, user_input):
        """Check if the message is asking about transport routes."""
        transit_keywords = ['train', 'bus', 'route', 'from', 'to', 'travel', 'trip', 'how to get']
        user_lower = user_input.lower()
        return any(kw in user_lower for kw in transit_keywords)

    def _search_transit(self, user_input, db):
        """Search the Transit table for a matching route."""
        try:
            all_routes = db.get_all_routes()
            user_lower = user_input.lower()
            for route in all_routes:
                start = str(route[0]).strip().lower() if route[0] else ""
                end   = str(route[1]).strip().lower() if route[1] else ""
                transport = route[2]
                time_est  = route[3]
                price     = route[4]
                if start in user_lower and end in user_lower:
                    return (
                        f"✅ Found a route! You can take a {transport} from "
                        f"{route[0]} to {route[1]}. "
                        f"It takes about {time_est} and costs Rs. {price}."
                    )
            return None  
        except Exception as e:
            return f"Database error while searching routes: {e}"