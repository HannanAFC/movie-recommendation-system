import pandas as pd
from flask import request, jsonify
from flask_jwt_extended import jwt_required, current_user, get_jwt_identity
from app.main import bp
from app.utils import sanitise_form_inputs, read_current_dataset
from app import dataset_manager, SOCKET_NAMESPACE, socketio, db
from app import tmdb_service, movie_search_service, initialise_recommender
import time
from datetime import datetime, timezone

@bp.route("/tmdb-api-key", methods=["POST"])
@jwt_required()
def set_tmdb_api_key():
    values = sanitise_form_inputs(request=request, fields=["api_key"])
    api_key = values["api_key"]

    if not api_key:
        return jsonify({
            "error": "Please enter a TMDB API key."
            }), 422

    is_valid = tmdb_service.validate_api_key(api_key)

    if not is_valid:
        current_user.tmdb_api_key_valid = False
        db.session.commit()
        return jsonify({
            "error": "Invalid TMDB API key."
            }), 422

    current_user.tmdb_api_key = api_key
    current_user.tmdb_api_key_valid = True
    current_user.tmdb_api_key_last_validated_at = datetime.now(timezone.utc)
    db.session.commit()

    tmdb_status = {
        "api_key_set": current_user.tmdb_api_key is not None,
        "api_key_valid": current_user.tmdb_api_key_valid,
        "api_key_last_validated_at": (
            current_user.tmdb_api_key_last_validated_at.isoformat()
            if current_user.tmdb_api_key_last_validated_at is not None
            else None
        )
    }

    return jsonify({
        "message": "TMDB API key saved successfully.",
        "tmdb": tmdb_status
        }), 200

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
    from flask import current_app
    app = current_app._get_current_object()

    values = sanitise_form_inputs(request=request, fields=["dataset"])
    dataset = values["dataset"]

    # Validate dataset
    valid_dataset = any(d["identifier"] == dataset for d in dataset_manager.downloadable_datasets())

    if not valid_dataset:
        return jsonify({"error": "Please select a valid dataset."}), 400

    dataset_identifier = next(
        (d["identifier"] for d in app.config["DATASET_URLS"] if d["identifier"] == dataset),
        None
    )

    if not dataset_identifier:
        return jsonify({"error": "Error selecting dataset."}), 500

    # Capture user_id BEFORE thread
    username = get_jwt_identity()
    last_emit_time = time.time()
    emit_interval = 0.25

    movies_path = app.config["MOVIES_PATH"]
    links_path = app.config["LINKS_PATH"]
    current_dataset_id_path = app.config["CURRENT_DATASET_PATH"]

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

    def run_download(app):
        socketio.emit("datasets_download_start",{"data": "Download starting"}, namespace=SOCKET_NAMESPACE, to=f"user_{username}")

        socketio.sleep(0)

        dataset_manager.download_dataset(dataset_identifier, progress_cb)
        movies = pd.read_csv(movies_path)
        links = pd.read_csv(links_path)
        current_dataset_id = read_current_dataset(current_dataset_id_path)
        movie_search_service.initialise_from_storage(movies, links, current_dataset_id)
        with app.app_context():
            app.extensions["movie_search_status"] = movie_search_service.get_status()
            initialise_recommender(app)
        socketio.emit("datasets_download_finish",{"data": "Download finished"}, namespace=SOCKET_NAMESPACE, to=f"user_{username}")
      
    socketio.start_background_task(run_download, app)

    return jsonify({"message": "Dataset download started successfully."}), 200