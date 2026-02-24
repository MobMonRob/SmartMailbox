# Server

Server code for the thesis.

## Run

### Dev

In sever directory run:
```sh 
uvicorn app.main:app --reload
OR
python -m app.main
```

## Image processing

### Input

- prompt = "" 
- images/image_texts = []
- user_data = [{"name": "", "surname": "", "address": "", "id": 0, }] # TODO : define user data

### Returns

#### SUCCESS 
- number of best image
- ID of best user match or multiple IDs 
- message for user about mail details

#### FAIL 
- literal "FAIL"
- reason for failure # TODO for each household a default mail for failed operations

#### Definition SUCCESS vs FAIL

*SUCCESS:*
- found match
- found multiple matches

*FAIL:*
- cannot read text
- cannot find match for text with certainty > ? % # TODO test certainty level, also configurable

### Testing
- prompt
- images
   - categories (different types of images), different quality
   - define correct answers
- user_data
   - users used for images
   - similar users not used
- integration of models
- test infrastructure
   - ? number of iterations
   - save timings (for tesseract get two timings)
   - save answers
- 5 images of every mail in ordered quality
    - 1. llm answer for each image individually (Testing models against each other)
    - 2. llm answer for all 5 at once (Testing that capabilities do not get worse if low quality images are also part of the input)

#### Images
mail types: postcard, letter, letter with window
writing: printed, handwriting, cursive handwriting
receivers: one, family, multiple
image qualities: perfect, slightly blurred, flash visible, very blurred, cut off

#### User Data
- only matching the receiver
- only not matching the receiver
- matching multiple receivers (family/multiple recipients)
- receiver and other person names are somewhat similar
- receiver and other person names are completely different
- receiver and other person names are very similar
- two persons with same name, so there is no correct answer # TODO What should be the correct answer if two people have the same name


## Database

### Configuration
tbd

### Recipients
- id (Int, key)
- firstname (Text)
- middlename (Text)
- surname (Text)
- title (Text)
- email (Text | NULL (household email is used))
- household (Int, foreign key -> Households)

### Households
- id (Int, key)
- email (Text) # default if failed match
- country (Text)
- zipcode (Text)
- city (Text)
- street (Text)
- house_number (Text)

### ModelTestResults
- (index)
- time (Real)
- tesseract_time (Real | NULL)
- llama_time (Real | NULL)
- match_found ("SUCCESS" | "FAIL")
- correct_answer (Bool) # all found recipient ids match all recipient ids for the test_case in the TestRecipientSolutions table
- test_id (Int, foreign key -> ModelTests.id)
- complete_response (Text)

### ModelTests
- id (Int, key)
- model (Int, foreign key -> Models.id)
- test_case_id (Int, foreign key -> TestCases.id)

### Models
- id (Int, key)
- name (Text) # llama-maverick, llama-scout, qwen3-vl:8b(/4b/32b), qwen3-vl:8b-thinking
- family ("Qwen3" | "Llama")

### TestCases
- id (Int, key)
- letter_id (Int, foreign key -> Letters.id)
- image_selection ("ALL" | "PERFECT" |  "SLIGHTLY_BLURRED" | "FLASH_VISIBLE" | "VERY_BLURRED" | "CUT_OFF")
- household_id (Int, foreign key)

### Prompts
- (index)
- model ("Qwen3" | "Llama", foreign key -> Models.family)
- prompt (Text)

### TestRecipientSolutions
- test_case_id (Int, foreign key, not unique)
- recipient_id (Int, foreign key, not unique)

### Letters
- id (Int, key)
 
### LetterQuality
- (index)
- letter_id (Int, foreign key -> Letters.id)
- quality ("PERFECT" | "SLIGHTLY_BLURRED" | "FLASH_VISIBLE" | "VERY_BLURRED" | "CUT_OFF")
- image_path (Text)