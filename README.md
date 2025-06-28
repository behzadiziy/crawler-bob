# Crawler-Bob

A Python-based web crawler designed to scrape product information from WooCommerce category pages. This script interactively prompts for a category URL and a scrape limit, extracts detailed product data, and sends it to a specified API endpoint for further processing.

It is specifically tailored for WooCommerce sites using themes like Woodmart (e.g., `bobesfanjishop.com`) but can be adapted for others.

---

## Features

-   **Interactive & User-Friendly**: No need to edit code or use command-line arguments. The script interactively asks for the target URL and the number of products to scrape.
-   **Category-Level Scraping**: Fetches all product links from a category page and processes them sequentially.
-   **Duplicate Prevention**: Keeps a log (`scraped_urls.log`) of all previously processed products to ensure it only scrapes new items on subsequent runs.
-   **Detailed Data Extraction**: Scrapes essential product data, including:
    -   Product Name
    -   Price
    -   Full HTML Description (from the main description tab)
    -   Product Attributes (from the "Additional Information" table)
    -   All Product Images (handling lazy-loaded images)
    -   SKU
-   **API Integration**: Sends the cleanly structured data for each scraped product to a specified API endpoint.
-   **Configurable**: API credentials are managed securely via a `.env` file.

---

## Requirements

-   Python 3.7+
-   pip (Python package installer)

---

## ⚙️ Installation & Setup

Follow these steps to get the crawler running on your local machine.

**1. Clone the Repository**

```bash
git clone https://github.com/your-username/crawler-bob.git
cd crawler-bob
```
*(Replace `your-username` with your actual GitHub username.)*

**2. Create a Virtual Environment (Recommended)**

A virtual environment keeps your project's dependencies isolated.

-   **On macOS / Linux:**
    ```bash
    python3 -m venv venv
    source venv/bin/activate
    ```

-   **On Windows:**
    ```bash
    python -m venv venv
    venv\Scripts\activate
    ```

**3. Install Dependencies**

This project's dependencies are listed in `requirements.txt`.

```bash
pip install -r requirements.txt
```
*(If a `requirements.txt` file doesn't exist, create one with the following content)*:
```
# requirements.txt
requests
beautifulsoup4
python-dotenv
```

**4. Configure Environment Variables**

The script uses a `.env` file to store your secret API credentials.

-   First, create a `.env` file by copying the example file:
    ```bash
    cp .env.example .env
    ```
-   Now, open the `.env` file with a text editor and add your API details:

    ```env
    # .env file

    # The full URL of the API endpoint that will receive the scraped product data
    API_URL="http://your-laravel-app.com/api/products"

    # The secret API key for authenticating with your API
    API_KEY="your_secret_api_key_here"
    ```

---

## ▶️ How to Run the Crawler

The script runs in interactive mode.

**1. Execute the Script**

Run the following command in your terminal (make sure your virtual environment is activated):

```bash
python crawler.py
```

**2. Follow the Prompts**

The script will ask you for the necessary information:

-   First, it will ask for the category URL. Paste the full URL of the product category page you want to scrape and press Enter.

    ```
    --- 🚀 Interactive Category Crawler ---
    Please enter the URL of the product category page to scrape:
    > https://bobesfanjishop.com/product-category/sunglasses/
    ```

-   Next, it will ask for the number of new products to process in this run.

    ```
    How many new products should be scraped from this category? (Enter a number):
    > 5
    ```

**3. Let it Run**

The crawler will then start fetching the category page, identifying new products, and scraping them one by one according to the limit you set.

---

## 📁 Project Structure

```
crawler-bob/
├── .env              # Your local environment configuration (created by you)
├── .env.example      # An example configuration file
├── crawler.py        # The main interactive crawler script
├── requirements.txt  # Python dependencies
├── scraped_urls.log  # A log of all scraped product URLs (created automatically)
└── README.md         # This file
```

---

## 📄 License

This project is licensed under the MIT License. See the `LICENSE` file for details.