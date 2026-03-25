# --- routes.py (FIXED) ---

from flask import request, jsonify, current_app
from flask_jwt_extended import jwt_required, current_user, verify_jwt_in_request, get_jwt_identity
from app.main import bp
from app.utils import sanitise_form_inputs
from app import dataset_manager, socketio
from flask_socketio import disconnect, join_room

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
    user_id = current_user.id
    print(f"=============UserID: {current_user.id}=============")

    print

    def progress_cb(blocknum: int, blocksize: int, totalsize: int):
        readed_data = blocknum * blocksize
        if totalsize > 0:
            download_percentage = min(readed_data * 100 / totalsize, 100)

            socketio.emit(
                'progress_update',
                {
                    'message': 'Downloading...',
                    'download_percentage': download_percentage
                },
                namespace='/api/datasets-download-progress',
                room=user_id
            )
            print(f"Download progress: {download_percentage}%")
        else:
            print("Download complete")

    def run_download():
        dataset_manager.download_dataset(dataset_url, progress_cb)
        print("Download complete")

        # Emit completion
        socketio.emit(
            'progress_complete',
            {'message': 'Download complete', 'download_percentage': 100},
            namespace='/api/datasets-download-progress',
            room=user_id
        )

    from threading import Thread
    Thread(target=run_download, daemon=True).start()

    return jsonify({"message": "Dataset download started successfully."}), 200


# --- SOCKET EVENTS ---

@socketio.on('connect', namespace='/api/datasets-download-progress')
def handle_connect():
    try:
        verify_jwt_in_request()
    except Exception:
        disconnect()
        return
    if not current_user:
        disconnect()
        return

    # Join a room based on user_id
    print(f"=============UserID: {current_user.id}=============")
    join_room(current_user.id)


@socketio.on('disconnect', namespace='/api/datasets-download-progress')
def handle_disconnect():
    pass