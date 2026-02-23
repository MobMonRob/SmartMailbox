# Server

Server code for the thesis.

# Run

## Dev

In sever directory run:
```sh 
uvicorn app.main:app --reload
OR
python -m app.main
```


# Database

## Configuration

## Recipients
- id (Int, key)
- firstname (Text)
- middlename (Text)
- surname (Text)
- title (Text)
- email (Text | NULL (household email is used))
- household (Int, foreign key -> Households)

## Households
- id (Int, key)
- email (Text) # default if failed match
- country (Text)
- zipcode (Text)
- city (Text)
- street (Text)
- house_number (Text)

## ModelTestResults
- (index)
- start_time (Timestamp)
- tesseract_middle_time (Timestamp | Null)
- end_time (Timestamp)
- match_found ("SUCCESS" | "FAIL")
- correct_answer (Bool) # all found recipient ids match all recipient ids for the test_case in the TestRecipientSolutions table
- test_id (Int, foreign key -> ModelTests.id)
- complete_response (Text)

## ModelTests
- id (Int, key)
- model (Int, foreign key -> Models.id)
- test_case_id (Int, foreign key -> TestCases.id)

## Models
- id (Int, key)
- name (Text) # llama-maverick, llama-scout, qwen3-vl:8b(/4b/32b), qwen3-vl:8b-thinking
- family ("Qwen3" | "Llama")

## TestCases
- id (Int, key)
- letter_id (Int, foreign key -> Letters.id)
- image_selection ("ALL" | "PERFECT" |  "SLIGHTLY_BLURRED" | "FLASH_VISIBLE" | "VERY_BLURRED" | "CUT_OFF")
- household_id (Int, foreign key)

## Prompts
- (index)
- model ("Qwen3" | "Llama", foreign key -> Models.family)
- prompt (Text)

## TestRecipientSolutions
- test_case_id (Int, foreign key, not unique)
- recipient_id (Int, foreign key, not unique)

## Letters
- id (Int, key)
 
## LetterQuality
- (index)
- letter_id (Int, foreign key -> Letters.id)
- quality ("PERFECT" | "SLIGHTLY_BLURRED" | "FLASH_VISIBLE" | "VERY_BLURRED" | "CUT_OFF")
- image_path (Text)