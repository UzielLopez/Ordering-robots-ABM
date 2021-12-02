import uuid

from flask import Flask, request
from flask.json import jsonify
from flask_restful import Api

from Simulation.main import Warehouse

app = Flask(__name__)
api = Api(app)

simulations = {}

@app.route("/createModel", methods=["POST"])
def create():
    k = int(request.form.get("numberOfBoxes", 1))
    m = int(request.form.get("columns", 6))
    n = int(request.form.get("rows", 6))
    time_limit = int(request.form.get("timeLimit", 100))
    id = str(uuid.uuid4())
    simulations[id] = Warehouse(k, m, n, time_limit)
    return "ok", 201, {"Location": "/step/"+str(id), "IdsForAgents": simulations[id].ids_by_agent_type}

@app.route("/step/<id>", methods=["GET"])
def next_step(id):

        if id in simulations:
            warehouse = simulations[id]
            state = jsonify(warehouse.state)
            warehouse.step()
            return state
                
        return 'error: No valid simulation with given id', 404

app.run(threaded=True)