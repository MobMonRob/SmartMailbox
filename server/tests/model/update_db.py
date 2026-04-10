import sqlite3
from typing import List

from server.tests.model.db.api import get_image_id
from server.tests.model.db.model import TestCase, ModelResponse, ModelAnswerCheck, ImageSelection, ImageQuality
from server.tests.model.model_tests_framework import get_image_paths_and_ids

# Path to the SQLite database file
DATABASE_PATH = 'C:/Programming/studienarbeit/SmartMailbox/server/app/db/database.db'

def check_response(model_response: str, test_case: TestCase, image_ids: List[int]) -> ModelAnswerCheck:
    try:
        response = ModelResponse.model_validate_json(model_response)
    except Exception as e:
        return ModelAnswerCheck(
            match_found=False,
            correct_recipient_ids=False,
            correct_image_id=False,
            error_msg=f"JSON/Schema Error: {e}",
        )

    errors = []

    # Check Recipient IDs
    recipient_err = check_recipient_ids(response.recipient_ids)
    if recipient_err:
        err = f"Error at correct recipients ID check: {recipient_err}"
        errors.append(err)

    # Check Image ID
    image_err = check_image_id(image_ids, test_case, response.best_image_id)
    if image_err:
        err = f"Error at correct image ID check: {image_err}"
        errors.append(err)

    if not response.success and not response.fail_reason:
        err = "Model failed but provided no reason."
        errors.append(err)

    return ModelAnswerCheck(
        match_found=response.success,
        correct_recipient_ids=not bool(recipient_err),
        correct_image_id=not bool(image_err),
        error_msg="\n".join(errors),
    )

def check_recipient_ids(recipient_ids: List[int]) -> str:
    correct_ids = [6]

    if len(correct_ids) != len(recipient_ids):
        if len(recipient_ids) == 0:
            return f"No recipient IDs provided. Expected {len(correct_ids)} ({correct_ids})"
        else:
            return f"Expected {len(correct_ids)} recipient IDs ({correct_ids}), but got {len(recipient_ids)}: {recipient_ids}"

    recipient_ids.sort()

    if recipient_ids == correct_ids:
        return ""

    return f"Provided recipient IDs do not match correct ids: {recipient_ids} != {correct_ids}"


def check_image_id(image_ids: List[int], test_case: TestCase, image_idx: int) -> str:
    """
    Check if the image idx in the response matches the solution of the test case.

    :param image_ids: The IDs of the images to check.
    :param test_case: The test case.
    :param image_idx: The idx of the image to check.
    :return: Empty string if correct, else an error message.
    """
    try:
        image_id = image_ids[image_idx]
    except IndexError:
        return f"Image idx is out of range of image paths: {image_idx} >= {len(image_ids)}"

    if test_case.image_selection == ImageSelection.ALL:
        # best image is image quality PERFECT
        correct_image_id = get_image_id(test_case.letter_id, ImageQuality.PERFECT)
    else:
        # best image is the image quality equal to test_case.image_selection
        quality = test_case.image_selection.value

        assert isinstance(quality, str)

        correct_image_id = get_image_id(test_case.letter_id, ImageQuality[quality])

    if image_id == correct_image_id:
        return ""

    return f"Provided image ID does not match correct image ID: {image_id} != {correct_image_id}"

def update_database():
    """
    Updates the database to correct the recipient_id for Olaf's letters.
    """
    try:
        # Connect to the SQLite database
        con = sqlite3.connect(DATABASE_PATH)
        con.row_factory = sqlite3.Row
        cursor = con.cursor()

        # 1. Get all letter_ids for Olaf's address
        olaf_address = "Olaf Jürgen Schmidt\\nGoethestraße 42b\\n70176 Stuttgart\\nDeutschland"
        cursor.execute("SELECT id FROM letters WHERE address = ?", [olaf_address])
        letter_ids = [row["id"] for row in cursor.fetchall()]
        print(f"Found {len(letter_ids)} letter_ids for Olaf's address: {letter_ids}")

        if not letter_ids:
            print("No letters found for Olaf's address. No updates needed.")
            return

        # 2. Get all test_case_ids for the letter_ids
        placeholders = ','.join('?' for _ in letter_ids)
        cursor.execute(f"SELECT id FROM test_cases WHERE letter_id IN ({placeholders})", letter_ids)
        test_case_ids = [row["id"] for row in cursor.fetchall()]
        print(f"Found {len(test_case_ids)} test_case_ids: {test_case_ids}")

        if not test_case_ids:
            print("No test cases found for the letters. No updates needed.")
            return

        # 3. Update recipient_id in test_case_solutions_correct_recipients
        placeholders = ','.join('?' for _ in test_case_ids)
        cursor.execute(f"UPDATE test_case_solutions_correct_recipients SET recipient_id = 6 WHERE test_case_id IN ({placeholders}) AND recipient_id = 7", test_case_ids)
        print(f"{cursor.rowcount} rows updated in test_case_solutions_correct_recipients.")

        # 4. Get all model_test_ids for the test_case_ids
        placeholders = ','.join('?' for _ in test_case_ids)
        cursor.execute(f"SELECT id FROM model_tests WHERE test_case_id IN ({placeholders})", test_case_ids)
        model_test_ids = [row["id"] for row in cursor.fetchall()]
        print(f"Found {len(model_test_ids)} model_test_ids: {model_test_ids}")

        if not model_test_ids:
            print("No model tests found for the test cases. No further updates needed.")
            con.commit()
            con.close()
            return

        # 5. Recheck and update all results in model_test_results
        placeholders = ','.join('?' for _ in model_test_ids)
        cursor.execute(f"SELECT model_test_id, complete_response FROM model_test_results WHERE model_test_id IN ({placeholders})", model_test_ids)

        updates_to_perform = []
        for model_test_id, complete_response in cursor.fetchall():
            test_case_id = cursor.execute("SELECT test_case_id FROM model_tests WHERE id = ?", [model_test_id]).fetchone()["test_case_id"]
            test_case = cursor.execute("select * from test_cases where id = ?", [test_case_id]).fetchone()
            test_case = TestCase(id=test_case["id"], letter_id=test_case["letter_id"], image_selection=ImageSelection(test_case["image_selection"]), household_id=test_case["household_id"])
            _, image_ids = get_image_paths_and_ids(test_case.letter_id, test_case.image_selection)
            model_answer_check = check_response(complete_response, test_case, image_ids)

            # print(test_case_id, test_case, image_ids, model_answer_check)
            updates_to_perform.append([model_answer_check.correct_recipient_ids,model_answer_check.correct_image_id , model_answer_check.error_msg, model_test_id ])

        # print(updates_to_perform)

        cursor.executemany("UPDATE model_test_results SET correct_recipient_ids = ?, correct_best_image_id = ?, error_msg = ? WHERE model_test_id = ?", updates_to_perform)
        print(f"{cursor.rowcount} rows updated in model_test_results.")

        # Commit the changes and close the connection
        con.commit()
        con.close()
        print("Database update complete.")

    except sqlite3.Error as e:
        print(f"Database error: {e}")
    except Exception as e:
        print(f"An error occurred: {e}")

if __name__ == '__main__':
    update_database()
