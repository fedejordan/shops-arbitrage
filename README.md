# Shops Arbitrage Platform

Welcome to the Shops Arbitrage project! This platform helps you compare product prices from major Argentinian retailers (Frávega, Garbarino, Musimundo, Coto, Jumbo, and more) so you can always find the best deal.

---

## 🚀 What does this project do?
- **Search and compare** products from multiple stores in one place.
- **Track price history** to see if it’s a good time to buy.
- **Discover discounts** and special offers.
- **Easy to use**: No technical knowledge required!

---

## 🖥️ How to use the platform

### 1. Frontend (Website)
- The website is where you search and compare products.
- **How to access:**
  - If the site is deployed, just visit the provided link (ask the project owner for the URL).
  - If you want to run it locally:
    1. Install [Node.js](https://nodejs.org/) (if you don’t have it).
    2. Open a terminal, go to the `frontend` folder, and run:
       ```bash
       npm install
       npm run dev
       ```
    3. Open [http://localhost:3000](http://localhost:3000) in your browser.

### 2. Backend (API)
- The backend powers the website and handles all the data.
- **How to start:**
    1. Make sure you have [Python 3.10+](https://www.python.org/) installed.
    2. Open a terminal, go to the `backend` folder, and run:
       ```bash
       pip install -r requirements.txt
       uvicorn main:app --reload
       ```
    3. The API will be available at [http://localhost:8000](http://localhost:8000)

### 3. Database
- All product and price data is stored in a PostgreSQL database.
- **How to set up:**
    1. Install [PostgreSQL](https://www.postgresql.org/download/).
    2. Create a database (e.g. `shops_arbitrage`).
    3. Run the SQL scripts in the `db/` folder to create the tables:
       - `schema.sql` (main structure)
       - Other `.sql` files for updates and extra features
    4. Make sure the backend can connect to your database. You may need to set an environment variable called `DATABASE_URL` (ask the project owner for details).

### 4. Scrapers (Getting the data)
- Scrapers collect product and price data from different stores.
- **How to run all scrapers:**
    1. Go to the `scrapers` folder in a terminal.
    2. Run:
       ```bash
       bash run-all-scrapers.sh
       ```
    3. This will update the database with the latest products and prices.

---

## 🧩 Project Structure
- `frontend/` – The website (Next.js, React)
- `backend/` – The API and business logic (Python, FastAPI)
- `db/` – Database schema and scripts (PostgreSQL)
- `scrapers/` – Scripts to collect data from stores

---

## 💡 Need help?
If you have any questions or need help, contact the project owner or check the documentation in each folder.

---

**Enjoy finding the best deals!**
