global_user_id = []


def set_user_id(new_value):
    global global_user_id
    global_user_id.append(new_value)


def remove_user_id(value_to_remove):
    global global_user_id
    if value_to_remove in global_user_id:
        global_user_id.remove(value_to_remove)
