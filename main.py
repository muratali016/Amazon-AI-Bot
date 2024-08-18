from playwright.sync_api import sync_playwright
from openai import OpenAI
import openai
import os
import speech_recognition as sr
import pyttsx3
import csv


os.environ["OPENAI_API_KEY"] = "sk-xx"
GPT_MODEL = "gpt-4o-mini"
client = OpenAI(api_key="sk-xx")

# Tools for the assistant
tools = [
    {"type": "function", "function": {"name": "product_analysis", "description": "Do product analysis"}},
    {"type": "function", "function": {"name": "find_product", "description": "Find the best fit for the user's query"}},
    {"type": "function", "function": {"name": "search_product", "description": "Performs a search on Amazon for products"}},
]

# Initialize text-to-speech engine
engine = pyttsx3.init()
voices = engine.getProperty('voices')

# Set voice to a different one
engine.setProperty('voice', voices[0].id)
def speak(text):
    engine.say(text)
    engine.runAndWait()

# Initialize speech recognition
recognizer = sr.Recognizer()

def listen():
    with sr.Microphone() as source:
        print("Listening...")
        speak("Listening...")
        try:
            audio = recognizer.listen(source, timeout=40)
            command = recognizer.recognize_google(audio)
            print(f"You said: {command}")
            return command
        except sr.UnknownValueError:
            print("Sorry, I didn't catch that.")
            return ""
        except sr.RequestError as e:
            print(f"Could not request results; {e}")
            return ""
        except sr.WaitTimeoutError:
            print("Listening timed out while waiting for phrase to start.")
            return ""

with sync_playwright() as playwright:
    browser = playwright.chromium.connect_over_cdp("http://localhost:9222")
    default_context = browser.contexts[0]
    page = default_context.pages[0]
    page.wait_for_load_state('networkidle')

    print("Page Title:", page.title())
    speak("Amazon bot is live and alive ask anything baby")
    speak(f"Page Title: {page.title()}")
    print("Page URL:", page.url)
    #speak(f"Page URL: {page.url}")

    while True:
        print("-" * 100)
        user_input = listen()  # Get input from voice command
        if not user_input:
            continue

        messages = [{"role": "system", "content": f"You are my Amazon Tool"},{"role": "user", "content": f"{user_input}"}]
        chat_response = openai.chat.completions.create(
            model=GPT_MODEL,
            messages=messages,
            tools=tools
        )

        assistant_message = chat_response.choices[0].message.tool_calls
        response_content = chat_response.choices[0].message.content
        print(response_content)
        if response_content is None or "None" in response_content:
            print("")
        else:
            speak(response_content)  # Narrate the response

        if chat_response.choices[0].message.tool_calls is not None:
            for tool_call in assistant_message:
                if tool_call.function.name == 'product_analysis':
                    print("product_analysis is running")
                    product_elements = page.query_selector_all('.p13n-grid-content')
                    product_list = [] 
                    products_dict = {}
                    for product in product_elements:
                        title_element = product.query_selector('div._cDEzb_p13n-sc-css-line-clamp-3_g3dy1')
                        title = title_element.inner_text() if title_element else 'No Title'

                        url_element = product.query_selector('a.a-link-normal')
                        url = url_element.get_attribute('href') if url_element else 'No URL'

                        price_element = product.query_selector('span._cDEzb_p13n-sc-price_3mJ9Z')
                        price = price_element.inner_text() if price_element else 'No Price'

                        products_dict[title] = {
                            'url': url,
                            'price': price
                        }

                        print("Product Title:", title)
                        print("Product URL:", url)
                        print("Product Price:", price)
                        print("-" * 40)
                        speak(f"Product Title: {title}, Product Price: {price}")

                    #page.get_by_text("Next page→").click()
                    csv_file = "product_analysis.csv"
                    with open(csv_file, mode='w', newline='', encoding='utf-8') as file:
                        writer = csv.writer(file)
                        writer.writerow(["Title", "URL", "Price"])  # Write header
                        writer.writerows(product_list)  # Write product data

                    print(f"Product data has been saved to {csv_file}")
                    speak(f"Product data has been saved to {csv_file}")
                elif tool_call.function.name == 'find_product':
                    print("find_product is running")
                    speak("I'm working on it count down to 10")
                    product_elements = page.query_selector_all('.p13n-grid-content')

                    products_dict = {}
                    for product in product_elements:
                        title_element = product.query_selector('div._cDEzb_p13n-sc-css-line-clamp-3_g3dy1')
                        title = title_element.inner_text() if title_element else 'No Title'

                        url_element = product.query_selector('a.a-link-normal')
                        url = url_element.get_attribute('href') if url_element else 'No URL'

                        price_element = product.query_selector('span._cDEzb_p13n-sc-price_3mJ9Z')
                        price = price_element.inner_text() if price_element else 'No Price'

                        products_dict[title] = {
                            'url': url,
                            'price': price
                        }

                        #print("Product Title:", title)
                        #print("Product URL:", url)
                        #print("Product Price:", price)
                        #print("-" * 40)
                        speak(f"Product Title: {title}, Product Price: {price}")

                    product_elements = page.query_selector_all('div[data-component-type="s-search-result"]')

                    for product in product_elements:
                        title_element = product.query_selector('h2 a.a-link-normal')
                        title = title_element.inner_text() if title_element else 'No Title'

                        url_element = product.query_selector('h2 a.a-link-normal')
                        url = url_element.get_attribute('href') if url_element else 'No URL'

                        price_element = product.query_selector('span.a-price-whole')
                        price = price_element.inner_text() if price_element else 'No Price'

                        products_dict[title] = {
                            'url': url,
                            'price': price
                        }

                    chat_response_in = openai.chat.completions.create(
                        model=GPT_MODEL,
                        messages=[{"role": "user", "content": f"Return !!only!! the Product URL only!, these are the products: {products_dict} {user_input}"}],
                    )
                    print(f"amazon.com/{chat_response_in.choices[0].message.content}")
                    speak("I found what you find Rick check it out")
                    #speak(f"Here is the product URL: amazon.com/{chat_response_in.choices[0].message.content}")

                elif tool_call.function.name == 'search_product':
                    print("search_product is running")
                    search_term = user_input.lower().replace('search for', '').strip()
                    page.fill('input#twotabsearchtextbox', search_term)
                    page.press('input#twotabsearchtextbox', 'Enter')

                    page.wait_for_selector('div.s-main-slot')
                    product_elements = page.query_selector_all('div.s-main-slot div[data-component-type="s-search-result"]')

                    products_dict = {}
                    for product in product_elements:
                        title_element = product.query_selector('h2 a.a-link-normal')
                        title = title_element.inner_text() if title_element else 'No Title'

                        url_element = product.query_selector('h2 a.a-link-normal')
                        url = url_element.get_attribute('href') if url_element else 'No URL'

                        price_element = product.query_selector('span.a-price-whole')
                        price = price_element.inner_text() if price_element else 'No Price'

                        products_dict[title] = {
                            'url': url,
                            'price': price
                        }

                        print("Product Title:", title)
                        print("Product URL:", url)
                        print("Product Price:", price)
                        print("-" * 40)
                    speak(f"Search has been performed and Results are ready, check it out Rick")

                else:
                    print("Unknown command")
                    speak("Unknown command")
        else:
            print("No tools were called.")
            speak("No tools were called.")
