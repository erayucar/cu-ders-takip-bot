import os
import time
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
from bs4 import BeautifulSoup
from telegram import Update
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters, ConversationHandler, CallbackContext
import asyncio
from dotenv import load_dotenv
from datetime import datetime
import logging
from flask import Flask
import threading

# Initialize Flask app
app = Flask(__name__)

@app.route('/health')
def health():
    return 'OK'

def run_flask():
    """Run Flask in a separate thread"""
    port = int(os.getenv('PORT', 10000))
    app.run(host='0.0.0.0', port=port)

# Load environment variables
load_dotenv()

# Configuration
TELEGRAM_BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')
LOGIN_URL = "https://login.cu.edu.tr"

# States for conversation
WAITING_USERNAME = 1
WAITING_PASSWORD = 2

# Global variables for single user
driver = None
last_check = {}
is_subscribed = False

def setup_driver():
    """Setup and return Chrome WebDriver"""
    try:
        chrome_options = Options()
        chrome_options.add_argument("--headless")
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("--disable-gpu")
        chrome_options.add_argument("--window-size=1920,1080")
        chrome_options.add_argument("--ignore-certificate-errors")
        chrome_options.add_argument("--disable-extensions")
        chrome_options.add_argument("--disable-software-rasterizer")
        
        # Use Chromium binary if available
        chrome_binary = os.getenv('CHROME_BIN')
        if chrome_binary:
            chrome_options.binary_location = chrome_binary
            
        # Use ChromeDriver path if specified
        chromedriver_path = os.getenv('CHROMEDRIVER_PATH')
        service = Service(executable_path=chromedriver_path) if chromedriver_path else Service()
        
        driver = webdriver.Chrome(service=service, options=chrome_options)
        driver.implicitly_wait(10)
        return driver
    except Exception as e:
        print(f"Error setting up ChromeDriver: {str(e)}")
        raise

def login_to_system(driver, username, password):
    """Login to the course registration system"""
    try:
        driver.get(LOGIN_URL)
        
        # Wait for and fill username
        username_input = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.ID, "ctl06_txtKullaniciAdi"))
        )
        username_input.send_keys(username)
        
        # Fill password
        password_input = driver.find_element(By.ID, "ctl06_txtSifre")
        password_input.send_keys(password)
        
        # Click login
        login_button = driver.find_element(By.CLASS_NAME, "btn-primary")
        login_button.click()
        
        # Check if login was successful by looking for error message
        try:
            error_message = WebDriverWait(driver, 3).until(
                EC.presence_of_element_located((By.CLASS_NAME, "validation-summary-errors"))
            )
            # If we found an error message, login failed
            return False
        except:
            # No error message found, try to navigate to course page
            driver.get("https://derskayit.cu.edu.tr/DerseYazilma")
            
            # Check for and click initial button if present
            try:
                button = WebDriverWait(driver, 5).until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, "input.btn"))
                )
                if button.is_displayed():
                    button.click()
            except:
                logging.info("Initial button not found or not clickable")
                
            return True
        
    except Exception as e:
        logging.error(f"Login failed: {str(e)}")
        return False

def get_course_info(driver):
    """Get course information from the page"""
    try:
        # Wait for the table to be present
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "td span.badge"))
        )
        
        # Get all course names and capacities
        course_names = driver.find_elements(By.CSS_SELECTOR, "div:nth-of-type(2) div:nth-of-type(2) td:nth-of-type(3) span:nth-of-type(1)")
        capacities = driver.find_elements(By.CSS_SELECTOR, "td span.badge")
        
        courses = {}
        for name, capacity in zip(course_names, capacities):
            course_name = name.text.strip()
            if course_name and "Kalan:" in capacity.text:
                available = int(capacity.text.split(":")[-1].strip())
                courses[course_name] = available
                
        return courses
        
    except Exception as e:
        logging.error(f"Error getting course info: {str(e)}")
        return {}

def get_password(update: Update, context: CallbackContext):
    """Get password and attempt login"""
    global driver, last_check
    try:
        password = update.message.text
        username = context.user_data['username']
        
        # Delete the password message for security
        try:
            update.message.delete()
        except:
            logging.warning("Could not delete password message")
        
        update.message.reply_text("🔄 Attempting to login...")
        
        # Clean up existing driver if any
        if driver:
            try:
                driver.quit()
            except:
                pass
        
        # Create new driver instance
        try:
            driver = setup_driver()
            if login_to_system(driver, username, password):
                # Store initial course data
                last_check = get_course_info(driver)
                
                update.message.reply_text(
                    "✅ Successfully logged in!\n"
                    "Bot created by @kefeyro\n\n"
                    "Use /subscribe to start receiving notifications about available courses."
                )
            else:
                if driver:
                    driver.quit()
                    driver = None
                update.message.reply_text(
                    "❌ Login failed. Please check your username and password and try again with /login"
                )
        except Exception as e:
            logging.error(f"Login error: {str(e)}")
            update.message.reply_text(
                "❌ An error occurred during login. Please try again with /login"
            )
            if driver:
                try:
                    driver.quit()
                except:
                    pass
                driver = None
    except Exception as e:
        logging.error(f"Unexpected error in get_password: {str(e)}")
        try:
            update.message.reply_text(
                "❌ An unexpected error occurred. Please try again with /login"
            )
        except:
            pass
    
    return ConversationHandler.END

def check_courses(context: CallbackContext):
    """Check for available courses and send notifications"""
    global driver, last_check, is_subscribed
    
    if not is_subscribed or not driver:
        return
        
    try:
        # Try to access the course page to verify login status
        driver.get("https://derskayit.cu.edu.tr/DerseYazilma")
        WebDriverWait(driver, 5).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "td span.badge"))
        )
    except Exception as e:
        logging.error(f"Session expired: {str(e)}")
        try:
            context.bot.send_message(
                chat_id=context.job.context,
                text="⚠️ Session expired. Please login again using /login"
            )
        except:
            logging.error("Could not send session expiry message")
        
        try:
            driver.quit()
        except:
            pass
        driver = None
        is_subscribed = False
        return
        
    try:
        current_courses = get_course_info(driver)
        
        if not current_courses:
            logging.error("No course information retrieved")
            return
            
        # Only notify for courses that changed from 0 to positive slots
        for name, current_slots in current_courses.items():
            last_slots = last_check.get(name, current_slots)
            
            if last_slots == 0 and current_slots > 0:
                message = (
                    f"🔔 Course Now Available!\n\n"
                    f"Course: {name}\n"
                    f"Available Slots: {current_slots}\n"
                    f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
                )
                
                try:
                    context.bot.send_message(chat_id=context.job.context, text=message)
                    logging.info(f"Sent availability notification for {name}")
                except:
                    logging.error("Could not send notification")
        
        # Update last check data
        last_check = current_courses
            
    except Exception as e:
        logging.error(f"Error in check_courses: {str(e)}")

def start(update: Update, context: CallbackContext):
    """Send a message when the command /start is issued."""
    message = (
        "👋 Welcome to the Course Availability Bot!\n"
        "Created by @kefeyro\n\n"
        "I will notify you when courses become available.\n\n"
        "Commands:\n"
        "/login - Login to the system\n"
        "/subscribe - Start receiving notifications\n"
        "/unsubscribe - Stop receiving notifications"
    )
    update.message.reply_text(message)

def login(update: Update, context: CallbackContext):
    """Login command handler"""
    update.message.reply_text("Please enter your username:")
    return WAITING_USERNAME

def get_username(update: Update, context: CallbackContext):
    """Handle username input"""
    context.user_data['username'] = update.message.text
    # Delete the message containing the username
    update.message.delete()
    update.message.reply_text("Please enter your password:")
    return WAITING_PASSWORD

def stop(update: Update, context: CallbackContext):
    """Stop monitoring command handler"""
    global driver, is_subscribed
    
    # Remove jobs
    current_jobs = context.job_queue.get_jobs_by_name(str(update.effective_chat.id))
    for job in current_jobs:
        job.schedule_removal()
    
    # Clean up driver
    if driver:
        try:
            driver.quit()
        except:
            pass
        driver = None
    
    is_subscribed = False
    update.message.reply_text("Course monitoring stopped.")

def cancel(update: Update, context: CallbackContext):
    """Cancel conversation command handler"""
    update.message.reply_text("Operation cancelled.")
    return ConversationHandler.END

def subscribe(update: Update, context: CallbackContext):
    """Subscribe to course availability notifications"""
    global driver, last_check, is_subscribed
    
    if not driver:
        update.message.reply_text(
            "❌ Please login first using the /login command before subscribing."
        )
        return
        
    try:
        # Try to access the course page to verify login status
        driver.get("https://derskayit.cu.edu.tr/DerseYazilma")
        WebDriverWait(driver, 5).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "td span.badge"))
        )
    except:
        update.message.reply_text(
            "❌ Session expired. Please login again using the /login command."
        )
        return
    
    # Get current course information
    try:
        current_courses = get_course_info(driver)
        if current_courses:
            message = "📚 Current Course Status:\n\n"
            for name, slots in current_courses.items():
                message += f"Course: {name}\n"
                message += f"Available Slots: {slots}\n"
                message += "-------------------\n"
            update.message.reply_text(message)
            
            # Update last check data
            last_check = current_courses
        else:
            update.message.reply_text("No course information available at the moment.")
    except Exception as e:
        logging.error(f"Error in initial course check: {str(e)}")
    
    is_subscribed = True
    update.message.reply_text(
        "✅ Successfully subscribed to course notifications!\n"
        "You will receive updates every 3 minutes when courses become available."
    )
    logging.info("New subscription activated")

def unsubscribe(update: Update, context: CallbackContext):
    """Unsubscribe from course availability notifications"""
    global driver, is_subscribed
    
    # Clean up driver
    if driver:
        try:
            driver.quit()
        except:
            pass
        driver = None
    
    is_subscribed = False
    update.message.reply_text("✅ Successfully unsubscribed from notifications.")
    logging.info("Unsubscribed from notifications")

def main():
    """Main function to run the bot"""
    # Load environment variables
    load_dotenv()
    
    # Configure logging
    logging.basicConfig(
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        level=logging.INFO
    )
    
    # Start Flask in a separate thread
    flask_thread = threading.Thread(target=run_flask)
    flask_thread.daemon = True
    flask_thread.start()
    
    # Initialize bot
    updater = Updater(token=os.getenv('TELEGRAM_BOT_TOKEN'))
    dispatcher = updater.dispatcher
    
    # Add conversation handler for login
    conv_handler = ConversationHandler(
        entry_points=[CommandHandler('login', login)],
        states={
            WAITING_USERNAME: [MessageHandler(Filters.text & ~Filters.command, get_username)],
            WAITING_PASSWORD: [MessageHandler(Filters.text & ~Filters.command, get_password)],
        },
        fallbacks=[CommandHandler('cancel', cancel)],
    )
    
    # Add handlers
    dispatcher.add_handler(CommandHandler("start", start))
    dispatcher.add_handler(conv_handler)
    dispatcher.add_handler(CommandHandler("stop", stop))
    dispatcher.add_handler(CommandHandler("subscribe", subscribe))
    dispatcher.add_handler(CommandHandler("unsubscribe", unsubscribe))
    
    # Add job queue
    job_queue = updater.job_queue
    job_queue.run_repeating(check_courses, interval=180, first=0, context=dispatcher.bot.id)
    
    # Start the bot
    updater.start_polling()
    updater.idle()
    
    # Clean up driver
    global driver
    if driver:
        try:
            driver.quit()
        except:
            pass

if __name__ == '__main__':
    main() 