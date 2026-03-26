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

```json
{
  "success": boolean, // true = success, false = fail
  "recipient_ids": [], // Comma-separated List of matched IDs: [1,2,3]
  "best_image_id": number,
  "fail_reason": string // reason for failure 
}
```

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

mail types: postcard, letter, letter with window \
writing: printed, handwriting, cursive handwriting \
receivers: one, family, multiple, wrong person, french receiver \
image qualities: perfect, slightly blurred, very blurred, cut off

*Naming convention*: l{letter_id}_{format}_{writing_style}_{quality}.png (e.g. l1_lpp.png, l10_pcv.png)
- letter_id: int
- format:
  - LETTER: l
  - POSTCARD: p
  - WINDOWED_LETTER: w
- writing_style:
  - PRINT: p
  - CURSIVE: c
  - HAND: h
- quality:
  - PERFECT: p
  - SLIGHTLY_BLURRED: s
  - VERY_BLURRED: v
  - CUT_OFF: c

cmd: 
```
rpicam-still -o l0_lhp -e png -t 1500
```

#### User Data

- only matching the receiver
- only not matching the receiver
- matching multiple receivers (family/multiple recipients)
- receiver and other person names are somewhat similar
- receiver and other person names are completely different
- receiver and other person names are very similar
- two persons with same name, so there is no correct answer

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
- correct_recipient_ids (Bool) # all found recipient ids match all recipient ids for the test_case in the TestRecipientSolutions table
- correct_best_image_id (Bool)
- model_test_id (Int, foreign key -> ModelTests.id)
- complete_response (Text)
- error_msg (Text)

### ModelTests
- id (Int, key)
- model (Int, foreign key -> Models.id)
- test_case_id (Int, foreign key -> TestCases.id)

### Models
- id (Int, key)
- name (Text) # llama3.2:1b, llama3.2:3b, llama4:scout, qwen3.5:9b(2b/4b/27b/35b/122b)
- family ("Qwen3" | "Llama")

### TestCases
- id (Int, key)
- letter_id (Int, foreign key -> Letters.id)
- image_selection ("ALL" | "PERFECT" |  "SLIGHTLY_BLURRED" | "VERY_BLURRED" | "CUT_OFF")
- household_id (Int, foreign key)

### Prompts
- (index)
- model ("Qwen3" | "Llama", foreign key -> Models.family)
- prompt (Text)

### TestCaseSolutionsCorrectRecipients
- test_case_id (Int, foreign key -> TestCases.id, not unique)
- recipient_id (Int, foreign key -> Images.id, not unique)

### Letters
- id (Int, key)
- format ("LETTER", "POSTCARD", "WINDOWED_LETTER")
- writing_style ("HAND", "PRINT", "CURSIVE")
- address (Text)
 
### Images
- id (Int, key)
- letter_id (Int, foreign key -> Letters.id)
- quality ("PERFECT" | "SLIGHTLY_BLURRED" | "VERY_BLURRED" | "CUT_OFF")
- image_path (Text)

## Prompts

### Qwen3

```
You are a mail sorting assistant specializing in physical letter delivery.

INPUTS:
- List of registered recipients in JSON format
- Images of the same mail piece (indexed from 0)

TASK:
1. Read the recipient name and address visible in the images
2. Identify which image shows the address most clearly
3. Match the name against the recipient list
4. Return a single JSON object

MATCHING INSTRUCTIONS:
- A match is valid if you can identify the recipient with reasonable certainty
- Accept approximate matches if you are confident it refers to the same person (e.g. handwriting ambiguity, abbreviated names, missing middle name, name order swapped, ...)
- If addressed to a household (e.g. "Familie Schneider"), include ALL recipients sharing that household_id
- If multiple recipients share the same name and there is no other clue to the correct one, include all of them
- "best_image_id" must be the 0-based index of the image that showed the address most clearly and completely or is most likely to be useful to a human viewer. Always provide this. 
- "fail_reason" must be empty string "" on success; on failure describe briefly why matching failed

---

EXAMPLE 1:

Images: [image 0 shows clearly: "Dr. Anna Müller, Hauptstraße 12, 76131 Karlsruhe"]

Recipients:
[{"recipient_id": 3, "household_id": 1, "email": "mueller@example.com", "firstname": "Anna", "middlename": "", "surname": "Müller", "title": "Dr.", "country": "DE", "zipcode": "76131", "city": "Karlsruhe", "street": "Hauptstraße", "house_number": "12"},
 {"recipient_id": 7, "household_id": 2, "email": "k.mueller@example.com", "firstname": "Klaus", "middlename": "", "surname": "Müller", "title": "", "country": "DE", "zipcode": "76131", "city": "Karlsruhe", "street": "Gartenweg", "house_number": "3"}]

Output:
{"success": true, "recipient_ids": [3], "best_image_id": 0, "fail_reason": ""}

EXAMPLE 2: 

Images: [image 0 is very blurred, image 1 shows partially: "Fam. Schneider, Rosenstr. 4, Berlin"]

Recipients:
[{"recipient_id": 11, "household_id": 5, "email": "schneider@example.com", "firstname": "Hans", "middlename": "", "surname": "Schneider", "title": "", "country": "DE", "zipcode": "10115", "city": "Berlin", "street": "Rosenstraße", "house_number": "4"},
 {"recipient_id": 12, "household_id": 5, "email": "schneider@example.com", "firstname": "Maria", "middlename": "", "surname": "Schneider", "title": "", "country": "DE", "zipcode": "10115", "city": "Berlin", "street": "Rosenstraße", "house_number": "4"}]

Output:
{"success": true, "recipient_ids": [11, 12], "best_image_id": 1, "fail_reason": ""}

EXAMPLE 3:

Images: [image 0 is completely blurred, image 1 shows only "76131 Karlsruhe"]

Recipients: [{"recipient_id": 5, ...}]

Output:
{"success": false, "recipient_ids": [], "best_image_id": 1,  "fail_reason": "address unreadable in all images"}

---

Recipients:
```

### Llama

```
You are a mail sorting assistant specializing in physical letter delivery.

INPUTS:
- List of registered recipients in JSON format
- Extracted text from images of the same mail piece (via OCR), each labeled with an image index

TASK:
1. Read the recipient name and address in the extracted text
2. Identify which image shows the address most clearly
3. Match the name against the recipient list
4. Return a single JSON object

MATCHING INSTRUCTIONS:
- A match is valid if you can identify the recipient with reasonable certainty
- Accept approximate matches if you are confident it refers to the same person (e.g. handwriting ambiguity, abbreviated names, missing middle name, name order swapped, ...)
- If addressed to a household (e.g. "Familie Schneider"), include ALL recipients sharing that household_id
- If multiple recipients share the same name and there is no other clue to the correct one, include all of them
- "best_image_id" must be the 0-based index of the image that showed the address most clearly and completely or is most likely to be useful to a human viewer. Always provide this. 
- "fail_reason" must be empty string "" on success; on failure describe briefly why matching failed

---

EXAMPLE 1:

Images: [image 0 shows clearly: "Dr. Anna Müller, Hauptstraße 12, 76131 Karlsruhe"]

Recipients:
[{"recipient_id": 3, "household_id": 1, "email": "mueller@example.com", "firstname": "Anna", "middlename": "", "surname": "Müller", "title": "Dr.", "country": "DE", "zipcode": "76131", "city": "Karlsruhe", "street": "Hauptstraße", "house_number": "12"},
 {"recipient_id": 7, "household_id": 2, "email": "k.mueller@example.com", "firstname": "Klaus", "middlename": "", "surname": "Müller", "title": "", "country": "DE", "zipcode": "76131", "city": "Karlsruhe", "street": "Gartenweg", "house_number": "3"}]

Output:
{"success": true, "recipient_ids": [3], "best_image_id": 0, "fail_reason": ""}

EXAMPLE 2: 

Images: [image 0 is very blurred, image 1 shows partially: "Fam. Schneider, Rosenstr. 4, Berlin"]

Recipients:
[{"recipient_id": 11, "household_id": 5, "email": "schneider@example.com", "firstname": "Hans", "middlename": "", "surname": "Schneider", "title": "", "country": "DE", "zipcode": "10115", "city": "Berlin", "street": "Rosenstraße", "house_number": "4"},
 {"recipient_id": 12, "household_id": 5, "email": "schneider@example.com", "firstname": "Maria", "middlename": "", "surname": "Schneider", "title": "", "country": "DE", "zipcode": "10115", "city": "Berlin", "street": "Rosenstraße", "house_number": "4"}]

Output:
{"success": true, "recipient_ids": [11, 12], "best_image_id": 1, "fail_reason": ""}

EXAMPLE 3:

Images: [image 0 is completely blurred, image 1 shows only "76131 Karlsruhe"]

Recipients: [{"recipient_id": 5, ...}]

Output:
{"success": false, "recipient_ids": [], "best_image_id": 1,  "fail_reason": "address unreadable in all images"}

---

Recipients:
```
