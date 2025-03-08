# E-Commerce Data Analysis Dashboard

This project analyzes an e-commerce public dataset to explore trends in sales, revenue, product categories, and customer behavior.

## Project Structure

```
submission
├───dashboard
| ├───main_data.csv
| └───dashboard.py
├───data
| ├───data_1.csv
| └───data_2.csv
├───notebook.ipynb
├───README.md
└───requirements.txt
└───url.txt
```

## Running the Dashboard

1. Make sure you have Python 3.8+ installed
2. Install the required packages:
```
pip install -r requirements.txt
```
3. Navigate to the dashboard directory:
```
cd dashboard
```
4. Run the Streamlit dashboard:
```
streamlit run dashboard.py
```
5. The dashboard should open automatically in your default web browser at `http://localhost:8501`

## Dashboard Features

The dashboard includes:

1. **Overview**: Key metrics and charts summarizing the dataset
2. **Sales & Revenue Trends**: Visualizations of order count and revenue over time
3. **Product Category Analysis**: Best and worst performing product categories
4. **Customer Analysis**: Customer distribution and RFM (Recency, Frequency, Monetary) analysis
5. **Additional Insights**: Delivery performance, payment methods, and review scores

## Data Analysis Process

The data analysis was performed in the Jupyter notebook (`notebook.ipynb`), which:
1. Loads and cleans the e-commerce dataset
2. Performs exploratory data analysis
3. Creates visualizations to answer key business questions
4. Exports the processed data to `main_data.csv` for the dashboard

## Author

- **Name:** Dias Utsman
- **Email:** utsmand91@gmail.com
- **ID Dicoding:** dias_utsman