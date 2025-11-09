import json
import boto3
import os
from pydantic import BaseModel, Field
from strands import Agent
import uuid

model_id = os.environ.get("MODEL_ID", "")
s3_client = boto3.client("s3")

agent = Agent(model=model_id, callback_handler=None)


class BankStatementData(BaseModel):
    """Model that contains information extracted from a bank statement"""

    BankName: str = Field(description="Name of the bank")
    AccountNumber: str = Field(description="Account number")
    OpeningBalance: float = Field(description="Opening balance")
    ClosingBalance: float = Field(description="Closing balance")
    StartDate: str = Field(description="Start date of the statement period")
    EndDate: str = Field(description="End date of the statement period")


def extract_bank_statement_data(document: bytes) -> dict:
    """
    Extracts structured data from a bank statement document.
    """
    extractor_prompt = """
Analyze the provided bank statement document and extract the following fields: BankName, AccountNumber, OpeningBalance, ClosingBalance, StartDate, and EndDate.

You MUST respond with only a single, valid JSON object containing the extracted data. Do not include any other text, explanations, or markdown formatting.
"""
    response = None
    try:
        response = agent(
            [
                {"text": extractor_prompt},
                {
                    "document": {
                        "format": "pdf",
                        "name": f"bank_statement-{uuid.uuid4()}",
                        "source": {
                            "bytes": document,
                        },
                    },
                },
            ],
            structured_output_model=BankStatementData,
        )

        raw_response_text = str(response)
        print(f"Raw LLM response for extraction: {raw_response_text}")

        # Manually find and parse the JSON from the raw response
        json_start = raw_response_text.find('{')
        json_end = raw_response_text.rfind('}') + 1
        if json_start == -1 or json_end == 0:
            raise ValueError("No JSON object found in the response.")
        
        cleaned_json_str = raw_response_text[json_start:json_end]
        
        parsed_json = json.loads(cleaned_json_str)
        
        # Validate the parsed JSON with the Pydantic model
        bank_statement_data = BankStatementData(**parsed_json)
        
        print("Successfully parsed and validated structured output for extraction manually.")
        return bank_statement_data.model_dump()

    except Exception as e:
        print(f"Could not extract and parse structured extraction result: {e}")
        return {}


def handler(event, context):
    """
    Lambda handler for document extraction.
    """
    try:
        print("Extracting document data...")
        print(f"Event: {json.dumps(event)}")

        bucket = event["bucket"]
        key = event["key"]

        # Get the object from S3
        response = s3_client.get_object(Bucket=bucket, Key=key)

        # Read the binary content
        file_content = response["Body"].read()

        extracted_data = extract_bank_statement_data(file_content)

        is_valid = bool(extracted_data)

        return {
            "bucket": bucket,
            "key": key,
            "valid": is_valid,
            "extracted_data": extracted_data,
            "retry_count": event.get("retry_count", 0) + 1,
        }
    except Exception as e:
        import traceback

        print("Handler in extractor failed with exception:")
        traceback.print_exc()
        # Return a failure response that can be handled by the next step
        return {
            "bucket": event.get("bucket"),
            "key": event.get("key"),
            "valid": False,
            "extracted_data": {},
            "retry_count": event.get("retry_count", 0) + 1,
            "error": str(e),
        }