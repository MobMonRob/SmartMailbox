# Image processing

# Input

- prompt = "" 
- images/image_texts = []
- user_data = [{"name": "", "surname": "", "address": "", "id": 0, }] # TODO : define user data

# Returns

## SUCCESS 
- number of best image
- ID of best user match or multiple IDs 
- message for user about mail details

## FAIL 
- literal "FAIL"
- reason for failure # TODO for each household a default mail for failed operations

## Definition SUCCESS vs FAIL

### SUCCESS
- found match
- found multiple matches

### FAIL
- cannot read text
- cannot find match for text with certainty > ? % # TODO test certainty level, also configurable

# Testing
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

## Images
mail types: postcard, letter, letter with window
writing: printed, handwriting, cursive handwriting
receivers: one, family, multiple
image qualities: perfect, slightly blurred, flash visible, very blurred, cut off

## User Data
- only matching the receiver
- only not matching the receiver
- matching multiple receivers (family/multiple recipients)
- receiver and other person names are somewhat similar
- receiver and other person names are completely different
- receiver and other person names are very similar
- two persons with same name, so there is no correct answer # TODO What should be the correct answer if two perople have the same name