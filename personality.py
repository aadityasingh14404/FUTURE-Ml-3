import json
import time
import requests

class Personality:
    def __init__(self, personality_file="memory/traits.json"):
        self.personality_file = personality_file
        self.traits = {
            "friendly": True,
            "curious": True,
            "helpful": True,
            "dynamic": True,
            "humorous": True,
            "analytical": True,
            "empathetic": True,
            "directness": True,
            "assertiveness": True,
            "openness": True,
            "conscientiousness": True,
            "adventurous": True
        }
        self.last_updated = None
        self.load_personality()
        
    def get_traits(self):
        return self.traits

    def load_personality(self):
        try:
            with open(self.personality_file, "r") as f:
                data = json.load(f)
                self.traits = data.get("traits", self.traits)
                self.last_updated = data.get("last_updated", None)
        except FileNotFoundError:
            self.save_personality()

    def save_personality(self):
        data = {
            "traits": self.traits,
            "last_updated": time.strftime("%Y-%m-%d %H:%M:%S")
        }
        with open(self.personality_file, "w") as f:
            json.dump(data, f, indent=4)

    def check_internet(self, timeout=5):
        try:
            requests.get("https://www.google.com", timeout=timeout)
            return True
        except requests.RequestException:
            return False

    def fetch_dynamic_data(self):
        if self.check_internet():
            try:
                response = requests.get("https://api.quotable.io/random", timeout=5)
                if response.status_code == 200:
                    data = response.json()
                    return data.get("content", "No data available")
            except requests.RequestException:
                return None
        return None

    def update_personality(self):
        if self.check_internet():
            dynamic_data = self.fetch_dynamic_data()
            if dynamic_data:
                if "innovate" in dynamic_data.lower():
                    self.traits["innovative"] = True
                else:
                    self.traits["innovative"] = False
                self.last_updated = time.strftime("%Y-%m-%d %H:%M:%S")
                self.save_personality()
                return f"Personality updated with online insight: {dynamic_data}"
            return "Dynamic data could not be fetched."
        return "No internet connection. Personality remains unchanged."

    def learn_from_conversation(self, conversation_context):
        if "fun" in conversation_context.lower():
            self.traits["humorous"] = True
        if "serious" in conversation_context.lower():
            self.traits["empathetic"] = True
            self.traits["analytical"] = True
        self.save_personality()
        return "Personality adapted based on conversation context."

    def decide_response_style(self, user_input):
        active_traits = [trait for trait, value in self.traits.items() if value]
        style = f"As someone who is {', '.join(active_traits)}, I think: "
        if "joke" in user_input.lower() and self.traits.get("humorous"):
            style += "Here's a funny take: "
        elif "analyze" in user_input.lower() and self.traits.get("analytical"):
            style += "Let me break it down: "
        return style

if __name__ == "__main__":
    p = Personality()
    print(p.get_traits())
    print(p.update_personality())
    