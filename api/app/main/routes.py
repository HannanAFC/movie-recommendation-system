from flask import request, jsonify, current_app
from flask_jwt_extended import jwt_required, current_user, verify_jwt_in_request, get_jwt_identity
from app.main import bp
from app.utils import sanitise_form_inputs
from app import dataset_manager, SOCKET_NAMESPACE, socketio
import time

@bp.route("/datasets-available", methods=["GET"])
def get_available_datasets():
    datasets = dataset_manager.downloadable_datasets()
    datasets_dicts = []
    for dataset in datasets:
        datasets_dicts.append({
            "identifier": dataset["identifier"],
            "name": dataset["client_name"]
        })

    if len(datasets_dicts) == 0:
        return jsonify({"error": "Error finding datasets."}), 500
    else:
        return datasets_dicts, 200


@bp.route("/datasets-select", methods=["POST"])
@jwt_required()
def select_dataset():
    values = sanitise_form_inputs(request=request, fields=["dataset"])
    dataset = values["dataset"]

    # Validate dataset
    valid_dataset = any(d["identifier"] == dataset for d in dataset_manager.downloadable_datasets())

    if not valid_dataset:
        return jsonify({"error": "Please select a valid dataset."}), 400

    dataset_url = next(
        (d["url"] for d in current_app.config["DATASET_URLS"] if d["identifier"] == dataset),
        None
    )

    if not dataset_url:
        return jsonify({"error": "Error selecting dataset."}), 500

    # Capture user_id BEFORE thread
    username = get_jwt_identity()
    last_emit_time = time.time()
    emit_interval = 0.25

    def progress_cb(blocknum: int, blocksize: int, totalsize: int):
        nonlocal last_emit_time
        readed_data = blocknum * blocksize
        if totalsize > 0:
            download_percentage = min(readed_data * 100 / totalsize, 100)
            current_time = time.time()
            if current_time - last_emit_time >= emit_interval:
                socketio.emit('datasets_download_progress', {'data': f"Download progress: {download_percentage}%", "download_percentage": download_percentage}, namespace=SOCKET_NAMESPACE, to=f"user_{username}")
                last_emit_time = current_time
                socketio.sleep(0)

    def run_download():
        socketio.emit("datasets_download_start",{"data": "Download starting"}, namespace=SOCKET_NAMESPACE, to=f"user_{username}")

        socketio.sleep(0)

        dataset_manager.download_dataset(dataset_url, progress_cb)
        socketio.emit("datasets_download_finish",{"data": "Download finished"}, namespace=SOCKET_NAMESPACE, to=f"user_{username}")


    socketio.start_background_task(run_download)

    return jsonify({"message": "Dataset download started successfully."}), 200