# Market Research AI

This Flask-based application automates the process of calculating Total Addressable Market (TAM), Serviceable Addressable Market (SAM), and Serviceable Obtainable Market (SOM) for businesses. It uses AI to analyze uploaded documents and user-provided business details to generate market size estimates.

## Setup

1. Clone the repository:
   ```
   git clone https://github.com/yourusername/market-research-ai.git
   cd market-research-ai
   ```

2. Create a virtual environment and activate it:
   ```
   python -m venv venv
   source venv/bin/activate  # On Windows, use `venv\Scripts\activate`
   ```

3. Install the required dependencies:
   ```
   pip install -r requirements.txt
   ```

4. Set up the environment variables:
   - Create a `.env` file in the root directory
   - Add your API keys to the `.env` file:
     ```
     OPENAI_API_KEY=your_openai_api_key
     GOOGLE_CLOUD_API_KEY=your_google_cloud_api_key
     ```

## Running the Application

1. Start the Flask application:
   ```
   flask run
   ```

2. Open a web browser and navigate to `http://localhost:5000` to access the web interface.

## Usage

1. Upload relevant market research documents using the file upload feature on the web interface.

2. Input your business details in the provided form, including:
   - Business name
   - Industry
   - Product or service description
   - Target market

3. Click the "Generate Market Size Estimates" button to process your inputs.

4. The system will analyze the uploaded documents and your business details to generate TAM, SAM, and SOM estimates.

5. Review the results displayed on the web interface, which will include market size estimates and relevant insights extracted from the analyzed documents.

## Note

Ensure that your API keys are kept secure and not shared publicly. The `.env` file is included in the `.gitignore` to prevent accidental exposure of sensitive information.
# market-research-ai
