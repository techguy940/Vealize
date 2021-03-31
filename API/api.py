from flask import Flask
import requests
from flask import request, jsonify
from flask_cors import CORS
import dateutil.parser
import wolframalpha
import urllib.parse
import json
# import waitress

client = wolframalpha.Client('appID')

app = Flask(__name__)
CORS(app)

token = "token"

headers = {"Accept": "application/vnd.github.v3+json",
            "Authorization": f"token {token}"}
BASE_URL = "https://api.github.com"

iframes = {}
iframes['python'] = 'http://pythontutor.com/iframe-embed.html#code={}&codeDivHeight=400&codeDivWidth=350&cumulative=false&curInstr=0&heapPrimitives=nevernest&origin=opt-frontend.js&py=3&rawInputLstJSON=%5B%5D&textReferences=false'

iframes['javascript'] = 'http://pythontutor.com/iframe-embed.html#code={}&codeDivHeight=400&codeDivWidth=350&cumulative=false&curInstr=0&heapPrimitives=nevernest&origin=opt-frontend.js&py=js&rawInputLstJSON=%5B%5D&textReferences=false'

iframes['c'] = 'http://pythontutor.com/iframe-embed.html#code={}&codeDivHeight=400&codeDivWidth=350&cumulative=false&curInstr=1&heapPrimitives=nevernest&origin=opt-frontend.js&py=c_gcc9.3.0&rawInputLstJSON=%5B%5D&textReferences=false'

iframes['c++'] = 'http://pythontutor.com/iframe-embed.html#code={}&codeDivHeight=400&codeDivWidth=350&cumulative=false&curInstr=0&heapPrimitives=nevernest&origin=opt-frontend.js&py=cpp_g%2B%2B9.3.0&rawInputLstJSON=%5B%5D&textReferences=false'


@app.route("/github/<username>/<repo>")
def github(username, repo):
    r = requests.get(BASE_URL + f"/repos/{username}/{repo}", headers=headers).json()
    if r.get('private') or r.get("message") == "Not Found":
        return jsonify({"success": False, "error": r})
    data = {}
    data['archived'] = r['archived']
    brances_data = requests.get(r['branches_url'].replace("{/branch}", ""), headers=headers).json()
    data['branchesCount'] = len(brances_data)
    commits_data = requests.get(r['commits_url'].replace("{/sha}", ""), headers=headers).json()
    data['commitsCount'] = len(commits_data)
    contributors_data = requests.get(r['contributors_url'], headers=headers).json()
    data['contributors'] = {}
    for i in contributors_data:
        data['contributors'][i['login']] = i['contributions']
    data['contributorsCount'] = len(contributors_data)
    data['createdAt'] = r['created_at'].replace("T", " ")[:-4]
    data['defaultBranch'] = r['default_branch']
    data['description'] = r['description'] or "No Description Provided"
    data['isForked'] = r['fork']
    data['forksCount'] = r['forks_count']
    # forks_data = requests.get(r['forks_url'], headers=headers).json()
    # data['forks'] = {}
    # for i in forks_data:
    #   date = i['created_at'][:10]
    #   if date in data['forks']:
    #       data['forks'][date] += 1
    #   else:
    #       data['forks'][date] = 1
    issues_data = requests.get(r['issue_events_url'].replace("{/number}", ""), headers=headers).json()
    data['issuesCount'] = len(issues_data)
    # data['issues'] = {"closed": 0, "opened": 0}
    # for i in issues_data:
    #   if i['issue']['state'] == 'closed':
    #       data['issues']['closed'] += 1
    #   else:
    #       data['issues']['opened'] += 1
    # for i in issues_data:
    #   date = i['created_at'][:10]
    #   if date in data['issues']:
    #       data['issues'][date] += 1
    #   else:
    #       data['issues'][date] = 1
    # data['languages'] = {}
    # languages_data = requests.get(r['languages_url'], headers=headers).json()
    # total = sum(list(languages_data.values()))
    # for i in languages_data:
    #   data['languages'][i] = str(round(languages_data[i]*100/total, 2)) + "%"
    data['name'] = r['name']
    data['owner'] = {}
    data['owner']['name'] = r['owner']['login']
    data['owner']['avatarUrl'] = r['owner']['avatar_url']
    data['private'] = r['private']
    data['stargazers'] = r['stargazers_count']
    data['url'] = r['url']
    data['success'] = True
    return jsonify(data)

@app.route("/githubGraph/<username>/<repo>")
def github_graph(username, repo):
    r = requests.get(BASE_URL + f"/repos/{username}/{repo}", headers=headers).json()
    if r.get('private') or r.get("message") == "Not Found":
        return jsonify({"success": False, "error": r})
    data = {}
    forks_data = requests.get(r['forks_url'], headers=headers).json()
    data['forks'] = {}
    for i in forks_data:
        date = i['created_at'][:10]
        if date in data['forks']:
            data['forks'][date] += 1
        else:
            data['forks'][date] = 1
    data['issues'] = {}
    issues_data = requests.get(r['issue_events_url'].replace("{/number}", ""), headers=headers).json()
    for i in issues_data:
        date = i['created_at'][:10]
        if date in data['issues']:
            data['issues'][date] += 1
        else:
            data['issues'][date] = 1
    data['languages'] = {}
    languages_data = requests.get(r['languages_url'], headers=headers).json()
    total = sum(list(languages_data.values()))
    for i in languages_data:
        data['languages'][i] = str(round(languages_data[i]*100/total, 2))
    return jsonify(data)

@app.route("/calc/<eq>")
def math(eq):
    res = client.query(eq.strip(), params=(("format", "image,plaintext"),))
    data = {}
    for p in res.pods:
        for s in p.subpods:
            if s.img.alt.lower() == "root plot":
                data['rootPlot'] = s.img.src
            elif s.img.alt.lower() == "number line":
                data['numberLine'] = s.img.src
    data['results'] = [i.texts for i in list(res.results)][0]
    return jsonify(data)

@app.route("/code/<lang>", methods=["POST", "GET"])
def viz_code(lang):
    code = request.form['code']
    if lang not in list(iframes.keys()):
        return jsonify({"Error": "Not Supported"})
    # print(code)
    code = code.replace("<br>", "\n")
    code = urllib.parse.quote_plus(code)
    # print(code)
    # print(iframes[lang].format(code))
    # return jsonify({"link": "http://pythontutor.com/iframe-embed.html#code=def%20hi():%20%20%20%20print('hi')hi()&codeDivHeight=400&codeDivWidth=350&cumulative=false&curInstr=0&heapPrimitives=nevernest&origin=opt-frontend.js&py=3&rawInputLstJSON=%255B%255D&textReferences=false"})
    return jsonify({"link": iframes[lang].format(code)})

@app.route("/contact", methods=["GET", "POST"])
def contact():
    name, email, msg = request.form.get("name", "No Name Provided")[:50], request.form.get("email", "No Email Provided")[:70], request.form.get("msg", "No Message Provided")[:200]
    with open("data.json") as f:
        data = json.load(f)
    data[email] = {}
    data[email]['name'] = name
    data[email]['msg'] = msg
    with open("data.json", "w") as f:
        json.dump(data, f, indent=4)
    return jsonify({})

@app.route("/getData", methods=["POST", "GET"])
def get_data():
    tok = request.form.get("token", None)
    if not tok:
        return jsonify({})
    if tok == 'secret':
        with open("data.json") as f:
            data = json.load(f)
        return jsonify(data)
    else:
        return jsonify({})
app.run(debug=True)

# waitress.serve(app, host = "0.0.0.0", port = 1351)
