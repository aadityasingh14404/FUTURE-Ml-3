import hashlib
import ollama
from memory_manager import EONMemoryManager
from personality import Personality

def formulate_response(memories, user_input, personality_traits):
    if memories:
        combined_memory = " ".join(memories)
        prompt = (
            f"Personality traits: {personality_traits}\n"
            f"Based on what I remember: {combined_memory}\n"
            f"Now, in response to your query: {user_input}"
        )
    else:
        prompt = f"Personality traits: {personality_traits}\nUser: {user_input}"
    try:
        response = ollama.chat(
            model="llama3.2",
            messages=[{"role": "user", "content": prompt}]
        )
        return response["message"]["content"]
    except Exception as e:
        return f"Error obtaining response: {e}"

def main():
    print("EON: Ready to assist, sir!")
    
    memory_manager = EONMemoryManager(db_path="memory/eon_memory.json")
    personality = Personality(personality_file="memory/traits.json")

    while True:
        user_input = input("You: ")
        if user_input.lower() in ["exit", "see ya", "bye"]:
            print("EON: Ok bro, See ya!")
            break
        
        # If the user asks for help-related queries
        if any(keyword in user_input.lower() for keyword in ["help", "what can you do", "what can i ask"]):
            memories = memory_manager.retrieve_memory(user_input, top_k=3)
            traits = personality.get_traits()
            bot_reply = formulate_response(memories, user_input, traits)
            print("EON:", bot_reply)
            continue  # Skip normal processing after help query
        
        memories = memory_manager.retrieve_memory(user_input, top_k=3)
        traits = personality.get_traits()
        bot_reply = formulate_response(memories, user_input, traits)
        print("EON:", bot_reply)

        memory_id = "memory_" + hashlib.sha256(user_input.encode()).hexdigest()
        memory_manager.add_memory(user_input, memory_id)

        memory_manager.summarize_memory_if_needed()

if __name__ == "__main__":
    main()
