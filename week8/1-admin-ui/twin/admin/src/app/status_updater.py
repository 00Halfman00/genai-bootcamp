import os
import boto3
import logging

logger = logging.getLogger()
logger.setLevel(logging.INFO)

dynamodb = boto3.resource('dynamodb')
table_name = os.environ.get('DDB_TABLE')
if not table_name:
    raise ValueError("DDB_TABLE environment variable is not set.")
table = dynamodb.Table(table_name)

def handler(event, context):
    """
    This function is triggered by an EventBridge rule when a Bedrock Knowledge
    Base ingestion job changes state.

    If the job has completed successfully, it updates all answered questions
    in the DynamoDB table to have `processed = True`.
    """
    logger.info(f"Received event: {event}")

    job_status = event.get('detail', {}).get('status')

    if job_status == 'COMPLETED':
        logger.info("Ingestion job completed. Marking all answered questions as processed.")
        try:
            # Get all questions from DynamoDB
            response = table.query(
                KeyConditionExpression=boto3.dynamodb.conditions.Key('PK').eq('QUESTIONS')
            )
            all_questions = response.get('Items', [])
            logger.info(f"Found {len(all_questions)} total questions.")

            # Filter for answered questions that are not yet processed
            answered_questions = [
                q for q in all_questions
                if 'answer' in q and q['answer'] and not q.get('processed', False)
            ]
            logger.info(f"Found {len(answered_questions)} answered questions to mark as processed.")

            if not answered_questions:
                logger.info("No questions to update.")
                return {'statusCode': 200, 'body': 'No questions to update.'}

            # Mark them as processed
            with table.batch_writer() as batch:
                for q in answered_questions:
                    q['processed'] = True
                    batch.put_item(Item=q)

            logger.info(f"Successfully marked {len(answered_questions)} questions as processed.")

        except Exception as e:
            logger.error(f"Error updating questions in DynamoDB: {e}", exc_info=True)
            raise
    
    elif job_status == 'FAILED':
        logger.error(f"Ingestion job failed. Details: {event.get('detail', {})}")
        # You could add logic here to notify an administrator.

    else:
        logger.info(f"Ingestion job status is '{job_status}'. No action taken.")

    return {
        'statusCode': 200,
        'body': 'Status update processed.'
    }
