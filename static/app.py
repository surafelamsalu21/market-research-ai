# market-research-ai/app.py
from fpdf import FPDF
import matplotlib.pyplot as plt
import os
from flask import Flask, render_template, request, jsonify, send_file
from flask_cors import CORS  # Added for CORS support
import io
from retrying import retry
import openai
from werkzeug.utils import secure_filename
from dotenv import load_dotenv
import logging
import requests
import json

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(filename='app.log', level=logging.ERROR)

app = Flask(__name__)
CORS(app)  # Enable CORS for all routes

# Configure upload folder
UPLOAD_FOLDER = 'uploads'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

# Configure API keys
openai_api_key = os.getenv('OPENAI_API_KEY')
perplexity_api_key = os.getenv('PERPLEXITY_API_KEY')

# Initialize OpenAI client
openai.api_key = openai_api_key

if not openai_api_key:
    logging.error("OPENAI_API_KEY is not set.")
    raise EnvironmentError("OPENAI_API_KEY is not set.")

if not perplexity_api_key:
    logging.error("PERPLEXITY_API_KEY is not set.")
    raise EnvironmentError("PERPLEXITY_API_KEY is not set.")

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/upload', methods=['POST'])
def upload_file():
    if 'file' not in request.files:
        return jsonify({'error': 'No file part'}), 400
    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': 'No selected file'}), 400
    if file:
        filename = secure_filename(file.filename)
        file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
        print(f"File uploaded: {filename}")  # Debug print
        return jsonify({'message': 'File uploaded successfully'}), 200

PERPLEXITY_API_URL = "https://api.perplexity.ai/chat/completions"

@retry(stop_max_attempt_number=3, wait_fixed=2000)
def query_perplexity_ai(prompt):
    headers = {
        "Authorization": f"Bearer {perplexity_api_key}",
        "Content-Type": "application/json"
    }
    data = {
        "model": "llama-3.1-sonar-small-128k-online",  # Updated to a supported model
        "messages": [{"role": "user", "content": prompt}],
        "max_tokens": 1000,  # Optional: specify as needed
        "temperature": 0.7  # Optional: adjust for response randomness
    }
    try:
        response = requests.post(PERPLEXITY_API_URL, json=data, headers=headers)
        response.raise_for_status()
        print(f"Perplexity AI response: {response.status_code}")  # Debug print
        return response.json()['choices'][0]['message']['content']
    except requests.exceptions.HTTPError as http_err:
        print(f"HTTP error occurred: {http_err}")  # HTTP error
        print(f"Response content: {response.text}")  # Log response content
        raise
    except requests.exceptions.RequestException as e:
        print(f"Error querying Perplexity AI: {str(e)}")  # Other errors
        raise

def generate_market_analysis_questions(product_service, target_geography, audience, industry):
    prompt = f"""
    Generate three comprehensive questions each for analyzing the TAM, SAM, and SOM for a business offering {product_service} in {target_geography} targeting {audience} in the {industry} industry.
    
    For TAM: Focus on global market size and growth potential.
    For SAM: Focus on regional market size, adoption trends, and target demographics.
    For SOM: Focus on competitive analysis, pricing models, and market share projections.
    
    Format the output as a JSON object with keys 'tam_questions', 'sam_questions', and 'som_questions', each containing an array of three questions.
    """
    
    try:
        response = openai.ChatCompletion.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": "You are a market research expert generating questions for TAM, SAM, and SOM analysis."},
                {"role": "user", "content": prompt}
            ]
        )
        print("Market analysis questions generated successfully")  # Debug print
        return response.choices[0].message.content
    except Exception as e:
        logging.error(f"Error in OpenAI API call: {str(e)}")
        print(f"Error generating market analysis questions: {str(e)}")  # Debug print
        return None

def get_market_data(questions, product_service, target_geography, industry):
    prompts = [
        f"Find real-time data for {industry} in {target_geography}. Focus on the global market size, growth rate, and key trends. Provide reliable sources for each data point, citing the original source. Address the following questions:\n{questions['tam_questions']}",
        f"Gather market data specific to {target_geography} for {product_service}. Identify regional market share of the global market, and specify relevant adoption rates, growth trends, and opportunities. Provide full citations for each source. Address the following questions:\n{questions['sam_questions']}",
        f"Identify the serviceable obtainable market (SOM) for {product_service} in {target_geography}. Focus on competitor analysis, pricing models, and adoption rates, and provide market penetration estimates for the next 5 years. Source all data. Address the following questions:\n{questions['som_questions']}"
    ]

    market_data = []
    for i, prompt in enumerate(prompts):
        try:
            response = query_perplexity_ai(prompt)
            market_data.append(response)
            print(f"Market data {i+1} retrieved successfully")  # Debug print
        except Exception as e:
            logging.error(f"Error querying Perplexity AI: {str(e)}")
            print(f"Error retrieving market data {i+1}: {str(e)}")  # Debug print
            market_data.append(None)

    return market_data

def analyze_market_data(market_data, product_service, target_geography, industry):
    analysis_prompt = f"""
    Analyze the following market data for {product_service} in {target_geography} ({industry}):

    TAM Data:
    {market_data[0]}

    SAM Data:
    {market_data[1]}

    SOM Data:
    {market_data[2]}

    Provide a comprehensive market analysis including:
    1. TAM, SAM, and SOM estimates with justifications
    2. Key market trends and growth projections
    3. Competitive landscape analysis
    4. Potential strategies for market entry or expansion
    5. Risks and opportunities in the market

    **Format the response strictly as a JSON object with the following structure:**
    {{
        "tam": "...",
        "sam": "...",
        "som": "..."
    }}

    Do not include any additional text or explanations outside of this JSON object.
    """

    try:
        response = openai.ChatCompletion.create(
            model="gpt-4",
            messages=[
                {
                    "role": "system",
                    "content": "You are a market research expert providing insights on TAM, SAM, and SOM."
                },
                {
                    "role": "user",
                    "content": analysis_prompt
                }
            ]
        )
        print("Market data analysis completed successfully")  # Debug print

        analysis_json = response.choices[0].message.content
        print("Analysis JSON:", analysis_json)  # Debug print

        # Parse the JSON string into a Python dictionary
        analysis_data = json.loads(analysis_json)
        return analysis_data
    except json.JSONDecodeError as json_err:
        logging.error(f"JSON decode error: {str(json_err)}")
        print(f"Error decoding JSON: {str(json_err)}")  # Debug print
        return None
    except Exception as e:
        logging.error(f"Error in OpenAI API call: {str(e)}")
        print(f"Error analyzing market data: {str(e)}")  # Debug print
        return None

@app.route('https://yappy-vivienne-surafelamsalu-d8298ba0.koyeb.app/analyze', methods=['POST'])
def analyze_market():
    try:
        # Retrieve form data
        country = request.form.get('country')
        target_geography = request.form.get('target_geography')
        audience_persona = request.form.get('audience_persona')
        product_service = request.form.get('product_service')
        industry = request.form.get('industry')

        print(f"Analyzing market for {product_service} in {target_geography}")  # Debug print

        # Generate questions
        questions = generate_market_analysis_questions(product_service, target_geography, audience_persona, industry)
        if not questions:
            raise Exception("Failed to generate market analysis questions")

        questions = json.loads(questions)

        # Get market data
        market_data = get_market_data(questions, product_service, target_geography, industry)
        if not all(market_data):
            raise Exception("Failed to retrieve market data")

        # Analyze market data
        analysis_result = analyze_market_data(market_data, product_service, target_geography, industry)
        if not analysis_result:
            raise Exception("Failed to analyze market data")

        print("Market analysis completed successfully")  # Debug print

        return jsonify(analysis_result), 200  # Return as JSON response
    except Exception as e:
        logging.error(f"Error in analysis: {str(e)}")
        print(f"Error in market analysis: {str(e)}")  # Debug print
        return jsonify({'error': str(e)}), 500

# Function to generate PDF report with market analysis and graphs
def generate_pdf_report(analysis_data, product_service, target_geography, industry):
    # Create a PDF object
    pdf = FPDF()
    pdf.set_auto_page_break(auto=True, margin=15)
    pdf.add_page()

    # Add a title
    pdf.set_font("Arial", size=16, style='B')
    pdf.cell(200, 10, txt="Market Analysis Report", ln=True, align="C")

    # Add detailed market analysis sections (TAM, SAM, SOM)
    pdf.ln(10)
    pdf.set_font("Arial", size=12, style='B')
    pdf.cell(200, 10, txt=f"Product/Service: {product_service}", ln=True)
    pdf.cell(200, 10, txt=f"Target Geography: {target_geography}", ln=True)
    pdf.cell(200, 10, txt=f"Industry: {industry}", ln=True)

    pdf.ln(10)
    pdf.set_font("Arial", size=12, style='B')
    pdf.cell(200, 10, txt="TAM Analysis:", ln=True)
    pdf.set_font("Arial", size=12)
    pdf.multi_cell(0, 10, txt=analysis_data.get('tam', 'N/A'))

    pdf.ln(5)
    pdf.set_font("Arial", size=12, style='B')
    pdf.cell(200, 10, txt="SAM Analysis:", ln=True)
    pdf.set_font("Arial", size=12)
    pdf.multi_cell(0, 10, txt=analysis_data.get('sam', 'N/A'))

    pdf.ln(5)
    pdf.set_font("Arial", size=12, style='B')
    pdf.cell(200, 10, txt="SOM Analysis:", ln=True)
    pdf.set_font("Arial", size=12)
    pdf.multi_cell(0, 10, txt=analysis_data.get('som', 'N/A'))

    # Add a graph
    plt.figure(figsize=(6,6))
    data = {
        'TAM': 30,  # Example data, replace with actual percentages if available
        'SAM': 40,
        'SOM': 30
    }
    labels = list(data.keys())
    sizes = list(data.values())
    plt.pie(sizes, labels=labels, autopct='%1.1f%%', startangle=140)
    plt.title('Market Share Distribution')
    plt.axis('equal')

    # Save the plot to a BytesIO buffer and add it to the PDF
    image_stream = io.BytesIO()
    plt.savefig(image_stream, format='png')
    plt.close()
    image_stream.seek(0)
    pdf.image(image_stream, x=10, y=pdf.get_y() + 10, w=100)

    # Output the PDF as a BytesIO stream to return it as a response
    pdf_output = io.BytesIO()
    pdf.output(pdf_output)
    pdf_output.seek(0)

    return pdf_output

# New route to download the PDF report
@app.route('/download_pdf', methods=['POST'])  # Ensure this matches the frontend
def download_pdf():
    try:
        data = request.get_json()

        if not data:
            return jsonify({"error": "No data provided"}), 400

        analysis_data = data.get('analysis_data')  # Ensure your frontend sends 'analysis_data'
        product_service = data.get('product_service')
        target_geography = data.get('target_geography')
        industry = data.get('industry')

        if not all([analysis_data, product_service, target_geography, industry]):
            return jsonify({"error": "Missing required fields"}), 400

        # Generate the PDF report
        pdf_output = generate_pdf_report(analysis_data, product_service, target_geography, industry)

        # Return the PDF as a downloadable file
        return send_file(
            pdf_output,
            as_attachment=True,
            download_name="Market_Analysis_Report.pdf",
            mimetype='application/pdf'
        )
    except Exception as e:
        logging.error(f"Error generating PDF report: {str(e)}")
        print(f"Error generating PDF report: {str(e)}")  # Debug print
        return jsonify({"error": "Failed to generate PDF report"}), 500

if __name__ == '__main__':
     app.run(host='0.0.0.0', port=8080)
