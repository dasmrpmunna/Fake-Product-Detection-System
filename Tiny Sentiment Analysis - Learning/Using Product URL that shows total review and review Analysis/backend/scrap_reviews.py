from flask import Flask, request, jsonify
from flask_cors import CORS
import time
import pandas as pd
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager

app = Flask(__name__)
CORS(app)  # Enable CORS

# Fake Review Detection Model (Placeholder)
def detect_fake_reviews(df):
    """Fake review detection logic"""
    fake_reviews_count = 0
    total_reviews = len(df)

    for _, row in df.iterrows():
        review = row["customer_review"]
        rating = row["customer_rating"]

        # Simple rule-based logic (replace with ML model)
        if rating >= 4 and "bad" in review.lower():
            fake_reviews_count += 1
        elif rating <= 2 and "good" in review.lower():
            fake_reviews_count += 1

    fake_percentage = (fake_reviews_count / total_reviews) * 100 if total_reviews > 0 else 0
    product_status = "Fake" if fake_percentage >= 50 else "Likely Fake" if fake_percentage >= 25 else "Genuine"

    return {
        "total_reviews": total_reviews,
        "fake_reviews_count": fake_reviews_count,
        "fake_percentage": round(fake_percentage, 2),
        "product_status": product_status
    }

@app.route('/analyze', methods=['POST'])
def analyze_product():
    data = request.json
    if not data or 'url' not in data:
        return jsonify({"error": "No URL provided"}), 400

    url = data['url']

    # Set up Selenium WebDriver
    chrome_options = Options()
    chrome_options.add_argument("--headless")  # Run in headless mode
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")

    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=chrome_options)

    try:
        driver.get(url)
        time.sleep(5)  # Wait for page to load

        reviews = []
        ratings = []

        # Extract product name (Modify selector based on site)
        try:
            product_name = driver.find_element(By.CSS_SELECTOR, "span.B_NuCI").text.strip()
        except:
            product_name = "Unknown Product"

        page_count = 0  # Track number of pages scraped

        while page_count < 3:  # Limit to 3 pages
            page_count += 1  # Increase page count

            # Scrape ratings
            rating_elements = driver.find_elements(By.CSS_SELECTOR, "div.XQDdHH.Ga3i8K")
            ratings.extend([float(rating.text.strip()) for rating in rating_elements if rating.text.strip().isdigit()])

            # Scrape reviews
            review_elements = driver.find_elements(By.CSS_SELECTOR, "p.z9E0IG")
            reviews.extend([review.text.strip() for review in review_elements])

            # Try to find and click the "Next" button
            try:
                next_button = driver.find_element(By.CSS_SELECTOR, "a._9QVEpD")  # Adjust selector
                driver.execute_script("arguments[0].click();", next_button)
                time.sleep(5)  # Wait for next page to load
            except:
                break  # If no next button, exit loop

        # Convert to DataFrame
        if len(reviews) > len(ratings):
            ratings.extend([0] * (len(reviews) - len(ratings)))  # Fill missing ratings with 0

        df = pd.DataFrame({"customer_review": reviews, "customer_rating": ratings})

        # Run Fake Review Detection
        analysis_result = detect_fake_reviews(df)

        return jsonify({
            "product_name": product_name,
            **analysis_result
        })

    except Exception as e:
        return jsonify({"error": str(e)}), 500

    finally:
        driver.quit()  # Always quit the browser

if __name__ == '__main__':
    app.run(debug=True)  # Run the Flask API
