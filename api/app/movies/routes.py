from flask import request, jsonify
import sqlalchemy as sa
from flask_jwt_extended import jwt_required, current_user
from app import dataset_manager, tmdb_service, movie_search_service
from app.movies import bp
from app.extensions import db
from app.utils import sanitise_form_inputs
from app.models import LikedMovie

@bp.route("/search", methods=["GET"])
@jwt_required()
def search_movies():
    query = (request.args.get("q") or "").strip()
    limit = int(request.args.get("limit", 10))

    if not query:
        return jsonify({"error": "Search query required."}), 422

    if not dataset_manager.dataset_exists():
        return jsonify({"error": "No dataset is currently installed."}), 409

    if movie_search_service is None or not movie_search_service.is_ready:
        return jsonify({"error": "Movie search is not ready."}), 503

    tmdb_enrichment_available = bool(
        current_user.tmdb_api_key and current_user.tmdb_api_key_valid
    )

    results = movie_search_service.search_and_enrich(
        query=query,
        limit=limit,
        api_key=current_user.tmdb_api_key if tmdb_enrichment_available else None,
        tmdb_service=tmdb_service
    )

    return jsonify({
        "results": results,
        "query": query,
        "tmdb_enrichment_available": tmdb_enrichment_available
    }), 200

@bp.route("/like", methods=["POST, DELETE"])
@jwt_required()
def like_movie(movie_id):
    values = sanitise_form_inputs(request=request, fields=["movie_id"])
    movie_id = values["movie_id"]

    if not movie_id:
        return jsonify({
                "error": "Please provide a movie ID."
            }), 422
    
    try:
        movie_id = int(movie_id)
    except ValueError:
        return jsonify({
            "error": "Invalid movie ID."
        })
    
    if movie_search_service == None and movie_search_service.is_ready:
        return jsonify({
            "error": "Movie search service is not ready."
        })
    
    if movie_search_service.movie_exists(movie_id) == False:
        return jsonify({
            "error": "Movie is not in the current dataset."
        })
    
    already_liked = db.session.scalar(
        sa.select(LikedMovie).where(
            LikedMovie.rating_author == current_user,
            LikedMovie.movie_id == str(movie_id)
        )
    )

    if already_liked != None:
        return jsonify({
            "error": "Movie already liked."
        })
    
    liked_movie = LikedMovie(
        movie_id=movie_id,
        rating_author=current_user
    )

    db.session.add(liked_movie)
    db.session.commit()

    needs_to_select_movies = len(current_user.get_user_ratings()) == 0 and len(current_user.get_liked_movies()) < 5

    return jsonify({
        "message": "Movie has been liked successfully.",
        "needs_to_select_movies": needs_to_select_movies
    }), 200