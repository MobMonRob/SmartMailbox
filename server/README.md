# Server

Server code for the thesis.

# Database

## Configuration

## Recipients
- id (Int)
- firstname (Text)
- middlename (Text)
- surname (Text)
- title (Text)
- country (Text)
- zipcode (Text)
- city (Text)
- street (Text)
- house_number (Text)
- email (Text)
- household (Int)

## Household
- id (Int)
- email (Text) # default if failed match

## ModelTestResults
- (index)
- model (Qwen3 | TesseractOllama)
- start_time (Timestamp)
- tesseract_middle_time (Timestamp | Null)
- end_time (Timestamp)
- match_found (Bool)
- correct_answer (Bool)
- test_id (Int)
- complete_response (Text)

## ModelTests
- id (Int)
- image_paths (Text[])
- correct_recipient_ids (Int[])

## (Images)
- id (Int ordered)
- path (Text) / image (BLOB)