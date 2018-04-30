import boto3, os, re, base64, json
from flask import Flask, render_template, request, redirect, url_for

#need this
app = Flask(__name__)
ddb = boto3.resource('dynamodb', region_name='us-east-1')
users = ddb.Table('users')
sessions = ddb.Table('sessions')

@app.route('/', methods=['GET'])
def home():
        return render_template('home.html')

@app.route('/login', methods=['POST'])
def login():
        response = users.get_item(Key={
                'username': request.form['username']
        })
        if 'Item' in response:
                item = response['Item']
                if item and item['password'] == request.form['password']:
                        rand = os.urandom(6)
                        rand = base64.b64encode(rand).decode('utf-8')
                        sessions.put_item(
                                Item={'sid': rand,
                                      'username':request.form['username']})
                        return redirect(url_for('user', sid = rand,
                                username=request.form['username'],
                        ))
        return redirect(url_for('home'))


@app.route('/user/<username>/<sid>', methods=['GET'])
def user(username, sid):
        response = sessions.get_item(Key={'sid':sid})
        if 'Item' in response:
                item = response['Item']
                if item and item['username'] == username:
                        response = users.get_item(Key={'username': username})
                        item=response['Item']
                        return render_template('user.html',
                                        sid = sid,
                                        username = username,
                                containers=json.loads(item['containers']))
        return redirect(url_for('home'))

@app.route('/logout/<sid>', methods=['POST'])
def logout(sid):
        #not secure b/c anyone can get logged out by someone
        response = sessions.delete_item(Key={'sid':sid})
        return redirect(url_for('home'))

@app.route('/register', methods=['GET','POST'])
def register():
        if request.method == 'GET':
                return render_template("register.html")
        else:
                username = request.form['username']
                password = request.form['password']
                response = users.get_item(Key={'username':username})
                if 'Item' not in response:
                        users.put_item(Item={
                                'username':username,
                                'password':password,
                                'nextid': '0',
                                'containers': "{}"})
                        return redirect(url_for('home'))
                else:
                        return redirect(url_for('register'))
                
@app.route('/remove/container/<username>/<sid>', methods=['POST'])
def removecontainer(username,sid):
        id = request.form['id']
        response = users.get_item(Key={'username':username})
        if 'Item' in response:
                item = response['Item']
                containers = json.loads(item['containers'])
                #lambda stuff here eventually
                del containers[id]
                users.update_item(Key={
                        'username':username
                },UpdateExpression='SET containers = :c',
                ExpressionAttributeValues={
                        ':c':json.dumps(containers),
                })
                return redirect(url_for('user', username=username, sid=sid))
                
        return redirect(url_for('home'))


                

@app.route('/add/container/<username>/<sid>', methods=['POST'])
def addcontainer(username,sid):
        response = users.get_item(Key={'username':username})
        if 'Item' in response:
                item = response['Item']
                containers = json.loads(item['containers'])
                next_id = int(item['nextid'])
                #lambda stuff here eventually
                containers[str(next_id)] = \
                "http://ec2-52-207-232-241.compute-1.amazonaws.com:5000"

                users.update_item(Key={
                        'username':username
                },UpdateExpression='SET containers = :c, nextid = :i',
                ExpressionAttributeValues={
                        ':c':json.dumps(containers),
                        ':i':(next_id+1)
                })
                return redirect(url_for('user', username=username, sid=sid))
                
        return redirect(url_for('home'))


        
#need this
if __name__ == '__main__':
        app.run(debug=True, host='0.0.0.0', port=80)
