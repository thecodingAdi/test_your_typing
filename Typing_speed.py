import pygame
import time
import threading
from transformers import AutoTokenizer, AutoModelForCausalLM, pipeline
import re

def clean_text(text):
    text = re.sub(r'[^\x20-\x7E]', '', text)  # Remove weird characters
    return text

def greet():
    current_hour = time.localtime().tm_hour
    if 5 <= current_hour < 12:
        return "Good Morning!!"
    elif 12 <= current_hour < 18:
        return "Good Afternoon!!"
    else:
        return "Good Evening!!"

paragraph_text = "Loading paragraph..."  # Placeholder until text is ready
paragraph_ready = False

def generate_paragraph():
    global paragraph_text, paragraph_ready
    try:
        model_name = "distilgpt2"
        tokenizer = AutoTokenizer.from_pretrained(model_name)
        model = AutoModelForCausalLM.from_pretrained(model_name)
        generator = pipeline("text-generation", model=model, tokenizer=tokenizer)
        prompt = "Write a random paragraph about anything:"
        output = generator(
            prompt,
            max_new_tokens=150,
            temperature=0.9,
            do_sample=True,
            top_k=50,
            top_p=0.95
        )[0]['generated_text']
        paragraph_text = clean_text(output.replace(prompt, "").strip())
        paragraph_ready = True
        print("Paragraph generated successfully.")
    except Exception as e:
        paragraph_text = "Error loading paragraph."
        print("Paragraph generation failed:", e)

# Display generated text on the pygame screen
def wrap_text(text, font, max_width):
    words = text.split(' ')
    lines = []
    current_line = ""
    for word in words:
        test_line = current_line + word + " "
        if font.size(test_line)[0] <= max_width:
            current_line = test_line
        else:
            lines.append(current_line.strip())
            current_line = word + " "
    lines.append(current_line.strip())
    return lines

# Generate a box where input is done
def rect_generate():
    pygame.draw.rect(screen, (20, 20, 20), (5, 395, 790, 130))
    pygame.draw.rect(screen, (100, 255, 100), (5, 395, 790, 130), 1)

# Function for calculating words per minute
def WPM():
    typed_chars = len(input_text)
    wpm = (typed_chars / 5) / (time_limit / 60)
    return wpm

# Accuracy checking function
def calculate_accuracy(target, typed):
    target_words = target.split()
    typed_words = typed.split()
    correct = 0

    for i in range(min(len(target_words), len(typed_words))):
        if target_words[i] == typed_words[i]:
            correct += 1

    accuracy = (correct / len(typed_words)) * 100 if typed_words else 0
    return int(accuracy)  # Convert to integer

# Initialize Pygame
pygame.init()
screen = pygame.display.set_mode((800, 600))
pygame.display.set_caption("TYPING TEST")
font = pygame.font.Font(None, 28)

# Start paragraph generation in background
thread = threading.Thread(target=generate_paragraph)
thread.daemon = True
thread.start()

greeting_text = greet()
input_text = ""

start_time = None         # Record when the test begins
ready_to_start_time = None  # Record when paragraph becomes ready
time_limit = 60                  # Total time allowed (in seconds)

running = True

while running:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        elif event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                running = False
            elif start_time is not None:
                if remaining_time == 0:
                    # Do nothing—just block typing but keep window open
                    pass
                else:
                    # Allow typing
                    if event.key == pygame.K_BACKSPACE:
                        input_text = input_text[:-1]
                    elif event.key == pygame.K_RETURN:
                        print("User typed:", input_text)
                        input_text = ""
                    else:
                        input_text += event.unicode
            
    screen.fill((10, 10, 10))

    # Greeting
    greeting_surface = font.render(greeting_text, True, (255, 255, 255))
    screen.blit(greeting_surface, (10, 10))

    # Add animated loading effect
    display_text = paragraph_text
    if "Loading" in paragraph_text:
        dots = "." * (int(time.time()) % 4)
        display_text = "Loading paragraph" + dots

    # Display the genearted paragraph 
    wrapped_lines = wrap_text(display_text, font, 780)
    for i, line in enumerate(wrapped_lines):
        line_surface = font.render(line, True, (255, 255, 255))
        screen.blit(line_surface, (10, 50 + i * 30))
    
    # Input box
    # Draw input box background 
    if paragraph_ready :
        rect_generate()

# Render wrapped input lines (max 4)
    input_lines = wrap_text(input_text, font, 780)
    for i, line in enumerate(input_lines[-4:]):
        input_surface = font.render(line, True, (0, 255, 0))
        screen.blit(input_surface, (10, 400 + i * 30))


    # Timer setup

    # Start delay countdown after paragraph is ready
    if paragraph_ready and ready_to_start_time is None:
        ready_to_start_time = time.time()

    # Show 10-second preview countdown before typing begins
    if ready_to_start_time is not None and start_time is None:
        preview_elapsed = time.time() - ready_to_start_time
        countdown = int(10 - preview_elapsed)
        if countdown > 0:
            preview_surface = font.render(f"⏳ Get ready... Typing starts in {countdown}s", True, (0, 200, 200))
            screen.blit(preview_surface, (10, 360))
        else:
            start_time = time.time()

    if start_time is not None:
        elapsed_time = time.time() - start_time
        remaining_time = max(0, int(time_limit - elapsed_time))

        # Render countdown timer
        timer_surface = font.render(f"Time Left: {remaining_time}s", True, (255, 255, 0))
        screen.blit(timer_surface, (10, 360))

        # When time runs out
        if remaining_time == 0:
            timeout_surface = font.render("⏳ Time's up! Press ESC to quit.", True, (255, 0, 0))
            screen.blit(timeout_surface, (500, 10))

            # Show WPM, accuracy 
            wpm=WPM()
            wpm_surface= font.render(f"Your WPM :{int(wpm)}",True,(0,255,255))
            screen.blit(wpm_surface,(300,330))

            accuracy = calculate_accuracy(paragraph_text, input_text)
            acc_surface = font.render(f"Accuracy: {int(accuracy)}%", True, (255, 255, 255))
            screen.blit(acc_surface, (300, 360))

            pygame.display.flip()
            continue  # Skip input processing after time expires

    pygame.display.flip()
pygame.quit()
