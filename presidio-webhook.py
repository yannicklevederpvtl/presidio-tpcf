from flask import Flask, request, jsonify
import os
from presidio_analyzer import AnalyzerEngine
from presidio_anonymizer import AnonymizerEngine

app = Flask(__name__)

# Initialize Presidio engines
analyzer = AnalyzerEngine()
anonymizer = AnonymizerEngine()

def anonymize_text(text):
    """
    Anonymize sensitive information in the given text using Presidio.
    """
    # Analyze the text to find sensitive information
    analysis_results = analyzer.analyze(
        text=text,
        entities=None,
        language='en'
    )

    # Anonymize the identified sensitive information
    anonymized_result = anonymizer.anonymize(
        text=text,
        analyzer_results=analysis_results
    )

    return anonymized_result.text

@app.route('/prompt', methods=['POST'])
def handle_chat_completion_request():
    """
    Handle incoming chat completion requests.
    Expects OpenAI API format for chat completion requests.
    """
    # Get the request payload
    request_data = request.get_json()

    # Log the incoming request (optional)
    print("Received chat completion request:", request_data)

    # Process messages if they exist in the request
    if 'messages' in request_data:
        for message in request_data['messages']:
            if 'content' in message and message['content']:
                # Anonymize the content of each message
                message['content'] = anonymize_text(message['content'])

    # Log the anonymized request
    print("Anonymized request data:", request_data)

    return jsonify(request_data)

@app.route('/response', methods=['POST'])
def handle_chat_completion_response():
    """
    Handle chat completion responses.
    Expects OpenAI API format for chat completion responses.
    """
    # Get the response payload
    response_data = request.get_json()

    # Log the incoming response (optional)
    print("Received chat completion response:", response_data)

    # Process the response content if it exists
    if 'choices' in response_data:
        for choice in response_data['choices']:
            if 'message' in choice and 'content' in choice['message']:
                # Anonymize the content of the response
                choice['message']['content'] = anonymize_text(choice['message']['content'])

    # Log the anonymized response
    print("Anonymized response data:", response_data)

    return jsonify(response_data)

if __name__ == '__main__':
    port = int(os.getenv('PORT', 8080))
    app.run(host='0.0.0.0', port=port)