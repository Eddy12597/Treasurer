from flask import Flask, request
from flask_cors import CORS
import budget_proposal
from version import get_version_info

app = Flask(__name__)

CORS(app, expose_headers=['Content-Disposition', 'Content-Type'])


@app.route('/')
def index():
    version_info = get_version_info()
    return f"Backend is running! Use /submit-budget-proposal to submit.\n\n{version_info}"


@app.route('/submit-budget-proposal', methods=['POST'])
def handle_submit_budget_proposal():
    data = request.form
    prop = budget_proposal.BudgetProposal.from_dict(data)
    return 'Success', 200

# if __name__ == "__main__":
#     app.run(debug=True)