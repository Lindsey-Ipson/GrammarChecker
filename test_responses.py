from errors import generate_api_response

user_text_1 = "Good work over week. Everyone on the team does a good job this past Wendsday. Please sent all of the expense report to my email address by tomorow. Tell Mike to sends me next weeks’ meeting aginda as well."

user_text_2 = "Mary bake delicious Cookies for her friends' every weekend. Yesterday she buy the ingredients. Her friends cannot waits to eat those."

user_text_3 = "The school principle announced a new initiative to improve student's performance in math and science. He's confident that this program will led to higher test scores and will prepares students for future challenge."

print(generate_api_response(user_text_1))
print(generate_api_response(user_text_2))
print(generate_api_response(user_text_3))