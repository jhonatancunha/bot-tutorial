import os
from flask import Flask, request
from github import Github, GithubIntegration

# https://smee.io/7dXBFbbaqeCdtxNl

app = Flask(__name__)

app_id = 184666

# Read the bot certificate
with open(
        os.path.normpath(os.path.expanduser('bot_key.pem')),
        'r'
) as cert_file:
    app_key = cert_file.read()

# Create an GitHub integration instance
git_integration = GithubIntegration(
    app_id,
    app_key,
)


def delete_branch_after_accepted_pr(repo, branch_name):
    branch = repo.get_git_ref("heads/%s" % branch_name)
    branch.delete()


def pr_accepted_event(repo, payload):
    pr = repo.get_issue(number=payload['pull_request']['number'])
    author = pr.user.login

    # is_first_pr = repo.get_issues(creator=author).totalCount

    # if is_first_pr == 1:
    response = f"Seu pull request foi aceito, @{author}! " \
        f"Obrigado por sua contribuição :smiling_face_with_three_hearts:"
    pr.create_comment(f"{response}")

    branch_name = payload['pull_request']['head']['ref']
    delete_branch_after_accepted_pr(repo, branch_name)


@app.route("/", methods=['POST'])
def bot():
    payload = request.json

    if not 'repository' in payload.keys():
        return "", 204

    owner = payload['repository']['owner']['login']
    repo_name = payload['repository']['name']

    git_connection = Github(
        login_or_token=git_integration.get_access_token(
            git_integration.get_installation(owner, repo_name).id
        ).token
    )
    repo = git_connection.get_repo(f"{owner}/{repo_name}")

    # Verifica se pull request foi aceito
    if all(k in payload.keys() for k in ['action', 'pull_request']) and payload['action'] == 'closed':
        if payload['pull_request']['merged']:
            pr_accepted_event(repo, payload)

    return "", 204


if __name__ == "__main__":
    app.run(debug=True, port=5000)
