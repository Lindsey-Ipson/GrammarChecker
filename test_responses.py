

from errors import generate_api_response, isolate_errors_from_api_response, add_grammar_errors_to_db, generate_grammar_errors_html

user_text_1 = "Good work over week. Everyone on the team does a good job this past Wendsday. Please sent all of the expense report to my email address by tomorow. Tell Mike to sends me next weeks’ meeting aginda as well."

user_text_2 = "Mary bake delicious Cookies for her friends' every weekend. Yesterday she buy the ingredients. Her friends cannot waits to eat those."

user_text_3 = "The school principle announced a new initiative to improve student's performance in math and science. He's confident that this program will led to higher test scores and will prepares students for future challenge."

# print(generate_api_response(user_text_1))
# print(generate_api_response(user_text_2))
# print(generate_api_response(user_text_3))

api_response = generate_api_response(user_text_1)
print('api_response', api_response)

grammar_errors_list = isolate_errors_from_api_response(api_response, 'grammar')

print('grammar errors', grammar_errors_list)
# print('spelling errors', isolate_errors_from_api_response(api_response, 'spelling')) 

# print('add_grammar_errors_to_db(grammar_errors_list)', add_grammar_errors_to_db(grammar_errors_list))



# print('generate_html(grammar_errors_list)', generate_html(grammar_errors_list))

# edited = apply_corrections(text, corrections)

# print('edited', edited)






def apply_all_corrections(text, corrections):
    sorted_corrections = sorted(corrections, key=lambda x: x['start'])
    corrected_text_parts = []
    current_index = 0
    
    for correction in sorted_corrections:
        sentence_start = correction['sentence_start']
        start = correction['start'] - sentence_start
        end = correction['end'] - sentence_start
        replacement = correction['replacement']
        
        corrected_text_parts.append(text[current_index:sentence_start + start])
        corrected_text_parts.append(replacement)
        current_index = sentence_start + end + 1
    
    corrected_text_parts.append(text[current_index:])
    return ''.join(corrected_text_parts)

# Example text
original_text = "My name is Jay Hammond I am a firefighter. I live in 128 Pine Lane, in Jackson, Mississippi.  I have two childs. One is a girl named Clair. The other  is boy named Thatcher. His name after my father. I also have a wife named Jenna. She is beutiful. She has long, dark, soft hair. We also got a dog named Buck. He is very obedient but sometimes he barks at night and it upsets our neighbors!"

# Example corrections
edits = {
    "edits": [
        {
            "end": 24,
            "error_type": "M:CONJ",
            "general_error_type": "Grammar",
            "id": "a89bcd63-e00b-5bfc-a75b-a7e619c57b77",
            "replacement": " and I",
            "sentence": "My name is Jay Hammond I am a firefighter.",
            "sentence_start": 0,
            "start": 23
        },
        {
            "end": 24,
            "error_type": "R:NOUN:POSS",
            "general_error_type": "Grammar",
            "id": "f772ad16-8a20-5ddc-8f02-04a7773442ae",
            "replacement": "in",
            "sentence": "I live in 128 Pine Lane, in Jackson, Mississippi.",
            "sentence_start": 29,
            "start": 39
        },
        # ... other corrections ...
    ]
}

corrections = edits['edits']

corrected_text = apply_corrections(original_text, corrections)
print(corrected_text)
