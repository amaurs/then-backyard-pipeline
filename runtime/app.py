from chalice import Chalice


app = Chalice(app_name='then-backyard-pipeline')


@app.route('/hello/{username}', methods=['GET'])
def get_user(username):
    return {"hello": username}
