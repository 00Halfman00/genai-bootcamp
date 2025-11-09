import json
import boto3
import os
from pydantic import BaseModel, Field
from strands import Agent
import uuid

model_id = os.environ.get("MODEL_ID", "")
s3_client = boto3.client("s3")

agent = Agent(model=model_id, callback_handler=None)


class ValidationResult(BaseModel):
    """Model that contains the validation result for a bank statement"""

    is_bank_statement: bool = Field(
        description="Whether the document is a bank statement"
    )


def validate_bank_statement(document: bytes) -> bool:
    """
    Validates if a document is a bank statement using structured output.
    """
    validator_prompt = """
Is this document a bank statement?

You MUST respond with only a single, valid JSON object with a single key "is_bank_statement" and a boolean value. Do not include any other text, explanations, or markdown formatting.
"""

    response = None
    try:
        response = agent(
            [
                {"text": validator_prompt},
                {
                    "document": {
                        "format": "pdf",
                        "name": f"check-{uuid.uuid4()}",
                        "source": {
                            "bytes": document,
                        },
                    },
                },
            ],
            structured_output_model=ValidationResult,
        )

        raw_response_text = str(response)
        print(f"Raw LLM response for validation: {raw_response_text}")

        # Manually find and parse the JSON from the raw response
        json_start = raw_response_text.find("{")
        json_end = raw_response_text.rfind("}") + 1
        if json_start == -1 or json_end == 0:
            raise ValueError("No JSON object found in the response.")

        cleaned_json_str = raw_response_text[json_start:json_end]

        parsed_json = json.loads(cleaned_json_str)

        validation_result = ValidationResult(**parsed_json)

        print("Successfully parsed structured output for validation manually.")
        return validation_result.is_bank_statement

    except Exception as e:
        print(f"Could not extract and parse structured validation result: {e}")
        return False


def handler(event, context):
    """
    Lambda handler for Step Functions triggered by S3 PutObject events.

    Args:
        event: Step Functions event containing S3 object information
        context: Lambda context object

    Returns:
        dict: Contains the binary content of the uploaded document as bytes
    """
    try:
        # Extract S3 bucket and key from the event
        # The event structure will contain S3 event information
        if "Records" in event:
            # Direct S3 event trigger
            s3_event = event["Records"][0]
            bucket = s3_event["s3"]["bucket"]["name"]
            key = s3_event["s3"]["object"]["key"]
        else:
            # Step Functions input format
            bucket = event.get("bucket")
            key = event.get("key")

        if not bucket or not key:
            raise ValueError("Missing bucket or key in event")

        # Get the object from S3
        response = s3_client.get_object(Bucket=bucket, Key=key)

        # Read the binary content
        file_content = response["Body"].read()

        validation_result = validate_bank_statement(file_content)

        return {"bucket": bucket, "key": key, "valid": validation_result}

    except Exception as e:
        import traceback

        print("Handler in input_validator failed with exception:")
        traceback.print_exc()
        return {
            "statusCode": 500,
            "error": f"An exception occurred in the input_validator Lambda: {str(e)}",
        }


if __name__ == "__main__":
    # For local testing
    test_event = {"bucket": "test-bucket", "key": "test-document.pdf"}
    result = handler(test_event, None)
    print(json.dumps(result, default=str))
